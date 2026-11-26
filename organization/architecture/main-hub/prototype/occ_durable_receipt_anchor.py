"""Durable local fixture authority, stored separately from OCC receipt journals."""

from collections.abc import Mapping
from contextlib import closing
from dataclasses import astuple, dataclass, replace
from datetime import datetime, timedelta
from hashlib import sha256
import hmac
import json
import re
from pathlib import Path
import sqlite3

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from occ_publisher_enrollment import verify_publisher_enrollment
from occ_receipt_anchor import ReceiptCheckpoint, custody_digest


_APPROVAL_DOMAIN = b"daivora.occ.custody-transition/synthetic-v1\x00"
_MAX_APPROVAL_TTL = timedelta(minutes=10)
_REPAIR_DOMAIN = b"daivora.occ.pending-receipt-repair/synthetic-v1\x00"
_MAX_REPAIR_TTL = timedelta(minutes=5)


def _utc(value):
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0) or value.microsecond:
        raise ValueError("custody approval requires UTC whole-second timestamps")
    return value


@dataclass(frozen=True)
class CustodyAuthorization:
    issued_at: datetime
    expires_at: datetime
    signature: bytes


def _checkpoint_fields(checkpoint):
    fields = astuple(checkpoint)
    return fields[:-1] if checkpoint.witnessed_enrollment_sha256 is None else fields


def pending_repair_bytes(local, anchored, wire_sha256, *, issued_at, expires_at):
    """Bind independent permission to repair one exact missing local receipt."""
    issued, expires = _utc(issued_at), _utc(expires_at)
    if (
        not timedelta(0) < expires - issued <= _MAX_REPAIR_TTL
        or not isinstance(wire_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", wire_sha256)
        or anchored.witnessed_enrollment_sha256 is None
        or anchored.count != local.count + 1
        or replace(local, count=anchored.count, head_sha256=anchored.head_sha256) != anchored
    ):
        raise ValueError("witnessed repair scope or approval window is invalid")
    record = [astuple(local), astuple(anchored), wire_sha256, issued.isoformat(), expires.isoformat()]
    return _REPAIR_DOMAIN + json.dumps(record, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def custody_transition_bytes(expected, replacement, *, issued_at, expires_at):
    """Bind approval to the exact current checkpoint, replacement and window."""
    issued, expires = _utc(issued_at), _utc(expires_at)
    if not timedelta(0) < expires - issued <= _MAX_APPROVAL_TTL:
        raise ValueError("invalid custody approval window")
    encoded = json.dumps([
        *_checkpoint_fields(expected), custody_digest(replacement), issued.isoformat(), expires.isoformat(),
    ], ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return _APPROVAL_DOMAIN + encoded


@dataclass(frozen=True)
class DurableReceiptAnchor:
    path: Path
    authority_public_keys: Mapping[str, bytes]
    enrollment_pins: Mapping[str, str] | None = None

    @classmethod
    def initialize(cls, path, scopes, *, authority_public_keys, enrollments=None, now=None):
        """Provision known offline custodian keys without recreating an existing store."""
        if not scopes or set(authority_public_keys) != set(scopes):
            raise ValueError("each company requires a separate custody authorization key")
        keys = tuple(authority_public_keys.values())
        if any(not isinstance(key, bytes) or len(key) != 32 for key in keys) or len(set(keys)) != len(keys):
            raise ValueError("custody authorization keys must be distinct Ed25519 public keys")
        if enrollments is not None and (
            not isinstance(enrollments, Mapping) or set(enrollments) != set(scopes)
        ):
            raise ValueError("witnessed enrollment is required for every configured company")
        checkpoints = []
        enrollment_pins = None if enrollments is None else {}
        for company, (journal_id, trust) in scopes.items():
            if (
                trust.company_id != company or trust.revoked is not False
                or trust.public_key in keys
            ):
                raise ValueError("publisher and custodian identities must be separate")
            checkpoint = ReceiptCheckpoint.genesis(company, journal_id, custody_digest(trust))
            checkpoints.append((*_checkpoint_fields(checkpoint), sha256(authority_public_keys[company]).hexdigest()))
            if enrollment_pins is not None:
                challenge, enrollment = enrollments[company]
                enrollment_pins[company] = verify_publisher_enrollment(
                    trust, journal_id, authority_public_keys[company], expected_challenge=challenge,
                    enrollment=enrollment, now=now,
                )
        anchor = cls(Path(path), dict(authority_public_keys), enrollment_pins)
        anchor.path.touch(mode=0o600, exist_ok=False)
        with closing(anchor._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""
                CREATE TABLE checkpoint (
                    company_id TEXT PRIMARY KEY, journal_id TEXT NOT NULL,
                    custody_sha256 TEXT NOT NULL, receipt_count INTEGER NOT NULL,
                    head_sha256 TEXT NOT NULL, approval_key_sha256 TEXT NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE custody_history (
                    company_id TEXT NOT NULL, custody_sha256 TEXT NOT NULL,
                    approval_sha256 TEXT,
                    PRIMARY KEY(company_id, custody_sha256)
                )
            """)
            db.executemany("INSERT INTO checkpoint VALUES (?, ?, ?, ?, ?, ?)", checkpoints)
            db.executemany("INSERT INTO custody_history VALUES (?, ?, NULL)",
                           ((row[0], row[2]) for row in checkpoints))
            if enrollment_pins is not None:
                db.execute("""
                    CREATE TABLE publisher_enrollment (
                        company_id TEXT PRIMARY KEY, proof_sha256 TEXT NOT NULL
                    )
                """)
                db.executemany("INSERT INTO publisher_enrollment VALUES (?, ?)", enrollment_pins.items())
        return anchor

    def _connect(self):
        db = sqlite3.connect(f"{Path(self.path).resolve().as_uri()}?mode=rw", uri=True, timeout=1)
        try:
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA synchronous=FULL")
        except BaseException:
            db.close()
            raise
        return db

    def _read(self, db, company):
        row = db.execute("SELECT * FROM checkpoint WHERE company_id=?", (company,)).fetchone()
        key = self.authority_public_keys.get(company)
        if (
            row is None or not isinstance(key, bytes) or len(key) != 32
            or not hmac.compare_digest(row[5], sha256(key).hexdigest())
        ):
            raise ValueError("independent custody authority is unavailable for this company")
        enrollment = self._verify_enrollment(db, company)
        count = db.execute(
            "SELECT COUNT(*) FROM custody_history WHERE company_id=? AND custody_sha256=?",
            (company, row[2]),
        ).fetchone()[0]
        if count != 1:
            raise ValueError("checkpoint custody is outside recorded history")
        return ReceiptCheckpoint(*row[:5], witnessed_enrollment_sha256=enrollment)

    def _verify_enrollment(self, db, company):
        table = db.execute(
            "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='publisher_enrollment'",
        ).fetchone()
        if bool(table) != (self.enrollment_pins is not None):
            raise ValueError("witnessed enrollment binding mode does not match")
        if table:
            row = db.execute(
                "SELECT proof_sha256 FROM publisher_enrollment WHERE company_id=?", (company,),
            ).fetchone()
            pin = self.enrollment_pins.get(company)
            if row is None or not isinstance(pin, str) or not hmac.compare_digest(row[0], pin):
                raise ValueError("witnessed enrollment pin is unavailable or changed")
            return pin
        return None

    def read(self, company_id):
        with closing(self._connect()) as db:
            return self._read(db, company_id)

    def advance(self, expected, successor):
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            if (
                self._read(db, expected.company_id) != expected
                or replace(successor, count=expected.count, head_sha256=expected.head_sha256) != expected
                or successor.count != expected.count + 1
                or successor.head_sha256 == expected.head_sha256
            ):
                raise ValueError("independent receipt checkpoint conflict")
            db.execute(
                "UPDATE checkpoint SET receipt_count=?, head_sha256=? WHERE company_id=?",
                (successor.count, successor.head_sha256, successor.company_id),
            )

    def verify_pending_repair(self, local, anchored, wire_sha256, authorization, *, now):
        company = anchored.company_id
        now = _utc(now)
        if (
            not isinstance(authorization, CustodyAuthorization)
            or not _utc(authorization.issued_at) <= now < _utc(authorization.expires_at)
        ):
            raise ValueError("independent repair witness is missing or expired")
        approval = pending_repair_bytes(
            local, anchored, wire_sha256,
            issued_at=authorization.issued_at, expires_at=authorization.expires_at,
        )
        with closing(self._connect()) as db:
            if self._read(db, company) != anchored:
                raise ValueError("independent repair checkpoint changed")
            try:
                Ed25519PublicKey.from_public_bytes(self.authority_public_keys[company]).verify(
                    authorization.signature, approval,
                )
            except InvalidSignature as exc:
                raise ValueError("independent repair witness did not verify") from exc

    def transition(self, expected, replacement, authorization, *, now):
        company = expected.company_id
        now = _utc(now)
        if (
            replacement.company_id != company or replacement.revoked is not False
            or replacement.public_key in self.authority_public_keys.values()
            or not isinstance(authorization, CustodyAuthorization)
            or not _utc(authorization.issued_at) <= now < _utc(authorization.expires_at)
        ):
            raise ValueError("custody transition scope or freshness is invalid")
        approval = custody_transition_bytes(
            expected, replacement, issued_at=authorization.issued_at, expires_at=authorization.expires_at,
        )
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            if self._read(db, company) != expected:
                raise ValueError("custody approval does not bind the current checkpoint")
            try:
                Ed25519PublicKey.from_public_bytes(self.authority_public_keys[company]).verify(
                    authorization.signature, approval,
                )
            except InvalidSignature as exc:
                raise ValueError("independent custody approval signature is invalid") from exc
            digest = custody_digest(replacement)
            if db.execute("SELECT 1 FROM custody_history WHERE company_id=? AND custody_sha256=?",
                          (company, digest)).fetchone():
                raise ValueError("custody digest has already been used")
            db.execute("INSERT INTO custody_history VALUES (?, ?, ?)",
                       (company, digest, sha256(approval + authorization.signature).hexdigest()))
            db.execute("UPDATE checkpoint SET custody_sha256=? WHERE company_id=?", (digest, company))
        return replace(expected, custody_sha256=digest)

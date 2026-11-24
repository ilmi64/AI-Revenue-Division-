"""Synthetic offline Ed25519 OCC reporting, with no company action authority."""

from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from jsonschema import Draft202012Validator, FormatChecker

from occ_company_visibility import _aevora_operations_view, _snapshot_view
from occ_divisional_telemetry import split_divisional_report
from occ_receipt_anchor import ReceiptAnchor, ReceiptCheckpoint, custody_digest
from occ_readonly import MAX_FIXTURE_BYTES, _enforce_json_resource_limits, _strict_object
from validate_m2_schema import EXPECTED_BLOB_SHAS, github_blob_sha1


AUDIENCE = "daivora.occ/offline-fixtures"
_DOMAIN = b"daivora.occ.visibility/synthetic-v1\x00"
_COMPANIES = ("ai_revenue", "trading_technology")
_TYPES = {"ai_revenue": "aevora_operations", "trading_technology": "m2_snapshot"}
_MAX_WIRE = 65536
_MAX_AGE = timedelta(minutes=5)
_SAFE_INTEGER = (1 << 53) - 1
_CLAIM_FIELDS = {
    "protocol_version", "audience", "report_type", "company_id", "publisher_id",
    "key_id", "source_revision", "sequence", "issued_at", "expires_at", "payload_sha256",
    "snapshot_id", "payload",
}


@dataclass(frozen=True)
class PublisherTrust:
    company_id: str
    publisher_id: str
    key_id: str
    public_key: bytes
    source_revision: str
    valid_from: datetime
    valid_until: datetime
    revoked: bool = False
    payload_source_revision: str | None = None
    divisional_telemetry: bool = False


def _utc(value):
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("clock must be an aware UTC datetime")
    return value


def _timestamp(value):
    value = _utc(value)
    if value.microsecond:
        raise ValueError("signed timestamps require whole seconds")
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_timestamp(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _signed_integer(raw):
    value = int(raw)
    if abs(value) > _SAFE_INTEGER:
        raise ValueError("integer is outside the signed protocol range")
    return value


def _reject_number(_):
    raise ValueError("signed protocol allows integer numbers only")


def _canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("ascii")


def _report_type(trust):
    base = _TYPES[trust.company_id]
    return base + "_with_divisions" if trust.divisional_telemetry else base


def sign_fixture(payload, *, trust, sequence, issued_at, expires_at, private_key):
    """Sign an offline fixture with a caller-owned synthetic private key."""
    report = payload["report"] if trust.divisional_telemetry else payload
    claims = {
        "protocol_version": 1,
        "audience": AUDIENCE,
        "company_id": trust.company_id,
        "publisher_id": trust.publisher_id,
        "key_id": trust.key_id,
        "source_revision": trust.source_revision,
        "report_type": _report_type(trust),
        "sequence": sequence,
        "issued_at": _timestamp(issued_at),
        "expires_at": _timestamp(expires_at),
        "payload_sha256": sha256(_canonical(payload)).hexdigest(),
        "snapshot_id": (
            report.get("snapshot_id") if trust.company_id == "trading_technology"
            else f"aevora-operations-{sequence}"
        ),
        "payload": payload,
    }
    signature = private_key.sign(_DOMAIN + _canonical(claims))
    return _canonical({"claims": claims, "signature_hex": signature.hex()})


@dataclass(frozen=True)
class ReceiptJournal:
    path: Path
    company_id: str | None = None
    anchor: ReceiptAnchor | None = None

    @classmethod
    def initialize(cls, path, *, company_id=None, anchor=None):
        """Provision an offline journal without overwriting existing state."""
        if company_id is not None and company_id not in _COMPANIES:
            raise ValueError("unknown receipt journal company")
        journal = cls(Path(path), company_id, anchor)
        checkpoint = None
        if anchor is not None:
            checkpoint = journal._read_checkpoint()
            genesis = ReceiptCheckpoint.genesis(
                checkpoint.company_id, checkpoint.journal_id, checkpoint.custody_sha256,
            )
            if checkpoint != genesis:
                raise ValueError("cannot reprovision an advanced anchored journal")
        journal.path.touch(mode=0o600, exist_ok=False)
        with closing(journal._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""
                CREATE TABLE receipt (
                    company_id TEXT NOT NULL, publisher_id TEXT NOT NULL, key_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL, snapshot_id TEXT NOT NULL, digest TEXT NOT NULL,
                    PRIMARY KEY (company_id, publisher_id, key_id, sequence),
                    UNIQUE (company_id, snapshot_id)
                )
            """)
            if company_id is not None:
                db.execute("""
                    CREATE TABLE receipt_binding (
                        singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                        company_id TEXT NOT NULL
                    )
                """)
                db.execute("INSERT INTO receipt_binding VALUES (1, ?)", (company_id,))
            if checkpoint is not None:
                db.execute("""
                    CREATE TABLE receipt_anchor (
                        singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                        journal_id TEXT NOT NULL,
                        custody_sha256 TEXT NOT NULL
                    )
                """)
                db.execute("INSERT INTO receipt_anchor VALUES (1, ?, ?)",
                           (checkpoint.journal_id, checkpoint.custody_sha256))
        return journal

    def _read_checkpoint(self):
        if self.company_id not in _COMPANIES:
            raise ValueError("anchored receipt journal must be company-scoped")
        try:
            checkpoint = self.anchor.read(self.company_id)
        except Exception as exc:
            raise ValueError("independent receipt checkpoint is unavailable") from exc
        if not isinstance(checkpoint, ReceiptCheckpoint) or checkpoint.company_id != self.company_id:
            raise ValueError("independent receipt checkpoint is outside company scope")
        return checkpoint

    def _anchor_checkpoints(self, db, trust):
        table = db.execute(
            "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='receipt_anchor'",
        ).fetchone()
        if bool(table) != (self.anchor is not None):
            raise ValueError("receipt anchor binding mode does not match")
        if self.anchor is None:
            return None, None
        checkpoint = self._read_checkpoint()
        binding = db.execute(
            "SELECT journal_id, custody_sha256 FROM receipt_anchor WHERE singleton=1",
        ).fetchone()
        if (
            binding is None or binding[0] != checkpoint.journal_id
            or custody_digest(trust) != checkpoint.custody_sha256
        ):
            raise ValueError("receipt anchor and publisher custody do not match")
        local = ReceiptCheckpoint.genesis(
            checkpoint.company_id, checkpoint.journal_id, binding[1],
        )
        for row in db.execute(
            "SELECT company_id, publisher_id, key_id, sequence, snapshot_id, digest FROM receipt ORDER BY rowid",
        ):
            if local.count >= checkpoint.count:
                raise ValueError("local receipt state is ahead of the independent checkpoint")
            local = local.append(row)
        return replace(local, custody_sha256=checkpoint.custody_sha256), checkpoint

    def _verify_anchor(self, db, trust):
        local, checkpoint = self._anchor_checkpoints(db, trust)
        if local != checkpoint:
            raise ValueError("local receipt state does not match the independent checkpoint")
        return checkpoint

    def _advance_anchor(self, checkpoint, row):
        successor = checkpoint.append(row)
        try:
            self.anchor.advance(checkpoint, successor)
        except Exception as exc:
            raise ValueError("independent receipt checkpoint advance is uncertain") from exc
        if self._read_checkpoint() != successor:
            raise ValueError("independent receipt checkpoint did not confirm the update")

    def _connect(self):
        return sqlite3.connect(f"{Path(self.path).resolve().as_uri()}?mode=rw", uri=True, timeout=1)

    def _verify_local_scope(self, db, expected_company):
        bound_journal = db.execute(
            "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='receipt_binding'"
        ).fetchone()
        if bool(bound_journal) != (self.company_id is not None):
            raise ValueError("receipt journal binding mode does not match")
        if bound_journal:
            binding = db.execute("SELECT company_id FROM receipt_binding WHERE singleton=1").fetchone()
            if binding != (self.company_id,) or expected_company != self.company_id:
                raise ValueError("receipt journal company does not match")

    def _pending_row(self, db, claims, wire):
        key = (claims["company_id"], claims["publisher_id"], claims["key_id"])
        latest = db.execute(
            "SELECT MAX(sequence) FROM receipt WHERE company_id=? AND publisher_id=? AND key_id=?",
            key,
        ).fetchone()[0]
        if latest is not None and claims["sequence"] <= latest:
            raise ValueError("receipt is not newer")
        return (*key, claims["sequence"], claims["snapshot_id"], sha256(wire).hexdigest())

    def _accept(self, claims, wire, *, trust):
        with closing(self._connect()) as db, db:
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            self._verify_local_scope(db, claims["company_id"])
            checkpoint = self._verify_anchor(db, trust)
            row = self._pending_row(db, claims, wire)
            db.execute("INSERT INTO receipt VALUES (?, ?, ?, ?, ?, ?)", row)
            if checkpoint is not None:
                # An uncertain advance leaves the feed suspended until exact repair.
                self._advance_anchor(checkpoint, row)

    def reconcile_pending_receipt(self, wire, *, trust, now):
        """Repair exactly one missing anchored receipt; produce no view or new receipt."""
        claims, _ = _verify(wire, trust, self.company_id, _utc(now))
        with closing(self._connect()) as db, db:
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            self._verify_local_scope(db, claims["company_id"])
            local, checkpoint = self._anchor_checkpoints(db, trust)
            row = self._pending_row(db, claims, wire)
            if local is None or local.append(row) != checkpoint or self._read_checkpoint() != checkpoint:
                raise ValueError("receipt does not match the single anchored interruption")
            db.execute("INSERT INTO receipt VALUES (?, ?, ?, ?, ?, ?)", row)

    def transition_custody(self, current, replacement, authorization, *, now):
        """Apply an explicitly authorized replacement only from aligned local history."""
        now = _utc(now)
        _trust_matches_company(replacement, self.company_id, now)
        if not isinstance(current, PublisherTrust) or current.company_id != self.company_id:
            raise ValueError("current publisher is outside the company scope")
        if current.public_key != replacement.public_key and current.key_id == replacement.key_id:
            raise ValueError("a replacement key requires a distinct key ID")
        transition = getattr(self.anchor, "transition", None)
        if transition is None:
            raise ValueError("custody transition authority unavailable")
        with closing(self._connect()) as db, db:
            db.execute("PRAGMA trusted_schema=OFF")
            db.execute("BEGIN IMMEDIATE")
            self._verify_local_scope(db, self.company_id)
            checkpoint = self._verify_anchor(db, current)
            successor = transition(checkpoint, replacement, authorization, now=now)
            if self._read_checkpoint() != successor:
                raise ValueError("custody transition could not be confirmed")


def _trust_matches_company(trust, company_id, now):
    if (
        not isinstance(trust, PublisherTrust) or trust.company_id != company_id
        or trust.revoked is not False
        or type(trust.divisional_telemetry) is not bool
        or not isinstance(trust.public_key, bytes) or len(trust.public_key) != 32
        or not all(re.fullmatch(r"[a-zA-Z0-9._-]{1,80}", name) for name in (trust.publisher_id, trust.key_id))
        or not re.fullmatch(r"[0-9a-f]{40}", trust.source_revision)
        or not _utc(trust.valid_from) <= now < _utc(trust.valid_until)
    ):
        raise ValueError("publisher trust unavailable")


def _verify_m2_schema(payload):
    relative = "schema/records.schema.json"
    path = Path(__file__).resolve().parents[1] / relative
    with path.open("rb") as file:
        raw = file.read(MAX_FIXTURE_BYTES + 1)
    if len(raw) > MAX_FIXTURE_BYTES or github_blob_sha1(raw) != EXPECTED_BLOB_SHAS[relative]:
        raise ValueError("pinned M2 schema is unavailable")
    schema = json.loads(raw)
    snapshot_schema = {
        "$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/snapshot",
    }
    if not Draft202012Validator(snapshot_schema, format_checker=FormatChecker()).is_valid(payload):
        raise ValueError("snapshot failed pinned M2 schema validation")


def _verify(wire, trust, company_id, now):
    _trust_matches_company(trust, company_id, now)
    if not isinstance(wire, bytes) or not 0 < len(wire) <= _MAX_WIRE:
        raise ValueError("wire size is invalid")
    record = json.loads(wire.decode("ascii"), object_pairs_hook=_strict_object,
                        parse_int=_signed_integer, parse_float=_reject_number,
                        parse_constant=_reject_number)
    _enforce_json_resource_limits(record)
    if not isinstance(record, dict) or set(record) != {"claims", "signature_hex"} or wire != _canonical(record):
        raise ValueError("wire shape or canonical representation is invalid")
    claims, signature = record["claims"], record["signature_hex"]
    if not isinstance(claims, dict) or set(claims) != _CLAIM_FIELDS:
        raise ValueError("signed claims are invalid")
    if (
        type(claims["protocol_version"]) is not int or claims["protocol_version"] != 1
        or claims["audience"] != AUDIENCE or claims["report_type"] != _report_type(trust)
        or claims["company_id"] != company_id or claims["publisher_id"] != trust.publisher_id
        or claims["key_id"] != trust.key_id or claims["source_revision"] != trust.source_revision
        or type(claims["sequence"]) is not int or claims["sequence"] < 1
        or not re.fullmatch(r"[0-9a-f]{128}", signature)
    ):
        raise ValueError("unregistered signed scope")
    Ed25519PublicKey.from_public_bytes(trust.public_key).verify(
        bytes.fromhex(signature), _DOMAIN + _canonical(claims),
    )
    payload = claims["payload"]
    if not isinstance(payload, dict) or claims["payload_sha256"] != sha256(_canonical(payload)).hexdigest():
        raise ValueError("payload digest mismatch")
    issued, expires = (_parse_timestamp(claims[field]) for field in ("issued_at", "expires_at"))
    if (
        not trust.valid_from <= issued <= now < expires <= trust.valid_until
        or expires - issued > _MAX_AGE
        or any(_timestamp(value) != claims[field]
               for field, value in (("issued_at", issued), ("expires_at", expires)))
    ):
        raise ValueError("report is outside its freshness window")
    telemetry = None
    if trust.divisional_telemetry:
        payload, telemetry = split_divisional_report(payload, company_id)
    if company_id == "ai_revenue":
        view = _aevora_operations_view(payload)
        if claims["snapshot_id"] != f'aevora-operations-{claims["sequence"]}':
            raise ValueError("invalid aggregate snapshot ID")
    else:
        _verify_m2_schema(payload)
        if telemetry is not None:
            totals = telemetry["company_totals"]
            if (
                totals["open_incident_count"] != payload["incident_summary"]["open_count"]
                or totals["blocker_count"] != len(payload["blockers"])
            ):
                raise ValueError("divisional company totals differ from the pinned snapshot")
        view = _snapshot_view(payload, company_id, now)
        view.pop("trust", None)
        if (
            not re.fullmatch(r"[a-zA-Z0-9._-]{1,100}", claims["snapshot_id"])
            or claims["snapshot_id"] != payload.get("snapshot_id")
            or payload.get("source_revision") != (trust.payload_source_revision or trust.source_revision)
        ):
            raise ValueError("snapshot pin mismatch")
        publication = _utc(datetime.fromisoformat(payload["published_at"]))
        if not issued - _MAX_AGE <= publication <= issued:
            raise ValueError("snapshot publication is outside the signed window")
    if view["input_status"] in {"REJECTED", "STALE"}:
        raise ValueError("report failed view checks")
    if telemetry is not None and view["input_status"] != "QUARANTINED":
        view["reported_divisional_telemetry"] = telemetry
    return claims, view


def build_authenticated_visibility(
    *, ai_revenue_wire=None, trading_wire=None, trust_by_company, journal=None,
    journal_by_company=None, now,
):
    """Verify and consume separate synthetic feeds; no unsigned fallback."""
    _utc(now)
    if journal is not None and journal_by_company is not None:
        raise ValueError("provide one receipt journal configuration")
    isolated = journal_by_company is not None
    if isolated and not isinstance(journal_by_company, Mapping):
        journal_by_company = {}
    companies = {}
    if not isinstance(trust_by_company, Mapping):
        trust_by_company = {}
    for company_id, wire in zip(_COMPANIES, (ai_revenue_wire, trading_wire), strict=True):
        if wire is None:
            companies[company_id] = {"input_status": "MISSING", "authentication": "UNVERIFIED"}
            continue
        trust = trust_by_company.get(company_id)
        peer = trust_by_company.get(next(name for name in _COMPANIES if name != company_id))
        try:
            if isinstance(trust, PublisherTrust) and isinstance(peer, PublisherTrust) and (
                trust.public_key == peer.public_key or trust.publisher_id == peer.publisher_id
            ):
                raise ValueError("trust roots are not company-separated")
            receipt_journal = journal_by_company.get(company_id) if isolated else journal
            if not isinstance(receipt_journal, ReceiptJournal):
                raise ValueError("receipt journal is unavailable")
            if isolated and receipt_journal.company_id != company_id:
                raise ValueError("receipt journal is not company-scoped")
            claims, view = _verify(wire, trust, company_id, now)
            if trust.divisional_telemetry and (
                receipt_journal.company_id != company_id or receipt_journal.anchor is None
            ):
                raise ValueError("divisional telemetry requires company-anchored custody")
            receipt_journal._accept(claims, wire, trust=trust)
        except (InvalidSignature, ValueError, TypeError, KeyError, RecursionError, OverflowError, OSError, sqlite3.Error):
            companies[company_id] = {"input_status": "REJECTED", "authentication": "UNVERIFIED"}
            continue
        companies[company_id] = {**view, "authentication": "AUTHENTICATED_OFFLINE"}
    return {"mode": "offline_read_only", "operational_claim": False, "companies": companies}

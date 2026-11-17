"""Create signed OCC stop-only snapshots for the PolyBot paper receiver.

This module emits an envelope only. It does not send network messages or
persist secrets. The HMAC key must be provisioned out of band.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Any
from uuid import uuid4


_ALLOWED_STOP_CONDITIONS = {
    "credential_or_secret_exposure_suspected",
    "unauthorised_access_or_action_detected",
    "data_provenance_or_licence_unknown_for_intended_use",
    "market_data_stale_delayed_indicative_reference_only_or_incomplete",
    "instrument_or_venue_mapping_ambiguous",
    "position_or_order_state_uncertain",
    "unreconciled_fill_or_transaction",
    "risk_limit_missing_or_invalid",
    "deterministic_validation_failed",
    "required_owner_approval_missing",
    "material_dependency_unavailable",
    "incident_severity_critical",
}


class SnapshotPublisherError(ValueError):
    """The OCC snapshot cannot safely be generated or signed."""


def canonical_snapshot_bytes(snapshot: dict[str, Any]) -> bytes:
    if not isinstance(snapshot, dict):
        raise SnapshotPublisherError("snapshot must be an object")
    try:
        return json.dumps(
            snapshot, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SnapshotPublisherError("snapshot is not canonical finite JSON") from exc


def policy_file_sha256(path: str | Path) -> str:
    """Calculate the exact SHA-256 digest of the approved policy file bytes."""
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SnapshotPublisherError(f"unable to read approved policy file: {type(exc).__name__}") from exc
    return digest.hexdigest()


def sign_snapshot(snapshot: dict[str, Any], secret: bytes) -> str:
    """Return lowercase HMAC-SHA256 hex; never persist or transmit the secret."""
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise SnapshotPublisherError("HMAC secret must contain at least 32 bytes")
    return hmac.new(secret, canonical_snapshot_bytes(snapshot), hashlib.sha256).hexdigest()


class SnapshotSequenceStore:
    """Persist monotonically increasing snapshot timestamps on one OCC host."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS occ_snapshot_sequence (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    last_generated_at_epoch REAL NOT NULL,
                    last_snapshot_id TEXT NOT NULL
                )
            """)
            db.execute(
                "INSERT OR IGNORE INTO occ_snapshot_sequence(singleton,last_generated_at_epoch,last_snapshot_id) VALUES(1,-1,'')"
            )
            db.commit()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(str(self.path), timeout=5.0)
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def issue(
        self,
        *,
        status: str,
        stop_conditions: list[str],
        evidence_refs: list[str],
        policy_sha256: str,
        portfolio_version: int,
        now_epoch: float,
        ttl_seconds: float,
        secret: bytes,
    ) -> dict[str, Any]:
        if not isinstance(status, str) or status not in {"CLEAR", "HALT"}:
            raise SnapshotPublisherError("status must be CLEAR or HALT")
        if not isinstance(stop_conditions, list) or any(
            not isinstance(item, str) or item not in _ALLOWED_STOP_CONDITIONS
            for item in stop_conditions
        ) or len(set(stop_conditions)) != len(stop_conditions):
            raise SnapshotPublisherError("stop_conditions contains unknown or duplicate values")
        if not isinstance(evidence_refs, list) or any(
            not isinstance(item, str) or not item.strip() or len(item) > 500
            for item in evidence_refs
        ):
            raise SnapshotPublisherError("evidence_refs must contain bounded non-empty strings")
        if status == "CLEAR" and (stop_conditions or evidence_refs):
            raise SnapshotPublisherError("CLEAR requires empty stop_conditions and evidence_refs")
        if status == "HALT" and (not stop_conditions or not evidence_refs):
            raise SnapshotPublisherError("HALT requires stop conditions and evidence references")
        if (not isinstance(policy_sha256, str) or len(policy_sha256) != 64
                or any(ch not in "0123456789abcdef" for ch in policy_sha256)):
            raise SnapshotPublisherError("policy_sha256 must be lowercase SHA-256")
        if (isinstance(portfolio_version, bool) or not isinstance(portfolio_version, int)
                or portfolio_version < 0):
            raise SnapshotPublisherError("portfolio_version must be a non-negative integer")
        for name, value in (("now_epoch", now_epoch), ("ttl_seconds", ttl_seconds)):
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value)):
                raise SnapshotPublisherError(f"{name} must be finite numeric data")
        if ttl_seconds <= 0 or ttl_seconds > 300:
            raise SnapshotPublisherError("ttl_seconds must be greater than 0 and at most 300")
        if now_epoch < 0:
            raise SnapshotPublisherError("now_epoch must be non-negative")
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise SnapshotPublisherError("HMAC secret must contain at least 32 bytes")

        snapshot_id = f"occ-{uuid4().hex}"
        snapshot = {
            "schema_version": 1,
            "source_system": "OCC",
            "snapshot_id": snapshot_id,
            "generated_at_epoch": float(now_epoch),
            "expires_at_epoch": float(now_epoch) + float(ttl_seconds),
            "policy_sha256": policy_sha256,
            "portfolio_version": portfolio_version,
            "status": status,
            "stop_conditions": list(stop_conditions),
            "evidence_refs": list(evidence_refs),
        }
        signature = sign_snapshot(snapshot, secret)

        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT last_generated_at_epoch FROM occ_snapshot_sequence WHERE singleton=1"
            ).fetchone()
            last_generated = float(row[0]) if row else -1.0
            if float(now_epoch) <= last_generated:
                raise SnapshotPublisherError(
                    "OCC clock is not strictly newer than the last snapshot; publication blocked"
                )
            db.execute(
                "UPDATE occ_snapshot_sequence SET last_generated_at_epoch=?,last_snapshot_id=? WHERE singleton=1",
                (float(now_epoch), snapshot_id),
            )
            db.commit()

        return {"snapshot": snapshot, "signature_hex": signature}


def write_envelope_atomic(envelope: dict[str, Any], destination: str | Path) -> Path:
    """Atomically publish a signed envelope to a trusted shared local inbox.

    The destination directory must be accessible only to the OCC publisher and
    the PolyBot receiver. This is a same-host/shared-filesystem transport, not
    a network service. The HMAC secret is never written to disk.
    """
    if not isinstance(envelope, dict) or set(envelope) != {"snapshot", "signature_hex"}:
        raise SnapshotPublisherError("envelope must contain exactly snapshot and signature_hex")
    if not isinstance(envelope["snapshot"], dict):
        raise SnapshotPublisherError("envelope snapshot must be an object")
    signature = envelope["signature_hex"]
    if (not isinstance(signature, str) or len(signature) != 64
            or any(ch not in "0123456789abcdef" for ch in signature)):
        raise SnapshotPublisherError("envelope signature must be lowercase HMAC-SHA256 hex")

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise SnapshotPublisherError("refusing to replace a symlink inbox destination")
    payload = json.dumps(
        envelope, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return path

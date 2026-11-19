"""Deterministic hash-linked OCC audit event primitives.

This module builds and verifies caller-held event sequences. It does not persist,
sign, authenticate, timestamp independently, or provide a trusted audit anchor.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

from .instrument_identity import InstrumentIdentityError, validate_instrument_identity

GENESIS_HASH = "0" * 64
EVENT_TYPES = {
    "FEED_CONFLICT_DETECTED",
    "QUARANTINE_ENTERED",
    "RECOVERY_REVIEW_REQUIRED",
    "RELEASE_CLAIM_RECORDED",
}
_FALSE_FLAGS = {
    "event_source_authenticated": False,
    "reviewer_authenticated": False,
    "market_data_trusted": False,
    "paper_use_authorized": False,
    "execution_eligible": False,
}


class AuditChainError(ValueError):
    """An audit event or hash-linked sequence is malformed."""


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise AuditChainError("event must contain finite JSON-compatible values") from exc
    return encoded.encode("utf-8")


def _timestamp(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AuditChainError("occurred_at_epoch must be a finite non-negative number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise AuditChainError("occurred_at_epoch must be a finite non-negative number") from exc
    if not math.isfinite(number) or number < 0:
        raise AuditChainError("occurred_at_epoch must be a finite non-negative number")
    return number


def _event_digest(event_without_hash: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(event_without_hash)).hexdigest()


def verify_audit_chain(events: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Verify sequence numbering, predecessor links, event shape and SHA-256 hashes."""
    if not isinstance(events, list):
        raise AuditChainError("events must be a list")
    previous_hash = GENESIS_HASH
    for index, event in enumerate(events, start=1):
        if not isinstance(event, Mapping):
            raise AuditChainError("each event must be a mapping")
        if event.get("sequence") != index:
            raise AuditChainError("event sequence is not contiguous")
        if event.get("previous_hash") != previous_hash:
            raise AuditChainError("event previous_hash does not match prior event")
        if event.get("event_type") not in EVENT_TYPES:
            raise AuditChainError("unsupported event_type")
        _timestamp(event.get("occurred_at_epoch"))
        try:
            validate_instrument_identity(event.get("instrument_identity"))
        except InstrumentIdentityError as exc:
            raise AuditChainError(f"invalid event instrument identity: {exc}") from exc
        if not isinstance(event.get("details"), Mapping):
            raise AuditChainError("event details must be a mapping")
        for flag, required in _FALSE_FLAGS.items():
            if event.get(flag) is not required:
                raise AuditChainError(f"{flag} must remain false")
        digest = event.get("event_hash")
        if not isinstance(digest, str) or len(digest) != 64:
            raise AuditChainError("event_hash must be a SHA-256 hex digest")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise AuditChainError("event_hash must be hexadecimal") from exc
        body = {key: value for key, value in event.items() if key != "event_hash"}
        if _event_digest(body) != digest:
            raise AuditChainError("event hash mismatch")
        previous_hash = digest
    return {
        "valid": True,
        "event_count": len(events),
        "head_hash": previous_hash,
        "chain_authenticated": False,
        "tamper_resistant": False,
        "persistent_audit_verified": False,
    }


def append_audit_event(
    events: list[Mapping[str, Any]],
    *,
    event_type: str,
    occurred_at_epoch: int | float,
    instrument_identity: Mapping[str, Any],
    details: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return a new list with one deterministic event appended; input is not mutated."""
    verify_audit_chain(events)
    if event_type not in EVENT_TYPES:
        raise AuditChainError("unsupported event_type")
    if not isinstance(details, Mapping):
        raise AuditChainError("details must be a mapping")
    try:
        identity = validate_instrument_identity(instrument_identity)
    except InstrumentIdentityError as exc:
        raise AuditChainError(f"invalid instrument identity: {exc}") from exc
    previous_hash = events[-1]["event_hash"] if events else GENESIS_HASH
    body: dict[str, Any] = {
        "sequence": len(events) + 1,
        "previous_hash": previous_hash,
        "event_type": event_type,
        "occurred_at_epoch": _timestamp(occurred_at_epoch),
        "instrument_identity": identity,
        "details": dict(details),
        **_FALSE_FLAGS,
    }
    digest = _event_digest(body)
    event = {**body, "event_hash": digest}
    # Validate JSON compatibility and the completed event before returning it.
    result = [dict(item) for item in events] + [event]
    verify_audit_chain(result)
    return result

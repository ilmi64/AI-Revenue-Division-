"""Versioned, provenance-aware venue/contract profile registry.

Pure validation and resolution only. This module does not fetch or authenticate
source documents, sign reviews, connect to venues, or grant live readiness.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any

from specialist_research.venue_risk_simulation import validate_venue_spec
from specialist_research.contract_lifecycle import validate_contract_profile

AUTHORITY = "research_only_no_execution_authority"
REGISTRY_VERSION = "1.0.0"
PROFILE_STATES = {"unverified", "under_review", "reviewed", "approved", "rejected", "suspended"}
VERIFICATION_STATES = {"unverified", "source_checked", "independently_corroborated"}
REVIEW_STATES = {"not_reviewed", "pending", "accepted", "rejected"}
PROFILE_TYPES = {"crypto_perpetual", "forex_cfd", "index_future", "index_cfd", "gold_future", "gold_cfd"}


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def validate_profile_record(record: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["profile record must be an object"]
    required = (
        "profile_id", "revision", "venue_id", "instrument_id", "instrument_type",
        "effective_from_utc", "profile_state", "verification_state", "review_state",
        "venue_spec", "contract_profile", "provenance",
    )
    for key in required:
        if key not in record:
            errors.append(f"{key} is required")
    if not _nonempty(record.get("profile_id")):
        errors.append("profile_id must be a non-empty string")
    if not isinstance(record.get("revision"), int) or isinstance(record.get("revision"), bool) or record.get("revision", 0) < 1:
        errors.append("revision must be a positive integer")
    for key in ("venue_id", "instrument_id"):
        if not _nonempty(record.get(key)):
            errors.append(f"{key} must be a non-empty string")
    if record.get("instrument_type") not in PROFILE_TYPES:
        errors.append("instrument_type is unsupported")
    if _utc(record.get("effective_from_utc")) is None:
        errors.append("effective_from_utc must be UTC ISO-8601 ending Z")
    effective_to = record.get("effective_to_utc")
    if effective_to is not None:
        end = _utc(effective_to)
        start = _utc(record.get("effective_from_utc"))
        if end is None or (start is not None and end <= start):
            errors.append("effective_to_utc must be UTC and later than effective_from_utc")
    if record.get("profile_state") not in PROFILE_STATES:
        errors.append("profile_state is unsupported")
    if record.get("verification_state") not in VERIFICATION_STATES:
        errors.append("verification_state is unsupported")
    if record.get("review_state") not in REVIEW_STATES:
        errors.append("review_state is unsupported")

    venue = record.get("venue_spec")
    contract = record.get("contract_profile")
    if isinstance(venue, dict):
        errors.extend(f"venue_spec: {e}" for e in validate_venue_spec(venue))
        if venue.get("venue_id") != record.get("venue_id"):
            errors.append("venue_spec.venue_id must match registry record")
        if venue.get("instrument_type") != record.get("instrument_type"):
            errors.append("venue_spec.instrument_type must match registry record")
    else:
        errors.append("venue_spec must be an object")
    if isinstance(contract, dict):
        errors.extend(f"contract_profile: {e}" for e in validate_contract_profile(contract))
        for key in ("venue_id", "instrument_id", "instrument_type"):
            if contract.get(key) != record.get(key):
                errors.append(f"contract_profile.{key} must match registry record")
    else:
        errors.append("contract_profile must be an object")

    provenance = record.get("provenance")
    if not isinstance(provenance, list) or not provenance:
        errors.append("provenance must contain at least one source record")
    else:
        seen_refs: set[str] = set()
        for index, item in enumerate(provenance):
            prefix = f"provenance[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            for key in ("source_id", "source_uri", "source_type", "captured_at_utc", "evidence_sha256"):
                if not _nonempty(item.get(key)):
                    errors.append(f"{prefix}.{key} is required")
            if _utc(item.get("captured_at_utc")) is None:
                errors.append(f"{prefix}.captured_at_utc must be UTC ISO-8601 ending Z")
            digest = item.get("evidence_sha256")
            if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                errors.append(f"{prefix}.evidence_sha256 must be a lowercase SHA-256 hex digest")
            ref = item.get("source_uri")
            if _nonempty(ref):
                if ref in seen_refs:
                    errors.append(f"{prefix}.source_uri is duplicated")
                seen_refs.add(ref)

    reviewed = record.get("review_state") == "accepted"
    approved = record.get("profile_state") == "approved"
    if reviewed:
        if not _nonempty(record.get("reviewer_id")):
            errors.append("accepted review requires reviewer_id")
        if _utc(record.get("reviewed_at_utc")) is None:
            errors.append("accepted review requires reviewed_at_utc")
    if approved and not reviewed:
        errors.append("approved profile requires accepted review")
    if approved and record.get("verification_state") == "unverified":
        errors.append("approved profile cannot have unverified source status")
    if record.get("profile_state") in {"rejected", "suspended"} and record.get("review_state") == "accepted":
        errors.append("rejected or suspended profile cannot have accepted review")
    return errors


def validate_registry(registry: Any) -> list[str]:
    if not isinstance(registry, dict):
        return ["registry must be an object"]
    errors: list[str] = []
    if registry.get("schema_version") != REGISTRY_VERSION:
        errors.append("registry schema_version must be 1.0.0")
    records = registry.get("profiles")
    if not isinstance(records, list):
        return errors + ["profiles must be an array"]
    identities: set[tuple[str, str, int]] = set()
    revisions: dict[tuple[str, str], list[int]] = {}
    for index, record in enumerate(records):
        record_errors = validate_profile_record(record)
        errors.extend(f"profiles[{index}]: {error}" for error in record_errors)
        if not isinstance(record, dict):
            continue
        key = (record.get("venue_id"), record.get("instrument_id"))
        revision = record.get("revision")
        if isinstance(revision, int) and not isinstance(revision, bool):
            identity = (key[0], key[1], revision)
            if identity in identities:
                errors.append(f"profiles[{index}] duplicates venue/instrument revision")
            identities.add(identity)
            revisions.setdefault(key, []).append(revision)
    for key, values in revisions.items():
        if sorted(values) != list(range(1, max(values) + 1)):
            errors.append(f"profile revisions for {key[0]}/{key[1]} must be contiguous from 1")
    return errors


def resolve_profile(registry: Any, venue_id: str, instrument_id: str,
                    as_of_utc: str) -> dict[str, Any]:
    """Resolve the latest effective profile; never promote it to operational use."""
    errors = validate_registry(registry)
    as_of = _utc(as_of_utc)
    if as_of is None:
        errors.append("as_of_utc must be UTC ISO-8601 ending Z")
    if errors:
        return {
            "status": "BLOCKED_INVALID_REGISTRY", "errors": errors,
            "profile": None, "research_eligible": False,
            "operational_readiness": False, "trade_authority": False,
            "live_readiness": False, "authority": AUTHORITY,
        }
    matches = [
        item for item in registry["profiles"]
        if item["venue_id"] == venue_id and item["instrument_id"] == instrument_id
        and _utc(item["effective_from_utc"]) <= as_of
        and (item.get("effective_to_utc") is None or as_of < _utc(item["effective_to_utc"]))
    ]
    if not matches:
        return {
            "status": "NO_EFFECTIVE_PROFILE", "errors": [],
            "profile": None, "research_eligible": False,
            "operational_readiness": False, "trade_authority": False,
            "live_readiness": False, "authority": AUTHORITY,
        }
    matches.sort(key=lambda item: (item["revision"], item["effective_from_utc"]))
    selected = matches[-1]
    if selected["profile_state"] in {"rejected", "suspended"}:
        state = "BLOCKED_PROFILE_STATE"
    elif selected["verification_state"] == "unverified":
        state = "BLOCKED_UNVERIFIED_PROFILE"
    elif selected["profile_state"] != "approved" or selected["review_state"] != "accepted":
        state = "BLOCKED_UNREVIEWED_PROFILE"
    else:
        state = "RESEARCH_ELIGIBLE_REVIEWED_PROFILE"
    eligible = state == "RESEARCH_ELIGIBLE_REVIEWED_PROFILE"
    return {
        "status": state, "errors": [], "profile": selected if eligible else None,
        "selected_profile_id": selected["profile_id"],
        "selected_revision": selected["revision"],
        "research_eligible": eligible, "operational_readiness": False,
        "trade_authority": False, "live_readiness": False,
        "authority": AUTHORITY,
        "limitations": [
            "Registry metadata and reviewer identity are caller-supplied and unauthenticated.",
            "Evidence hashes establish only equality to supplied bytes; evidence authenticity is not established.",
            "Research eligibility is not broker validation, operational approval or live-trading readiness.",
        ],
    }


def append_profile_revision(registry: Any, record: Any) -> dict[str, Any]:
    """Return a new registry value; does not mutate files or persistent storage."""
    errors = validate_registry(registry)
    errors.extend(validate_profile_record(record))
    if errors:
        return {"status": "BLOCKED_INVALID_REGISTRY_OR_PROFILE", "errors": errors, "registry": None}
    key = (record["venue_id"], record["instrument_id"])
    existing = [item for item in registry["profiles"]
                if (item["venue_id"], item["instrument_id"]) == key]
    expected = max((item["revision"] for item in existing), default=0) + 1
    if record["revision"] != expected:
        return {
            "status": "BLOCKED_REVISION_SEQUENCE",
            "errors": [f"new revision must be {expected}"], "registry": None,
        }
    prior = sorted(existing, key=lambda item: item["revision"])
    if prior:
        latest = prior[-1]
        if _utc(record["effective_from_utc"]) <= _utc(latest["effective_from_utc"]):
            return {
                "status": "BLOCKED_EFFECTIVE_DATE",
                "errors": ["new revision must have a later effective_from_utc"], "registry": None,
            }
        if latest.get("effective_to_utc") is not None and _utc(latest["effective_to_utc"]) > _utc(record["effective_from_utc"]):
            return {
                "status": "BLOCKED_OVERLAPPING_EFFECTIVE_DATES",
                "errors": ["new revision overlaps the prior revision"], "registry": None,
            }
    updated = dict(registry)
    updated_profiles = list(registry["profiles"])
    if prior and prior[-1].get("effective_to_utc") is None:
        # Close the previous validity interval in the returned registry snapshot.
        # Prior revision data remains available, with an explicit end boundary.
        prior_index = updated_profiles.index(prior[-1])
        closed = dict(prior[-1])
        closed["effective_to_utc"] = record["effective_from_utc"]
        updated_profiles[prior_index] = closed
    updated_profiles.append(dict(record))
    updated["profiles"] = updated_profiles
    return {
        "status": "APPENDED_IN_MEMORY", "errors": [], "registry": updated,
        "registry_sha256": _canonical_hash(updated),
        "persistence_performed": False,
        "authority": AUTHORITY, "trade_authority": False, "live_readiness": False,
    }

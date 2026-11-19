"""Fail-closed OCC market-data quarantine and recovery-review state machine.

Pure transition logic over caller-supplied snapshots. It does not persist state,
authenticate operators, clear quarantine, or control external systems.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from .instrument_identity import InstrumentIdentityError, validate_instrument_identity

_FALSE_FLAGS = (
    "independence_verified",
    "provider_identity_authenticated",
    "registry_authority_authenticated",
    "market_data_trusted",
    "consensus_authorized",
    "paper_use_authorized",
    "execution_eligible",
)
_IDENTITY_FIELDS = (
    "market_class", "product_type", "venue", "symbol", "base_currency",
    "quote_currency", "contract_unit", "contract_multiplier",
    "settlement_method", "expiry", "custody_model", "financing_model",
)


class QuarantineStateError(ValueError):
    """A quarantine transition input is malformed or inconsistent."""


def _epoch(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QuarantineStateError(f"{field} must be a finite non-negative epoch")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise QuarantineStateError(f"{field} must be a finite non-negative epoch") from exc
    if not math.isfinite(number) or number < 0:
        raise QuarantineStateError(f"{field} must be a finite non-negative epoch")
    return number


def _identity_key(identity: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(identity.get(field) for field in _IDENTITY_FIELDS)


def _validate_report(report: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(report, Mapping):
        raise QuarantineStateError("agreement_report must be a mapping")
    for flag in _FALSE_FLAGS:
        if report.get(flag) is not False:
            raise QuarantineStateError(f"{flag} must remain false")
    try:
        identity = validate_instrument_identity(report.get("expected_instrument_identity"))
    except InstrumentIdentityError as exc:
        raise QuarantineStateError(f"invalid report instrument identity: {exc}") from exc
    observations = report.get("accepted_observations")
    if not isinstance(observations, list):
        raise QuarantineStateError("accepted_observations must be a list")
    source_ids: list[str] = []
    for item in observations:
        if not isinstance(item, Mapping):
            raise QuarantineStateError("accepted observation must be a mapping")
        source_id = item.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise QuarantineStateError("accepted observation requires source_id")
        source_ids.append(source_id.strip())
    if len(set(source_ids)) != len(source_ids):
        raise QuarantineStateError("accepted source IDs must be unique")
    return identity, sorted(source_ids)


def transition_market_data_quarantine(
    agreement_report: Mapping[str, Any],
    *,
    now_epoch: int | float,
    prior_state: Mapping[str, Any] | None = None,
    recovery_review_claim: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute one fail-closed state transition; no transition clears quarantine.

    A recovery review claim is recorded as unverified metadata only. An
    authenticated host-controlled release mechanism is intentionally absent.
    """
    now = _epoch(now_epoch, "now_epoch")
    identity, source_ids = _validate_report(agreement_report)
    status = agreement_report.get("status")
    if status not in {
        "INPUTS_REJECTED", "INSUFFICIENT_SOURCES",
        "DECLARED_GROUPS_NOT_INDEPENDENTLY_VERIFIED",
        "CONFLICT_DETECTED", "AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED",
    }:
        raise QuarantineStateError("unsupported agreement status")

    prior = prior_state
    was_quarantined = False
    quarantined_at = None
    conflict_count = 0
    prior_source_ids: list[str] = []
    if prior is not None:
        if not isinstance(prior, Mapping):
            raise QuarantineStateError("prior_state must be a mapping")
        if prior.get("state") not in {"NOT_QUARANTINED", "QUARANTINED", "RECOVERY_REVIEW_REQUIRED"}:
            raise QuarantineStateError("unsupported prior quarantine state")
        try:
            prior_identity = validate_instrument_identity(prior.get("instrument_identity"))
        except InstrumentIdentityError as exc:
            raise QuarantineStateError(f"invalid prior instrument identity: {exc}") from exc
        if _identity_key(prior_identity) != _identity_key(identity):
            raise QuarantineStateError("prior state instrument identity mismatch")
        was_quarantined = prior.get("state") in {"QUARANTINED", "RECOVERY_REVIEW_REQUIRED"}
        if was_quarantined:
            quarantined_at = _epoch(prior.get("quarantined_at_epoch"), "quarantined_at_epoch")
            if quarantined_at > now:
                raise QuarantineStateError("prior quarantine timestamp is in the future")
        count = prior.get("conflict_count", 0)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise QuarantineStateError("prior conflict_count must be a non-negative integer")
        conflict_count = count
        values = prior.get("source_ids", [])
        if not isinstance(values, list) or any(not isinstance(x, str) or not x.strip() for x in values):
            raise QuarantineStateError("prior source_ids must be a list of non-empty strings")
        prior_source_ids = sorted(set(x.strip() for x in values))

    if status == "CONFLICT_DETECTED":
        spread = agreement_report.get("diagnostic_spread_bps")
        threshold = agreement_report.get("max_spread_bps")
        spread_n = _epoch(spread, "diagnostic_spread_bps")
        threshold_n = _epoch(threshold, "max_spread_bps")
        if spread_n <= threshold_n:
            raise QuarantineStateError("conflict spread must exceed configured threshold")
        if len(source_ids) < 2:
            raise QuarantineStateError("conflict requires at least two accepted source IDs")
        state = "QUARANTINED"
        quarantined_at = quarantined_at if was_quarantined else now
        conflict_count += 1
        reason = "MARKET_DATA_SOURCE_CONFLICT"
    elif was_quarantined:
        if status == "AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED" and len(source_ids) >= 2:
            state = "RECOVERY_REVIEW_REQUIRED"
            reason = "FRESH_AGREEMENT_IS_NOT_AUTHORIZED_RELEASE"
        else:
            state = "QUARANTINED"
            reason = "RECOVERY_EVIDENCE_INSUFFICIENT"
    else:
        state = "NOT_QUARANTINED"
        reason = "NO_ACTIVE_CONFLICT_REPORTED"

    review_record = None
    if recovery_review_claim is not None:
        if not was_quarantined and state == "NOT_QUARANTINED":
            raise QuarantineStateError("recovery review claim requires an existing quarantine")
        if not isinstance(recovery_review_claim, Mapping):
            raise QuarantineStateError("recovery_review_claim must be a mapping")
        decision = recovery_review_claim.get("decision")
        reviewer = recovery_review_claim.get("reviewer_id")
        evidence = recovery_review_claim.get("evidence_ref")
        reviewed_at = _epoch(recovery_review_claim.get("reviewed_at_epoch"), "reviewed_at_epoch")
        if decision != "APPROVE_RELEASE":
            raise QuarantineStateError("recovery review decision must be APPROVE_RELEASE")
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise QuarantineStateError("reviewer_id must be non-empty")
        if not isinstance(evidence, str) or not evidence.strip():
            raise QuarantineStateError("evidence_ref must be non-empty")
        if reviewed_at > now:
            raise QuarantineStateError("review timestamp cannot be in the future")
        review_record = {
            "decision_claim": decision,
            "reviewer_id_claim": reviewer.strip(),
            "evidence_ref_claim": evidence.strip(),
            "reviewed_at_epoch_claim": reviewed_at,
            "review_claim_authenticated": False,
            "release_authorized": False,
        }
        state = "RECOVERY_REVIEW_REQUIRED"
        reason = "RELEASE_CLAIM_RECORDED_BUT_NOT_AUTHENTICATED"

    merged_sources = sorted(set(prior_source_ids).union(source_ids))
    return {
        "state": state,
        "reason_code": reason,
        "instrument_identity": identity,
        "source_ids": merged_sources,
        "quarantined_at_epoch": quarantined_at,
        "last_evaluated_at_epoch": now,
        "conflict_count": conflict_count,
        "recovery_review": review_record,
        "quarantine_active": state in {"QUARANTINED", "RECOVERY_REVIEW_REQUIRED"},
        "automatic_recovery_performed": False,
        "operator_claim_authenticated": False,
        "release_authorized": False,
        "market_data_trusted": False,
        "paper_use_authorized": False,
        "execution_eligible": False,
        "persistent_audit_written": False,
        "external_system_changed": False,
    }

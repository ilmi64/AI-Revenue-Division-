"""Diagnostic agreement analysis across caller-supplied market observations.

This module never authenticates providers or independence, and never creates
an approved/authoritative price. It is a fail-closed diagnostic only.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from statistics import median
from typing import Any

from .instrument_identity import InstrumentIdentityError, validate_instrument_identity
from .market_data_observation import (
    MarketDataObservationError,
    validate_market_data_observation,
)
from .market_source_registry import (
    MarketSourceRegistryError,
    validate_source_registry,
)

_IDENTITY_FIELDS = (
    "market_class", "product_type", "venue", "symbol", "base_currency",
    "quote_currency", "contract_unit", "contract_multiplier",
    "settlement_method", "expiry", "custody_model", "financing_model",
)


class FeedAgreementError(ValueError):
    """Agreement inputs or thresholds are malformed."""


def _identity_key(identity: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(identity.get(field) for field in _IDENTITY_FIELDS)


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FeedAgreementError(f"{field} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise FeedAgreementError(f"{field} must be a finite number") from exc
    if not math.isfinite(number):
        raise FeedAgreementError(f"{field} must be a finite number")
    return number


def analyze_independent_feed_agreement(
    expected_identity: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
    registry_entries: Sequence[Mapping[str, Any]],
    *,
    now_epoch: int | float,
    max_age_seconds: int | float = 30,
    max_future_skew_seconds: int | float = 5,
    max_spread_bps: int | float = 25,
    min_sources: int = 2,
    min_declared_groups: int = 2,
) -> dict[str, Any]:
    """Return a diagnostic comparison; consensus is never authorized.

    Registry approval and independence-group labels are caller claims. The
    output midpoint median and spread are diagnostic statistics, not a
    consolidated/approved market price.
    """
    if isinstance(observations, (str, bytes, bytearray)) or not isinstance(observations, Sequence):
        raise FeedAgreementError("observations must be a sequence")
    if isinstance(registry_entries, (str, bytes, bytearray)) or not isinstance(registry_entries, Sequence):
        raise FeedAgreementError("registry_entries must be a sequence")
    if isinstance(min_sources, bool) or not isinstance(min_sources, int) or min_sources < 2:
        raise FeedAgreementError("min_sources must be an integer >= 2")
    if isinstance(min_declared_groups, bool) or not isinstance(min_declared_groups, int) or min_declared_groups < 2:
        raise FeedAgreementError("min_declared_groups must be an integer >= 2")

    now = _finite_number(now_epoch, "now_epoch")
    max_age = _finite_number(max_age_seconds, "max_age_seconds")
    future_skew = _finite_number(max_future_skew_seconds, "max_future_skew_seconds")
    threshold = _finite_number(max_spread_bps, "max_spread_bps")
    if max_age < 0 or future_skew < 0 or threshold < 0:
        raise FeedAgreementError("age, future-skew and spread limits cannot be negative")

    try:
        identity = validate_instrument_identity(expected_identity)
        registry = validate_source_registry(registry_entries, now_epoch=now)
    except (InstrumentIdentityError, MarketSourceRegistryError) as exc:
        raise FeedAgreementError(f"invalid identity or registry: {exc}") from exc

    expected_key = _identity_key(identity)
    registry_by_pair: dict[tuple[str, str], Mapping[str, Any]] = {}
    registry_issues: list[str] = []
    for entry in registry["entries"]:
        if _identity_key(entry["instrument_identity"]) != expected_key:
            # A registry may cover many instruments; unrelated valid records
            # are out of scope, not evidence of a malformed observation.
            continue
        pair = (entry["source_id"], entry["adapter_id"])
        registry_by_pair[pair] = entry

    accepted: list[dict[str, Any]] = []
    issues: list[str] = list(registry_issues)
    seen_sources: set[str] = set()
    seen_adapters: set[str] = set()
    seen_source_events: set[tuple[str, str]] = set()

    for index, raw in enumerate(observations):
        if not isinstance(raw, Mapping):
            issues.append(f"observation {index}: record is not a mapping")
            continue
        source_id = raw.get("source_id")
        adapter_id = raw.get("adapter_id")
        if not isinstance(source_id, str) or not source_id.strip():
            issues.append(f"observation {index}: missing source_id")
            continue
        if not isinstance(adapter_id, str) or not adapter_id.strip():
            issues.append(f"observation {index}: missing adapter_id")
            continue
        source_id, adapter_id = source_id.strip(), adapter_id.strip()
        event_id = raw.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            issues.append(f"observation {index}: missing event_id")
            continue
        event_key = (source_id, event_id.strip())
        if event_key in seen_source_events:
            issues.append(f"observation {index}: duplicate event_id for source")
            continue
        seen_source_events.add(event_key)
        if source_id in seen_sources:
            issues.append(f"observation {index}: repeated source_id")
            continue
        if adapter_id in seen_adapters:
            issues.append(f"observation {index}: repeated adapter_id")
            continue

        registry_entry = registry_by_pair.get((source_id, adapter_id))
        if registry_entry is None:
            issues.append(f"observation {index}: no exact instrument-scoped registry record")
            continue
        if registry_entry["review_state"] != "APPROVED_FOR_PAPER":
            issues.append(f"observation {index}: registry review state is not APPROVED_FOR_PAPER")
            continue
        if raw.get("provider_id") != source_id:
            issues.append(f"observation {index}: provider_id does not match source_id")
            continue

        try:
            quote = validate_market_data_observation(
                raw, identity, now_epoch=now,
                max_age_seconds=max_age,
                max_future_skew_seconds=future_skew,
            )
        except MarketDataObservationError as exc:
            issues.append(f"observation {index}: {exc}")
            continue

        if quote["venue"] != registry_entry["venue"]:
            issues.append(f"observation {index}: venue does not match registry")
            continue

        seen_sources.add(source_id)
        seen_adapters.add(adapter_id)
        midpoint = (quote["bid"] + quote["ask"]) / 2.0
        accepted.append({
            "source_id": source_id,
            "adapter_id": adapter_id,
            "declared_independence_group": registry_entry["independence_group"],
            "event_id": quote["event_id"],
            "bid": quote["bid"],
            "ask": quote["ask"],
            "midpoint_diagnostic_only": midpoint,
            "age_seconds": quote["age_seconds"],
        })

    groups = sorted({item["declared_independence_group"] for item in accepted})
    mids = [item["midpoint_diagnostic_only"] for item in accepted]
    diagnostic_median = median(mids) if mids else None
    spread_bps = None
    if len(mids) >= 2 and diagnostic_median and diagnostic_median > 0:
        spread_bps = ((max(mids) - min(mids)) / diagnostic_median) * 10000.0

    if issues:
        status = "INPUTS_REJECTED"
    elif len(accepted) < min_sources:
        status = "INSUFFICIENT_SOURCES"
    elif spread_bps is not None and spread_bps > threshold:
        status = "CONFLICT_DETECTED"
    elif len(groups) < min_declared_groups:
        status = "DECLARED_GROUPS_NOT_INDEPENDENTLY_VERIFIED"
    else:
        status = "AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED"

    return {
        "status": status,
        "expected_instrument_identity": identity,
        "accepted_observation_count": len(accepted),
        "accepted_observations": accepted,
        "declared_independence_groups": groups,
        "declared_group_count": len(groups),
        "diagnostic_midpoint_median": diagnostic_median,
        "diagnostic_spread_bps": spread_bps,
        "max_spread_bps": threshold,
        "issues": issues,
        "independence_verified": False,
        "provider_identity_authenticated": False,
        "registry_authority_authenticated": False,
        "market_data_trusted": False,
        "consensus_authorized": False,
        "paper_use_authorized": False,
        "execution_eligible": False,
    }

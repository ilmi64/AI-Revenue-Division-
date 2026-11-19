"""Project diagnostic market-data conflicts into normalized OCC incident records.

This is a pure projection. It does not persist, acknowledge, resolve or notify.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


class FeedConflictProjectionError(ValueError):
    """A conflict diagnostic cannot safely be projected into an OCC incident."""


_REQUIRED_FALSE_FLAGS = (
    "independence_verified",
    "provider_identity_authenticated",
    "registry_authority_authenticated",
    "market_data_trusted",
    "consensus_authorized",
    "paper_use_authorized",
    "execution_eligible",
)


def project_feed_conflict_incident(
    agreement_report: Mapping[str, Any], *, now_epoch: int | float
) -> dict[str, Any] | None:
    """Return an OPEN CRITICAL OCC incident for a validated conflict, else None.

    Non-conflict statuses intentionally produce no incident. A conflict report
    must retain all false trust/authorization flags from the agreement layer.
    """
    if not isinstance(agreement_report, Mapping):
        raise FeedConflictProjectionError("agreement_report must be a mapping")
    if isinstance(now_epoch, bool) or not isinstance(now_epoch, (int, float)):
        raise FeedConflictProjectionError("now_epoch must be a finite non-negative epoch")
    now = float(now_epoch)
    if not math.isfinite(now) or now < 0:
        raise FeedConflictProjectionError("now_epoch must be a finite non-negative epoch")

    status = agreement_report.get("status")
    if status != "CONFLICT_DETECTED":
        return None

    for flag in _REQUIRED_FALSE_FLAGS:
        if agreement_report.get(flag) is not False:
            raise FeedConflictProjectionError(f"{flag} must remain false")

    identity = agreement_report.get("expected_instrument_identity")
    if not isinstance(identity, Mapping):
        raise FeedConflictProjectionError("conflict report is missing instrument identity")
    symbol = identity.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip():
        raise FeedConflictProjectionError("instrument symbol must be non-empty")

    observations = agreement_report.get("accepted_observations")
    if not isinstance(observations, list) or len(observations) < 2:
        raise FeedConflictProjectionError("conflict requires at least two accepted observations")
    source_ids = []
    for item in observations:
        if not isinstance(item, Mapping):
            raise FeedConflictProjectionError("accepted observation must be a mapping")
        source_id = item.get("source_id")
        if not isinstance(source_id, str) or not source_id.strip():
            raise FeedConflictProjectionError("accepted observation is missing source_id")
        source_ids.append(source_id.strip())
    if len(set(source_ids)) != len(source_ids):
        raise FeedConflictProjectionError("conflict report contains repeated source IDs")

    spread = agreement_report.get("diagnostic_spread_bps")
    threshold = agreement_report.get("max_spread_bps")
    for value, field in ((spread, "diagnostic_spread_bps"), (threshold, "max_spread_bps")):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise FeedConflictProjectionError(f"{field} must be finite")
    if float(spread) <= float(threshold) or float(threshold) < 0:
        raise FeedConflictProjectionError("conflict spread must exceed a non-negative threshold")

    source_ids.sort()
    incident_id = f"feed-conflict:{symbol.strip().upper()}:{','.join(source_ids)}"
    return {
        "source_system": "OCC_MARKET_DATA_AGREEMENT",
        "source_incident_id": incident_id,
        "division": "OCC",
        "severity": "CRITICAL",
        "status": "OPEN",
        "reason_code": "MARKET_DATA_SOURCE_CONFLICT",
        "summary": (
            f"Conflicting market-data observations for {symbol.strip().upper()}; "
            "market-data trust and all use authorizations remain disabled."
        ),
        "observed_at_epoch": now,
        "updated_at_epoch": now,
        "instrument": symbol.strip().upper(),
        "source_ids": source_ids,
        "diagnostic_spread_bps": float(spread),
        "configured_threshold_bps": float(threshold),
        "read_only_projection": True,
        "source_mutation_performed": False,
        "notification_sent": False,
        "execution_eligible": False,
    }

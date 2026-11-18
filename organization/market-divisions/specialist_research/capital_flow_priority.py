"""Conservative Capital Flow research queue priority; never a trading signal."""
from __future__ import annotations

from typing import Any


BLOCKING_FLAGS = {
    "stale_observation", "duplicate_conflict", "possible_self_transfer",
    "exchange_hot_wallet_reshuffle", "bridge_hop", "wrapped_token_mint_burn",
    "internal_treasury_move", "self_transfer",
}


def assess_research_priority(event: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    flags = event.get("quality_flags", [])
    flags = flags if isinstance(flags, list) else ["malformed_quality_flags"]
    blockers = sorted(BLOCKING_FLAGS.intersection(x for x in flags if isinstance(x, str)))
    reasons: list[str] = []
    materiality = event.get("materiality")
    reliability = event.get("source_reliability")
    attribution = event.get("attribution_confidence")
    confidence = event.get("event_confidence")
    if blockers:
        reasons.append("blocking_quality_flags:" + ",".join(blockers))
        priority = "blocked_from_priority_queue"
    elif provenance.get("status") != "metadata_complete_unverified":
        reasons.append("evidence_provenance_metadata_incomplete")
        priority = "insufficient_provenance"
    elif any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 5
             for v in (materiality, reliability, attribution, confidence)):
        reasons.append("one_or_more_confidence_dimensions_invalid")
        priority = "insufficient_evidence"
    elif materiality >= 4 and reliability >= 3 and attribution >= 3 and confidence >= 4:
        reasons.append("high_materiality_and_minimum_quality_thresholds_met")
        priority = "high_review_priority"
    elif materiality >= 2 and reliability >= 2 and attribution >= 2 and confidence >= 2:
        reasons.append("baseline_research_thresholds_met")
        priority = "standard_review_priority"
    else:
        reasons.append("below_baseline_research_thresholds")
        priority = "low_review_priority"
    return {
        "priority": priority,
        "reasons": reasons,
        "review_queue_only": True,
        "not_a_directional_signal": True,
        "not_a_market_observation": True,
        "trade_authority": False,
        "live_readiness": False,
    }

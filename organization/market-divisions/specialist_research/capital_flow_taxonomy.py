"""Deterministic Capital Flow event taxonomy and research materiality annotations.

Classification is descriptive only. It does not create a directional signal,
prove source independence, or authorize trading.
"""
from __future__ import annotations

from typing import Any

# Exact aliases first; conservative substring groups second.
EVENT_TYPES = {
    "large_wallet_transfer": ("whale_movement", "large_wallet_transfer"),
    "whale_transfer": ("whale_movement", "large_wallet_transfer"),
    "exchange_inflow": ("exchange_flow", "exchange_inflow"),
    "exchange_outflow": ("exchange_flow", "exchange_outflow"),
    "exchange_netflow": ("exchange_flow", "exchange_netflow"),
    "treasury_transfer": ("treasury_activity", "treasury_transfer"),
    "treasury_deployment": ("treasury_activity", "treasury_deployment"),
    "token_unlock": ("supply_event", "token_unlock"),
    "vesting_unlock": ("supply_event", "vesting_unlock"),
    "fundraising_round": ("fundraising", "fundraising_round"),
    "token_launch": ("launch_activity", "token_launch"),
    "launchpad_sale": ("launch_activity", "launchpad_sale"),
    "vc_investment": ("institutional_capital", "vc_investment"),
    "fund_investment": ("institutional_capital", "fund_investment"),
    "developer_funding": ("ecosystem_capital", "developer_funding"),
    "ecosystem_grant": ("ecosystem_capital", "ecosystem_grant"),
    "bridge_transfer": ("cross_chain_flow", "bridge_transfer"),
    "protocol_revenue": ("protocol_fundamentals", "protocol_revenue"),
}
KEYWORDS = (
    (("whale", "large_wallet"), ("whale_movement", "large_wallet_transfer")),
    (("exchange", "inflow"), ("exchange_flow", "exchange_inflow")),
    (("exchange", "outflow"), ("exchange_flow", "exchange_outflow")),
    (("treasury", "deploy"), ("treasury_activity", "treasury_deployment")),
    (("treasury",), ("treasury_activity", "treasury_transfer")),
    (("unlock", "vesting"), ("supply_event", "vesting_unlock")),
    (("unlock",), ("supply_event", "token_unlock")),
    (("fundrais",), ("fundraising", "fundraising_round")),
    (("launchpad",), ("launch_activity", "launchpad_sale")),
    (("launch",), ("launch_activity", "token_launch")),
    (("venture", "invest"), ("institutional_capital", "vc_investment")),
    (("vc",), ("institutional_capital", "vc_investment")),
    (("developer", "fund"), ("ecosystem_capital", "developer_funding")),
    (("grant",), ("ecosystem_capital", "ecosystem_grant")),
    (("bridge",), ("cross_chain_flow", "bridge_transfer")),
    (("revenue",), ("protocol_fundamentals", "protocol_revenue")),
)

def classify_event(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("event_type")
    normalized = raw.strip().lower().replace("-", "_").replace(" ", "_") if isinstance(raw, str) else ""
    category, subtype = EVENT_TYPES.get(normalized, ("unclassified", "unclassified"))
    if category == "unclassified":
        for terms, mapped in KEYWORDS:
            if all(term in normalized for term in terms):
                category, subtype = mapped
                break
    materiality = event.get("materiality")
    tier = ("unknown" if isinstance(materiality, bool) or not isinstance(materiality, int)
            else "low" if materiality <= 1
            else "moderate" if materiality <= 2
            else "high" if materiality <= 4
            else "critical")
    source_ids = event.get("source_ids")
    source_count = len(set(source_ids)) if isinstance(source_ids, list) and all(
        isinstance(item, str) for item in source_ids) else 0
    claimed = event.get("corroboration_count", 0)
    if isinstance(claimed, bool) or not isinstance(claimed, int) or claimed < 0:
        claimed = None
    return {
        "category": category,
        "subtype": subtype,
        "classification_status": "classified" if category != "unclassified" else "unclassified",
        "materiality_score": materiality if tier != "unknown" else None,
        "materiality_tier": tier,
        "source_reliability_score": event.get("source_reliability"),
        "attribution_confidence_score": event.get("attribution_confidence"),
        "event_confidence_score": event.get("event_confidence"),
        "source_count": source_count,
        "claimed_corroboration_count": claimed,
        "corroboration_assessment": (
            "multiple_sources_claimed_independence_not_verified" if source_count > 1 or (claimed or 0) > 1
            else "single_or_unconfirmed_source"
        ),
        "source_independence_verified": False,
        "direction": event.get("direction", "unknown"),
        "research_only": True,
        "trade_authority": False,
    }

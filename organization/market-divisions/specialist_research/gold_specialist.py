"""Independent Gold/XAUUSD macro, session and instrument-basis research contract.

Consumes supplied observations only. It does not fetch prices, infer a trade
direction, create a signal, or grant execution authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

MACRO_FACTORS = {
    "real_yields": {"real_yield", "real_rate", "inflation_adjusted_yield"},
    "usd": {"dxy", "usd_index", "usd_broad_index", "usd_pair"},
    "central_bank_demand": {"central_bank_gold_demand", "official_sector_purchase"},
    "etf_flows": {"gold_etf_flow", "gold_etf_holdings"},
    "positioning": {"cot_positioning", "futures_open_interest", "managed_money_position"},
    "physical_demand": {"physical_gold_demand", "bar_coin_premium", "regional_premium"},
    "geopolitical_risk": {"geopolitical_risk_context"},
    "rates_policy": {"central_bank_policy", "policy_rate_expectation"},
}
MAX_EVIDENCE_AGE_SECONDS = 7 * 24 * 60 * 60


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.utcoffset() == timezone.utc.utcoffset(parsed) else None


def build_gold_research_context(observation: dict[str, Any], now_utc: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    now = _parse_utc(now_utc)
    if now is None:
        errors.append("evaluation timestamp must be valid UTC")
    kind = observation.get("instrument_type")
    if kind not in {"xauusd_spot", "gold_future", "gold_cfd"}:
        errors.append("Gold desk instrument type is unsupported")
    basis = observation.get("gold_price_basis")
    allowed_basis = {
        "xauusd_spot": {"broker_executable_xauusd", "indicative_bullion_spot", "synthetic_test"},
        "gold_future": {"comex_futures", "synthetic_test"},
        "gold_cfd": {"gold_cfd", "synthetic_test"},
    }
    if basis not in allowed_basis.get(kind, set()):
        errors.append("quote/contract basis does not match Gold instrument type")
    evidence = observation.get("macro_evidence", [])
    if not isinstance(evidence, list):
        errors.append("macro_evidence must be an array")
        evidence = []
    accepted: dict[str, list[dict[str, Any]]] = {key: [] for key in MACRO_FACTORS}
    seen_refs: set[str] = set()
    seen_source_category: set[tuple[str, str]] = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"macro_evidence[{index}] must be an object")
            continue
        category = item.get("factor")
        evidence_type = item.get("evidence_type")
        if category not in MACRO_FACTORS or evidence_type not in MACRO_FACTORS.get(category, set()):
            errors.append(f"macro_evidence[{index}] has unsupported factor/evidence_type")
            continue
        ref, source = item.get("evidence_ref"), item.get("source_id")
        if not isinstance(ref, str) or not ref.strip() or ref in seen_refs:
            errors.append(f"macro_evidence[{index}] has missing or duplicate evidence_ref")
            continue
        if not isinstance(source, str) or not source.strip():
            errors.append(f"{ref}: source_id missing")
            continue
        seen_refs.add(ref)
        observed = _parse_utc(item.get("observed_at_utc"))
        if observed is None:
            errors.append(f"{ref}: observed_at_utc must be valid UTC")
            continue
        age = (now - observed).total_seconds() if now else None
        if age is not None and (age < 0 or age > MAX_EVIDENCE_AGE_SECONDS):
            warnings.append(f"{ref}: macro evidence is future-dated or older than seven days")
        if item.get("source_status") not in {"verified", "approved"}:
            warnings.append(f"{ref}: source status is not verified/approved")
        accepted[category].append({
            "evidence_ref": ref, "source_id": source,
            "evidence_type": evidence_type, "observed_at_utc": item.get("observed_at_utc"),
            "value": item.get("value"), "unit": item.get("unit"),
            "source_status": item.get("source_status"),
            "declared_source_group": item.get("source_group"),
        })
        seen_source_category.add((category, source))
    for factor in MACRO_FACTORS:
        if not accepted[factor]:
            warnings.append(f"Gold macro factor missing: {factor}")
    session = observation.get("gold_session")
    if not isinstance(session, dict):
        errors.append("gold_session must be a structured session/calendar object")
        session = {}
    else:
        if session.get("market_timezone") not in {"America/New_York", "Europe/London", "Asia/Hong_Kong", "UTC"}:
            warnings.append("Gold session timezone missing or outside supported reference zones")
        if session.get("session_name") not in {"asia", "london", "new_york", "overlap", "closed", "holiday"}:
            errors.append("Gold session_name invalid")
        if session.get("calendar_status") not in {"verified", "holiday_checked", "unknown"}:
            warnings.append("Gold trading calendar has not been verified")
    spread = observation.get("spread")
    bid, ask = observation.get("bid"), observation.get("ask")
    quote_currency = observation.get("currency")
    if quote_currency != "USD":
        errors.append("XAUUSD quote currency must be USD")
    try:
        bid, ask = float(bid), float(ask)
        if bid <= 0 or ask <= bid:
            raise ValueError
        calculated = ask - bid
        if spread is not None and abs(float(spread) - calculated) > max(1e-8, calculated * 0.01):
            errors.append("reported spread does not reconcile to ask minus bid")
        spread = calculated
    except (TypeError, ValueError):
        errors.append("Gold bid/ask must be positive and ask must exceed bid")
    try:
        quote_age = float(observation.get("quote_age_seconds"))
        stale_limit = float(observation.get("stale_threshold_seconds"))
        if quote_age < 0 or stale_limit <= 0 or quote_age > stale_limit or observation.get("is_stale") is not False:
            errors.append("Gold quote stale or freshness flag invalid")
    except (TypeError, ValueError):
        errors.append("Gold quote age and stale threshold required")
    if kind == "gold_future":
        if not observation.get("contract_code") or not _parse_utc(observation.get("expiry_utc")):
            errors.append("COMEX contract code and UTC expiry required")
        if observation.get("roll_status") not in {"front_month", "next_month", "roll_window", "expired", "unknown"}:
            errors.append("futures roll_status invalid")
        if observation.get("roll_status") in {"roll_window", "expired", "unknown"}:
            warnings.append("futures roll/expiry basis requires manual review")
    if kind == "gold_cfd":
        if not observation.get("broker_symbol") or not observation.get("contract_unit"):
            errors.append("Gold CFD broker symbol and contract unit required")
    if observation.get("financing_status") not in {"reviewed", "not_applicable"}:
        warnings.append("overnight financing/swap terms not reviewed")
    if observation.get("settlement_type") not in {"physical", "cash", "cash_settled", "not_applicable"}:
        warnings.append("settlement mechanics not verified")
    if observation.get("shariah_review_status") != "instrument_specific_reviewed":
        warnings.append("instrument-specific Shariah/product review not completed")
    if basis == "indicative_bullion_spot":
        warnings.append("indicative bullion spot is not broker-executable XAUUSD")
    return {
        "desk_id": "gold",
        "instrument_id": observation.get("instrument_id"),
        "instrument_type": kind,
        "price_basis": basis,
        "macro_evidence": accepted,
        "macro_factor_coverage": {key: bool(value) for key, value in accepted.items()},
        "macro_factor_count": sum(bool(value) for value in accepted.values()),
        "session": session,
        "microstructure": {
            "bid": observation.get("bid"), "ask": observation.get("ask"),
            "spread": spread, "currency": quote_currency,
            "quote_age_seconds": observation.get("quote_age_seconds"),
        },
        "contract": {
            "contract_code": observation.get("contract_code"),
            "expiry_utc": observation.get("expiry_utc"),
            "broker_symbol": observation.get("broker_symbol"),
            "contract_unit": observation.get("contract_unit"),
            "roll_status": observation.get("roll_status", "unknown"),
            "financing_status": observation.get("financing_status", "unknown"),
            "settlement_type": observation.get("settlement_type", "unknown"),
            "shariah_review_status": observation.get("shariah_review_status", "unassessed"),
        },
        "source_independence_verified": False,
        "errors": errors, "warnings": warnings,
        "status": "halt" if errors else "unverified" if warnings else "research",
        "authority": "research_only_no_execution_authority",
        "trade_authority": False, "live_readiness": False,
        "directional_signal": None,
        "limitations": [
            "Macro evidence is supplied by the caller and is not independently authenticated",
            "Different source IDs do not prove independent ownership or collection paths",
            "Macro factor coverage is descriptive, not a forecast or directional score",
            "This module does not calculate leverage, position size, orders or execution permission",
        ],
    }

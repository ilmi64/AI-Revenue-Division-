"""Offline, deterministic specialist research engines for OCC Sprint 3.

These engines consume already-collected observations and evidence. They perform no
network access, market-data retrieval, broker/wallet interaction, or execution.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

try:
    from .gold_specialist import build_gold_research_context
except ImportError:
    from gold_specialist import build_gold_research_context

DESK_TYPES = {
    "crypto": {"crypto_spot", "crypto_perpetual"},
    "forex": {"fx_spot"},
    "indices": {"index_cash", "index_future", "index_cfd"},
    "gold": {"xauusd_spot", "gold_future", "gold_cfd"},
}
RESEARCH_STATES = {"watch", "research", "unverified", "corroborated", "rejected", "expired"}


def _utc(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        errors.append(f"{field} must be an ISO-8601 UTC timestamp ending Z")
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            raise ValueError
        return parsed
    except ValueError:
        errors.append(f"{field} is not a valid UTC timestamp")
        return None


def _base_packet(desk: str, observation: dict[str, Any], now_utc: str,
                 evidence_refs: list[str] | None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    instrument_type = observation.get("instrument_type")
    if instrument_type not in DESK_TYPES[desk]:
        errors.append(f"instrument_type is not valid for {desk} desk")
    if not isinstance(observation.get("instrument_id"), str) or not observation.get("instrument_id"):
        errors.append("instrument_id missing")
    if not isinstance(observation.get("source_id"), str) or not observation.get("source_id"):
        errors.append("source_id missing")
    source_time = _utc(observation.get("source_timestamp_utc"), "source_timestamp_utc", errors)
    received_time = _utc(observation.get("received_timestamp_utc"), "received_timestamp_utc", errors)
    now = _utc(now_utc, "now_utc", errors)
    if source_time and received_time and received_time < source_time:
        warnings.append("received timestamp precedes source timestamp")
    if source_time and now and source_time > now:
        errors.append("observation timestamp is in the future")
    if observation.get("data_class") != "live":
        warnings.append("non-live observation: research context only")
    if observation.get("licence_status") not in {"approved", "not_applicable"}:
        errors.append("source licence is not approved")
    if observation.get("session_state") in {None, "unknown", "halted"}:
        warnings.append("session state is unknown or halted")
    refs = evidence_refs if evidence_refs is not None else observation.get("evidence_refs", [])
    if not isinstance(refs, list) or any(not isinstance(x, str) or not x for x in refs):
        errors.append("evidence_refs must be an array of non-empty strings")
        refs = []
    if not refs:
        warnings.append("no supporting evidence references supplied")
    return {
        "desk_id": desk,
        "instrument_id": observation.get("instrument_id"),
        "instrument_type": instrument_type,
        "as_of_utc": now_utc,
        "portfolio_version": observation.get("portfolio_version"),
        "mode": "research_only",
        "status": "unverified",
        "confidence_band": "not_assessed",
        "evidence_refs": sorted(set(refs)),
        "data_quality": {"errors": errors, "warnings": warnings},
        "risk_flags": [],
        "context": {},
        "limitations": ["No trade authority", "No live-readiness determination"],
        "trade_authority": False,
    }


def _finish(packet: dict[str, Any]) -> dict[str, Any]:
    if packet["data_quality"]["errors"]:
        packet["status"] = "halt"
        packet["risk_flags"].append("DATA_QUALITY_BLOCK")
    elif packet["data_quality"]["warnings"]:
        packet["status"] = "unverified"
    else:
        packet["status"] = "research"
    packet["risk_flags"] = sorted(set(packet["risk_flags"]))
    return packet


def assess_crypto(observation: dict[str, Any], now_utc: str,
                  evidence_refs: list[str] | None = None) -> dict[str, Any]:
    p = _base_packet("crypto", observation, now_utc, evidence_refs)
    errors = p["data_quality"]["errors"]
    base, quote = observation.get("base_asset"), observation.get("quote_asset")
    if not base or not quote or base == quote:
        errors.append("Crypto base/quote identity missing or invalid")
    if observation.get("market_pair") != f"{base}/{quote}":
        errors.append("market_pair must exactly match BASE/QUOTE")
    if observation.get("currency") != quote or observation.get("quote_asset") != quote:
        errors.append("quote asset must match observation currency")
    if observation.get("token_identity_status") != "verified":
        errors.append("token or market identity is not verified")
        p["risk_flags"].append("TOKEN_IDENTITY_UNVERIFIED")
    elif not observation.get("chain_id") or not observation.get("contract_address"):
        errors.append("verified Crypto identity requires chain_id and contract_address")
    if observation.get("instrument_type") == "crypto_perpetual":
        if not observation.get("settlement_asset"):
            errors.append("perpetual settlement asset missing")
        rate, interval = observation.get("funding_rate"), observation.get("funding_interval_hours")
        if rate is None or interval is None:
            p["data_quality"]["warnings"].append("funding context incomplete")
        p["context"]["funding_rate"] = rate
        p["context"]["funding_interval_hours"] = interval
    p["context"].update({
        "base_asset": base, "quote_asset": quote,
        "chain_id": observation.get("chain_id"),
        "contract_address": observation.get("contract_address"),
        "liquidity_evidence": observation.get("liquidity_evidence", "not_supplied"),
        "unlock_flow_evidence": observation.get("unlock_flow_evidence", "not_supplied"),
        "venue_market_structure": observation.get("venue_market_structure", "not_supplied"),
    })
    if not observation.get("liquidity_evidence"):
        p["data_quality"]["warnings"].append("liquidity/depth evidence not supplied")
    return _finish(p)


def assess_forex(observation: dict[str, Any], now_utc: str,
                 evidence_refs: list[str] | None = None) -> dict[str, Any]:
    p = _base_packet("forex", observation, now_utc, evidence_refs)
    errors = p["data_quality"]["errors"]
    base, quote = observation.get("base_currency"), observation.get("quote_currency")
    if not base or not quote or base == quote:
        errors.append("FX base/quote currency mapping missing or invalid")
    if observation.get("quote_convention") != "quote_per_base":
        errors.append("FX quote convention must be quote currency per one base unit")
    if observation.get("currency") != quote:
        errors.append("FX observation currency must equal quote currency")
    p["context"].update({
        "base_currency": base, "quote_currency": quote,
        "quote_convention": observation.get("quote_convention"),
        "central_bank_evidence": observation.get("central_bank_evidence", "not_supplied"),
        "macro_calendar_evidence": observation.get("macro_calendar_evidence", "not_supplied"),
        "session_calendar": observation.get("session_calendar", "not_supplied"),
        "financing_status": observation.get("financing_status", "unknown"),
    })
    if not observation.get("central_bank_evidence") or not observation.get("macro_calendar_evidence"):
        p["data_quality"]["warnings"].append("macro/central-bank evidence incomplete")
    if observation.get("financing_status") in {None, "unknown", "not_reviewed"}:
        p["data_quality"]["warnings"].append("financing and rollover terms unassessed")
        p["risk_flags"].append("FINANCING_UNASSESSED")
    return _finish(p)


def assess_indices(observation: dict[str, Any], now_utc: str,
                   evidence_refs: list[str] | None = None) -> dict[str, Any]:
    p = _base_packet("indices", observation, now_utc, evidence_refs)
    errors = p["data_quality"]["errors"]
    kind = observation.get("instrument_type")
    if kind == "index_cash":
        if not observation.get("index_code") or observation.get("index_calculation_currency") != observation.get("currency"):
            errors.append("cash index code/calculation currency mismatch")
    elif kind == "index_future":
        if not observation.get("contract_code") or not observation.get("expiry_utc"):
            errors.append("index future contract code and expiry required")
    elif kind == "index_cfd":
        if not observation.get("broker_symbol") or not observation.get("contract_unit"):
            errors.append("index CFD broker symbol and contract unit required")
    p["context"].update({
        "index_code": observation.get("index_code"),
        "contract_code": observation.get("contract_code"),
        "expiry_utc": observation.get("expiry_utc"),
        "broker_symbol": observation.get("broker_symbol"),
        "contract_unit": observation.get("contract_unit"),
        "constituent_weight_provenance": observation.get("constituent_weight_provenance", "not_supplied"),
        "roll_basis_evidence": observation.get("roll_basis_evidence", "not_supplied"),
    })
    if not observation.get("constituent_weight_provenance"):
        p["data_quality"]["warnings"].append("constituent and concentration provenance not supplied")
    if kind == "index_future" and not observation.get("roll_basis_evidence"):
        p["data_quality"]["warnings"].append("futures roll/basis evidence not supplied")
    return _finish(p)


def assess_gold(observation: dict[str, Any], now_utc: str,
                evidence_refs: list[str] | None = None) -> dict[str, Any]:
    p = _base_packet("gold", observation, now_utc, evidence_refs)
    errors = p["data_quality"]["errors"]
    kind = observation.get("instrument_type")
    expected = {
        "xauusd_spot": {"broker_executable_xauusd", "indicative_bullion_spot", "synthetic_test"},
        "gold_future": {"comex_futures", "synthetic_test"},
        "gold_cfd": {"gold_cfd", "synthetic_test"},
    }
    if observation.get("gold_price_basis") not in expected.get(kind, set()):
        errors.append("Gold price basis does not match instrument type")
    if not observation.get("gold_session"):
        errors.append("Gold session/calendar provenance missing")
    try:
        age = float(observation.get("quote_age_seconds"))
        threshold = float(observation.get("stale_threshold_seconds"))
        if age < 0 or threshold <= 0:
            raise ValueError
        if age > threshold or observation.get("is_stale") is not False:
            errors.append("Gold quote is stale or stale flag is not explicitly false")
    except (TypeError, ValueError):
        errors.append("Gold quote age/threshold invalid")
    if kind == "gold_future" and (not observation.get("contract_code") or not observation.get("expiry_utc")):
        errors.append("Gold futures contract code and expiry required")
    if kind == "gold_cfd" and (not observation.get("broker_symbol") or not observation.get("contract_unit")):
        errors.append("Gold CFD broker symbol and contract unit required")
    financing = observation.get("financing_status", "unknown")
    settlement = observation.get("settlement_type", "unknown")
    if financing in {None, "unknown", "not_reviewed"}:
        p["data_quality"]["warnings"].append("financing/swap terms unassessed")
        p["risk_flags"].append("FINANCING_UNASSESSED")
    if settlement in {None, "unknown", "not_reviewed"}:
        p["data_quality"]["warnings"].append("settlement structure unassessed")
        p["risk_flags"].append("SETTLEMENT_UNASSESSED")
    if observation.get("gold_price_basis") == "indicative_bullion_spot":
        p["data_quality"]["warnings"].append("indicative bullion is not broker-executable XAUUSD")
    if observation.get("spot_futures_basis") is not None:
        refs = observation.get("evidence_refs", [])
        sources = observation.get("spot_futures_leg_source_ids")
        times = observation.get("spot_futures_leg_timestamps_utc")
        if not isinstance(refs, list) or len(set(refs)) < 2:
            errors.append("spot/futures basis requires two evidence references")
        if not isinstance(sources, list) or len(set(sources)) != 2:
            errors.append("spot/futures basis requires two distinct source IDs")
        if not isinstance(times, list) or len(times) != 2:
            errors.append("spot/futures basis requires two leg timestamps")
        else:
            t1 = _utc(times[0], "spot_futures_leg_timestamps_utc[0]", errors)
            t2 = _utc(times[1], "spot_futures_leg_timestamps_utc[1]", errors)
            if t1 and t2 and abs((t1 - t2).total_seconds()) > 5:
                errors.append("spot/futures basis legs are not time-aligned")
    p["context"].update({
        "gold_price_basis": observation.get("gold_price_basis"),
        "gold_session": observation.get("gold_session"),
        "quote_age_seconds": observation.get("quote_age_seconds"),
        "financing_status": financing,
        "settlement_type": settlement,
        "real_yield_evidence": observation.get("real_yield_evidence", "not_supplied"),
        "usd_evidence": observation.get("usd_evidence", "not_supplied"),
        "central_bank_demand_evidence": observation.get("central_bank_demand_evidence", "not_supplied"),
        "spot_futures_basis": observation.get("spot_futures_basis"),
        "expiry_utc": observation.get("expiry_utc"),
        "roll_status": observation.get("roll_status", "unknown"),
        "shariah_review_status": observation.get("shariah_review_status", "unassessed"),
    })
    if not all(observation.get(k) for k in ("real_yield_evidence", "usd_evidence", "central_bank_demand_evidence")):
        p["data_quality"]["warnings"].append("Gold macro evidence set incomplete")
    if observation.get("shariah_review_status") != "instrument_specific_reviewed":
        p["risk_flags"].append("SHARIAH_PRODUCT_REVIEW_UNASSESSED")
        p["data_quality"]["warnings"].append("No instrument-specific Shariah/product conclusion")
    if isinstance(observation.get("gold_session"), dict) or "macro_evidence" in observation:
        specialist = build_gold_research_context(observation, now_utc)
        p["context"]["gold_specialist_research"] = specialist
        p["data_quality"]["errors"].extend(specialist["errors"])
        p["data_quality"]["warnings"].extend(specialist["warnings"])
        if specialist["status"] == "halt":
            p["risk_flags"].append("GOLD_SPECIALIST_CONTEXT_BLOCK")
    return _finish(p)


ASSESSORS: dict[str, Callable[..., dict[str, Any]]] = {
    "crypto": assess_crypto, "forex": assess_forex,
    "indices": assess_indices, "gold": assess_gold,
}


def coordinate(packets: list[dict[str, Any]], now_utc: str) -> dict[str, Any]:
    """OCC read-only aggregation. Any valid desk stop challenge vetoes the batch."""
    errors: list[str] = []
    if not isinstance(packets, list) or not packets:
        errors.append("no specialist packets supplied")
        packets = []
    identities = [
        (p.get("desk_id"), p.get("instrument_id"))
        for p in packets if isinstance(p, dict)
    ]
    if len(identities) != len(set(identities)):
        errors.append("duplicate desk/instrument packet identity in coordination batch")
    instrument_ids = [p.get("instrument_id") for p in packets
                      if isinstance(p, dict) and isinstance(p.get("instrument_id"), str)]
    if len(instrument_ids) != len(set(instrument_ids)):
        errors.append("duplicate instrument_id across coordination batch")
    versions = {p.get("portfolio_version") for p in packets if isinstance(p, dict)}
    times = {p.get("as_of_utc") for p in packets if isinstance(p, dict)}
    if len(versions) > 1:
        errors.append("portfolio version mismatch across desks")
    if len(times) > 1:
        errors.append("as_of timestamp mismatch across desks")
    halts = [p.get("desk_id") for p in packets
             if isinstance(p, dict) and (p.get("status") == "halt" or
                 "STOP_CHALLENGE" in p.get("risk_flags", []))]
    invalid = [p.get("desk_id") if isinstance(p, dict) else "non_object_packet" for p in packets
               if not isinstance(p, dict) or p.get("mode") != "research_only"
               or p.get("trade_authority") is not False]
    if invalid:
        errors.append("packet violates research-only authority contract")
    status = "halt" if errors or halts else (
        "unverified" if any(isinstance(p, dict) and p.get("status") == "unverified" for p in packets) else "research"
    )
    return {
        "desk_id": "occ_coordinator",
        "as_of_utc": now_utc,
        "status": status,
        "mode": "research_only",
        "portfolio_version": next(iter(versions)) if len(versions) == 1 else None,
        "desk_count": len({p.get("desk_id") for p in packets if isinstance(p, dict)}),
        "packet_count": len(packets),
        "halted_desks": sorted(halts),
        "errors": errors,
        "packets": packets,
        "authority": "coordination_and_stop_veto_only",
        "trade_authority": False,
        "live_readiness": False,
    }

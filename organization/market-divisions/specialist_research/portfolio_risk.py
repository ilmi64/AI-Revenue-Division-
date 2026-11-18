"""Deterministic, read-only OCC portfolio risk aggregation.

Consumes explicitly supplied, already-valued exposure records from specialist packets.
It never invents positions, prices, FX conversions, correlations or risk limits.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

DESKS = ("crypto", "forex", "indices", "gold")
AUTHORITY = "research_only_no_execution_authority"


def _number(value: Any, field: str, errors: list[str], *, minimum: float = 0.0) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        errors.append(f"{field} must be a finite number")
        return None
    result = float(value)
    if result < minimum:
        errors.append(f"{field} must be >= {minimum}")
        return None
    return result


def _utc(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        errors.append(f"{field} must be a UTC ISO-8601 timestamp ending Z")
        return None
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        errors.append(f"{field} is invalid")
        return None
    if result.utcoffset() != timezone.utc.utcoffset(result):
        errors.append(f"{field} must be UTC")
        return None
    return result


def assess_portfolio_risk(
    packets: list[dict[str, Any]],
    now_utc: str,
    risk_config: dict[str, Any] | None = None,
    correlation_evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggregate comparable exposure and fail closed on missing/invalid inputs.

    Each packet may carry context.portfolio_risk = {
      "positions": [{
        "position_id", "instrument_id", "asset_class", "side",
        "notional", "currency", "valuation_currency", "valuation_amount",
        "exposure_group", "evidence_refs", "source_timestamp_utc"
      }]
    }
    valuation_amount must already be converted using separately evidenced FX
    conversion; this function does not perform conversions.
    """
    errors: list[str] = []
    warnings: list[str] = []
    now = _utc(now_utc, "now_utc", errors)
    seen_desks = {p.get("desk_id") for p in packets if isinstance(p, dict)}
    missing_desks = sorted(set(DESKS) - seen_desks)
    if missing_desks:
        warnings.append("missing specialist risk coverage: " + ", ".join(missing_desks))

    position_rows: list[dict[str, Any]] = []
    seen_positions: set[str] = set()
    desk_exposure: dict[str, dict[str, float]] = {
        desk: {"gross": 0.0, "net": 0.0, "position_count": 0} for desk in DESKS
    }
    currency_totals: dict[str, dict[str, float]] = {}
    group_totals: dict[str, dict[str, float]] = {}
    stop_sources: list[dict[str, str]] = []
    missing_risk_desks: list[str] = []

    for packet in packets:
        if not isinstance(packet, dict):
            errors.append("specialist packet must be an object")
            continue
        desk = packet.get("desk_id")
        if desk not in DESKS:
            errors.append(f"unknown specialist desk: {desk}")
            continue
        flags = packet.get("risk_flags", [])
        if packet.get("status") == "halt" or (isinstance(flags, list) and "STOP_CHALLENGE" in flags):
            stop_sources.append({"desk_id": desk, "instrument_id": str(packet.get("instrument_id", "unknown")),
                                 "reason": "specialist_halt_or_stop_challenge"})
        context = packet.get("context")
        risk = context.get("portfolio_risk") if isinstance(context, dict) else None
        if not isinstance(risk, dict) or not isinstance(risk.get("positions"), list):
            missing_risk_desks.append(desk)
            continue
        for index, position in enumerate(risk["positions"]):
            prefix = f"{desk}.positions[{index}]"
            if not isinstance(position, dict):
                errors.append(f"{prefix} must be an object")
                continue
            pid = position.get("position_id")
            if not isinstance(pid, str) or not pid.strip() or pid in seen_positions:
                errors.append(f"{prefix}.position_id missing or duplicate")
                continue
            seen_positions.add(pid)
            if position.get("instrument_id") != packet.get("instrument_id"):
                errors.append(f"{prefix}.instrument_id must match its specialist packet")
            asset_class = position.get("asset_class")
            side = position.get("side")
            if not isinstance(asset_class, str) or not asset_class.strip():
                errors.append(f"{prefix}.asset_class missing")
            if side not in {"long", "short"}:
                errors.append(f"{prefix}.side must be long or short")
            notional = _number(position.get("notional"), f"{prefix}.notional", errors, minimum=0.0)
            amount = _number(position.get("valuation_amount"), f"{prefix}.valuation_amount", errors, minimum=0.0)
            currency = position.get("currency")
            valuation_currency = position.get("valuation_currency")
            group = position.get("exposure_group")
            refs = position.get("evidence_refs")
            if not isinstance(currency, str) or not currency.strip():
                errors.append(f"{prefix}.currency missing")
            if not isinstance(valuation_currency, str) or not valuation_currency.strip():
                errors.append(f"{prefix}.valuation_currency missing")
            if not isinstance(group, str) or not group.strip():
                errors.append(f"{prefix}.exposure_group missing")
            if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or not x.strip() for x in refs):
                errors.append(f"{prefix}.evidence_refs must be a non-empty string array")
            timestamp = _utc(position.get("source_timestamp_utc"), f"{prefix}.source_timestamp_utc", errors)
            if timestamp and now and timestamp > now:
                errors.append(f"{prefix}.source_timestamp_utc is in the future")
            if None in (notional, amount) or side not in {"long", "short"}:
                continue
            signed = amount if side == "long" else -amount
            row = {
                "position_id": pid, "desk_id": desk, "instrument_id": packet.get("instrument_id"),
                "asset_class": asset_class, "side": side, "notional": notional,
                "currency": currency, "valuation_currency": valuation_currency,
                "valuation_amount": amount, "signed_valuation_amount": signed,
                "exposure_group": group, "evidence_refs": refs,
                "source_timestamp_utc": position.get("source_timestamp_utc"),
            }
            position_rows.append(row)
            desk_exposure[desk]["gross"] += amount
            desk_exposure[desk]["net"] += signed
            desk_exposure[desk]["position_count"] += 1
            if isinstance(valuation_currency, str) and valuation_currency:
                totals = currency_totals.setdefault(valuation_currency, {"gross": 0.0, "net": 0.0, "position_count": 0})
                totals["gross"] += amount
                totals["net"] += signed
                totals["position_count"] += 1
            if isinstance(group, str) and group and isinstance(valuation_currency, str) and valuation_currency:
                currency_groups = group_totals.setdefault(valuation_currency, {})
                totals = currency_groups.setdefault(group, {"gross": 0.0, "net": 0.0, "position_count": 0})
                totals["gross"] += amount
                totals["net"] += signed
                totals["position_count"] += 1

    for desk in DESKS:
        if desk not in seen_desks:
            continue
        if desk not in missing_risk_desks:
            continue
    if missing_risk_desks:
        warnings.append("portfolio exposure records missing for desk(s): " + ", ".join(sorted(set(missing_risk_desks))))

    # Correlation is reported only from explicitly supplied, timestamped evidence.
    correlations = []
    correlation_errors = []
    for index, item in enumerate(correlation_evidence or []):
        prefix = f"correlation_evidence[{index}]"
        if not isinstance(item, dict):
            correlation_errors.append(f"{prefix} must be an object")
            continue
        left, right = item.get("instrument_id_a"), item.get("instrument_id_b")
        value = item.get("correlation")
        if not isinstance(left, str) or not left or not isinstance(right, str) or not right or left == right:
            correlation_errors.append(f"{prefix} instrument pair invalid")
            continue
        corr = _number(value, f"{prefix}.correlation_abs", [], minimum=0.0) if isinstance(value, (int, float)) and not isinstance(value, bool) else None
        if corr is None or abs(float(value)) > 1:
            correlation_errors.append(f"{prefix}.correlation must be between -1 and 1")
            continue
        stamp = _utc(item.get("observed_at_utc"), f"{prefix}.observed_at_utc", correlation_errors)
        if stamp and now and stamp > now:
            correlation_errors.append(f"{prefix}.observed_at_utc is in the future")
        refs = item.get("evidence_refs")
        if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or not x for x in refs):
            correlation_errors.append(f"{prefix}.evidence_refs missing")
        if not isinstance(item.get("source_id"), str) or not item.get("source_id"):
            correlation_errors.append(f"{prefix}.source_id missing")
        correlations.append({
            "instrument_id_a": left, "instrument_id_b": right,
            "correlation": float(value), "observed_at_utc": item.get("observed_at_utc"),
            "source_id": item.get("source_id"), "evidence_refs": refs if isinstance(refs, list) else [],
            "authentication_status": "not_authenticated",
        })
    errors.extend(correlation_errors)

    config_status = "NOT_CONFIGURED"
    limit_results: list[dict[str, Any]] = []
    if risk_config is not None:
        if not isinstance(risk_config, dict) or risk_config.get("schema_version") != "1.0.0":
            errors.append("risk_config must be an object with schema_version 1.0.0")
            config_status = "INVALID"
        else:
            limits = risk_config.get("limits")
            if not isinstance(limits, list) or not limits:
                errors.append("risk_config.limits must be a non-empty array")
                config_status = "INVALID"
            else:
                config_status = "VALID"
                for i, limit in enumerate(limits):
                    if not isinstance(limit, dict) or not isinstance(limit.get("scope"), str) or not limit.get("scope"):
                        errors.append(f"risk_config.limits[{i}] malformed")
                        config_status = "INVALID"
                        continue
                    metric = limit.get("metric")
                    if metric not in {"gross_exposure", "absolute_net_exposure"}:
                        errors.append(f"risk_config.limits[{i}].metric unsupported")
                        config_status = "INVALID"
                        continue
                    threshold = _number(limit.get("max_value"), f"risk_config.limits[{i}].max_value", errors, minimum=0.0)
                    currency = limit.get("valuation_currency")
                    if threshold is None or not isinstance(currency, str) or not currency:
                        errors.append(f"risk_config.limits[{i}] requires valuation_currency and valid max_value")
                        config_status = "INVALID"
                        continue
                    scope = limit["scope"]
                    if scope == "portfolio":
                        totals = currency_totals.get(currency)
                    elif scope.startswith("desk:") and scope.split(":", 1)[1] in DESKS:
                        totals = desk_exposure.get(scope.split(":", 1)[1])
                    elif scope.startswith("group:") and scope.split(":", 1)[1]:
                        totals = group_totals.get(currency, {}).get(scope.split(":", 1)[1])
                    else:
                        errors.append(f"risk_config.limits[{i}].scope must be portfolio, desk:<desk>, or group:<name>")
                        config_status = "INVALID"
                        continue
                    if totals is None:
                        limit_results.append({"scope": scope, "metric": metric, "status": "UNKNOWN",
                                              "reason": f"no comparable exposure in {currency}"})
                        continue
                    actual = totals["gross"] if metric == "gross_exposure" else abs(totals["net"])
                    breached = actual > threshold
                    limit_results.append({"scope": scope, "metric": metric, "valuation_currency": currency,
                                          "actual": actual, "limit": threshold,
                                          "status": "BREACH" if breached else "WITHIN_LIMIT"})

    stop_active = bool(stop_sources)
    if errors or stop_active:
        status = "HALT"
    elif missing_desks or missing_risk_desks or config_status != "VALID" or any(x["status"] == "UNKNOWN" for x in limit_results):
        status = "UNKNOWN"
    elif any(x["status"] == "BREACH" for x in limit_results):
        status = "HALT"
    elif not correlations:
        status = "UNKNOWN"
        warnings.append("correlation risk is unknown; absence of evidence is not independence")
    else:
        status = "ASSESSED_WITHIN_CONFIGURED_LIMITS"

    return {
        "schema_version": "1.0.0",
        "status": status,
        "coverage": {"present_desks": sorted(seen_desks), "missing_desks": missing_desks,
                     "missing_risk_desks": sorted(set(missing_risk_desks))},
        "position_count": len(position_rows),
        "positions": position_rows,
        "desk_exposure": desk_exposure,
        "exposure_by_valuation_currency": currency_totals,
        "exposure_by_group": group_totals,
        "risk_limits": {"config_status": config_status, "results": limit_results},
        "correlation_risk": {"status": "EVIDENCE_PROVIDED" if correlations else "UNKNOWN",
                             "pairs": correlations, "independence_assumed": False},
        "simultaneous_stop_count": len(stop_sources),
        "stop_sources": stop_sources,
        "errors": errors,
        "warnings": warnings,
        "authority": AUTHORITY,
        "trade_authority": False,
        "live_readiness": False,
        "limitations": [
            "Exposure values are caller-supplied and are not independently verified.",
            "Valuation amounts must already share their declared valuation currency; no FX conversion is performed.",
            "Correlation evidence is descriptive, not authenticated or statistically validated by this module.",
            "Missing exposure, limits or correlation evidence is UNKNOWN, never zero or independent.",
            "This report is not a trading signal, execution instruction or live-readiness assessment.",
        ],
    }

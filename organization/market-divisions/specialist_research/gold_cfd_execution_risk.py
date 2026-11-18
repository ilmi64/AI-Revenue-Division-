"""Offline OANDA-style XAU/USD CFD session and execution-risk assessment.

This is a schedule/risk overlay, not a broker quote feed or margin engine.
All live spread, reference spread, holiday status, notional and shock inputs
are caller-supplied. No order, closeout or position action is performed.
"""
from __future__ import annotations

from datetime import datetime, time, timezone
from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo

AUTHORITY = "research_only_no_execution_authority"
NEW_YORK = ZoneInfo("America/New_York")


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return result if result.utcoffset() == timezone.utc.utcoffset(result) else None


def assess_xauusd_weekly_session(evaluation_utc: Any, holiday_status: Any = "unknown") -> dict[str, Any]:
    """Assess the published weekly schedule in New York local time.

    holiday_status must be caller-supplied as 'open', 'closed' or 'unknown'.
    The weekly schedule alone cannot establish actual holiday/session status.
    """
    errors: list[str] = []
    moment = _utc(evaluation_utc)
    if moment is None:
        errors.append("evaluation_utc must be UTC ISO-8601 ending Z")
    if not isinstance(holiday_status, str) or holiday_status not in {"open", "closed", "unknown"}:
        errors.append("holiday_status must be open, closed or unknown")
    if errors:
        return _session_result("INVALID_SESSION_INPUT", errors, [], None, None)

    local = moment.astimezone(NEW_YORK)
    weekday, clock = local.weekday(), local.time().replace(tzinfo=None)
    daily_open, daily_close = time(18, 5), time(16, 59)
    if weekday == 5:
        scheduled_open = False
    elif weekday == 6:
        scheduled_open = clock >= daily_open
    else:
        scheduled_open = clock < daily_close or clock >= daily_open

    warnings: list[str] = []
    if holiday_status == "closed":
        scheduled_open = False
        warnings.append("CALLER_REPORTS_HOLIDAY_OR_EXCEPTIONAL_CLOSURE")
    elif holiday_status == "unknown":
        warnings.append("HOLIDAY_AND_EXCEPTIONAL_CLOSURE_STATUS_NOT_VERIFIED")

    if scheduled_open and holiday_status == "open":
        status = "SCHEDULE_OPEN_STATUS_CONFIRMED_BY_CALLER"
    elif scheduled_open:
        status = "SCHEDULE_OPEN_BUT_CALENDAR_UNVERIFIED"
    elif holiday_status == "closed":
        status = "CLOSED_BY_CALLER_REPORTED_EXCEPTION"
    else:
        status = "CLOSED_BY_PUBLISHED_WEEKLY_SCHEDULE"

    return _session_result(status, [], warnings, local.isoformat(), scheduled_open)


def assess_gold_cfd_execution_stress(
    current_spread: Any,
    reference_spread: Any,
    spread_warning_multiple: Any,
    spread_halt_multiple: Any,
    gap_shock_bps: Any,
    position_notional: Any,
    quote_currency: Any,
) -> dict[str, Any]:
    """Assess caller-supplied spread and gap stress; never estimate broker closeout."""
    errors: list[str] = []
    values = {
        "current_spread": current_spread,
        "reference_spread": reference_spread,
        "spread_warning_multiple": spread_warning_multiple,
        "spread_halt_multiple": spread_halt_multiple,
        "gap_shock_bps": gap_shock_bps,
        "position_notional": position_notional,
    }
    parsed: dict[str, float] = {}
    for key, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            errors.append(f"{key} must be a finite number")
        else:
            parsed[key] = float(value)
    if "current_spread" in parsed and parsed["current_spread"] <= 0:
        errors.append("current_spread must be positive")
    if "reference_spread" in parsed and parsed["reference_spread"] <= 0:
        errors.append("reference_spread must be positive")
    if "spread_warning_multiple" in parsed and parsed["spread_warning_multiple"] <= 1:
        errors.append("spread_warning_multiple must exceed 1")
    if "spread_halt_multiple" in parsed and parsed["spread_halt_multiple"] <= 1:
        errors.append("spread_halt_multiple must exceed 1")
    if {"spread_warning_multiple", "spread_halt_multiple"} <= parsed.keys() and parsed["spread_halt_multiple"] < parsed["spread_warning_multiple"]:
        errors.append("spread_halt_multiple must be >= spread_warning_multiple")
    if "gap_shock_bps" in parsed and not 0 <= parsed["gap_shock_bps"] <= 10000:
        errors.append("gap_shock_bps must be between 0 and 10000")
    if "position_notional" in parsed and parsed["position_notional"] < 0:
        errors.append("position_notional must be non-negative")
    if not isinstance(quote_currency, str) or len(quote_currency) != 3 or not quote_currency.isalpha() or quote_currency.upper() != quote_currency:
        errors.append("quote_currency must be a three-letter uppercase currency code")
    if errors:
        return _stress_result("INVALID_STRESS_INPUT", errors, None, None, None, None)

    spread_multiple = parsed["current_spread"] / parsed["reference_spread"]
    estimated_gap_loss = parsed["position_notional"] * parsed["gap_shock_bps"] / 10000.0
    if spread_multiple >= parsed["spread_halt_multiple"]:
        status = "HALT_SPREAD_STRESS"
    elif spread_multiple >= parsed["spread_warning_multiple"]:
        status = "WARN_SPREAD_STRESS"
    else:
        status = "STRESS_INPUTS_WITHIN_CONFIGURED_SPREAD_THRESHOLDS"
    return _stress_result(
        status, [], spread_multiple, estimated_gap_loss,
        quote_currency, parsed["gap_shock_bps"],
    )


def _session_result(status: str, errors: list[str], warnings: list[str],
                    local_time: str | None, scheduled_open: bool | None) -> dict[str, Any]:
    return {
        "status": status, "errors": errors, "warnings": warnings,
        "evaluation_new_york": local_time,
        "scheduled_open_by_weekly_hours": scheduled_open,
        "holiday_calendar_authenticated": False,
        "broker_market_status_authenticated": False,
        "position_action_performed": False, "trade_authority": False,
        "live_readiness": False, "research_only": True, "authority": AUTHORITY,
    }


def _stress_result(status: str, errors: list[str], spread_multiple: float | None,
                   estimated_gap_loss: float | None, quote_currency: str | None,
                   gap_shock_bps: float | None) -> dict[str, Any]:
    return {
        "status": status, "errors": errors,
        "current_to_reference_spread_multiple": spread_multiple,
        "gap_stress_loss_estimate": estimated_gap_loss,
        "gap_stress_quote_currency": quote_currency,
        "gap_shock_bps": gap_shock_bps,
        "forced_closeout_model": "NOT_MODELLED_BROKER_MAY_CLOSE_ALL_TRADABLE_POSITIONS",
        "stop_loss_execution_guaranteed": False,
        "spread_and_gap_inputs_authenticated": False,
        "position_action_performed": False, "trade_authority": False,
        "live_readiness": False, "research_only": True, "authority": AUTHORITY,
        "limitations": [
            "Spread thresholds and quote observations are caller-supplied, not live broker data.",
            "Gap loss is a linear notional stress estimate, not a fill-price prediction.",
            "Broker margin closeout threshold, sequence and execution prices are not modelled.",
            "A stop-loss is not assumed to guarantee execution at its requested price.",
        ],
    }

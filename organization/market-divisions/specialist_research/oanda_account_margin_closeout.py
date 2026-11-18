"""Offline account-level replay of OANDA Canada v20-style margin rules.

The caller supplies account-currency NAV_mid, Margin Used, verified trading-day
sequence and position market availability. This is a conservative rule replay,
not a broker integration, execution-price model or live account calculation.
"""
from __future__ import annotations

from datetime import datetime, time, timezone
from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo

AUTHORITY = "research_only_no_execution_authority"
NEW_YORK = ZoneInfo("America/New_York")
DAILY_CHECK_TIME = time(15, 45)
EARLY_CLOSEOUT_RATIO = 0.5
TIME_BASED_TRADING_DAYS = 6


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.utcoffset() == timezone.utc.utcoffset(parsed) else None


def assess_oanda_margin_state(nav_mid: Any, margin_used: Any) -> dict[str, Any]:
    """Calculate margin call and closeout thresholds from same-currency inputs."""
    errors: list[str] = []
    parsed: dict[str, float] = {}
    for key, value in (("nav_mid", nav_mid), ("margin_used", margin_used)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            errors.append(f"{key} must be a finite numeric account-currency amount")
        else:
            parsed[key] = float(value)
    if "nav_mid" in parsed and parsed["nav_mid"] < 0:
        errors.append("nav_mid cannot be negative")
    if "margin_used" in parsed and parsed["margin_used"] < 0:
        errors.append("margin_used cannot be negative")
    if errors:
        return {
            "status": "INVALID_MARGIN_INPUT", "errors": errors,
            "trade_authority": False, "live_readiness": False,
            "research_only": True, "authority": AUTHORITY,
        }

    nav, used = parsed["nav_mid"], parsed["margin_used"]
    margin_call = used > 0 and nav < used
    early_closeout = used > 0 and nav <= EARLY_CLOSEOUT_RATIO * used
    if used == 0:
        closeout_pct = 0.0
    elif nav == 0:
        closeout_pct = None
    else:
        closeout_pct = (EARLY_CLOSEOUT_RATIO * used / nav) * 100.0
    return {
        "status": "EARLY_CLOSEOUT_THRESHOLD_REACHED" if early_closeout
                  else "MARGIN_CALL_THRESHOLD_REACHED" if margin_call
                  else "WITHIN_MARGIN_REQUIREMENTS",
        "nav_mid": nav, "margin_used": used,
        "margin_call": margin_call,
        "margin_closeout_percentage": closeout_pct,
        "margin_closeout_percentage_unbounded": used > 0 and nav == 0,
        "early_closeout_threshold": "NAV_mid <= 50% of Margin Used",
        "early_closeout_triggered": early_closeout,
        "trade_authority": False, "live_readiness": False,
        "research_only": True, "authority": AUTHORITY,
    }


def replay_oanda_account_margin_closeout(
    account_currency: Any,
    initial_positions: Any,
    observations: Any,
) -> dict[str, Any]:
    """Replay account-wide margin checks and batch closeouts.

    Each observation has timestamp_utc, nav_mid, margin_used,
    position_market_status (mapping active position IDs to open/closed/halted),
    and optionally trading_day_check, trading_day_sequence and
    trading_calendar_status. Daily checks must be at 15:45 America/New_York.
    The caller must provide consecutive, verified trading-day sequence numbers.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if (not isinstance(account_currency, str) or len(account_currency) != 3
            or not account_currency.isalpha() or account_currency.upper() != account_currency):
        errors.append("account_currency must be a three-letter uppercase currency code")
    if not isinstance(initial_positions, list) or not initial_positions:
        errors.append("initial_positions must be a non-empty array")
        initial_positions = []
    if not isinstance(observations, list) or not observations:
        errors.append("observations must be a non-empty array")
        observations = []

    positions: dict[str, dict[str, Any]] = {}
    for index, position in enumerate(initial_positions):
        if not isinstance(position, dict):
            errors.append(f"initial_positions[{index}] must be an object")
            continue
        pid = position.get("position_id")
        if not isinstance(pid, str) or not pid.strip() or pid in positions:
            errors.append(f"initial_positions[{index}] has missing or duplicate position_id")
            continue
        market_status = position.get("market_status", "open")
        if not isinstance(market_status, str) or market_status not in {"open", "closed", "halted"}:
            errors.append(f"{pid}: market_status must be open, closed or halted")
            continue
        positions[pid] = {
            "position_id": pid,
            "desk_id": position.get("desk_id", "unspecified"),
            "instrument_id": position.get("instrument_id", "unspecified"),
            "market_status": market_status,
            "position_state": "open",
        }

    parsed_events: list[tuple[datetime, dict[str, Any], int]] = []
    previous_time: datetime | None = None
    previous_sequence: int | None = None
    for index, event in enumerate(observations):
        if not isinstance(event, dict):
            errors.append(f"observations[{index}] must be an object")
            continue
        moment = _utc(event.get("timestamp_utc"))
        if moment is None:
            errors.append(f"observations[{index}].timestamp_utc must be UTC ISO-8601 ending Z")
            continue
        if previous_time is not None and moment <= previous_time:
            errors.append("observation timestamps must be strictly increasing")
        previous_time = moment
        state = assess_oanda_margin_state(event.get("nav_mid"), event.get("margin_used"))
        if state["status"] == "INVALID_MARGIN_INPUT":
            errors.extend([f"observations[{index}]: {e}" for e in state["errors"]])
        market_map = event.get("position_market_status")
        active_ids = {pid for pid, p in positions.items() if p["position_state"] == "open"}
        if not isinstance(market_map, dict) or set(market_map) != active_ids:
            errors.append(f"observations[{index}].position_market_status must cover exactly the currently open position IDs")
        elif any(not isinstance(value, str) or value not in {"open", "closed", "halted"} for value in market_map.values()):
            errors.append(f"observations[{index}].position_market_status contains an invalid market state")

        daily_check = event.get("trading_day_check", False)
        if not isinstance(daily_check, bool):
            errors.append(f"observations[{index}].trading_day_check must be boolean")
            daily_check = False
        sequence = event.get("trading_day_sequence")
        if daily_check:
            local = moment.astimezone(NEW_YORK)
            if local.time().replace(tzinfo=None) != DAILY_CHECK_TIME:
                errors.append(f"observations[{index}] daily margin check must be at 15:45 America/New_York")
            if local.weekday() >= 5:
                errors.append(f"observations[{index}] daily margin check cannot be on a Saturday or Sunday")
            if event.get("trading_calendar_status") != "verified":
                errors.append(f"observations[{index}] daily margin check requires caller-verified trading calendar")
            if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
                errors.append(f"observations[{index}] requires positive integer trading_day_sequence")
            elif previous_sequence is not None and sequence != previous_sequence + 1:
                errors.append("daily trading_day_sequence values must be consecutive; missing checks cannot be inferred")
            if isinstance(sequence, int) and not isinstance(sequence, bool):
                previous_sequence = sequence
        elif sequence is not None:
            errors.append(f"observations[{index}] trading_day_sequence is only valid for a daily margin check")
        parsed_events.append((moment, event, index))

    if errors:
        return _blocked_result(errors, warnings)

    daily_under_margin_days = 0
    closeout_batches: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    deferred_closeout_retry_pending = False
    for moment, event, index in parsed_events:
        state = assess_oanda_margin_state(event["nav_mid"], event["margin_used"])
        for pid, market_status in event["position_market_status"].items():
            if positions[pid]["position_state"] == "open":
                positions[pid]["market_status"] = market_status

        if event.get("trading_day_check", False):
            if state["margin_call"]:
                daily_under_margin_days += 1
            else:
                daily_under_margin_days = 0

        if deferred_closeout_retry_pending and not state["margin_call"]:
            deferred_closeout_retry_pending = False
        retry_pending = deferred_closeout_retry_pending and state["margin_call"]
        time_based = daily_under_margin_days >= TIME_BASED_TRADING_DAYS and state["margin_call"]
        early = state["early_closeout_triggered"]
        trigger = early or time_based or retry_pending
        trigger_reason = ("EARLY_100_PERCENT_MARGIN_CLOSEOUT" if early else
                          "SIX_CONSECUTIVE_UNDERMARGINED_TRADING_DAYS" if time_based else
                          "RETRY_DEFERRED_CLOSEOUT_WHILE_UNDERMARGINED")
        open_positions = [
            pid for pid, p in positions.items()
            if p["position_state"] == "open"
        ]
        tradable = [
            pid for pid in open_positions
            if positions[pid]["market_status"] == "open"
        ]
        deferred = [
            pid for pid in open_positions
            if positions[pid]["market_status"] in {"closed", "halted"}
        ]
        closed_now: list[str] = []
        if trigger and tradable:
            for pid in tradable:
                positions[pid]["position_state"] = "closed_by_model"
                closed_now.append(pid)
            closeout_batches.append({
                "timestamp_utc": event["timestamp_utc"],
                "trigger": trigger_reason,
                "position_ids_closed_as_batch": closed_now,
                "position_ids_deferred_market_closed_or_halted": deferred,
                "execution_prices": "NOT_MODELLED_CURRENT_BROKER_RATES_UNAVAILABLE",
                "position_ordering": "NO_SEQUENCE_ASSUMED_BATCH_CLOSEOUT",
            })
            deferred_closeout_retry_pending = bool(deferred)
        elif trigger and deferred:
            closeout_batches.append({
                "timestamp_utc": event["timestamp_utc"],
                "trigger": trigger_reason,
                "position_ids_closed_as_batch": [],
                "position_ids_deferred_market_closed_or_halted": deferred,
                "execution_prices": "NOT_MODELLED_CURRENT_BROKER_RATES_UNAVAILABLE",
                "position_ordering": "NO_SEQUENCE_ASSUMED_BATCH_CLOSEOUT",
            })
            deferred_closeout_retry_pending = True
            warnings.append(
                f"{event['timestamp_utc']}: closeout threshold reached but all remaining positions are closed or halted"
            )

        timeline.append({
            "timestamp_utc": event["timestamp_utc"],
            "margin_state": state,
            "trading_day_check": event.get("trading_day_check", False),
            "consecutive_under_margined_trading_days": daily_under_margin_days,
            "time_based_closeout_threshold_reached": time_based,
            "early_closeout_threshold_reached": early,
            "closeout_triggered": trigger,
            "deferred_closeout_retry_pending": deferred_closeout_retry_pending,
            "position_ids_closed": closed_now,
            "position_ids_deferred": deferred if trigger else [],
        })

    remaining = [
        {"position_id": pid, "desk_id": p["desk_id"], "instrument_id": p["instrument_id"],
         "market_status": p["market_status"]}
        for pid, p in positions.items() if p["position_state"] == "open"
    ]
    closed_ids = [pid for pid, p in positions.items() if p["position_state"] == "closed_by_model"]
    overall = "CLOSEOUT_TRIGGERED" if closeout_batches else (
        "MARGIN_CALL_ACTIVE" if timeline and timeline[-1]["margin_state"]["margin_call"]
        else "WITHIN_MARGIN_REQUIREMENTS"
    )
    return {
        "status": overall,
        "account_currency": account_currency,
        "timeline": timeline,
        "closeout_batches": closeout_batches,
        "position_ids_closed_by_model": closed_ids,
        "remaining_open_positions": remaining,
        "consecutive_under_margined_trading_days": daily_under_margin_days,
        "rules_basis": {
            "margin_call": "NAV_mid < Margin Used",
            "margin_closeout_percentage": "(50% * Margin Used / NAV_mid) * 100",
            "early_closeout": "NAV_mid <= 50% of Margin Used (100% margin closeout percentage)",
            "time_based_closeout": "six consecutive caller-verified trading-day checks at 15:45 America/New_York while under-margined",
            "market_unavailable": "closed/halted positions remain open; retry on reopening if NAV_mid remains below Margin Used",
        },
        "pending_orders": "NOT_MODELLED; unrelated pending orders are not assumed cancelled",
        "calendar_authentication": False,
        "account_values_authenticated": False,
        "broker_execution_prices_modelled": False,
        "position_action_performed": False,
        "trade_authority": False, "live_readiness": False,
        "research_only": True, "authority": AUTHORITY,
        "warnings": warnings,
        "limitations": [
            "NAV_mid and Margin Used are caller-supplied in the same account currency; no conversion is inferred.",
            "Trading-day sequence and holiday calendar are caller-supplied and not authenticated.",
            "The six-day rule is replayed only when every consecutive daily 15:45 ET checkpoint is supplied.",
            "The model closes all currently tradable positions as one batch; it does not infer broker liquidation order or execution prices.",
            "Positions in closed or halted markets remain open; a deferred closeout is retried on reopening while NAV_mid remains below Margin Used, and is cancelled from the replay if the account recovers.",
            "This model does not cancel pending orders, calculate margin requirements, or reproduce account-specific exceptions.",
        ],
    }


def _blocked_result(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "status": "BLOCKED_INVALID_OR_INCOMPLETE_INPUT",
        "errors": errors, "warnings": warnings,
        "closeout_batches": [], "position_action_performed": False,
        "trade_authority": False, "live_readiness": False,
        "research_only": True, "authority": AUTHORITY,
    }

"""Fail-closed GC/MGC physical-delivery and FCM deadline controls.

All dates and cutoffs are caller-supplied from the exact contract-month
exchange calendar and the account's FCM policy. This module never derives
First Notice dates or invents broker deadlines.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

AUTHORITY = "research_only_no_execution_authority"
PRODUCTS = {"GC": "113", "MGC": "120"}


def _date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
        return parsed if parsed.isoformat() == value else None
    except ValueError:
        return None


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        return parsed if parsed.utcoffset() is not None else None
    except ValueError:
        return None


def assess_gold_delivery_controls(contract: Any, position: Any, evaluation_utc: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return _result("HALT_DELIVERY_CONTROLS", ["contract must be an object"], [], False)
    if not isinstance(position, dict):
        return _result("HALT_DELIVERY_CONTROLS", ["position must be an object"], [], False)

    product = contract.get("product_code")
    if product not in PRODUCTS:
        errors.append("product_code must be GC or MGC")
    elif contract.get("rulebook_chapter") != PRODUCTS[product]:
        errors.append("rulebook_chapter does not match product code")
    if contract.get("settlement_type") != "physical":
        errors.append("GC/MGC settlement_type must be physical")
    for key in ("contract_id", "contract_month", "exchange_calendar_revision_id",
                "fcm_policy_revision_id", "exchange_calendar_source_ref",
                "fcm_policy_source_ref", "fcm_timezone"):
        if not isinstance(contract.get(key), str) or not contract[key].strip():
            errors.append(f"{key} is required")
    month = contract.get("contract_month")
    if not isinstance(month, str) or len(month) != 7 or month[4:5] != "-" or not month[:4].isdigit() or not month[5:].isdigit() or not 1 <= int(month[5:]) <= 12:
        errors.append("contract_month must use YYYY-MM")
    date_keys = ("first_position_date", "first_notice_date", "last_trade_date",
                 "delivery_start_date", "delivery_end_date",
                 "fcm_long_position_cutoff_date", "fcm_short_position_cutoff_date",
                 "new_position_freeze_date")
    dates = {key: _date(contract.get(key)) for key in date_keys}
    for key, parsed in dates.items():
        if parsed is None:
            errors.append(f"{key} must be an ISO calendar date from official calendar or FCM policy")
    for key in ("fcm_long_cutoff_utc", "fcm_short_cutoff_utc", "new_position_freeze_utc"):
        if _utc(contract.get(key)) is None:
            errors.append(f"{key} must be an explicit UTC timestamp ending Z")
    evaluation = _utc(evaluation_utc)
    if evaluation is None:
        errors.append("evaluation_utc must be an explicit UTC timestamp ending Z")

    if not errors:
        if not (dates["first_position_date"] <= dates["first_notice_date"] <= dates["delivery_end_date"]):
            errors.append("First Position/First Notice/delivery date sequence is inconsistent")
        if not (dates["delivery_start_date"] <= dates["delivery_end_date"]):
            errors.append("delivery_start_date must not exceed delivery_end_date")
        if dates["last_trade_date"] > dates["delivery_end_date"]:
            errors.append("last_trade_date must not exceed delivery_end_date")
        if dates["fcm_long_position_cutoff_date"] > dates["first_position_date"]:
            errors.append("FCM long-position cutoff must be no later than First Position Date")
        if dates["fcm_short_position_cutoff_date"] > dates["last_trade_date"]:
            errors.append("FCM short-position cutoff must be no later than last trade date")
        if dates["new_position_freeze_date"] > dates["first_position_date"]:
            errors.append("new-position freeze must be no later than First Position Date")
        if _utc(contract["fcm_long_cutoff_utc"]) > _utc(contract["fcm_short_cutoff_utc"]):
            errors.append("FCM long cutoff must not occur after FCM short cutoff")
        if _utc(contract["new_position_freeze_utc"]) > _utc(contract["fcm_long_cutoff_utc"]):
            errors.append("new-position freeze must not occur after FCM long cutoff")

    side = position.get("side")
    is_open = position.get("is_open")
    if side not in {"long", "short", "flat"}:
        errors.append("position.side must be long, short or flat")
    if not isinstance(is_open, bool):
        errors.append("position.is_open must be boolean")
    if side == "flat" and is_open is True:
        errors.append("flat position cannot be marked open")

    if errors:
        return _result("HALT_DELIVERY_CONTROLS", errors, [], False)

    warnings: list[str] = []
    blocks: list[str] = []
    if is_open:
        if side == "long" and evaluation >= _utc(contract["fcm_long_cutoff_utc"]):
            blocks.append("LONG_POSITION_AT_OR_AFTER_FCM_RECEIVE_CUTOFF")
        if side == "short" and evaluation >= _utc(contract["fcm_short_cutoff_utc"]):
            blocks.append("SHORT_POSITION_AT_OR_AFTER_FCM_DELIVERY_CUTOFF")
        if evaluation >= _utc(contract["new_position_freeze_utc"]):
            warnings.append("NEW_POSITION_FREEZE_ACTIVE")
    else:
        if evaluation >= _utc(contract["new_position_freeze_utc"]):
            blocks.append("NEW_POSITION_PROHIBITED_BY_FCM_FREEZE")
    if evaluation.date() >= dates["first_position_date"]:
        warnings.append("PHYSICAL_DELIVERY_POSITION_PERIOD_REACHED")
    if evaluation.date() >= dates["first_notice_date"]:
        warnings.append("FIRST_NOTICE_DATE_REACHED")
    status = "HALT_DELIVERY_CONTROLS" if blocks else ("WARN_DELIVERY_CONTROLS" if warnings else "DELIVERY_CONTROLS_CLEAR")
    return _result(status, [], warnings, bool(blocks), blocks)


def _result(status: str, errors: list[str], warnings: list[str], blocked: bool,
            blocks: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": status, "errors": errors, "warnings": warnings,
        "blocks": blocks or [], "position_action_blocked": blocked,
        "exchange_dates_and_fcm_cutoffs_caller_supplied": True,
        "calendar_and_fcm_policy_independently_authenticated": False,
        "delivery_instructions_submitted": False, "position_changed": False,
        "trade_authority": False, "live_readiness": False,
        "research_only": True, "authority": AUTHORITY,
        "limitations": [
            "No First Position, First Notice, last-trade or delivery date is inferred.",
            "FCM cutoffs must be obtained for the actual account and contract month.",
            "This control does not liquidate, roll, submit delivery intent or change positions.",
            "Calendar and FCM policy provenance is caller-supplied and unauthenticated.",
        ],
    }

"""Read-only post-margin-closeout audit of OANDA v20 pending-order exposure.

The audit classifies contingent orders linked to liquidated trades separately
from unrelated pending orders. It never cancels, modifies or submits orders.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

AUTHORITY = "research_only_no_execution_authority"
PENDING_TYPES = {"LIMIT", "STOP", "MARKET_IF_TOUCHED"}
DEPENDENT_CLOSE_TYPES = {"TAKE_PROFIT", "STOP_LOSS", "GUARANTEED_STOP_LOSS", "TRAILING_STOP_LOSS"}
POSITION_FILL = {"OPEN_ONLY", "REDUCE_FIRST", "REDUCE_ONLY", "DEFAULT"}


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.utcoffset() == timezone.utc.utcoffset(parsed) else None


def _blocked(errors: list[str], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": "HALT", "errors": errors, "warnings": warnings or [],
        "closeout_occurred": None, "pending_orders_complete": False,
        "pending_order_count": 0,
        "orders_still_pending_for_liquidated_trades": [], "orders_still_linked_to_open_trades": [],
        "dependent_order_cancellation_transaction_verified": False,
        "orders_surviving_and_potentially_opening": [],
        "orders_surviving_but_reduce_only": [], "unclassified_orders": [],
        "possible_exposure_reopening": True,
        "order_cancellation_performed": False,
        "trade_authority": False, "live_readiness": False,
        "research_only": True, "authority": AUTHORITY,
    }


def assess_oanda_post_closeout_pending_orders(
    pending_orders: Any,
    liquidated_trade_ids: Any,
    remaining_open_trade_ids: Any,
    remaining_open_trade_ids_complete: Any,
    reported_pending_order_count: Any,
    account_hedging_enabled: Any,
    source_timestamp_utc: Any,
    evaluated_at_utc: Any,
    max_snapshot_age_seconds: Any,
    pending_orders_complete: Any,
    closeout_occurred: Any = True,
) -> dict[str, Any]:
    """Classify a complete post-closeout pending-order snapshot.

    OANDA v20 semantics used:
    - orders with tradeID are dependent close orders;
    - a dependent order on a liquidated trade should be cancelled;
    - unrelated orders remain active;
    - OPEN_ONLY and REDUCE_FIRST can open/extend exposure;
    - REDUCE_ONLY cannot open a new position;
    - DEFAULT resolves to OPEN_ONLY for hedging accounts and REDUCE_FIRST
      for non-hedging accounts. Both may open exposure.
    """
    errors: list[str] = []
    warnings: list[str] = []
    if closeout_occurred is not True:
        errors.append("closeout_occurred must be explicitly true for post-closeout reconciliation")
    if pending_orders_complete is not True:
        errors.append("pending_orders_complete must be explicitly true; partial order lists cannot establish safety")
    if not isinstance(account_hedging_enabled, bool):
        errors.append("account_hedging_enabled must be supplied from the account snapshot")
    source_time = _utc(source_timestamp_utc)
    evaluated_time = _utc(evaluated_at_utc)
    if source_time is None:
        errors.append("source_timestamp_utc must be UTC ISO-8601 ending Z")
    if evaluated_time is None:
        errors.append("evaluated_at_utc must be UTC ISO-8601 ending Z")
    if (isinstance(max_snapshot_age_seconds, bool)
            or not isinstance(max_snapshot_age_seconds, (int, float))
            or not isfinite(max_snapshot_age_seconds) or max_snapshot_age_seconds <= 0):
        errors.append("max_snapshot_age_seconds must be a positive finite caller-selected value")
    elif source_time is not None and evaluated_time is not None:
        age = (evaluated_time - source_time).total_seconds()
        if age < 0:
            errors.append("pending-order source snapshot cannot be future-dated")
        elif age > max_snapshot_age_seconds:
            errors.append("pending-order source snapshot exceeds caller-selected freshness limit")

    if not isinstance(liquidated_trade_ids, list):
        errors.append("liquidated_trade_ids must be a complete array")
        liquidated_trade_ids = []
    elif (any(not isinstance(item, str) or not item.strip() for item in liquidated_trade_ids)
          or len(set(liquidated_trade_ids)) != len(liquidated_trade_ids)):
        errors.append("liquidated_trade_ids must contain unique non-empty strings")

    if remaining_open_trade_ids_complete is not True:
        errors.append("remaining_open_trade_ids_complete must be explicitly true")
    if (isinstance(reported_pending_order_count, bool)
            or not isinstance(reported_pending_order_count, int) or reported_pending_order_count < 0):
        errors.append("reported_pending_order_count must be a non-negative integer from the account snapshot")
    if not isinstance(remaining_open_trade_ids, list):
        errors.append("remaining_open_trade_ids must be a complete array")
        remaining_open_trade_ids = []
    elif (any(not isinstance(item, str) or not item.strip() for item in remaining_open_trade_ids)
          or len(set(remaining_open_trade_ids)) != len(remaining_open_trade_ids)):
        errors.append("remaining_open_trade_ids must contain unique non-empty strings")
    if not isinstance(pending_orders, list):
        errors.append("pending_orders must be a complete array, including an empty array when none remain")
        pending_orders = []

    if errors:
        return _blocked(errors, warnings)
    if reported_pending_order_count != len(pending_orders):
        return _blocked(["reported_pending_order_count does not match the supplied complete pending_orders array"], warnings)

    liquidated = set(liquidated_trade_ids)
    remaining = set(remaining_open_trade_ids)
    if liquidated & remaining:
        return _blocked(["liquidated_trade_ids and remaining_open_trade_ids must be disjoint"], warnings)
    dependent_orders_still_pending: list[dict[str, str]] = []
    linked_survivors: list[dict[str, Any]] = []
    exposure_survivors: list[dict[str, Any]] = []
    reduce_only_survivors: list[dict[str, Any]] = []
    unclassified: list[dict[str, Any]] = []
    seen: set[str] = set()

    for index, order in enumerate(pending_orders):
        if not isinstance(order, dict):
            errors.append(f"pending_orders[{index}] must be an object")
            continue
        order_id = order.get("id")
        if not isinstance(order_id, str) or not order_id.strip() or order_id in seen:
            errors.append(f"pending_orders[{index}] has missing or duplicate id")
            continue
        seen.add(order_id)
        if order.get("state") != "PENDING":
            errors.append(f"{order_id}: supplied order snapshot must contain only PENDING orders")
            continue
        order_type = order.get("type")
        if not isinstance(order_type, str):
            errors.append(f"{order_id}: order type is missing")
            continue
        order_type = order_type.upper()
        if order_type not in PENDING_TYPES | DEPENDENT_CLOSE_TYPES:
            errors.append(f"{order_id}: unsupported pending order type {order_type}")
            continue

        trade_id = order.get("tradeID")
        if trade_id is not None and (not isinstance(trade_id, str) or not trade_id.strip()):
            errors.append(f"{order_id}: tradeID must be a non-empty string when supplied")
            continue

        if order_type in PENDING_TYPES and (not isinstance(order.get("instrument"), str) or not order["instrument"].strip()):
            errors.append(f"{order_id}: entry order instrument is required")
            continue

        if order_type in DEPENDENT_CLOSE_TYPES:
            if trade_id is None:
                errors.append(f"{order_id}: dependent close order is missing its required tradeID")
                continue
            if trade_id in liquidated:
                dependent_orders_still_pending.append({"order_id": order_id, "trade_id": trade_id, "type": order_type})
                errors.append(f"{order_id}: order linked to a liquidated trade is still pending; expected cancellation is not reflected")
                continue
            if trade_id not in remaining:
                errors.append(f"{order_id}: tradeID is neither confirmed liquidated nor confirmed open")
                continue
            linked_survivors.append({
                "order_id": order_id, "type": order_type, "trade_id": trade_id,
                "classification": "DEPENDENT_CLOSE_ORDER_ON_NON_LIQUIDATED_TRADE",
                "may_open_new_position": False,
            })
            continue

        if trade_id is not None:
            errors.append(f"{order_id}: entry-type order unexpectedly contains tradeID; order relationship is ambiguous")
            continue

        raw_units = order.get("units")
        try:
            units = float(raw_units) if not isinstance(raw_units, bool) else float("nan")
        except (TypeError, ValueError, OverflowError):
            units = float("nan")
        if not isfinite(units) or units == 0:
            errors.append(f"{order_id}: units must be a finite non-zero signed quantity")
            continue
        position_fill = order.get("positionFill", "DEFAULT")
        if not isinstance(position_fill, str) or position_fill not in POSITION_FILL:
            errors.append(f"{order_id}: positionFill is missing or unsupported")
            continue
        if position_fill == "REDUCE_ONLY":
            reduce_only_survivors.append({
                "order_id": order_id, "type": order_type, "instrument": order.get("instrument"),
                "units": units, "position_fill": position_fill,
                "classification": "UNRELATED_PENDING_ORDER_REDUCE_ONLY",
                "may_open_new_position": False,
            })
        else:
            effective_fill = position_fill
            if position_fill == "DEFAULT":
                effective_fill = "OPEN_ONLY" if account_hedging_enabled else "REDUCE_FIRST"
            exposure_survivors.append({
                "order_id": order_id, "type": order_type, "instrument": order.get("instrument"),
                "units": units, "position_fill": position_fill,
                "effective_position_fill": effective_fill,
                "classification": "UNRELATED_PENDING_ORDER_MAY_REOPEN_EXPOSURE",
                "may_open_new_position": True,
            })

    if errors:
        blocked = _blocked(errors, warnings)
        blocked["orders_still_pending_for_liquidated_trades"] = dependent_orders_still_pending
        return blocked

    possible_reopening = bool(exposure_survivors)
    if possible_reopening:
        warnings.append("Unrelated pending orders remain capable of opening or extending exposure after the margin closeout.")
    if linked_survivors:
        warnings.append("Dependent close orders remain attached to explicitly identified non-liquidated open trades; they are not entry orders.")
    if reduce_only_survivors:
        warnings.append("Reduce-only pending orders remain; they cannot open new positions but may be ineffective if no eligible position exists.")
    return {
        "status": "HALT" if possible_reopening else "PASS",
        "source_timestamp_utc": source_timestamp_utc,
        "evaluated_at_utc": evaluated_at_utc,
        "snapshot_age_seconds": (evaluated_time - source_time).total_seconds(),
        "max_snapshot_age_seconds": float(max_snapshot_age_seconds),
        "account_hedging_enabled": account_hedging_enabled,
        "closeout_occurred": True, "pending_orders_complete": True,
        "pending_order_count": len(pending_orders),
        "reported_pending_order_count": reported_pending_order_count,
        "remaining_open_trade_ids_complete": True,
        "liquidated_trade_count": len(liquidated),
        "remaining_open_trade_count": len(remaining),
        "orders_still_pending_for_liquidated_trades": dependent_orders_still_pending,
        "dependent_order_cancellation_transaction_verified": False,
        "orders_still_linked_to_open_trades": linked_survivors,
        "orders_surviving_and_potentially_opening": exposure_survivors,
        "orders_surviving_but_reduce_only": reduce_only_survivors,
        "unclassified_orders": unclassified,
        "possible_exposure_reopening": possible_reopening,
        "order_cancellation_performed": False,
        "trade_authority": False, "live_readiness": False,
        "research_only": True, "authority": AUTHORITY,
        "errors": [], "warnings": warnings,
        "limitations": [
            "This is a read-only classification of a caller-supplied complete OANDA v20 pending-order snapshot, not a live broker query.",
            "It does not cancel, modify or place orders.",
            "It does not calculate whether a surviving order will trigger, fill, or create a specific post-fill margin requirement.",
            "Absence of a dependent order from the post-closeout pending list is not proof of the cancellation transaction or its terminal reason; transaction-history reconciliation is not yet implemented.",
            "Order relationship and account hedging mode must be copied from the same authenticated account snapshot; this module does not authenticate the caller or source.",
            "A PASS means no supplied unrelated pending order can open new exposure under the supplied positionFill semantics; it does not mean the account is safe or live-ready.",
        ],
    }

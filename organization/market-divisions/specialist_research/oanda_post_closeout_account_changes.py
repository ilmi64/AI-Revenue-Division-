"""Offline reconciliation of OANDA v20 account changes after margin closeout.

Consumes caller-supplied GET /accounts/{accountID}/changes output and a
subsequent full account snapshot. It performs no network or broker actions.
"""
from __future__ import annotations

from math import isfinite
from typing import Any

AUTHORITY = "research_only_no_execution_authority"
CHANGE_ARRAYS = (
    "ordersCreated", "ordersCancelled", "ordersFilled", "ordersTriggered",
    "tradesOpened", "tradesReduced", "tradesClosed", "positions", "transactions",
)


def _numeric_id(value: Any) -> int | None:
    if not isinstance(value, str) or not value.isdigit():
        return None
    try:
        return int(value)
    except (ValueError, OverflowError):
        return None


def _units(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    try:
        result = float(value)
    except (ValueError, OverflowError):
        return None
    return result if isfinite(result) else None


def _halt(errors: list[str], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": "HALT", "errors": errors, "warnings": warnings or [],
        "newly_opened_trade_ids": [], "unexpectedly_open_trades": [],
        "unexpectedly_remaining_closed_trades": [], "filled_preexisting_order_ids": [],
        "new_pending_order_ids": [], "current_pending_order_ids": [],
        "position_reconciliation": "blocked",
        "account_change_reconciliation_complete": False,
        "trade_authority": False, "live_readiness": False,
        "research_only": True, "authority": AUTHORITY,
    }


def _records(value: Any, field: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"changes.{field} must be an array")
        return []
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"changes.{field}[{index}] must be an object")
        else:
            result.append(item)
    return result


def _position_units(position: dict[str, Any], side: str) -> float | None:
    value = position.get(side)
    if not isinstance(value, dict):
        return None
    return _units(value.get("units"))


def assess_oanda_post_closeout_account_changes(
    account_id: Any,
    since_transaction_id: Any,
    changes_response: Any,
    post_closeout_account_snapshot: Any,
    expected_closeout_trade_ids: Any,
    pre_closeout_pending_order_ids: Any,
    expected_cancelled_order_ids: Any,
    evaluated_at_utc: Any,
    changes_observed_at_utc: Any,
    account_snapshot_observed_at_utc: Any,
    max_snapshot_age_seconds: Any,
) -> dict[str, Any]:
    """Reconcile OANDA account changes and full account state; read-only only."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(account_id, str) or not account_id.strip():
        errors.append("account_id must be a non-empty string")
    since_id = _numeric_id(since_transaction_id)
    if since_id is None:
        errors.append("since_transaction_id must be a numeric string")
    if not isinstance(changes_response, dict):
        errors.append("changes_response must be an object")
        changes_response = {}
    if not isinstance(post_closeout_account_snapshot, dict):
        errors.append("post_closeout_account_snapshot must be an object")
        post_closeout_account_snapshot = {}
    last_id = _numeric_id(changes_response.get("lastTransactionID"))
    snapshot_last_id = _numeric_id(post_closeout_account_snapshot.get("lastTransactionID"))
    if last_id is None or snapshot_last_id is None:
        errors.append("changes and full account snapshot must include numeric lastTransactionID")
    elif last_id != snapshot_last_id:
        errors.append("changes response and full account snapshot lastTransactionID do not match")
    if since_id is not None and last_id is not None and last_id < since_id:
        errors.append("lastTransactionID cannot precede since_transaction_id")

    for label, value in (
        ("expected_closeout_trade_ids", expected_closeout_trade_ids),
        ("pre_closeout_pending_order_ids", pre_closeout_pending_order_ids),
        ("expected_cancelled_order_ids", expected_cancelled_order_ids),
    ):
        if (not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value)
                or len(set(value)) != len(value)):
            errors.append(f"{label} must be a unique array of non-empty string IDs")
    expected_closed = set(expected_closeout_trade_ids) if isinstance(expected_closeout_trade_ids, list) else set()
    pre_order_ids = set(pre_closeout_pending_order_ids) if isinstance(pre_closeout_pending_order_ids, list) else set()
    expected_cancelled = set(expected_cancelled_order_ids) if isinstance(expected_cancelled_order_ids, list) else set()

    observed_times = (evaluated_at_utc, changes_observed_at_utc, account_snapshot_observed_at_utc)
    if any(not isinstance(x, str) or not x.endswith("Z") for x in observed_times):
        errors.append("evaluation and source-observation timestamps must be UTC ISO-8601 ending Z")
    else:
        from datetime import datetime, timezone
        parsed = []
        for value in observed_times:
            try:
                dt = datetime.fromisoformat(value[:-1] + "+00:00")
                if dt.utcoffset() != timezone.utc.utcoffset(dt):
                    raise ValueError
                parsed.append(dt)
            except ValueError:
                errors.append("invalid UTC source-observation timestamp")
                break
        if len(parsed) == 3:
            evaluation, changes_time, snapshot_time = parsed
            if changes_time > evaluation or snapshot_time > evaluation:
                errors.append("account-change or account-snapshot observation is future-dated")
            if snapshot_time < changes_time:
                errors.append("full account snapshot must be observed at or after the changes response")
            age = (evaluation - snapshot_time).total_seconds()
            if (isinstance(max_snapshot_age_seconds, bool)
                    or not isinstance(max_snapshot_age_seconds, (int, float))
                    or not isfinite(max_snapshot_age_seconds) or max_snapshot_age_seconds <= 0):
                errors.append("max_snapshot_age_seconds must be positive and finite")
            elif age < 0 or age > max_snapshot_age_seconds:
                errors.append("full account snapshot is future-dated or stale")

    changes = changes_response.get("changes")
    if not isinstance(changes, dict):
        errors.append("changes_response.changes must be an object")
        changes = {}
    arrays = {name: _records(changes.get(name), name, errors) for name in CHANGE_ARRAYS}
    account_snapshot = post_closeout_account_snapshot.get("account")
    if not isinstance(account_snapshot, dict):
        errors.append("post-closeout snapshot must contain an account object")
        account_snapshot = {}
    if account_snapshot.get("id") != account_id:
        errors.append("post-closeout account snapshot ID does not match account_id")
    account_last_id = _numeric_id(account_snapshot.get("lastTransactionID"))
    if account_last_id is None or (last_id is not None and account_last_id != last_id):
        errors.append("account.lastTransactionID must match the changes response lastTransactionID")

    current_orders = account_snapshot.get("orders")
    current_trades = account_snapshot.get("trades")
    current_positions = account_snapshot.get("positions")
    if not isinstance(current_orders, list) or not isinstance(current_trades, list) or not isinstance(current_positions, list):
        errors.append("full account snapshot must include complete orders, trades and positions arrays")
        current_orders = current_orders if isinstance(current_orders, list) else []
        current_trades = current_trades if isinstance(current_trades, list) else []
        current_positions = current_positions if isinstance(current_positions, list) else []

    if errors:
        return _halt(errors, warnings)

    order_ids: dict[str, str] = {}
    for index, order in enumerate(current_orders):
        oid = order.get("id")
        if not isinstance(oid, str) or not oid or oid in order_ids:
            errors.append(f"post-closeout account orders[{index}] has missing or duplicate ID")
        else:
            state = order.get("state")
            if state != "PENDING":
                errors.append(f"post-closeout account order {oid} is not in PENDING state")
            order_ids[oid] = str(state)
    trade_ids: set[str] = set()
    for index, trade in enumerate(current_trades):
        tid = trade.get("id")
        if not isinstance(tid, str) or not tid or tid in trade_ids:
            errors.append(f"post-closeout account trades[{index}] has missing or duplicate ID")
        else:
            trade_ids.add(tid)
    position_map: dict[str, dict[str, Any]] = {}
    for index, position in enumerate(current_positions):
        instrument = position.get("instrument")
        if not isinstance(instrument, str) or not instrument or instrument in position_map:
            errors.append(f"post-closeout account positions[{index}] has missing or duplicate instrument")
        else:
            position_map[instrument] = position

    opened = {item.get("id") for item in arrays["tradesOpened"] if isinstance(item.get("id"), str)}
    reduced = {item.get("id") for item in arrays["tradesReduced"] if isinstance(item.get("id"), str)}
    closed = {item.get("id") for item in arrays["tradesClosed"] if isinstance(item.get("id"), str)}
    if len(opened) != len(arrays["tradesOpened"]) or len(closed) != len(arrays["tradesClosed"]):
        errors.append("trade change records must each include a string trade id")
    missing_closeout = expected_closed - closed
    if missing_closeout:
        errors.append("expected margin-closeout trades are absent from changes.tradesClosed: " + ", ".join(sorted(missing_closeout)))
    unexpected_remaining = closed & trade_ids
    if unexpected_remaining:
        errors.append("trades reported closed remain in the full account snapshot: " + ", ".join(sorted(unexpected_remaining)))
    unexpectedly_open = opened - trade_ids - closed
    if unexpectedly_open:
        errors.append("newly opened trades are absent from the full account snapshot and were not subsequently closed: " + ", ".join(sorted(unexpectedly_open)))

    filled_order_ids = set()
    for order in arrays["ordersFilled"]:
        oid = order.get("id")
        if not isinstance(oid, str) or not oid:
            errors.append("changes.ordersFilled contains an order without a string ID")
        else:
            filled_order_ids.add(oid)
    cancelled_order_ids = set()
    for order in arrays["ordersCancelled"]:
        oid = order.get("id")
        if not isinstance(oid, str) or not oid:
            errors.append("changes.ordersCancelled contains an order without a string ID")
        else:
            cancelled_order_ids.add(oid)
    missing_cancelled = expected_cancelled - cancelled_order_ids
    if missing_cancelled:
        errors.append("expected dependent-order cancellations are absent from changes.ordersCancelled: " + ", ".join(sorted(missing_cancelled)))

    tx_order_fills: set[str] = set()
    tx_ids: set[int] = set()
    for index, tx in enumerate(arrays["transactions"]):
        tid = _numeric_id(tx.get("id"))
        if tid is None or (since_id is not None and tid <= since_id) or (last_id is not None and tid > last_id):
            errors.append(f"changes.transactions[{index}] has an ID outside the requested transaction interval")
        elif tid in tx_ids:
            errors.append(f"changes.transactions[{index}] has a duplicate transaction ID")
        else:
            tx_ids.add(tid)
        if tx.get("accountID") != account_id:
            errors.append(f"changes.transactions[{index}] accountID mismatch")
        if tx.get("type") == "ORDER_FILL" and isinstance(tx.get("orderID"), str):
            tx_order_fills.add(tx["orderID"])
    if filled_order_ids - tx_order_fills:
        errors.append("ordersFilled contains IDs without matching ORDER_FILL transactions: " + ", ".join(sorted(filled_order_ids - tx_order_fills)))

    for instrument_position in arrays["positions"]:
        instrument = instrument_position.get("instrument")
        if not isinstance(instrument, str):
            errors.append("changed position instrument is missing or invalid")
            continue
        final_position = position_map.get(instrument)
        for side in ("long", "short"):
            changed_units = _position_units(instrument_position, side)
            # A fully closed position may no longer appear in the full account
            # snapshot; absence is equivalent to zero units on both sides.
            final_units = _position_units(final_position, side) if final_position is not None else 0.0
            if changed_units is None or final_units is None:
                errors.append(f"position {instrument} {side} units missing or invalid")
            elif changed_units != final_units:
                errors.append(f"position {instrument} {side} units differ between changes and full account snapshot")

    filled_preexisting = sorted(filled_order_ids & pre_order_ids)
    new_pending = sorted(set(order_ids) - pre_order_ids)
    newly_opened = sorted(opened)
    if newly_opened:
        warnings.append("Account changes report one or more newly opened trades after the closeout boundary; OCC stop must remain active pending independent review.")
    if filled_preexisting:
        warnings.append("One or more pre-closeout pending orders filled during the reconciliation interval.")
    if new_pending:
        warnings.append("The full account snapshot contains pending orders not present in the pre-closeout order set.")

    if errors:
        result = _halt(errors, warnings)
        result.update({
            "newly_opened_trade_ids": newly_opened,
            "unexpectedly_open_trades": sorted(unexpectedly_open),
            "unexpectedly_remaining_closed_trades": sorted(unexpected_remaining),
            "filled_preexisting_order_ids": filled_preexisting,
            "new_pending_order_ids": new_pending,
            "current_pending_order_ids": sorted(order_ids),
        })
        return result

    return {
        "status": "HALT" if newly_opened or filled_preexisting else "PASS",
        "errors": [],
        "warnings": warnings,
        "since_transaction_id": str(since_id),
        "last_transaction_id": str(last_id),
        "newly_opened_trade_ids": newly_opened,
        "unexpectedly_open_trades": [],
        "unexpectedly_remaining_closed_trades": [],
        "filled_preexisting_order_ids": filled_preexisting,
        "new_pending_order_ids": new_pending,
        "current_pending_order_ids": sorted(order_ids),
        "closed_trade_ids_confirmed": sorted(closed),
        "reduced_trade_ids": sorted(reduced),
        "cancelled_order_ids_confirmed": sorted(cancelled_order_ids),
        "position_instruments_reconciled": sorted(position_map),
        "position_reconciliation": "PASS",
        "account_change_reconciliation_complete": True,
        "trade_authority": False, "live_readiness": False,
        "research_only": True, "authority": AUTHORITY,
        "limitations": [
            "Inputs are caller-supplied OANDA response and account snapshot; no API connection, authentication or completeness proof is performed.",
            "AccountChanges.positions contains changed positions, while the full account snapshot is used as the comparison state; this module compares reported long/short units only.",
            "Price-dependent state such as NAV, unrealized P/L and margin may change independently of transactions and is not treated as transaction reconciliation.",
            "A PASS means the supplied transaction-driven changes agree with the supplied full account snapshot; it is not proof of broker state or permission to resume trading.",
        ],
    }

"""Offline reconciliation of OANDA v20 closeout order-cancellation transactions.

Consumes caller-supplied pre/post pending-order snapshots and a complete,
unfiltered transaction-ID range. It never connects to or changes a broker.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

AUTHORITY = "research_only_no_execution_authority"
ENTRY_TYPES = {"LIMIT", "STOP", "MARKET_IF_TOUCHED"}
DEPENDENT_TYPES = {"TAKE_PROFIT", "STOP_LOSS", "GUARANTEED_STOP_LOSS", "TRAILING_STOP_LOSS"}
TERMINAL_TYPES = {"ORDER_CANCEL", "ORDER_FILL", "ORDER_CANCEL_REJECT"}


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.utcoffset() == timezone.utc.utcoffset(parsed) else None


def _id(value: Any) -> int | None:
    if not isinstance(value, str) or not value.isdigit():
        return None
    try:
        return int(value)
    except (ValueError, OverflowError):
        return None


def _blocked(errors: list[str], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": "HALT", "errors": errors, "warnings": warnings or [],
        "closeout_transaction_ids": [], "liquidated_trade_ids": [],
        "orders_expected_cancelled": [], "orders_confirmed_cancelled": [],
        "orders_unexpectedly_still_pending": [], "orders_disappeared_without_terminal_event": [],
        "orders_filled_during_reconciliation": [], "new_pending_order_ids": [],
        "transaction_range_complete": False,
        "cancellation_reconciliation_complete": False,
        "order_cancellation_performed": False, "trade_authority": False,
        "live_readiness": False, "research_only": True, "authority": AUTHORITY,
    }


def _validate_order_list(value: Any, label: str, errors: list[str]) -> tuple[dict[str, dict[str, Any]], set[str]]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a complete array")
        return {}, set()
    result: dict[str, dict[str, Any]] = {}
    for index, order in enumerate(value):
        if not isinstance(order, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        order_id = order.get("id")
        if not isinstance(order_id, str) or not order_id.strip() or order_id in result:
            errors.append(f"{label}[{index}] has a missing or duplicate order id")
            continue
        if order.get("state") != "PENDING":
            errors.append(f"{label}[{index}] must contain only PENDING orders")
            continue
        order_type = order.get("type")
        if not isinstance(order_type, str) or order_type.upper() not in ENTRY_TYPES | DEPENDENT_TYPES:
            errors.append(f"{label}[{index}] has an unsupported order type")
            continue
        order_type = order_type.upper()
        trade_id = order.get("tradeID")
        if order_type in DEPENDENT_TYPES and (not isinstance(trade_id, str) or not trade_id.strip()):
            errors.append(f"{label}[{index}] dependent close order requires tradeID")
            continue
        if order_type in ENTRY_TYPES and trade_id is not None:
            errors.append(f"{label}[{index}] entry order must not contain tradeID")
            continue
        result[order_id] = dict(order, type=order_type)
    return result, set(result)


def assess_oanda_closeout_transaction_reconciliation(
    account_id: Any,
    pre_closeout_pending_orders: Any,
    post_closeout_pending_orders: Any,
    transactions: Any,
    transaction_id_start_exclusive: Any,
    transaction_id_end_inclusive: Any,
    transaction_range_complete: Any,
    transaction_range_unfiltered: Any,
    pre_closeout_orders_complete: Any,
    post_closeout_orders_complete: Any,
    pre_closeout_snapshot_timestamp_utc: Any,
    post_closeout_snapshot_timestamp_utc: Any,
    evaluated_at_utc: Any,
    max_snapshot_age_seconds: Any,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(account_id, str) or not account_id.strip():
        errors.append("account_id must be a non-empty account identifier")
    if transaction_range_complete is not True or transaction_range_unfiltered is not True:
        errors.append("transaction range must be explicitly complete and unfiltered")
    if pre_closeout_orders_complete is not True or post_closeout_orders_complete is not True:
        errors.append("pre- and post-closeout pending-order snapshots must both be complete")
    start_id, end_id = _id(transaction_id_start_exclusive), _id(transaction_id_end_inclusive)
    if start_id is None or end_id is None or end_id <= start_id:
        errors.append("transaction ID bounds must be numeric strings with end greater than start")
    pre_time = _utc(pre_closeout_snapshot_timestamp_utc)
    post_time = _utc(post_closeout_snapshot_timestamp_utc)
    evaluated_time = _utc(evaluated_at_utc)
    if pre_time is None or post_time is None or evaluated_time is None:
        errors.append("pre, post and evaluation timestamps must be UTC ISO-8601 ending Z")
    if pre_time is not None and post_time is not None and post_time < pre_time:
        errors.append("post-closeout snapshot cannot precede the pre-closeout snapshot")
    if (isinstance(max_snapshot_age_seconds, bool)
            or not isinstance(max_snapshot_age_seconds, (int, float))
            or not isfinite(max_snapshot_age_seconds) or max_snapshot_age_seconds <= 0):
        errors.append("max_snapshot_age_seconds must be a positive finite number")
    elif post_time is not None and evaluated_time is not None:
        age = (evaluated_time - post_time).total_seconds()
        if age < 0 or age > max_snapshot_age_seconds:
            errors.append("post-closeout order snapshot is future-dated or stale")

    pre_orders, pre_ids = _validate_order_list(pre_closeout_pending_orders, "pre_closeout_pending_orders", errors)
    post_orders, post_ids = _validate_order_list(post_closeout_pending_orders, "post_closeout_pending_orders", errors)
    if not isinstance(transactions, list) or not transactions:
        errors.append("transactions must be a non-empty complete array")
        transactions = []

    parsed_transactions: list[tuple[int, datetime, dict[str, Any]]] = []
    seen_transaction_ids: set[int] = set()
    for index, transaction in enumerate(transactions):
        if not isinstance(transaction, dict):
            errors.append(f"transactions[{index}] must be an object")
            continue
        transaction_id = _id(transaction.get("id"))
        transaction_time = _utc(transaction.get("time"))
        if transaction_id is None or transaction_time is None:
            errors.append(f"transactions[{index}] requires numeric-string id and UTC time")
            continue
        if transaction_id in seen_transaction_ids:
            errors.append(f"transactions[{index}] has duplicate transaction id")
            continue
        seen_transaction_ids.add(transaction_id)
        if transaction.get("accountID") != account_id:
            errors.append(f"transactions[{index}] accountID does not match the supplied account")
            continue
        if not isinstance(transaction.get("type"), str):
            errors.append(f"transactions[{index}] type is missing")
            continue
        parsed_transactions.append((transaction_id, transaction_time, transaction))

    if errors:
        return _blocked(errors, warnings)
    parsed_transactions.sort(key=lambda item: item[0])
    ids = [item[0] for item in parsed_transactions]
    contiguous = (len(ids) == end_id - start_id and
                  all(transaction_id == start_id + index + 1 for index, transaction_id in enumerate(ids)))
    if not contiguous:
        return _blocked(["transaction IDs are not a complete contiguous range from the supplied exclusive start to inclusive end"], warnings)
    if any(parsed_transactions[index][1] > parsed_transactions[index + 1][1]
           for index in range(len(parsed_transactions) - 1)):
        return _blocked(["transaction timestamps move backwards as transaction IDs increase"], warnings)

    closeout_fills: list[tuple[int, datetime, dict[str, Any]]] = []
    for item in parsed_transactions:
        transaction = item[2]
        if transaction.get("type") == "ORDER_FILL" and transaction.get("reason") == "MARKET_ORDER_MARGIN_CLOSEOUT":
            closeout_fills.append(item)
    if not closeout_fills:
        return _blocked(["complete transaction range contains no ORDER_FILL with reason MARKET_ORDER_MARGIN_CLOSEOUT"], warnings)

    closeout_time_by_trade: dict[str, datetime] = {}
    closeout_ids: list[str] = []
    for transaction_id, transaction_time, transaction in closeout_fills:
        closeout_ids.append(str(transaction_id))
        trades_closed = transaction.get("tradesClosed")
        if not isinstance(trades_closed, list):
            errors.append(f"closeout fill {transaction_id} is missing tradesClosed array")
            continue
        for trade in trades_closed:
            if not isinstance(trade, dict) or not isinstance(trade.get("tradeID"), str) or not trade["tradeID"].strip():
                errors.append(f"closeout fill {transaction_id} has malformed tradesClosed entry")
                continue
            closeout_time_by_trade[trade["tradeID"]] = transaction_time
    if not closeout_time_by_trade:
        errors.append("closeout fill transactions do not identify any closed trade IDs")
    if pre_time is not None and any(pre_time > item[1] for item in closeout_fills):
        errors.append("pre-closeout snapshot timestamp is later than a margin-closeout fill")
    if post_time is not None and any(post_time < item[1] for item in parsed_transactions):
        errors.append("post-closeout snapshot timestamp precedes one or more supplied transactions")
    if errors:
        return _blocked(errors, warnings)

    transaction_events: dict[str, list[tuple[int, datetime, dict[str, Any]]]] = {}
    for item in parsed_transactions:
        transaction = item[2]
        if transaction.get("type") in TERMINAL_TYPES:
            order_id = transaction.get("orderID")
            if isinstance(order_id, str) and order_id.strip():
                transaction_events.setdefault(order_id, []).append(item)

    expected_cancel_ids: list[str] = []
    confirmed_cancelled: list[dict[str, str]] = []
    unexpected_pending: list[str] = []
    disappeared_unexplained: list[str] = []
    filled_orders: list[str] = []

    for order_id, order in pre_orders.items():
        events = transaction_events.get(order_id, [])
        in_post = order_id in post_ids
        linked_trade = order.get("tradeID") if order["type"] in DEPENDENT_TYPES else None
        must_cancel_for_closeout = linked_trade in closeout_time_by_trade if linked_trade else False
        if must_cancel_for_closeout:
            expected_cancel_ids.append(order_id)
            if in_post:
                unexpected_pending.append(order_id)
                errors.append(f"dependent order {order_id} for margin-closed trade {linked_trade} remains pending")
            cancels = [item for item in events if item[2].get("type") == "ORDER_CANCEL"
                       and item[2].get("reason") == "LINKED_TRADE_CLOSED"]
            rejects = [item for item in events if item[2].get("type") == "ORDER_CANCEL_REJECT"]
            if rejects:
                errors.append(f"dependent order {order_id} has an ORDER_CANCEL_REJECT transaction")
            if len(cancels) > 1:
                errors.append(f"dependent order {order_id} has multiple ORDER_CANCEL transactions")
            if not cancels:
                errors.append(f"dependent order {order_id} lacks ORDER_CANCEL reason LINKED_TRADE_CLOSED")
            else:
                valid_cancel = [item for item in cancels if item[1] >= closeout_time_by_trade[linked_trade]]
                if not valid_cancel:
                    errors.append(f"dependent order {order_id} cancellation predates the margin-closeout fill")
                else:
                    confirmed_cancelled.append({
                        "order_id": order_id, "trade_id": linked_trade,
                        "transaction_id": str(valid_cancel[-1][0]),
                        "reason": "LINKED_TRADE_CLOSED",
                    })
        elif not in_post:
            terminal = [item for item in events if item[2].get("type") in {"ORDER_CANCEL", "ORDER_FILL"}]
            if len(terminal) != 1:
                disappeared_unexplained.append(order_id)
                errors.append(f"pre-closeout order {order_id} disappeared without exactly one terminal ORDER_CANCEL or ORDER_FILL")
            elif terminal[0][2].get("type") == "ORDER_FILL":
                filled_orders.append(order_id)
        elif any(item[2].get("type") in {"ORDER_CANCEL", "ORDER_FILL"} for item in events):
            errors.append(f"order {order_id} is still pending post-closeout but also has a terminal transaction")

    new_pending = sorted(post_ids - pre_ids)
    if new_pending:
        warnings.append("Post-closeout snapshot contains new pending order IDs not present in the pre-closeout snapshot; review their creation transactions and exposure semantics.")

    if errors:
        result = _blocked(errors, warnings)
        result.update({
            "closeout_transaction_ids": closeout_ids,
            "liquidated_trade_ids": sorted(closeout_time_by_trade),
            "orders_expected_cancelled": sorted(expected_cancel_ids),
            "orders_confirmed_cancelled": confirmed_cancelled,
            "orders_unexpectedly_still_pending": sorted(set(unexpected_pending)),
            "orders_disappeared_without_terminal_event": sorted(set(disappeared_unexplained)),
            "orders_filled_during_reconciliation": sorted(set(filled_orders)),
            "new_pending_order_ids": new_pending,
            "transaction_range_complete": True,
        })
        return result

    return {
        "status": "PASS", "errors": [], "warnings": warnings,
        "account_id": account_id,
        "transaction_id_start_exclusive": str(start_id),
        "transaction_id_end_inclusive": str(end_id),
        "transaction_count": len(parsed_transactions),
        "transaction_range_complete": True,
        "closeout_transaction_ids": closeout_ids,
        "liquidated_trade_ids": sorted(closeout_time_by_trade),
        "orders_expected_cancelled": sorted(expected_cancel_ids),
        "orders_confirmed_cancelled": confirmed_cancelled,
        "orders_unexpectedly_still_pending": [],
        "orders_disappeared_without_terminal_event": [],
        "orders_filled_during_reconciliation": sorted(set(filled_orders)),
        "new_pending_order_ids": new_pending,
        "pre_closeout_order_count": len(pre_orders),
        "post_closeout_order_count": len(post_orders),
        "cancellation_reconciliation_complete": True,
        "order_cancellation_performed": False,
        "trade_authority": False, "live_readiness": False,
        "research_only": True, "authority": AUTHORITY,
        "limitations": [
            "This replay consumes caller-supplied transaction history; it does not call OANDA or authenticate the account, data export or API response.",
            "A contiguous transaction ID range is a caller-asserted complete, unfiltered range; the module cannot independently prove that no records were omitted before export.",
            "It verifies cancellation records for dependent orders linked to trades closed by MARKET_ORDER_MARGIN_CLOSEOUT fills; it does not validate every possible account-side order lifecycle.",
            "Filled unrelated orders are listed but their resulting trade/position state requires separate account-change reconciliation.",
            "This is a historical evidence audit only; it never submits, cancels, modifies or closes orders.",
        ],
    }

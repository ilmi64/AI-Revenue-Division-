"""Synthetic regression tests for OANDA closeout transaction reconciliation."""
import unittest

from specialist_research.oanda_closeout_transaction_reconciliation import (
    assess_oanda_closeout_transaction_reconciliation,
)


def dependent(order_id="sl-1", trade_id="T1"):
    return {"id": order_id, "state": "PENDING", "type": "STOP_LOSS", "tradeID": trade_id}


def entry(order_id="entry-1"):
    return {
        "id": order_id, "state": "PENDING", "type": "STOP",
        "instrument": "XAU_USD", "units": "1", "positionFill": "OPEN_ONLY",
    }


def closeout_fill(transaction_id="101", trade_id="T1", time="2026-11-18T05:00:01Z"):
    return {
        "id": transaction_id, "accountID": "acct-1", "time": time,
        "type": "ORDER_FILL", "reason": "MARKET_ORDER_MARGIN_CLOSEOUT",
        "orderID": "100", "tradesClosed": [{"tradeID": trade_id, "units": "1"}],
    }


def cancel(transaction_id="102", order_id="sl-1", reason="LINKED_TRADE_CLOSED",
           time="2026-11-18T05:00:01Z"):
    return {
        "id": transaction_id, "accountID": "acct-1", "time": time,
        "type": "ORDER_CANCEL", "orderID": order_id, "reason": reason,
    }


def assess(pre=None, post=None, tx=None, **overrides):
    args = {
        "account_id": "acct-1",
        "pre_closeout_pending_orders": [dependent()] if pre is None else pre,
        "post_closeout_pending_orders": [] if post is None else post,
        "transactions": [closeout_fill(), cancel()] if tx is None else tx,
        "transaction_id_start_exclusive": "100",
        "transaction_id_end_inclusive": "102",
        "reported_last_transaction_id": "102",
        "transaction_range_complete": True,
        "transaction_range_unfiltered": True,
        "pre_closeout_orders_complete": True,
        "post_closeout_orders_complete": True,
        "pre_closeout_snapshot_timestamp_utc": "2026-11-18T05:00:00Z",
        "post_closeout_snapshot_timestamp_utc": "2026-11-18T05:00:02Z",
        "evaluated_at_utc": "2026-11-18T05:00:03Z",
        "max_snapshot_age_seconds": 60,
    }
    args.update(overrides)
    return assess_oanda_closeout_transaction_reconciliation(**args)


class OandaCloseoutTransactionReconciliationTests(unittest.TestCase):
    def test_dependent_order_cancellation_is_verified_by_transaction(self):
        result = assess()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["orders_expected_cancelled"], ["sl-1"])
        self.assertEqual(result["orders_confirmed_cancelled"][0]["reason"], "LINKED_TRADE_CLOSED")
        self.assertFalse(result["order_cancellation_performed"])
        self.assertFalse(result["trade_authority"])

    def test_dependent_order_still_pending_after_closeout_halts(self):
        result = assess(post=[dependent()])
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["orders_unexpectedly_still_pending"], ["sl-1"])

    def test_missing_linked_trade_closed_cancel_event_halts(self):
        result = assess(tx=[closeout_fill(), {
            "id": "102", "accountID": "acct-1", "time": "2026-11-18T05:00:01Z",
            "type": "ORDER_CANCEL", "orderID": "sl-1", "reason": "CLIENT_REQUEST",
        }])
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("LINKED_TRADE_CLOSED" in e for e in result["errors"]))

    def test_missing_cancel_event_halts(self):
        result = assess(tx=[closeout_fill(), {
            "id": "102", "accountID": "acct-1", "time": "2026-11-18T05:00:01Z",
            "type": "MARGIN_CALL_ENTER",
        }])
        self.assertEqual(result["status"], "HALT")

    def test_cancel_reject_halts(self):
        result = assess(tx=[closeout_fill(), {
            "id": "102", "accountID": "acct-1", "time": "2026-11-18T05:00:01Z",
            "type": "ORDER_CANCEL_REJECT", "orderID": "sl-1",
        }])
        self.assertEqual(result["status"], "HALT")

    def test_unrelated_later_account_transaction_does_not_invalidate_order_snapshot(self):
        result = assess(
            tx=[closeout_fill(), cancel(), {
                "id": "103", "accountID": "acct-1", "time": "2026-11-18T05:00:05Z",
                "type": "MARGIN_CALL_EXIT",
            }],
            transaction_id_end_inclusive="103", reported_last_transaction_id="103",,
            evaluated_at_utc="2026-11-18T05:00:06Z",
        )
        self.assertEqual(result["status"], "PASS")

    def test_dependent_order_snapshot_must_follow_linked_trade_cancel(self):
        result = assess(tx=[
            closeout_fill(), cancel(time="2026-11-18T05:00:03Z"),
        ])
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("predates its linked-trade cancellation" in error for error in result["errors"]))

    def test_unrelated_order_snapshot_must_follow_its_terminal_event(self):
        result = assess(
            pre=[dependent(), entry()], post=[],
            tx=[closeout_fill(), cancel(), {
                "id": "103", "accountID": "acct-1", "time": "2026-11-18T05:00:03Z",
                "type": "ORDER_CANCEL", "orderID": "entry-1", "reason": "CLIENT_REQUEST",
            }],
            transaction_id_end_inclusive="103", reported_last_transaction_id="103",
        )
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("occurred after the post-closeout snapshot" in error for error in result["errors"]))

    def test_cancel_before_closeout_fill_halts(self):
        result = assess(tx=[
            cancel(transaction_id="101", time="2026-11-18T05:00:00Z"),
            closeout_fill(transaction_id="102", time="2026-11-18T05:00:01Z"),
        ])
        self.assertEqual(result["status"], "HALT")

    def test_unrelated_pending_order_can_remain(self):
        result = assess(pre=[dependent(), entry()], post=[entry()])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["post_closeout_order_count"], 1)

    def test_unrelated_order_disappearance_with_cancel_event_is_reconciled(self):
        result = assess(
            pre=[dependent(), entry()],
            post=[],
            tx=[closeout_fill(), cancel(), {
                "id": "103", "accountID": "acct-1", "time": "2026-11-18T05:00:01Z",
                "type": "ORDER_CANCEL", "orderID": "entry-1", "reason": "CLIENT_REQUEST",
            }],
            transaction_id_end_inclusive="103", reported_last_transaction_id="103",
        )
        self.assertEqual(result["status"], "PASS")

    def test_unrelated_order_disappearance_without_terminal_event_halts(self):
        result = assess(
            pre=[dependent(), entry()], post=[],
            tx=[closeout_fill(), cancel()],
        )
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["orders_disappeared_without_terminal_event"], ["entry-1"])

    def test_unrelated_order_disappearance_with_fill_is_reported(self):
        result = assess(
            pre=[dependent(), entry()], post=[],
            tx=[closeout_fill(), cancel(), {
                "id": "103", "accountID": "acct-1", "time": "2026-11-18T05:00:01Z",
                "type": "ORDER_FILL", "orderID": "entry-1", "reason": "STOP_ORDER",
            }],
            transaction_id_end_inclusive="103", reported_last_transaction_id="103",
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["orders_filled_during_reconciliation"], ["entry-1"])

    def test_order_cannot_be_pending_and_terminal(self):
        result = assess(post=[dependent(), entry()])
        self.assertEqual(result["status"], "HALT")

    def test_transaction_ids_must_be_contiguous(self):
        result = assess(tx=[closeout_fill(), cancel(transaction_id="103")])
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("contiguous range" in e for e in result["errors"]))

    def test_transaction_timestamps_must_not_move_backwards(self):
        result = assess(tx=[
            closeout_fill(transaction_id="101", time="2026-11-18T05:00:02Z"),
            cancel(transaction_id="102", time="2026-11-18T05:00:01Z"),
        ])
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("timestamps move backwards" in error for error in result["errors"]))

    def test_multiple_linked_trade_cancellation_transactions_halt(self):
        result = assess(tx=[
            closeout_fill(), cancel(),
            cancel(transaction_id="103", time="2026-11-18T05:00:02Z"),
        ], transaction_id_end_inclusive="103", reported_last_transaction_id="103")
        self.assertEqual(result["status"], "HALT")

    def test_duplicate_transaction_id_halts(self):
        result = assess(tx=[closeout_fill(), cancel(), cancel()])
        self.assertEqual(result["status"], "HALT")

    def test_transaction_account_must_match(self):
        bad = cancel()
        bad["accountID"] = "other-account"
        result = assess(tx=[closeout_fill(), bad])
        self.assertEqual(result["status"], "HALT")

    def test_reported_last_transaction_id_must_match_range_end(self):
        result = assess(reported_last_transaction_id="103")
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("reported_last_transaction_id" in error for error in result["errors"]))

    def test_transaction_range_must_be_complete(self):
        self.assertEqual(assess(transaction_range_complete=False)["status"], "HALT")

    def test_transaction_range_must_be_unfiltered(self):
        self.assertEqual(assess(transaction_range_unfiltered=False)["status"], "HALT")

    def test_both_order_snapshots_must_be_complete(self):
        self.assertEqual(assess(pre_closeout_orders_complete=False)["status"], "HALT")
        self.assertEqual(assess(post_closeout_orders_complete=False)["status"], "HALT")

    def test_pre_snapshot_must_precede_closeout(self):
        result = assess(pre_closeout_snapshot_timestamp_utc="2026-11-18T05:00:02Z")
        self.assertEqual(result["status"], "HALT")

    def test_post_snapshot_must_follow_all_transactions(self):
        result = assess(post_closeout_snapshot_timestamp_utc="2026-11-18T05:00:00Z")
        self.assertEqual(result["status"], "HALT")

    def test_stale_post_snapshot_halts(self):
        result = assess(evaluated_at_utc="2026-11-18T05:02:00Z", max_snapshot_age_seconds=60)
        self.assertEqual(result["status"], "HALT")

    def test_no_margin_closeout_fill_halts(self):
        result = assess(tx=[{
            "id": "101", "accountID": "acct-1", "time": "2026-11-18T05:00:01Z",
            "type": "ORDER_FILL", "reason": "MARKET_ORDER", "tradesClosed": [],
        }, cancel()])
        self.assertEqual(result["status"], "HALT")

    def test_closeout_fill_requires_closed_trade_ids(self):
        fill = closeout_fill()
        fill.pop("tradesClosed")
        self.assertEqual(assess(tx=[fill, cancel()])["status"], "HALT")

    def test_dependent_order_for_other_trade_is_not_expected_cancelled(self):
        result = assess(
            pre=[dependent(trade_id="T2")], post=[dependent(trade_id="T2")],
            tx=[closeout_fill(), {
                "id": "102", "accountID": "acct-1", "time": "2026-11-18T05:00:01Z",
                "type": "MARGIN_CALL_ENTER",
            }],
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["orders_expected_cancelled"], [])

    def test_new_post_closeout_order_is_visible(self):
        new_order = entry("new-order")
        result = assess(post=[new_order])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["new_pending_order_ids"], ["new-order"])
        self.assertTrue(result["warnings"])

    def test_missing_or_invalid_account_id_halts(self):
        self.assertEqual(assess(account_id="")["status"], "HALT")

    def test_authority_is_never_promoted(self):
        result = assess()
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertEqual(result["authority"], "research_only_no_execution_authority")


if __name__ == "__main__":
    unittest.main()

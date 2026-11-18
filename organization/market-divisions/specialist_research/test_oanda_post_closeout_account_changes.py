"""Synthetic tests for offline OANDA post-closeout account-change reconciliation."""
import unittest

from specialist_research.oanda_post_closeout_account_changes import (
    assess_oanda_post_closeout_account_changes,
)


def base(changes=None, account=None, **overrides):
    arrays = {
        "ordersCreated": [],
        "ordersCancelled": [{"id": "sl-1"}],
        "ordersFilled": [],
        "ordersTriggered": [],
        "tradesOpened": [],
        "tradesReduced": [],
        "tradesClosed": [{"id": "T1"}],
        "positions": [],
        "transactions": [
            {"id": "101", "accountID": "acct-1", "type": "ORDER_FILL", "orderID": "closeout"},
            {"id": "102", "accountID": "acct-1", "type": "ORDER_CANCEL", "orderID": "sl-1"},
        ],
    }
    if changes:
        arrays.update(changes)
    account_data = {
        "id": "acct-1", "lastTransactionID": "102",
        "orders": [], "trades": [], "positions": [],
    }
    if account:
        account_data.update(account)
    args = {
        "account_id": "acct-1",
        "since_transaction_id": "100",
        "changes_response": {"lastTransactionID": "102", "changes": arrays},
        "post_closeout_account_snapshot": {
            "lastTransactionID": "102", "account": account_data,
        },
        "expected_closeout_trade_ids": ["T1"],
        "pre_closeout_pending_order_ids": ["sl-1", "entry-1"],
        "expected_cancelled_order_ids": ["sl-1"],
        "evaluated_at_utc": "2026-11-18T05:00:10Z",
        "changes_observed_at_utc": "2026-11-18T05:00:05Z",
        "account_snapshot_observed_at_utc": "2026-11-18T05:00:06Z",
        "max_snapshot_age_seconds": 60,
    }
    args.update(overrides)
    return assess_oanda_post_closeout_account_changes(**args)


class OandaPostCloseoutAccountChangesTests(unittest.TestCase):
    def test_closed_trade_and_linked_order_cancellation_reconcile(self):
        result = base()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["closed_trade_ids_confirmed"], ["T1"])
        self.assertEqual(result["cancelled_order_ids_confirmed"], ["sl-1"])
        self.assertFalse(result["trade_authority"])

    def test_missing_expected_closed_trade_halts(self):
        result = base(changes={"tradesClosed": []})
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("tradesClosed" in item for item in result["errors"]))

    def test_closed_trade_must_not_remain_open(self):
        result = base(account={"trades": [{"id": "T1"}]})
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(result["unexpectedly_remaining_closed_trades"])

    def test_new_trade_opened_after_closeout_halts(self):
        result = base(
            changes={
                "ordersFilled": [{"id": "entry-1"}],
                "tradesOpened": [{"id": "T2"}],
                "transactions": [
                    {"id": "101", "accountID": "acct-1", "type": "ORDER_FILL",
                     "orderID": "closeout"},
                    {"id": "102", "accountID": "acct-1", "type": "ORDER_FILL",
                     "orderID": "entry-1", "tradeOpened": {"tradeID": "T2"}},
                ],
            },
            account={"trades": [{"id": "T2"}]},
        )
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["newly_opened_trade_ids"], ["T2"])
        self.assertEqual(result["filled_preexisting_order_ids"], ["entry-1"])

    def test_new_trade_must_appear_in_full_account_snapshot(self):
        result = base(changes={"tradesOpened": [{"id": "T2"}]})
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("absent from the full account" in item for item in result["errors"]))

    def test_filled_order_requires_matching_fill_transaction(self):
        result = base(changes={"ordersFilled": [{"id": "entry-1"}]})
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("ORDER_FILL" in item for item in result["errors"]))

    def test_new_order_fill_after_closeout_halts_even_without_open_trade(self):
        result = base(
            changes={
                "ordersFilled": [{"id": "new-entry"}],
                "transactions": [
                    {"id": "101", "accountID": "acct-1", "type": "ORDER_FILL",
                     "orderID": "closeout", "reason": "MARKET_ORDER_MARGIN_CLOSEOUT"},
                    {"id": "102", "accountID": "acct-1", "type": "ORDER_FILL",
                     "orderID": "new-entry", "reason": "CLIENT_ORDER"},
                ],
            }
        )
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["unexpected_filled_order_ids"], ["new-entry"])

    def test_newly_created_order_halts_even_if_not_pending_at_snapshot(self):
        result = base(
            changes={
                "ordersCreated": [{"id": "new-order"}],
                "ordersCancelled": [{"id": "sl-1"}, {"id": "new-order"}],
            }
        )
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["newly_created_order_ids"], ["new-order"])

    def test_triggered_order_after_closeout_halts(self):
        result = base(changes={"ordersTriggered": [{"id": "entry-1"}]})
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["triggered_order_ids"], ["entry-1"])

    def test_explicit_margin_closeout_fill_is_not_classified_as_unexpected(self):
        result = base(
            changes={
                "ordersFilled": [{"id": "closeout"}],
                "transactions": [
                    {"id": "101", "accountID": "acct-1", "type": "ORDER_FILL",
                     "orderID": "closeout", "reason": "MARKET_ORDER_MARGIN_CLOSEOUT"},
                    {"id": "102", "accountID": "acct-1", "type": "ORDER_CANCEL", "orderID": "sl-1"},
                ],
            }
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["unexpected_filled_order_ids"], [])

    def test_new_pending_order_after_closeout_halts_for_exposure_review(self):
        result = base(account={"orders": [{"id": "new-entry", "state": "PENDING"}]})
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["new_pending_order_ids"], ["new-entry"])

    def test_expected_linked_order_cancellation_must_be_reported(self):
        result = base(changes={"ordersCancelled": []})
        self.assertEqual(result["status"], "HALT")

    def test_unrelated_cancellations_do_not_expand_expected_linked_order_subset(self):
        result = base(changes={"ordersCancelled": [{"id": "sl-1"}, {"id": "unrelated-2"}]})
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["cancelled_order_ids_confirmed"], ["sl-1", "unrelated-2"])
        self.assertEqual(result["expected_cancelled_order_ids_confirmed"], ["sl-1"])

    def test_account_snapshot_and_changes_last_transaction_id_must_match(self):
        result = base(account={"lastTransactionID": "103"})
        result["post_closeout_account_snapshot"]["lastTransactionID"] = "103"
        self.assertEqual(result["status"], "HALT")

    def test_position_units_must_match_full_account_snapshot(self):
        result = base(
            changes={"positions": [{
                "instrument": "EUR_USD",
                "long": {"units": "10"}, "short": {"units": "0"},
            }]},
            account={"positions": [{
                "instrument": "EUR_USD",
                "long": {"units": "5"}, "short": {"units": "0"},
            }]},
        )
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("units differ" in item for item in result["errors"]))

    def test_position_units_match(self):
        result = base(
            changes={"positions": [{
                "instrument": "EUR_USD",
                "long": {"units": "10"}, "short": {"units": "0"},
            }]},
            account={"positions": [{
                "instrument": "EUR_USD",
                "long": {"units": "10"}, "short": {"units": "0"},
            }]},
        )
        self.assertEqual(result["status"], "PASS")

    def test_fully_closed_position_may_be_absent_from_full_account_positions(self):
        result = base(changes={"positions": [{
            "instrument": "EUR_USD",
            "long": {"units": "0"}, "short": {"units": "0"},
        }]})
        self.assertEqual(result["status"], "PASS")

    def test_future_snapshot_is_rejected(self):
        result = base(account_snapshot_observed_at_utc="2026-11-18T05:00:11Z")
        self.assertEqual(result["status"], "HALT")

    def test_wrong_account_id_is_rejected(self):
        result = base(account={"id": "other"})
        self.assertEqual(result["status"], "HALT")


if __name__ == "__main__":
    unittest.main()

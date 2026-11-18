"""Synthetic regression tests for OANDA post-closeout pending-order audit."""
import unittest

from specialist_research.oanda_pending_order_exposure import assess_oanda_post_closeout_pending_orders


def assess(orders=None, liquidated=None, **overrides):
    args = {
        "pending_orders": orders or [],
        "liquidated_trade_ids": liquidated if liquidated is not None else ["trade-1"],
        "remaining_open_trade_ids": ["trade-2"],
        "remaining_open_trade_ids_complete": True,
        "reported_pending_order_count": len(orders or []),
        "account_hedging_enabled": False,
        "source_timestamp_utc": "2026-11-17T20:45:00Z",
        "evaluated_at_utc": "2026-11-17T20:45:20Z",
        "max_snapshot_age_seconds": 60,
        "pending_orders_complete": True,
        "closeout_occurred": True,
    }
    args.update(overrides)
    return assess_oanda_post_closeout_pending_orders(**args)


def entry(order_id="entry-1", **extra):
    value = {
        "id": order_id, "state": "PENDING", "type": "STOP",
        "instrument": "XAU_USD", "units": "10", "positionFill": "OPEN_ONLY",
    }
    value.update(extra)
    return value


def linked(order_id="dependent-1", trade_id="trade-1", order_type="STOP_LOSS"):
    return {"id": order_id, "state": "PENDING", "type": order_type, "tradeID": trade_id}


class OandaPendingOrderExposureTests(unittest.TestCase):
    def test_empty_pending_order_snapshot_passes(self):
        result = assess()
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["possible_exposure_reopening"])

    def test_unrelated_open_only_order_halts(self):
        result = assess([entry()])
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["orders_surviving_and_potentially_opening"][0]["order_id"], "entry-1")

    def test_unrelated_default_non_hedging_order_can_reopen(self):
        result = assess([entry(positionFill="DEFAULT")], account_hedging_enabled=False)
        self.assertEqual(result["orders_surviving_and_potentially_opening"][0]["effective_position_fill"], "REDUCE_FIRST")
        self.assertTrue(result["possible_exposure_reopening"])

    def test_unrelated_default_hedging_order_can_reopen(self):
        result = assess([entry(positionFill="DEFAULT")], account_hedging_enabled=True)
        self.assertEqual(result["orders_surviving_and_potentially_opening"][0]["effective_position_fill"], "OPEN_ONLY")

    def test_reduce_first_order_can_reopen_after_reducing(self):
        result = assess([entry(positionFill="REDUCE_FIRST")])
        self.assertEqual(result["status"], "HALT")

    def test_reduce_only_order_does_not_reopen_exposure(self):
        result = assess([entry(positionFill="REDUCE_ONLY")])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["orders_surviving_but_reduce_only"]), 1)

    def test_dependent_stop_loss_for_liquidated_trade_must_be_cancelled(self):
        result = assess([linked()])
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("expected cancellation" in item for item in result["errors"]))

    def test_dependent_take_profit_for_liquidated_trade_must_be_cancelled(self):
        result = assess([linked(order_type="TAKE_PROFIT")])
        self.assertEqual(result["status"], "HALT")

    def test_dependent_order_for_non_liquidated_trade_remains_linked(self):
        result = assess([linked(trade_id="trade-2")])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["orders_still_linked_to_open_trades"][0]["trade_id"], "trade-2")

    def test_dependent_order_for_unknown_trade_id_blocks(self):
        result = assess([linked(trade_id="trade-unknown")])
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("neither confirmed liquidated nor confirmed open" in item for item in result["errors"]))

    def test_liquidated_and_remaining_trade_sets_must_be_disjoint(self):
        result = assess(remaining_open_trade_ids=["trade-1"])
        self.assertEqual(result["status"], "HALT")

    def test_boolean_order_units_are_rejected(self):
        self.assertEqual(assess([entry(units=True)])["status"], "HALT")

    def test_trailing_stop_for_non_liquidated_trade_remains_linked(self):
        result = assess([linked(trade_id="trade-2", order_type="TRAILING_STOP_LOSS")])
        self.assertEqual(result["status"], "PASS")

    def test_unrelated_limit_order_halts(self):
        result = assess([entry(type="LIMIT")])
        self.assertEqual(result["status"], "HALT")

    def test_unrelated_market_if_touched_order_halts(self):
        result = assess([entry(type="MARKET_IF_TOUCHED")])
        self.assertEqual(result["status"], "HALT")

    def test_unknown_order_type_blocks(self):
        result = assess([entry(type="UNKNOWN")])
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(result["errors"])

    def test_duplicate_order_ids_block(self):
        result = assess([entry("same"), entry("same")])
        self.assertEqual(result["status"], "HALT")

    def test_non_pending_order_blocks(self):
        result = assess([entry(state="FILLED")])
        self.assertEqual(result["status"], "HALT")

    def test_missing_units_blocks(self):
        order = entry()
        order.pop("units")
        self.assertEqual(assess([order])["status"], "HALT")

    def test_zero_units_block(self):
        self.assertEqual(assess([entry(units="0")])["status"], "HALT")

    def test_unknown_position_fill_blocks(self):
        self.assertEqual(assess([entry(positionFill="MAYBE")])["status"], "HALT")

    def test_reported_pending_order_count_mismatch_blocks(self):
        result = assess([entry()], reported_pending_order_count=0)
        self.assertEqual(result["status"], "HALT")

    def test_incomplete_remaining_trade_snapshot_blocks(self):
        result = assess(remaining_open_trade_ids_complete=False)
        self.assertEqual(result["status"], "HALT")

    def test_missing_hedging_mode_blocks(self):
        result = assess(account_hedging_enabled=None)
        self.assertEqual(result["status"], "HALT")

    def test_missing_closeout_confirmation_blocks(self):
        result = assess(closeout_occurred=False)
        self.assertEqual(result["status"], "HALT")

    def test_explicit_empty_liquidated_trade_list_is_valid(self):
        result = assess(liquidated=[])
        self.assertEqual(result["status"], "PASS")

    def test_missing_liquidated_trade_list_blocks(self):
        result = assess(liquidated_trade_ids=None)
        self.assertEqual(result["status"], "HALT")

    def test_incomplete_pending_order_snapshot_blocks(self):
        result = assess(pending_orders_complete=False)
        self.assertEqual(result["status"], "HALT")

    def test_missing_snapshot_timestamp_blocks(self):
        self.assertEqual(assess(source_timestamp_utc=None)["status"], "HALT")

    def test_stale_snapshot_blocks(self):
        result = assess(evaluated_at_utc="2026-11-17T20:47:00Z", max_snapshot_age_seconds=60)
        self.assertEqual(result["status"], "HALT")

    def test_future_snapshot_blocks(self):
        result = assess(source_timestamp_utc="2026-11-17T20:46:00Z")
        self.assertEqual(result["status"], "HALT")

    def test_boolean_freshness_limit_blocks(self):
        self.assertEqual(assess(max_snapshot_age_seconds=True)["status"], "HALT")

    def test_order_cancellation_is_never_performed(self):
        result = assess([entry()])
        self.assertFalse(result["order_cancellation_performed"])
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])


if __name__ == "__main__":
    unittest.main()

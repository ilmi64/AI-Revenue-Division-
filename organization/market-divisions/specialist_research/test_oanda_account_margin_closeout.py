"""Synthetic tests for OANDA Canada account-level margin closeout replay."""
import unittest

from specialist_research.oanda_account_margin_closeout import (
    assess_oanda_margin_state, replay_oanda_account_margin_closeout,
)


def positions():
    return [
        {"position_id": "gold-xau", "desk_id": "gold", "instrument_id": "XAUUSD", "market_status": "open"},
        {"position_id": "fx-eurusd", "desk_id": "forex", "instrument_id": "EURUSD", "market_status": "open"},
        {"position_id": "index-spx", "desk_id": "indices", "instrument_id": "SPX500", "market_status": "open"},
    ]


def observation(day, nav=1000, used=1000, statuses=None, sequence=None, daily=True, trading_date=None):
    date_value = trading_date or f"2026-11-{day:02d}"
    event = {
        "timestamp_utc": f"{date_value}T20:45:00Z",
        "nav_mid": nav,
        "margin_used": used,
        "position_market_status": statuses or {
            "gold-xau": "open", "fx-eurusd": "open", "index-spx": "open",
        },
        "trading_day_check": daily,
    }
    if daily:
        event["trading_day_sequence"] = sequence if sequence is not None else day - 16
        event["trading_calendar_status"] = "verified"
    return event


class OandaMarginStateTests(unittest.TestCase):
    def test_within_margin_requirements(self):
        result = assess_oanda_margin_state(1200, 1000)
        self.assertEqual(result["status"], "WITHIN_MARGIN_REQUIREMENTS")
        self.assertFalse(result["margin_call"])
        self.assertFalse(result["early_closeout_triggered"])

    def test_margin_call_below_margin_used(self):
        result = assess_oanda_margin_state(999, 1000)
        self.assertTrue(result["margin_call"])
        self.assertFalse(result["early_closeout_triggered"])
        self.assertAlmostEqual(result["margin_closeout_percentage"], 50.05005005)

    def test_exact_half_margin_triggers_early_closeout(self):
        result = assess_oanda_margin_state(500, 1000)
        self.assertTrue(result["early_closeout_triggered"])
        self.assertEqual(result["margin_closeout_percentage"], 100.0)

    def test_below_half_margin_triggers_early_closeout(self):
        self.assertTrue(assess_oanda_margin_state(400, 1000)["early_closeout_triggered"])

    def test_zero_nav_is_handled_without_infinity_json_value(self):
        result = assess_oanda_margin_state(0, 1000)
        self.assertIsNone(result["margin_closeout_percentage"])
        self.assertTrue(result["margin_closeout_percentage_unbounded"])
        self.assertTrue(result["early_closeout_triggered"])

    def test_margin_call_recovery_remains_historically_latched(self):
        result = replay_oanda_account_margin_closeout("CAD", positions(), [
            observation(17, nav=900, used=1000, daily=False),
            {
                "timestamp_utc": "2026-11-18T14:00:00Z", "nav_mid": 1200, "margin_used": 1000,
                "position_market_status": {"gold-xau": "open", "fx-eurusd": "open", "index-spx": "open"},
                "trading_day_check": False,
            },
        ])
        self.assertEqual(result["status"], "MARGIN_CALL_OBSERVED_RECOVERED")
        self.assertTrue(result["margin_call_observed"])
        self.assertFalse(result["current_margin_call_active"])

    def test_zero_margin_used_has_no_margin_trigger(self):
        result = assess_oanda_margin_state(0, 0)
        self.assertFalse(result["margin_call"])
        self.assertFalse(result["early_closeout_triggered"])

    def test_extreme_margin_percentage_does_not_emit_infinity(self):
        result = assess_oanda_margin_state(1e-308, 1e308)
        self.assertTrue(result["early_closeout_triggered"])
        self.assertIsNone(result["margin_closeout_percentage"])
        self.assertTrue(result["margin_closeout_percentage_unbounded"])

    def test_boolean_amount_rejected(self):
        self.assertEqual(assess_oanda_margin_state(True, 100)["status"], "INVALID_MARGIN_INPUT")


class OandaAccountCloseoutReplayTests(unittest.TestCase):
    def test_early_closeout_batches_all_tradable_positions_across_desks(self):
        result = replay_oanda_account_margin_closeout(
            "CAD", positions(), [observation(17, nav=500, used=1000)]
        )
        self.assertEqual(result["status"], "CLOSEOUT_TRIGGERED")
        self.assertEqual(set(result["position_ids_closed_by_model"]), {"gold-xau", "fx-eurusd", "index-spx"})
        self.assertEqual(result["closeout_batches"][0]["position_ordering"], "NO_SEQUENCE_ASSUMED_BATCH_CLOSEOUT")

    def test_closed_market_position_is_deferred(self):
        result = replay_oanda_account_margin_closeout(
            "CAD", positions(), [observation(17, nav=500, used=1000, statuses={
                "gold-xau": "open", "fx-eurusd": "closed", "index-spx": "halted",
            })]
        )
        batch = result["closeout_batches"][0]
        self.assertEqual(batch["position_ids_closed_as_batch"], ["gold-xau"])
        self.assertEqual(set(batch["position_ids_deferred_market_closed_or_halted"]), {"fx-eurusd", "index-spx"})
        self.assertEqual(len(result["remaining_open_positions"]), 2)

    def test_deferred_positions_can_be_closed_on_reopen_if_threshold_remains(self):
        events = [
            observation(17, nav=500, used=1000, statuses={
                "gold-xau": "open", "fx-eurusd": "closed", "index-spx": "halted",
            }),
            {
                "timestamp_utc": "2026-11-18T14:00:00Z",
                "nav_mid": 400, "margin_used": 1000,
                "position_market_status": {"fx-eurusd": "open", "index-spx": "open"},
                "trading_day_check": False,
            },
        ]
        result = replay_oanda_account_margin_closeout("CAD", positions(), events)
        self.assertEqual(len(result["closeout_batches"]), 2)
        self.assertEqual(set(result["position_ids_closed_by_model"]), {"gold-xau", "fx-eurusd", "index-spx"})

    def test_deferred_early_closeout_retries_at_market_reopen_while_still_under_margin(self):
        events = [
            observation(17, nav=500, used=1000, statuses={
                "gold-xau": "open", "fx-eurusd": "closed", "index-spx": "halted",
            }),
            {
                "timestamp_utc": "2026-11-18T14:00:00Z",
                "nav_mid": 900, "margin_used": 1000,
                "position_market_status": {"fx-eurusd": "open", "index-spx": "open"},
                "trading_day_check": False,
            },
        ]
        result = replay_oanda_account_margin_closeout("CAD", positions(), events)
        self.assertEqual(len(result["closeout_batches"]), 2)
        self.assertEqual(result["closeout_batches"][1]["trigger"], "RETRY_DEFERRED_CLOSEOUT_WHILE_UNDERMARGINED")
        self.assertEqual(set(result["position_ids_closed_by_model"]), {"gold-xau", "fx-eurusd", "index-spx"})

    def test_six_consecutive_under_margined_daily_checks_trigger_closeout(self):
        events = [observation(i, nav=900, used=1000, sequence=i, trading_date=date) for i, date in enumerate(["2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-23", "2026-11-24"], 1)]
        result = replay_oanda_account_margin_closeout("CAD", positions(), events)
        self.assertEqual(result["status"], "CLOSEOUT_TRIGGERED")
        self.assertEqual(result["closeout_batches"][0]["trigger"], "SIX_CONSECUTIVE_UNDERMARGINED_TRADING_DAYS")

    def test_five_under_margined_days_do_not_trigger_time_closeout(self):
        events = [observation(i, nav=900, used=1000, sequence=i, trading_date=date) for i, date in enumerate(["2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-23"], 1)]
        result = replay_oanda_account_margin_closeout("CAD", positions(), events)
        self.assertEqual(result["status"], "MARGIN_CALL_ACTIVE")
        self.assertEqual(result["closeout_batches"], [])

    def test_recovery_resets_consecutive_day_counter(self):
        events = [
            observation(1, nav=900, used=1000, sequence=1, trading_date="2026-11-17"),
            observation(2, nav=900, used=1000, sequence=2, trading_date="2026-11-18"),
            observation(3, nav=1100, used=1000, sequence=3, trading_date="2026-11-19"),
            observation(4, nav=900, used=1000, sequence=4, trading_date="2026-11-20"),
            observation(5, nav=900, used=1000, sequence=5, trading_date="2026-11-23"),
            observation(6, nav=900, used=1000, sequence=6, trading_date="2026-11-24"),
            observation(7, nav=900, used=1000, sequence=7, trading_date="2026-11-25"),
        ]
        result = replay_oanda_account_margin_closeout("CAD", positions(), events)
        self.assertEqual(result["consecutive_under_margined_trading_days"], 5)
        self.assertEqual(result["closeout_batches"], [])

    def test_weekend_daily_check_blocks(self):
        result = replay_oanda_account_margin_closeout("CAD", positions(), [observation(21)])
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")

    def test_six_day_closeout_deferred_until_market_reopens_while_still_undermargined(self):
        dates = ["2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-23", "2026-11-24"]
        events = [observation(i, nav=900, used=1000, sequence=i, trading_date=date,
                              statuses={"gold-xau": "closed", "fx-eurusd": "closed", "index-spx": "closed"} if i == 6 else None)
                  for i, date in enumerate(dates, 1)]
        events.append({
            "timestamp_utc": "2026-11-25T14:00:00Z", "nav_mid": 900, "margin_used": 1000,
            "position_market_status": {"gold-xau": "open", "fx-eurusd": "open", "index-spx": "open"},
            "trading_day_check": False,
        })
        result = replay_oanda_account_margin_closeout("CAD", positions(), events)
        self.assertEqual(len(result["closeout_batches"]), 2)
        self.assertEqual(set(result["position_ids_closed_by_model"]), {"gold-xau", "fx-eurusd", "index-spx"})

    def test_wrong_daily_check_time_blocks(self):
        event = observation(17)
        event["timestamp_utc"] = "2026-11-17T20:44:00Z"
        result = replay_oanda_account_margin_closeout("CAD", positions(), [event])
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")

    def test_unverified_calendar_blocks_time_rule(self):
        event = observation(17)
        event["trading_calendar_status"] = "unknown"
        result = replay_oanda_account_margin_closeout("CAD", positions(), [event])
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")

    def test_missing_daily_sequence_blocks_time_rule(self):
        event = observation(17)
        del event["trading_day_sequence"]
        result = replay_oanda_account_margin_closeout("CAD", positions(), [event])
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")

    def test_nonconsecutive_daily_sequence_blocks_time_rule(self):
        events = [observation(17, sequence=1), observation(18, sequence=3)]
        result = replay_oanda_account_margin_closeout("CAD", positions(), events)
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")

    def test_missing_position_market_status_blocks(self):
        event = observation(17)
        del event["position_market_status"]["index-spx"]
        result = replay_oanda_account_margin_closeout("CAD", positions(), [event])
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")

    def test_invalid_position_metadata_blocks(self):
        items = [{"position_id": "gold", "desk_id": {"not": "text"}, "instrument_id": "XAUUSD"}]
        result = replay_oanda_account_margin_closeout("CAD", items, [{
            "timestamp_utc": "2026-11-17T20:45:00Z", "nav_mid": 1000, "margin_used": 900,
            "position_market_status": {"gold": "open"}, "trading_day_check": False,
        }])
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")

    def test_duplicate_position_ids_block(self):
        items = positions() + [positions()[0]]
        result = replay_oanda_account_margin_closeout("CAD", items, [observation(17)])
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")

    def test_timestamps_must_be_strictly_increasing(self):
        events = [observation(17, sequence=1), observation(17, sequence=2)]
        result = replay_oanda_account_margin_closeout("CAD", positions(), events)
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")

    def test_intraday_early_trigger_does_not_require_daily_checkpoint(self):
        event = observation(17, nav=500, used=1000, daily=False)
        result = replay_oanda_account_margin_closeout("CAD", positions(), [event])
        self.assertEqual(result["status"], "CLOSEOUT_TRIGGERED")

    def test_intraday_recovery_after_six_day_trigger_does_not_close_deferred_positions(self):
        events = [observation(i, nav=900, used=1000, sequence=i, trading_date=date) for i, date in enumerate(["2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-23", "2026-11-24"], 1)]
        events[5]["position_market_status"] = {
            "gold-xau": "closed", "fx-eurusd": "closed", "index-spx": "closed",
        }
        events.append({
            "timestamp_utc": "2026-11-25T14:00:00Z",
            "nav_mid": 1200, "margin_used": 1000,
            "position_market_status": {
                "gold-xau": "open", "fx-eurusd": "open", "index-spx": "open",
            },
            "trading_day_check": False,
        })
        result = replay_oanda_account_margin_closeout("CAD", positions(), events)
        self.assertEqual(len(result["closeout_batches"]), 1)
        self.assertEqual(result["closeout_batches"][0]["trigger"], "SIX_CONSECUTIVE_UNDERMARGINED_TRADING_DAYS")
        self.assertEqual(result["closeout_batches"][0]["position_ids_closed_as_batch"], [])
        self.assertEqual(len(result["remaining_open_positions"]), 3)

    def test_output_never_grants_authority_or_claims_execution(self):
        result = replay_oanda_account_margin_closeout(
            "CAD", positions(), [observation(17, nav=500, used=1000)]
        )
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertFalse(result["position_action_performed"])
        self.assertEqual(result["pending_orders"], "NOT_MODELLED; unrelated pending orders are not assumed cancelled")

    def test_invalid_currency_blocks(self):
        result = replay_oanda_account_margin_closeout("cad", positions(), [observation(17)])
        self.assertEqual(result["status"], "BLOCKED_INVALID_OR_INCOMPLETE_INPUT")


if __name__ == "__main__":
    unittest.main()

"""Synthetic tests for XAU/USD CFD session and execution-risk overlays."""
import unittest

from specialist_research.gold_cfd_execution_risk import (
    assess_gold_cfd_execution_stress, assess_xauusd_weekly_session,
)


class GoldCFDExecutionRiskTests(unittest.TestCase):
    def test_weekday_new_york_session_open(self):
        result = assess_xauusd_weekly_session("2026-11-17T15:00:00Z", "open")
        self.assertEqual(result["status"], "SCHEDULE_OPEN_STATUS_CONFIRMED_BY_CALLER")
        self.assertTrue(result["scheduled_open_by_weekly_hours"])

    def test_daily_close_window_is_scheduled_closed(self):
        result = assess_xauusd_weekly_session("2026-11-17T22:30:00Z", "open")
        self.assertFalse(result["scheduled_open_by_weekly_hours"])
        self.assertEqual(result["status"], "CLOSED_BY_PUBLISHED_WEEKLY_SCHEDULE")

    def test_sunday_before_open_is_closed(self):
        result = assess_xauusd_weekly_session("2026-11-22T22:00:00Z", "open")
        self.assertFalse(result["scheduled_open_by_weekly_hours"])

    def test_sunday_after_open_is_open(self):
        result = assess_xauusd_weekly_session("2026-11-22T23:10:00Z", "open")
        self.assertTrue(result["scheduled_open_by_weekly_hours"])

    def test_saturday_is_closed(self):
        result = assess_xauusd_weekly_session("2026-11-21T15:00:00Z", "open")
        self.assertFalse(result["scheduled_open_by_weekly_hours"])

    def test_unknown_holiday_status_warns(self):
        result = assess_xauusd_weekly_session("2026-11-17T15:00:00Z")
        self.assertIn("HOLIDAY_AND_EXCEPTIONAL_CLOSURE_STATUS_NOT_VERIFIED", result["warnings"])

    def test_caller_reported_holiday_closure_overrides_weekly_schedule(self):
        result = assess_xauusd_weekly_session("2026-11-17T15:00:00Z", "closed")
        self.assertFalse(result["scheduled_open_by_weekly_hours"])
        self.assertEqual(result["status"], "CLOSED_BY_CALLER_REPORTED_EXCEPTION")

    def test_invalid_session_timestamp_fails_closed(self):
        result = assess_xauusd_weekly_session("2026-11-17T15:00:00")
        self.assertEqual(result["status"], "INVALID_SESSION_INPUT")

    def test_spread_within_threshold(self):
        result = assess_gold_cfd_execution_stress(0.3, 0.2, 2.0, 3.0, 100, 10000, "USD")
        self.assertEqual(result["status"], "STRESS_INPUTS_WITHIN_CONFIGURED_SPREAD_THRESHOLDS")
        self.assertAlmostEqual(result["gap_stress_loss_estimate"], 100)

    def test_spread_warning_threshold(self):
        result = assess_gold_cfd_execution_stress(0.5, 0.2, 2.0, 3.0, 100, 10000, "USD")
        self.assertEqual(result["status"], "WARN_SPREAD_STRESS")

    def test_spread_halt_threshold(self):
        result = assess_gold_cfd_execution_stress(0.7, 0.2, 2.0, 3.0, 100, 10000, "USD")
        self.assertEqual(result["status"], "HALT_SPREAD_STRESS")

    def test_invalid_spread_or_gap_input_fails_closed(self):
        result = assess_gold_cfd_execution_stress(True, 0.2, 2.0, 3.0, 100, 10000, "USD")
        self.assertEqual(result["status"], "INVALID_STRESS_INPUT")

    def test_forced_closeout_and_stop_guarantee_not_invented(self):
        result = assess_gold_cfd_execution_stress(0.3, 0.2, 2.0, 3.0, 100, 10000, "USD")
        self.assertEqual(result["forced_closeout_model"], "NOT_MODELLED_BROKER_MAY_CLOSE_ALL_TRADABLE_POSITIONS")
        self.assertFalse(result["stop_loss_execution_guaranteed"])
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])


if __name__ == "__main__":
    unittest.main()

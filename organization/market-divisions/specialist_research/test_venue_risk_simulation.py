"""Synthetic regression tests for the venue risk simulator."""
import unittest

from specialist_research.venue_risk_simulation import (
    AUTHORITY, simulate_derivative_path, validate_venue_spec,
)


def spec(partial=False):
    return {
        "schema_version": "1.0.0", "venue_id": "synthetic-venue",
        "instrument_type": "crypto_perpetual", "quote_currency": "USD",
        "mark_price_rule": "mark", "contract_multiplier": 1.0,
        "initial_margin_rate": 0.2, "liquidation_fee_rate": 0.01,
        "max_impact_bps": 100.0, "impact_coefficient": 10.0,
        "liquidation_buffer_ratio": 1.2,
        "partial_liquidation_supported": partial,
        "maintenance_tiers": [
            {"notional_cap": 1000.0, "maintenance_rate": 0.1},
            {"notional_cap": None, "maintenance_rate": 0.2},
        ],
    }


def position(**overrides):
    value = {
        "position_id": "p-1", "instrument_id": "BTC-PERP",
        "side": "long", "quantity": 1.0, "entry_price": 100.0,
        "initial_margin": 20.0, "available_margin": 0.0,
    }
    value.update(overrides)
    return value


def step(timestamp, price, **overrides):
    value = {
        "timestamp_utc": timestamp, "mark_price": price,
        "executable_depth_notional": 10000.0,
        "funding_rate": 0.001, "funding_interval_hours": 8.0,
        "gap_flag": False,
    }
    value.update(overrides)
    return value


class VenueRiskSimulationTests(unittest.TestCase):
    def test_valid_spec(self):
        self.assertEqual(validate_venue_spec(spec()), [])

    def test_missing_venue_rule_blocks_without_guessing(self):
        bad = spec()
        del bad["mark_price_rule"]
        result = simulate_derivative_path(bad, position(), [step("2026-01-01T01:00:00Z", 100)])
        self.assertEqual(result["status"], "BLOCKED_INVALID_MODEL_INPUTS")
        self.assertFalse(result["trade_authority"])

    def test_no_liquidation_on_flat_path(self):
        result = simulate_derivative_path(
            spec(), position(),
            [step("2026-01-01T01:00:00Z", 100),
             step("2026-01-01T02:00:00Z", 101)],
        )
        self.assertEqual(result["status"], "SIMULATED_NO_LIQUIDATION")
        self.assertFalse(result["liquidation_occurred"])
        self.assertAlmostEqual(result["steps"][1]["price_pnl"], 1.0)

    def test_long_price_loss_triggers_full_liquidation(self):
        result = simulate_derivative_path(
            spec(), position(initial_margin=20),
            [step("2026-01-01T01:00:00Z", 100),
             step("2026-01-01T02:00:00Z", 80)],
        )
        self.assertEqual(result["status"], "LIQUIDATION_MODEL_TRIGGERED")
        self.assertEqual(result["steps"][-1]["liquidation_event"], "FULL_LIQUIDATION")
        self.assertEqual(result["final_position_quantity"], 0.0)

    def test_supported_partial_liquidation_reduces_quantity(self):
        result = simulate_derivative_path(
            spec(partial=True), position(initial_margin=20),
            [step("2026-01-01T01:00:00Z", 100),
             step("2026-01-01T02:00:00Z", 90)],
        )
        self.assertEqual(result["status"], "LIQUIDATION_MODEL_TRIGGERED")
        self.assertEqual(result["steps"][-1]["liquidation_event"], "PARTIAL_LIQUIDATION")
        self.assertGreater(result["final_position_quantity"], 0.0)
        self.assertLess(result["final_position_quantity"], 1.0)

    def test_short_profit_and_funding_direction(self):
        result = simulate_derivative_path(
            spec(), position(side="short", initial_margin=50),
            [step("2026-01-01T01:00:00Z", 100),
             step("2026-01-01T09:00:00Z", 90)],
        )
        self.assertGreater(result["steps"][1]["price_pnl"], 0)
        self.assertLess(result["cumulative_funding_cost"], 0)

    def test_non_monotonic_timestamps_block(self):
        result = simulate_derivative_path(
            spec(), position(),
            [step("2026-01-01T02:00:00Z", 100),
             step("2026-01-01T01:00:00Z", 101)],
        )
        self.assertEqual(result["status"], "BLOCKED_INVALID_PATH")

    def test_gap_is_reported_not_interpolated(self):
        result = simulate_derivative_path(
            spec(), position(initial_margin=50),
            [step("2026-01-01T01:00:00Z", 100),
             step("2026-01-01T02:00:00Z", 95, gap_flag=True)],
        )
        self.assertTrue(result["steps"][-1]["gap_flag"])
        self.assertIn("intrabar path", " ".join(result["model_limitations"]))

    def test_authority_is_always_research_only(self):
        result = simulate_derivative_path(
            spec(), position(), [step("2026-01-01T01:00:00Z", 100)]
        )
        self.assertEqual(result["authority"], AUTHORITY)
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertTrue(result["simulation_only"])


if __name__ == "__main__":
    unittest.main()

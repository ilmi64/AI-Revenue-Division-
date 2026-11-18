"""Synthetic integration tests for the unified simulation orchestrator."""
import unittest

from specialist_research.simulation_orchestrator import simulate_unified_derivative


def venue():
    return {
        "schema_version": "1.0.0", "venue_id": "synthetic",
        "instrument_type": "crypto_perpetual", "quote_currency": "USD",
        "mark_price_rule": "mark", "contract_multiplier": 1.0,
        "initial_margin_rate": 0.2, "liquidation_fee_rate": 0.01,
        "max_impact_bps": 100.0, "impact_coefficient": 10.0,
        "liquidation_buffer_ratio": 1.2,
        "partial_liquidation_supported": False,
        "maintenance_tiers": [{"notional_cap": None, "maintenance_rate": 0.1}],
    }


def profile():
    return {
        "schema_version": "1.0.0", "profile_id": "synthetic-perp",
        "venue_id": "synthetic", "instrument_id": "BTC-PERP",
        "instrument_type": "crypto_perpetual", "quote_currency": "USD",
        "settlement_currency": "USD", "settlement_method": "not_applicable",
        "roll_method": "not_applicable", "financing_convention": "funding_rate",
    }


def position(**overrides):
    value = {
        "position_id": "p-1", "instrument_id": "BTC-PERP",
        "side": "long", "quantity": 1.0, "entry_price": 100.0,
        "initial_margin": 20.0, "available_margin": 0.0,
        "contract_id": "BTC-PERP",
    }
    value.update(overrides)
    return value


def path(**overrides):
    value = {
        "timestamp_utc": "2026-11-01T01:00:00Z",
        "mark_price": 101.0, "mark_price_basis": "mark",
        "executable_depth_notional": 10000.0,
        "funding_rate": 0.0, "funding_interval_hours": 8.0,
        "gap_flag": False,
    }
    value.update(overrides)
    return [value]


class SimulationOrchestratorTests(unittest.TestCase):
    def test_price_and_carry_ledgers_reconcile_without_double_count(self):
        result = simulate_unified_derivative(
            venue(), profile(), position(), path(), [{
                "event_id": "fund-1", "event_type": "funding",
                "timestamp_utc": "2026-11-01T02:00:00Z",
                "cashflow": -1.25, "currency": "USD",
            }]
        )
        self.assertEqual(result["status"], "SIMULATED_OK")
        self.assertEqual(result["reconciliation"]["status"], "PASS_RECONCILIATION")
        self.assertEqual(result["reconciliation"]["carry_source"], "contract_lifecycle_only")
        self.assertEqual(result["lifecycle_replay"]["cashflow_total"], -1.25)
        self.assertEqual(result["venue_simulation"]["cumulative_funding_cost"], 0.0)
        self.assertIsNone(result["reconciliation"]["combined_equity_estimate"])
        self.assertFalse(result["reconciliation"]["currency_merge_performed"])
        self.assertFalse(result["trade_authority"])

    def test_nonzero_path_funding_is_rejected_as_duplicate_carry_risk(self):
        result = simulate_unified_derivative(
            venue(), profile(), position(), path(funding_rate=0.001), []
        )
        self.assertEqual(result["status"], "BLOCKED_INPUT_RECONCILIATION")
        self.assertIn("funding_rate must be exactly zero", " ".join(result["errors"]))

    def test_instrument_type_mismatch_blocks(self):
        other = profile()
        other["instrument_type"] = "gold_future"
        result = simulate_unified_derivative(venue(), other, position(), path(), [])
        self.assertEqual(result["status"], "BLOCKED_INPUT_RECONCILIATION")

    def test_component_failure_blocks_reconciliation(self):
        bad = path()
        bad[0]["mark_price_basis"] = "last"
        result = simulate_unified_derivative(venue(), profile(), position(), bad, [])
        self.assertEqual(result["status"], "BLOCKED_COMPONENT_FAILURE")
        self.assertEqual(result["reconciliation"]["status"], "FAILED")

    def test_cashflow_currency_mismatch_blocks_component(self):
        result = simulate_unified_derivative(
            venue(), profile(), position(), path(), [{
                "event_type": "funding", "timestamp_utc": "2026-11-01T02:00:00Z",
                "cashflow": -1.0, "currency": "EUR",
            }]
        )
        self.assertEqual(result["status"], "BLOCKED_COMPONENT_FAILURE")

    def test_settlement_after_path_is_reconciled(self):
        dated = profile()
        dated.update({
            "instrument_type": "gold_future", "instrument_id": "GCZ6",
            "settlement_method": "cash", "roll_method": "manual_close_open",
            "financing_convention": "none", "contract_code": "GCZ6",
            "expiry_utc": "2026-12-28T18:30:00Z",
        })
        v = venue()
        v["instrument_type"] = "gold_future"
        p = position(instrument_id="GCZ6", contract_id="GCZ6")
        result = simulate_unified_derivative(
            v, dated, p, path(), [{
                "event_type": "expiry_settlement",
                "timestamp_utc": "2026-12-28T18:31:00Z",
                "contract_id": "GCZ6", "settlement_price": 4250.0,
                "settlement_method": "cash", "realized_cashflow": 10.0,
                "currency": "USD",
            }]
        )
        self.assertEqual(result["status"], "SIMULATED_SETTLEMENT")
        self.assertTrue(result["reconciliation"]["checks"][-2]["passed"])

    def test_path_after_settlement_blocks(self):
        dated = profile()
        dated.update({
            "instrument_type": "gold_future", "instrument_id": "GCZ6",
            "settlement_method": "cash", "roll_method": "manual_close_open",
            "financing_convention": "none", "contract_code": "GCZ6",
            "expiry_utc": "2026-12-28T18:30:00Z",
        })
        v = venue()
        v["instrument_type"] = "gold_future"
        p = position(instrument_id="GCZ6", contract_id="GCZ6")
        after = path(timestamp_utc="2026-12-28T18:32:00Z")
        result = simulate_unified_derivative(
            v, dated, p, after, [{
                "event_type": "expiry_settlement",
                "timestamp_utc": "2026-12-28T18:31:00Z",
                "contract_id": "GCZ6", "settlement_price": 4250.0,
                "settlement_method": "cash", "realized_cashflow": 10.0,
                "currency": "USD",
            }]
        )
        self.assertEqual(result["status"], "BLOCKED_RECONCILIATION")

    def test_authority_never_promoted(self):
        result = simulate_unified_derivative(venue(), profile(), position(), path(), [])
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertTrue(result["simulation_only"])


if __name__ == "__main__":
    unittest.main()

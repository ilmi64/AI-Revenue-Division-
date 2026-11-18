import unittest

from portfolio_risk import assess_portfolio_risk


NOW = "2026-11-17T12:00:00Z"
DESKS = ("crypto", "forex", "indices", "gold")


def packets(status_overrides=None):
    result = []
    for desk in DESKS:
        instrument = {"crypto": "BTC-USD", "forex": "EUR-USD", "indices": "SPX", "gold": "XAUUSD"}[desk]
        result.append({
            "desk_id": desk, "instrument_id": instrument,
            "status": (status_overrides or {}).get(desk, "research"),
            "risk_flags": [],
            "context": {"portfolio_risk": {"positions": [{
                "position_id": "position-" + desk,
                "instrument_id": instrument,
                "asset_class": desk,
                "side": "long" if desk != "forex" else "short",
                "notional": 100.0,
                "instrument_type": {"crypto": "crypto_spot", "forex": "forex_spot", "indices": "index_future", "gold": "gold_future"}[desk],
                "valuation_basis": {"crypto": "spot_mark_to_market", "forex": "base_currency_units", "indices": "futures_contract_notional", "gold": "futures_contract_notional"}[desk],
                "units": 1.0,
                "contract_multiplier": 1.0 if desk in {"indices", "gold"} else None,
                "leverage": None,
                "margin_amount": 10.0 if desk in {"indices", "gold"} else None,
                "delta": 1.0,
                "currency": "USD",
                "valuation_currency": "USD",
                "valuation_amount": 100.0,
                "exposure_group": "macro-risk" if desk in {"forex", "indices", "gold"} else "crypto-beta",
                "evidence_refs": ["fixture:" + desk],
                "source_timestamp_utc": NOW,
            }]}}
        })
    return result


def config(maximum=1000.0):
    return {"schema_version": "1.0.0", "limits": [{
        "scope": "portfolio", "metric": "gross_exposure",
        "valuation_currency": "USD", "max_value": maximum,
    }], "stress_scenarios": [{
        "scenario_id": "risk_off",
        "shocks_by_asset_class": {"crypto": -0.2, "forex": 0.05, "indices": -0.1, "gold": 0.08},
    }]}


def correlations():
    return [{
        "instrument_id_a": "EUR-USD", "instrument_id_b": "XAUUSD",
        "correlation": -0.35, "observed_at_utc": NOW,
        "source_id": "fixture-correlation", "sample_count": 30,
        "lookback_window": "30d", "methodology": "pearson_returns",
        "evidence_refs": ["fixture:corr"],
    }]


class PortfolioRiskTests(unittest.TestCase):
    def test_comparable_exposures_limits_and_signed_correlation_are_reported(self):
        result = assess_portfolio_risk(packets(), NOW, config(), correlations())
        self.assertEqual(result["status"], "ASSESSED_WITHIN_CONFIGURED_LIMITS")
        self.assertEqual(result["instrument_normalization"]["status"], "INPUTS_VALIDATED_NOT_REPRICED")
        self.assertEqual(result["stress_testing"]["status"], "ASSESSED")
        self.assertEqual(result["position_count"], 4)
        self.assertEqual(result["exposure_by_valuation_currency"]["USD"]["gross"], 400.0)
        self.assertEqual(result["exposure_by_valuation_currency"]["USD"]["net"], 200.0)
        self.assertEqual(result["correlation_risk"]["pairs"][0]["correlation"], -0.35)
        self.assertIsNotNone(result["correlation_risk"]["pairs"][0]["pairwise_correlation_adjusted_exposure_proxy"])
        self.assertFalse(result["correlation_risk"]["independence_assumed"])
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])

    def test_missing_position_context_is_unknown_not_zero(self):
        rows = packets()
        rows[0]["context"] = {}
        result = assess_portfolio_risk(rows, NOW, config(), correlations())
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["coverage"]["missing_risk_desks"], ["crypto"])
        self.assertEqual(result["position_count"], 3)

    def test_missing_correlation_is_unknown_not_independence(self):
        result = assess_portfolio_risk(packets(), NOW, config(), [])
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["correlation_risk"]["status"], "UNKNOWN")
        self.assertFalse(result["correlation_risk"]["independence_assumed"])

    def test_limit_breach_escalates_to_halt(self):
        result = assess_portfolio_risk(packets(), NOW, config(399.0), correlations())
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["risk_limits"]["results"][0]["status"], "BREACH")

    def test_simultaneous_specialist_halts_escalate_portfolio(self):
        result = assess_portfolio_risk(packets({"crypto": "halt", "gold": "halt"}), NOW, config(), correlations())
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["simultaneous_stop_count"], 2)

    def test_invalid_negative_exposure_fails_closed(self):
        rows = packets()
        rows[0]["context"]["portfolio_risk"]["positions"][0]["valuation_amount"] = -1
        result = assess_portfolio_risk(rows, NOW, config(), correlations())
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("valuation_amount" in error for error in result["errors"]))

    def test_duplicate_position_id_fails_closed(self):
        rows = packets()
        rows[1]["context"]["portfolio_risk"]["positions"][0]["position_id"] = "position-crypto"
        result = assess_portfolio_risk(rows, NOW, config(), correlations())
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("duplicate" in error for error in result["errors"]))

    def test_invalid_boolean_limit_rejected(self):
        result = assess_portfolio_risk(packets(), NOW, config(True), correlations())
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("max_value" in error for error in result["errors"]))


    def test_desk_scoped_limit_uses_only_that_desk_and_currency(self):
        scoped = {"schema_version": "1.0.0", "limits": [{
            "scope": "desk:forex", "metric": "gross_exposure",
            "valuation_currency": "USD", "max_value": 99.0,
        }]}
        result = assess_portfolio_risk(packets(), NOW, scoped, correlations())
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["risk_limits"]["results"][0]["actual"], 100.0)

    def test_group_scoped_limit_uses_currency_partitioned_group_exposure(self):
        scoped = {"schema_version": "1.0.0", "limits": [{
            "scope": "group:macro-risk", "metric": "gross_exposure",
            "valuation_currency": "USD", "max_value": 299.0,
        }]}
        result = assess_portfolio_risk(packets(), NOW, scoped, correlations())
        self.assertEqual(result["status"], "HALT")
        self.assertEqual(result["risk_limits"]["results"][0]["actual"], 300.0)

    def test_stress_scenario_reports_currency_partitioned_pnl_and_loss(self):
        result = assess_portfolio_risk(packets(), NOW, config(), correlations())
        stress = result["stress_testing"]["scenarios"][0]
        self.assertEqual(stress["status"], "ASSESSED")
        self.assertAlmostEqual(stress["by_valuation_currency"]["USD"]["pnl"], -27.0)
        self.assertAlmostEqual(stress["by_valuation_currency"]["USD"]["loss"], 35.0)

    def test_missing_stress_shock_leaves_scenario_incomplete_and_portfolio_unknown(self):
        cfg = config()
        cfg["stress_scenarios"][0]["shocks_by_asset_class"].pop("gold")
        result = assess_portfolio_risk(packets(), NOW, cfg, correlations())
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["stress_testing"]["scenarios"][0]["status"], "INCOMPLETE")
        self.assertIn("position-gold", result["stress_testing"]["scenarios"][0]["uncovered_position_ids"])

    def test_instrument_specific_basis_is_enforced(self):
        rows = packets()
        rows[2]["context"]["portfolio_risk"]["positions"][0]["valuation_basis"] = "spot_mark_to_market"
        result = assess_portfolio_risk(rows, NOW, config(), correlations())
        self.assertEqual(result["status"], "HALT")
        self.assertTrue(any("valuation_basis" in error for error in result["errors"]))

    def test_currency_buckets_are_not_combined(self):
        rows = packets()
        rows[1]["context"]["portfolio_risk"]["positions"][0]["valuation_currency"] = "EUR"
        result = assess_portfolio_risk(rows, NOW, config(), correlations())
        self.assertEqual(result["exposure_by_valuation_currency"]["USD"]["gross"], 300.0)
        self.assertEqual(result["exposure_by_valuation_currency"]["EUR"]["gross"], 100.0)


if __name__ == "__main__":
    unittest.main()

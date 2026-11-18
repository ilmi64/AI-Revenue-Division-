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
    }]}


def correlations():
    return [{
        "instrument_id_a": "EUR-USD", "instrument_id_b": "XAUUSD",
        "correlation": -0.35, "observed_at_utc": NOW,
        "source_id": "fixture-correlation", "evidence_refs": ["fixture:corr"],
    }]


class PortfolioRiskTests(unittest.TestCase):
    def test_comparable_exposures_limits_and_signed_correlation_are_reported(self):
        result = assess_portfolio_risk(packets(), NOW, config(), correlations())
        self.assertEqual(result["status"], "ASSESSED_WITHIN_CONFIGURED_LIMITS")
        self.assertEqual(result["position_count"], 4)
        self.assertEqual(result["exposure_by_valuation_currency"]["USD"]["gross"], 400.0)
        self.assertEqual(result["exposure_by_valuation_currency"]["USD"]["net"], 200.0)
        self.assertEqual(result["correlation_risk"]["pairs"][0]["correlation"], -0.35)
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

    def test_currency_buckets_are_not_combined(self):
        rows = packets()
        rows[1]["context"]["portfolio_risk"]["positions"][0]["valuation_currency"] = "EUR"
        result = assess_portfolio_risk(rows, NOW, config(), correlations())
        self.assertEqual(result["exposure_by_valuation_currency"]["USD"]["gross"], 300.0)
        self.assertEqual(result["exposure_by_valuation_currency"]["EUR"]["gross"], 100.0)


if __name__ == "__main__":
    unittest.main()

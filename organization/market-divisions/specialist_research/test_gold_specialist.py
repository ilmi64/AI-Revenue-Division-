import unittest

from specialist_research.gold_specialist import build_gold_research_context


NOW = "2026-11-17T12:00:00Z"


def observation(**overrides):
    value = {
        "instrument_id": "XAUUSD-SYNTHETIC", "instrument_type": "xauusd_spot",
        "gold_price_basis": "broker_executable_xauusd", "currency": "USD",
        "bid": 1999.9, "ask": 2000.1, "spread": 0.2,
        "quote_age_seconds": 1, "stale_threshold_seconds": 10, "is_stale": False,
        "gold_session": {"session_name": "london", "market_timezone": "Europe/London",
                         "calendar_status": "verified"},
        "financing_status": "reviewed", "settlement_type": "cash",
        "shariah_review_status": "instrument_specific_reviewed",
        "macro_evidence": [
            {"factor": "real_yields", "evidence_type": "real_yield", "evidence_ref": "ref:real",
             "source_id": "src-real", "observed_at_utc": NOW, "value": 1.8, "unit": "percent",
             "source_status": "verified", "source_group": "group-real"},
            {"factor": "usd", "evidence_type": "dxy", "evidence_ref": "ref:usd",
             "source_id": "src-usd", "observed_at_utc": NOW, "value": 103.2, "unit": "index",
             "source_status": "verified", "source_group": "group-usd"},
            {"factor": "central_bank_demand", "evidence_type": "central_bank_gold_demand",
             "evidence_ref": "ref:cb", "source_id": "src-cb", "observed_at_utc": NOW,
             "value": 200, "unit": "tonnes", "source_status": "approved", "source_group": "group-cb"},
            {"factor": "etf_flows", "evidence_type": "gold_etf_flow", "evidence_ref": "ref:etf",
             "source_id": "src-etf", "observed_at_utc": NOW, "value": 2, "unit": "tonnes",
             "source_status": "verified", "source_group": "group-etf"},
            {"factor": "positioning", "evidence_type": "cot_positioning", "evidence_ref": "ref:cot",
             "source_id": "src-cot", "observed_at_utc": NOW, "value": 1000, "unit": "contracts",
             "source_status": "verified", "source_group": "group-cot"},
            {"factor": "physical_demand", "evidence_type": "physical_gold_demand", "evidence_ref": "ref:physical",
             "source_id": "src-physical", "observed_at_utc": NOW, "value": 80, "unit": "tonnes",
             "source_status": "verified", "source_group": "group-physical"},
            {"factor": "geopolitical_risk", "evidence_type": "geopolitical_risk_context",
             "evidence_ref": "ref:geo", "source_id": "src-geo", "observed_at_utc": NOW,
             "value": "descriptive", "unit": "text", "source_status": "verified", "source_group": "group-geo"},
            {"factor": "rates_policy", "evidence_type": "central_bank_policy",
             "evidence_ref": "ref:policy", "source_id": "src-policy", "observed_at_utc": NOW,
             "value": "unchanged", "unit": "text", "source_status": "verified", "source_group": "group-policy"},
        ],
    }
    value.update(overrides)
    return value


class GoldSpecialistTests(unittest.TestCase):
    def test_complete_gold_context_passes_as_research_only(self):
        result = build_gold_research_context(observation(), NOW)
        self.assertEqual(result["status"], "research")
        self.assertEqual(result["macro_factor_count"], 8)
        self.assertAlmostEqual(result["microstructure"]["spread"], 0.2)
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])

    def test_macro_factor_coverage_is_separate_not_directional(self):
        result = build_gold_research_context(observation(), NOW)
        self.assertTrue(all(result["macro_factor_coverage"].values()))
        self.assertIsNone(result["directional_signal"])
        self.assertFalse(result["source_independence_verified"])

    def test_missing_macro_factor_warns(self):
        o = observation(macro_evidence=[])
        result = build_gold_research_context(o, NOW)
        self.assertEqual(result["status"], "unverified")
        self.assertTrue(any("factor missing" in x for x in result["warnings"]))

    def test_future_and_stale_macro_evidence_warns(self):
        o = observation()
        o["macro_evidence"][0]["observed_at_utc"] = "2026-11-18T00:00:00Z"
        result = build_gold_research_context(o, NOW)
        self.assertTrue(any("future-dated" in x for x in result["warnings"]))

    def test_bad_quote_basis_halts(self):
        result = build_gold_research_context(observation(gold_price_basis="comex_futures"), NOW)
        self.assertEqual(result["status"], "halt")

    def test_spread_must_reconcile_to_bid_ask(self):
        result = build_gold_research_context(observation(spread=2.0), NOW)
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any("spread" in x for x in result["errors"]))

    def test_future_expired_contract_basis_is_not_silently_accepted(self):
        o = observation(instrument_type="gold_future", gold_price_basis="comex_futures",
                        contract_code="GCZ26", expiry_utc="2026-12-28T00:00:00Z",
                        roll_status="unknown")
        result = build_gold_research_context(o, NOW)
        self.assertEqual(result["status"], "unverified")
        self.assertTrue(any("roll" in x for x in result["warnings"]))

    def test_cfd_requires_broker_symbol_and_contract_unit(self):
        o = observation(instrument_type="gold_cfd", gold_price_basis="gold_cfd")
        result = build_gold_research_context(o, NOW)
        self.assertEqual(result["status"], "halt")
        self.assertTrue(any("CFD" in x for x in result["errors"]))

    def test_non_usd_quote_currency_halts(self):
        result = build_gold_research_context(observation(currency="CAD"), NOW)
        self.assertEqual(result["status"], "halt")

    def test_unreviewed_financing_and_shariah_are_warnings(self):
        o = observation(financing_status="unknown", shariah_review_status="unassessed")
        result = build_gold_research_context(o, NOW)
        self.assertEqual(result["status"], "unverified")
        self.assertTrue(any("financing" in x for x in result["warnings"]))
        self.assertTrue(any("Shariah" in x for x in result["warnings"]))

    def test_duplicate_macro_evidence_reference_halts(self):
        o = observation()
        o["macro_evidence"][1]["evidence_ref"] = o["macro_evidence"][0]["evidence_ref"]
        result = build_gold_research_context(o, NOW)
        self.assertEqual(result["status"], "halt")

    def test_missing_structured_session_halts(self):
        result = build_gold_research_context(observation(gold_session="london"), NOW)
        self.assertEqual(result["status"], "halt")


if __name__ == "__main__":
    unittest.main()

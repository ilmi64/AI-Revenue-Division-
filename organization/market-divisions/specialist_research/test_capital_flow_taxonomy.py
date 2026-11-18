import unittest

from specialist_research.capital_flow_taxonomy import classify_event


class CapitalFlowTaxonomyTests(unittest.TestCase):
    def test_classifies_whale_transfer(self):
        result = classify_event({"event_type": "large_wallet_transfer", "materiality": 4,
                                 "source_ids": ["a", "b"], "corroboration_count": 2})
        self.assertEqual(result["category"], "whale_movement")
        self.assertEqual(result["materiality_tier"], "high")
        self.assertFalse(result["source_independence_verified"])
        self.assertEqual(result["corroboration_assessment"],
                         "multiple_sources_claimed_independence_not_verified")

    def test_classifies_exchange_inflow_and_outflow_separately(self):
        self.assertEqual(classify_event({"event_type": "exchange_inflow"})["subtype"], "exchange_inflow")
        self.assertEqual(classify_event({"event_type": "exchange_outflow"})["subtype"], "exchange_outflow")

    def test_classifies_treasury_deployment(self):
        self.assertEqual(classify_event({"event_type": "treasury_deployment"})["category"],
                         "treasury_activity")

    def test_classifies_unlock_and_vesting(self):
        self.assertEqual(classify_event({"event_type": "vesting_unlock"})["subtype"], "vesting_unlock")

    def test_classifies_fundraising_and_vc(self):
        self.assertEqual(classify_event({"event_type": "fundraising_round"})["category"], "fundraising")
        self.assertEqual(classify_event({"event_type": "vc_investment"})["category"], "institutional_capital")

    def test_classifies_launchpad_and_ecosystem_capital(self):
        self.assertEqual(classify_event({"event_type": "launchpad_sale"})["category"], "launch_activity")
        self.assertEqual(classify_event({"event_type": "developer_funding"})["category"], "ecosystem_capital")

    def test_unknown_event_type_is_not_guessed(self):
        result = classify_event({"event_type": "mystery_activity", "materiality": 3})
        self.assertEqual(result["classification_status"], "unclassified")
        self.assertEqual(result["category"], "unclassified")

    def test_materiality_tiers_are_bounded(self):
        expected = {0: "low", 1: "low", 2: "moderate", 3: "high", 4: "high", 5: "critical"}
        for score, tier in expected.items():
            with self.subTest(score=score):
                self.assertEqual(classify_event({"event_type": "protocol_revenue",
                                                 "materiality": score})["materiality_tier"], tier)

    def test_invalid_materiality_is_unknown_not_promoted(self):
        for score in (True, "5", -1, 6, None):
            with self.subTest(score=score):
                self.assertEqual(classify_event({"event_type": "protocol_revenue",
                                                 "materiality": score})["materiality_tier"], "unknown")

    def test_no_classification_grants_trade_authority(self):
        result = classify_event({"event_type": "large_wallet_transfer", "materiality": 5})
        self.assertTrue(result["research_only"])
        self.assertFalse(result["trade_authority"])


if __name__ == "__main__":
    unittest.main()

import unittest

from specialist_research.capital_flow_priority import assess_research_priority


class CapitalFlowPriorityTests(unittest.TestCase):
    def event(self, **overrides):
        value = {"materiality": 5, "source_reliability": 4, "attribution_confidence": 4,
                 "event_confidence": 5, "quality_flags": []}
        value.update(overrides)
        return value

    def provenance(self, **overrides):
        value = {"status": "metadata_complete_unverified"}
        value.update(overrides)
        return value

    def test_high_priority_requires_complete_metadata_and_all_thresholds(self):
        result = assess_research_priority(self.event(), self.provenance())
        self.assertEqual(result["priority"], "high_review_priority")
        self.assertTrue(result["review_queue_only"])
        self.assertTrue(result["not_a_directional_signal"])
        self.assertFalse(result["trade_authority"])

    def test_incomplete_provenance_prevents_high_priority(self):
        result = assess_research_priority(self.event(), self.provenance(status="incomplete"))
        self.assertEqual(result["priority"], "insufficient_provenance")

    def test_exchange_reshuffle_and_self_transfer_flags_block_priority(self):
        for flag in ("exchange_hot_wallet_reshuffle", "self_transfer", "internal_treasury_move"):
            with self.subTest(flag=flag):
                result = assess_research_priority(self.event(quality_flags=[flag]), self.provenance())
                self.assertEqual(result["priority"], "blocked_from_priority_queue")

    def test_low_confidence_is_not_promoted(self):
        result = assess_research_priority(self.event(event_confidence=1), self.provenance())
        self.assertEqual(result["priority"], "low_review_priority")

    def test_invalid_confidence_is_insufficient_evidence(self):
        result = assess_research_priority(self.event(materiality=True), self.provenance())
        self.assertEqual(result["priority"], "insufficient_evidence")

    def test_priority_never_grants_market_or_execution_authority(self):
        result = assess_research_priority(self.event(), self.provenance())
        self.assertTrue(result["not_a_market_observation"])
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])


if __name__ == "__main__":
    unittest.main()

import unittest

from specialist_research.capital_flow_provenance import assess_event_provenance


NOW = "2026-11-17T12:00:00Z"


class CapitalFlowProvenanceTests(unittest.TestCase):
    def base(self):
        return {
            "source_ids": ["source-a", "source-b"],
            "evidence_refs": ["ref:a", "ref:b"],
            "evidence_items": [
                {"evidence_ref": "ref:a", "source_id": "source-a", "publisher": "Publisher A",
                 "canonical_source_id": "publisher-a", "source_family": "onchain-indexer",
                 "published_at_utc": "2026-11-17T10:00:00Z", "independence_group": "group-a"},
                {"evidence_ref": "ref:b", "source_id": "source-b", "publisher": "Publisher B",
                 "canonical_source_id": "publisher-b", "source_family": "newswire",
                 "published_at_utc": "2026-11-17T10:05:00Z", "independence_group": "group-b"},
            ],
        }

    def test_complete_metadata_does_not_claim_authentication(self):
        result = assess_event_provenance(self.base(), NOW)
        self.assertEqual(result["status"], "metadata_complete_unverified")
        self.assertEqual(result["distinct_declared_publishers"], 2)
        self.assertEqual(result["declared_independence_groups"], 2)
        self.assertFalse(result["independent_corroboration_established"])
        self.assertEqual(result["authentication_status"], "not_authenticated")

    def test_missing_evidence_metadata_is_incomplete(self):
        event = self.base()
        event["evidence_items"] = event["evidence_items"][:1]
        result = assess_event_provenance(event, NOW)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["evidence_refs_without_metadata"], ["ref:b"])

    def test_future_evidence_timestamp_is_flagged(self):
        event = self.base()
        event["evidence_items"][0]["published_at_utc"] = "2026-11-18T00:00:00Z"
        result = assess_event_provenance(event, NOW)
        self.assertTrue(any("future" in error for error in result["metadata_errors"]))
        self.assertEqual(result["status"], "incomplete")

    def test_unparseable_timestamp_is_flagged(self):
        event = self.base()
        event["evidence_items"][0]["published_at_utc"] = "yesterday"
        result = assess_event_provenance(event, NOW)
        self.assertTrue(any("timestamp" in error for error in result["metadata_errors"]))

    def test_unmapped_source_and_duplicate_reference_are_flagged(self):
        event = self.base()
        event["evidence_items"][0]["source_id"] = "unknown-source"
        event["evidence_items"][1]["evidence_ref"] = "ref:a"
        result = assess_event_provenance(event, NOW)
        self.assertTrue(any("source_id" in error for error in result["metadata_errors"]))
        self.assertTrue(any("duplicate" in error for error in result["metadata_errors"]))

    def test_missing_publisher_identity_is_flagged(self):
        event = self.base()
        event["evidence_items"][0]["publisher"] = ""
        result = assess_event_provenance(event, NOW)
        self.assertTrue(any("publisher" in error for error in result["metadata_errors"]))


if __name__ == "__main__":
    unittest.main()

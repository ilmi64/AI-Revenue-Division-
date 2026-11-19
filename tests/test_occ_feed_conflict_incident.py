"""Tests for the OCC market-data conflict incident projection."""
import unittest

from occ.feed_conflict_incident import (
    FeedConflictProjectionError,
    project_feed_conflict_incident,
)


def conflict_report():
    return {
        "status": "CONFLICT_DETECTED",
        "expected_instrument_identity": {"symbol": "XAUUSD", "market_class": "METALS"},
        "accepted_observations": [
            {"source_id": "feed-b"}, {"source_id": "feed-a"},
        ],
        "diagnostic_spread_bps": 41.0,
        "max_spread_bps": 25.0,
        "independence_verified": False,
        "provider_identity_authenticated": False,
        "registry_authority_authenticated": False,
        "market_data_trusted": False,
        "consensus_authorized": False,
        "paper_use_authorized": False,
        "execution_eligible": False,
    }


class FeedConflictIncidentTests(unittest.TestCase):
    def test_conflict_projects_to_open_critical_occ_incident(self):
        incident = project_feed_conflict_incident(conflict_report(), now_epoch=1000)
        self.assertEqual(incident["severity"], "CRITICAL")
        self.assertEqual(incident["status"], "OPEN")
        self.assertEqual(incident["division"], "OCC")
        self.assertEqual(incident["reason_code"], "MARKET_DATA_SOURCE_CONFLICT")
        self.assertEqual(incident["source_ids"], ["feed-a", "feed-b"])
        self.assertFalse(incident["source_mutation_performed"])
        self.assertFalse(incident["notification_sent"])
        self.assertFalse(incident["execution_eligible"])

    def test_non_conflict_produces_no_incident(self):
        report = conflict_report()
        report["status"] = "AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED"
        self.assertIsNone(project_feed_conflict_incident(report, now_epoch=1000))

    def test_missing_trust_boundary_flag_rejected(self):
        report = conflict_report()
        del report["consensus_authorized"]
        with self.assertRaises(FeedConflictProjectionError):
            project_feed_conflict_incident(report, now_epoch=1000)

    def test_spread_must_exceed_threshold(self):
        report = conflict_report()
        report["diagnostic_spread_bps"] = 25.0
        with self.assertRaises(FeedConflictProjectionError):
            project_feed_conflict_incident(report, now_epoch=1000)

    def test_duplicate_source_ids_rejected(self):
        report = conflict_report()
        report["accepted_observations"] = [{"source_id": "same"}, {"source_id": "same"}]
        with self.assertRaises(FeedConflictProjectionError):
            project_feed_conflict_incident(report, now_epoch=1000)

    def test_invalid_time_rejected(self):
        with self.assertRaises(FeedConflictProjectionError):
            project_feed_conflict_incident(conflict_report(), now_epoch=float("nan"))


if __name__ == "__main__":
    unittest.main()

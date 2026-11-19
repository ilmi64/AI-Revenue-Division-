import unittest

from occ.incident_intake import (
    IncidentIntakeError, build_incident_report, validate_incident,
)


class IncidentIntakeTests(unittest.TestCase):
    def setUp(self):
        self.open = {
            "source_system": "solana-paper-exit",
            "source_incident_id": "market-data:md-1",
            "division": "Crypto",
            "severity": "critical",
            "status": "open",
            "reason_code": "EXIT_MARK_STALE",
            "summary": "Independent exit marks are stale",
            "observed_at_epoch": 100.0,
            "updated_at_epoch": 110.0,
            "instrument": "SOL/CAD",
        }

    def test_report_is_read_only_and_counts_active_and_resolved(self):
        resolved = {
            **self.open, "source_incident_id": "market-data:md-2",
            "severity": "INFO", "status": "RESOLVED",
        }
        report = build_incident_report([self.open, resolved], now_epoch=500.0)
        self.assertTrue(report["read_only"])
        self.assertEqual(report["active_count"], 1)
        self.assertEqual(report["resolved_count"], 1)
        self.assertEqual(report["stale_active_count"], 1)
        self.assertEqual(report["incidents"][0]["severity"], "CRITICAL")
        self.assertEqual(self.open["status"], "open")

    def test_duplicate_source_identity_is_rejected(self):
        with self.assertRaisesRegex(IncidentIntakeError, "duplicate"):
            build_incident_report([self.open, self.open], now_epoch=120.0)

    def test_future_timestamp_is_rejected(self):
        with self.assertRaisesRegex(IncidentIntakeError, "future"):
            validate_incident({**self.open, "updated_at_epoch": 121.0}, now_epoch=120.0)

    def test_unknown_status_is_rejected(self):
        with self.assertRaises(IncidentIntakeError):
            validate_incident({**self.open, "status": "AUTO_CLEARED"}, now_epoch=120.0)

    def test_acknowledged_incident_remains_active(self):
        report = build_incident_report(
            [{**self.open, "status": "ACKNOWLEDGED"}], now_epoch=120.0,
        )
        self.assertEqual(report["active_count"], 1)
        self.assertEqual(report["status_counts"], {"ACKNOWLEDGED": 1})


if __name__ == "__main__":
    unittest.main()

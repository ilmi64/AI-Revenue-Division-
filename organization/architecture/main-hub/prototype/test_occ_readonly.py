"""Standard-library tests for conservative OCC display behaviour."""
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from occ_readonly import SnapshotError, assess_snapshot, build_report

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
NOW = datetime(2026, 11, 20, 12, 39, tzinfo=timezone.utc)


def load(name):
    with (FIXTURES / name).open(encoding="utf-8") as handle:
        return json.load(handle)


class OccReadOnlyTests(unittest.TestCase):
    def test_both_companies_remain_separate_and_untrusted(self):
        report = build_report(FIXTURES, now=NOW)
        self.assertEqual([x["company_id"] for x in report["companies"]],
                         ["ai_revenue", "trading_technology"])
        self.assertTrue(all(x["display_status"] == "UNKNOWN" for x in report["companies"]))
        self.assertTrue(all(x["trust"] == "SYNTHETIC_UNTRUSTED" for x in report["companies"]))
        self.assertFalse(report["operational_claim"])

    def test_company_identity_mismatch_rejected(self):
        snapshot = load("ai-revenue.snapshot.example.json")
        with self.assertRaises(SnapshotError):
            assess_snapshot(snapshot, "trading_technology", now=NOW)

    def test_unapproved_extra_field_rejected(self):
        snapshot = load("ai-revenue.snapshot.example.json")
        snapshot["api_key"] = "must-never-be-accepted"
        with self.assertRaises(SnapshotError):
            assess_snapshot(snapshot, "ai_revenue", now=NOW)

    def test_critical_waived_gate_is_not_pass(self):
        snapshot = load("ai-revenue.snapshot.example.json")
        snapshot["gates"][0]["status"] = "WAIVED"
        result = assess_snapshot(snapshot, "ai_revenue", now=NOW)
        self.assertEqual(result["critical_gates_not_passed"], ["operational_readiness"])

    def test_old_snapshot_is_stale_and_never_green(self):
        snapshot = load("trading-technology.snapshot.example.json")
        snapshot["source_revision"] = "abcdef123456"
        snapshot["published_at"] = "2026-11-18T00:00:00Z"
        result = assess_snapshot(snapshot, "trading_technology", now=NOW)
        self.assertTrue(result["stale"])
        self.assertEqual(result["display_status"], "STALE")
        self.assertNotEqual(result["display_status"], "HEALTHY")

    def test_timezone_required(self):
        snapshot = load("ai-revenue.snapshot.example.json")
        snapshot["published_at"] = "2026-11-20T12:00:00"
        with self.assertRaises(SnapshotError):
            assess_snapshot(snapshot, "ai_revenue", now=NOW)

    def test_naive_reference_clock_rejected(self):
        snapshot = load("ai-revenue.snapshot.example.json")
        naive_now = datetime(2026, 11, 20, 12, 39)
        with self.assertRaises(SnapshotError):
            assess_snapshot(snapshot, "ai_revenue", now=naive_now)

    def test_malformed_nested_incident_record_rejected(self):
        snapshot = load("ai-revenue.snapshot.example.json")
        snapshot["incident_summary"] = []
        with self.assertRaises(SnapshotError):
            assess_snapshot(snapshot, "ai_revenue", now=NOW)

    def test_unexpected_nested_evidence_field_rejected(self):
        snapshot = load("trading-technology.snapshot.example.json")
        snapshot["evidence"][0]["private_key"] = "not-accepted"
        with self.assertRaises(SnapshotError):
            assess_snapshot(snapshot, "trading_technology", now=NOW)

    def test_non_string_enum_value_rejected_cleanly(self):
        snapshot = load("ai-revenue.snapshot.example.json")
        snapshot["gates"][0]["status"] = []
        with self.assertRaises(SnapshotError):
            assess_snapshot(snapshot, "ai_revenue", now=NOW)

    def test_old_synthetic_snapshot_is_also_marked_stale(self):
        snapshot = load("ai-revenue.snapshot.example.json")
        snapshot["published_at"] = "2026-11-18T00:00:00Z"
        result = assess_snapshot(snapshot, "ai_revenue", now=NOW)
        self.assertTrue(result["stale"])
        self.assertEqual(result["display_status"], "STALE")
        self.assertEqual(result["trust"], "SYNTHETIC_UNTRUSTED")


if __name__ == "__main__":
    unittest.main()

"""Tests for the read-only OCC division health report."""
import unittest

from occ.division_health import (
    DivisionHealthError,
    build_division_health_report,
    validate_health_snapshot,
)


def snapshot(**overrides):
    value = {
        "division": "Crypto",
        "component": "market-data",
        "source_system": "adapter-a",
        "health_status": "HEALTHY",
        "evidence_level": "UNVERIFIED",
        "observed_at_epoch": 990.0,
        "summary": "Latest observation received",
    }
    value.update(overrides)
    return value


class DivisionHealthTests(unittest.TestCase):
    def test_healthy_snapshot_does_not_grant_readiness(self):
        result = validate_health_snapshot(snapshot(), now_epoch=1000.0)
        self.assertEqual(result["effective_health_status"], "HEALTHY")
        self.assertFalse(result["readiness_assessed"])

    def test_stale_snapshot_is_effectively_unknown(self):
        result = validate_health_snapshot(
            snapshot(observed_at_epoch=600.0),
            now_epoch=1000.0,
            stale_after_seconds=300.0,
        )
        self.assertTrue(result["stale"])
        self.assertEqual(result["effective_health_status"], "UNKNOWN")

    def test_missing_expected_division_makes_aggregate_unknown(self):
        report = build_division_health_report(
            [snapshot()], now_epoch=1000.0,
            expected_divisions=["Crypto", "Forex", "Indices", "Gold"],
        )
        self.assertEqual(
            report["missing_expected_divisions"], ["Forex", "Gold", "Indices"]
        )
        self.assertEqual(report["health_status"], "UNKNOWN")
        self.assertFalse(report["operational_ready"])

    def test_failed_component_dominates_aggregate(self):
        report = build_division_health_report(
            [snapshot(), snapshot(
                component="risk-engine", source_system="local-check",
                health_status="FAILED",
            )],
            now_epoch=1000.0,
        )
        self.assertEqual(report["health_status"], "FAILED")

    def test_duplicate_component_source_identity_is_rejected(self):
        with self.assertRaises(DivisionHealthError):
            build_division_health_report(
                [snapshot(), snapshot()], now_epoch=1000.0
            )

    def test_future_timestamp_is_rejected(self):
        with self.assertRaises(DivisionHealthError):
            validate_health_snapshot(
                snapshot(observed_at_epoch=1001.0), now_epoch=1000.0
            )

    def test_invalid_health_state_is_rejected(self):
        with self.assertRaises(DivisionHealthError):
            validate_health_snapshot(
                snapshot(health_status="READY"), now_epoch=1000.0
            )

    def test_invalid_evidence_level_is_rejected(self):
        with self.assertRaises(DivisionHealthError):
            validate_health_snapshot(
                snapshot(evidence_level="AUTHENTICATED"), now_epoch=1000.0
            )

    def test_source_snapshot_is_not_mutated(self):
        source = snapshot()
        before = dict(source)
        build_division_health_report([source], now_epoch=1000.0)
        self.assertEqual(source, before)

    def test_empty_report_is_unknown_not_healthy(self):
        report = build_division_health_report([], now_epoch=1000.0)
        self.assertEqual(report["health_status"], "UNKNOWN")
        self.assertEqual(report["source_snapshot_count"], 0)
        self.assertFalse(report["operational_ready"])

    def test_boolean_timestamp_is_rejected(self):
        with self.assertRaises(DivisionHealthError):
            validate_health_snapshot(
                snapshot(observed_at_epoch=True), now_epoch=1000.0
            )


if __name__ == "__main__":
    unittest.main()

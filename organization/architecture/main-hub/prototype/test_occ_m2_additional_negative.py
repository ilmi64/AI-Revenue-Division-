"""Additional fail-closed M2 reader regression cases.

Authored only: not executed. No network, runtime or publication activity.
"""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from occ_readonly import (
    MAX_OBJECT_MEMBERS, MAX_JSON_NODES, SnapshotError,
    assess_snapshot, build_report,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
NOW = datetime(2026, 11, 20, 12, 39, tzinfo=timezone.utc)


def synthetic_snapshot():
    return json.loads((FIXTURES / "ai-revenue.snapshot.example.json").read_text(encoding="utf-8"))


class OccM2AdditionalNegativeTests(unittest.TestCase):
    def test_object_member_limit_rejected_before_semantic_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            payload = {f"key{i}": i for i in range(MAX_OBJECT_MEMBERS + 1)}
            (path / "ai-revenue.snapshot.example.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )
            with self.assertRaisesRegex(SnapshotError, "maximum member count"):
                build_report(path, now=NOW)

    def test_total_node_limit_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            payload = {"groups": [[0] * 500 for _ in range(50)]}
            self.assertGreater(50 * 500, MAX_JSON_NODES)
            (path / "ai-revenue.snapshot.example.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )
            with self.assertRaisesRegex(SnapshotError, "maximum node count"):
                build_report(path, now=NOW)

    def test_invalid_utf8_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "ai-revenue.snapshot.example.json").write_bytes(b"\xff")
            with self.assertRaisesRegex(SnapshotError, "not valid UTF-8"):
                build_report(path, now=NOW)

    def test_missing_company_fixture_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(SnapshotError, "cannot read fixture"):
                build_report(Path(directory), now=NOW)

    def test_future_timestamp_beyond_grace_is_stale(self):
        snapshot = synthetic_snapshot()
        snapshot["published_at"] = "2026-11-20T12:45:00Z"
        report = assess_snapshot(snapshot, "ai_revenue", now=NOW)
        self.assertTrue(report["stale"])
        self.assertEqual(report["display_status"], "STALE")

    def test_evidence_reference_must_resolve_by_id_not_url(self):
        snapshot = synthetic_snapshot()
        snapshot["gates"][0]["evidence_refs"] = ["https://example.invalid/evidence"]
        with self.assertRaisesRegex(SnapshotError, "unknown evidence_id"):
            assess_snapshot(snapshot, "ai_revenue", now=NOW)


if __name__ == "__main__":
    unittest.main()

"""Authored only, not executed: offline envelope semantic regression cases."""
import copy
import json
import unittest
from pathlib import Path

from m2_envelope_semantics import EnvelopeSemanticError, check_m2_envelope_semantics, check_snapshot_fixture_agreement

ENVELOPE = Path(__file__).resolve().parents[1] / "fixtures" / "main-hub-envelope.example.json"


class M2EnvelopeSemanticTests(unittest.TestCase):
    def setUp(self):
        self.envelope = json.loads(ENVELOPE.read_text(encoding="utf-8"))

    def test_exact_fixture_semantics(self):
        check_m2_envelope_semantics(self.envelope)

    def test_snapshot_gate_unknown_evidence_rejected_by_reader(self):
        from occ_readonly import SnapshotError, assess_snapshot
        snapshot = self.envelope["status_snapshots"][0]
        snapshot["gates"][0]["evidence_refs"] = ["EV-NOT-FOUND"]
        with self.assertRaisesRegex(SnapshotError, "unknown evidence_id"):
            assess_snapshot(snapshot, "ai_revenue")

    def test_snapshot_wrong_company_rejected_by_reader(self):
        from occ_readonly import SnapshotError, assess_snapshot
        snapshot = self.envelope["status_snapshots"][0]
        with self.assertRaisesRegex(SnapshotError, "company identity mismatch"):
            assess_snapshot(snapshot, "trading_technology")

    def test_pinned_snapshot_agreement(self):
        fixtures = {
            item["company_id"]: copy.deepcopy(item)
            for item in self.envelope["status_snapshots"]
        }
        check_snapshot_fixture_agreement(self.envelope, fixtures)

    def test_pinned_snapshot_drift_rejected(self):
        fixtures = {
            item["company_id"]: copy.deepcopy(item)
            for item in self.envelope["status_snapshots"]
        }
        fixtures["ai_revenue"]["overall_status"] = "HEALTHY"
        with self.assertRaisesRegex(EnvelopeSemanticError, "differs from pinned"):
            check_snapshot_fixture_agreement(self.envelope, fixtures)

    def test_pinned_snapshot_wrong_identity_rejected(self):
        fixtures = {
            item["company_id"]: copy.deepcopy(item)
            for item in self.envelope["status_snapshots"]
        }
        fixtures["ai_revenue"]["company_id"] = "trading_technology"
        with self.assertRaisesRegex(EnvelopeSemanticError, "pinned fixture identity mismatch"):
            check_snapshot_fixture_agreement(self.envelope, fixtures)

    def test_pinned_snapshot_missing_company_rejected(self):
        fixtures = {"ai_revenue": copy.deepcopy(self.envelope["status_snapshots"][0])}
        with self.assertRaisesRegex(EnvelopeSemanticError, "company set mismatch"):
            check_snapshot_fixture_agreement(self.envelope, fixtures)

    def test_duplicate_company_record(self):
        self.envelope["company_registry"][1] = copy.deepcopy(self.envelope["company_registry"][0])
        with self.assertRaises(EnvelopeSemanticError):
            check_m2_envelope_semantics(self.envelope)

    def test_unknown_workstream_dependency(self):
        self.envelope["workstreams"][0]["depends_on"] = ["WS-DOES-NOT-EXIST"]
        with self.assertRaisesRegex(EnvelopeSemanticError, "unknown workstream dependency"):
            check_m2_envelope_semantics(self.envelope)

    def test_self_dependency(self):
        item = self.envelope["workstreams"][0]
        item["depends_on"] = [item["workstream_id"]]
        with self.assertRaisesRegex(EnvelopeSemanticError, "self-dependent"):
            check_m2_envelope_semantics(self.envelope)

    def test_cyclic_workstream_dependency(self):
        first, second = self.envelope["workstreams"][:2]
        first["depends_on"] = [second["workstream_id"]]
        second["depends_on"] = [first["workstream_id"]]
        with self.assertRaisesRegex(EnvelopeSemanticError, "cyclic workstream dependency"):
            check_m2_envelope_semantics(self.envelope)

    def test_decision_unknown_workstream(self):
        # The committed fixture intentionally has no decisions; inject a synthetic one.
        self.envelope["decisions"].append({"decision_id": "DEC-SYNTHETIC", "workstream_ids": ["WS-UNKNOWN"]})
        with self.assertRaisesRegex(EnvelopeSemanticError, "decision references unknown"):
            check_m2_envelope_semantics(self.envelope)


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from revenue_commissioning_snapshot import snapshot
from revenue_evidence_custody import LocalEvidenceCustody
from revenue_identity_boundary import IdentityAssessment
from revenue_occ_export import export_occ_snapshot
from revenue_occ_replay_guard import assess_replay, ReplayState


class ReplayGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.custody = LocalEvidenceCustody(Path(self.tmp.name) / "journal.sqlite")
        self.custody.append("demo_001:01", "agent_1", "engineering", b"first")
        self.identity = IdentityAssessment("demo_001:01", "HOLD", ("identity_missing",))
        self.payload = self.export()

    def tearDown(self):
        self.tmp.cleanup()

    def export(self):
        return export_occ_snapshot(snapshot(self.identity, self.custody))

    def assess(self, payload, prior):
        return assess_replay(payload, hashlib.sha256(payload).hexdigest(), prior)

    def test_first_report_read_only(self):
        result = self.assess(self.payload, None)
        self.assertEqual(result.status, "READ_ONLY_NEW_REPORT")
        self.assertFalse(result.launch_authorized)
        self.assertFalse(result.execution_authorized)

    def test_replay_rejected(self):
        first = self.assess(self.payload, None)
        self.assertIn("replayed_report", self.assess(self.payload, first.next_state).blockers)

    def test_older_sequence_rejected(self):
        state = ReplayState(2, "0" * 64)
        self.assertIn("stale_sequence", self.assess(self.payload, state).blockers)

    def test_conflicting_same_sequence_rejected(self):
        data = json.loads(self.payload)
        data["blockers"].append("different")
        changed = json.dumps(data).encode()
        self.assertIn("same_sequence_conflict", self.assess(changed, ReplayState(1, hashlib.sha256(self.payload).hexdigest())).blockers)

    def test_new_sequence_accepted_without_authority(self):
        first = self.assess(self.payload, None)
        self.custody.append("demo_001:02", "agent_1", "engineering", b"second")
        next_result = self.assess(self.export(), first.next_state)
        self.assertEqual(next_result.status, "READ_ONLY_NEW_REPORT")
        self.assertEqual(next_result.next_state.sequence, 2)
        self.assertFalse(next_result.external_actions_authorized)

    def test_wrong_pin_rejected(self):
        self.assertIn("pin_mismatch", assess_replay(self.payload, "f"*64, None).blockers)


if __name__ == "__main__":
    unittest.main()

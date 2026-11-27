import sqlite3
import tempfile
import unittest
from pathlib import Path

from revenue_commissioning_snapshot import snapshot
from revenue_evidence_custody import LocalEvidenceCustody
from revenue_identity_boundary import IdentityAssessment


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "evidence.sqlite"
        self.custody = LocalEvidenceCustody(self.path)
        self.custody.append("demo_001:01", "agent_1", "engineering", b"artifact")
        self.identity = IdentityAssessment("demo_001:01", "IDENTITY_EVIDENCE_REPORTED", ())

    def tearDown(self):
        self.tmp.cleanup()

    def test_read_only_blocked(self):
        report = snapshot(self.identity, self.custody)
        self.assertEqual(report.company, "Aevora AI Revenue")
        self.assertEqual(report.evidence_records, 1)
        self.assertTrue(report.local_chain_valid)
        self.assertFalse(report.launch_authorized)
        self.assertFalse(report.agent_execution_authorized)
        self.assertFalse(report.external_actions_authorized)

    def test_self_supplied_checkpoint_cannot_authorize(self):
        seq, digest = self.custody.head()
        report = snapshot(self.identity, self.custody,
                          anchor_sequence=seq, anchor_digest=digest)
        self.assertEqual(report.gate_status, "BLOCKED")
        self.assertIn("authenticated_identity_not_established", report.blockers)

    def test_tampering_surfaces_as_blocker(self):
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE evidence SET actor_role='tampered' WHERE sequence=1")
        report = snapshot(self.identity, self.custody)
        self.assertFalse(report.local_chain_valid)
        self.assertIn("local_evidence_chain_invalid", report.blockers)


if __name__ == "__main__":
    unittest.main()

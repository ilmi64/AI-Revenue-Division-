import sqlite3
import tempfile
import unittest
from pathlib import Path

from revenue_evidence_custody import LocalEvidenceCustody


class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "evidence.sqlite"
        self.custody = LocalEvidenceCustody(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_append_and_restart(self):
        first = self.custody.append("demo_001:01", "agent_1", "engineering", b"artifact")
        second = LocalEvidenceCustody(self.path).append("demo_001:02", "reviewer_2", "quality", b"review")
        self.assertEqual(second.sequence, 2)
        self.assertEqual(second.previous_digest, first.record_digest)
        self.assertTrue(self.custody.verify_chain())

    def test_tampering_detected(self):
        self.custody.append("demo_001:01", "agent_1", "engineering", b"artifact")
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE evidence SET actor_role='unknown' WHERE sequence=1")
        self.assertFalse(self.custody.verify_chain())

    def test_missing_record_detected(self):
        self.custody.append("demo_001:01", "agent_1", "engineering", b"first")
        self.custody.append("demo_001:02", "agent_1", "engineering", b"second")
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM evidence WHERE sequence=1")
        self.assertFalse(self.custody.verify_chain())

    def test_independently_held_head_detects_truncation(self):
        self.custody.append("demo_001:01", "agent_1", "engineering", b"first")
        self.custody.append("demo_001:02", "agent_1", "engineering", b"second")
        anchor = self.custody.head()
        self.assertTrue(self.custody.verify_anchor(*anchor))
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM evidence WHERE sequence=2")
        self.assertTrue(self.custody.verify_chain())
        self.assertFalse(self.custody.verify_anchor(*anchor))

    def test_invalid_external_anchor_fails_closed(self):
        self.assertFalse(self.custody.verify_anchor(True, "0" * 64))
        self.assertFalse(self.custody.verify_anchor(0, "not-a-digest"))

    def test_corrupted_chain_blocks_future_append(self):
        self.custody.append("demo_001:01", "agent_1", "engineering", b"first")
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE evidence SET actor_role='tampered' WHERE sequence=1")
        with self.assertRaises(ValueError):
            self.custody.append("demo_001:02", "agent_1", "engineering", b"second")
        self.assertEqual(self.custody.head()[0], 1)

    def test_task_identity_must_match_queue_format(self):
        with self.assertRaises(ValueError):
            self.custody.append("demo_001::01", "agent_1", "engineering", b"artifact")

    def test_invalid_evidence_rejected(self):
        with self.assertRaises(ValueError):
            self.custody.append("demo_001:01", "agent_1", "engineering", b"")
        with self.assertRaises(ValueError):
            self.custody.append("demo_001:01", "../actor", "engineering", b"artifact")


if __name__ == "__main__":
    unittest.main()

import hashlib
import tempfile
import unittest
from pathlib import Path

from revenue_commissioning_snapshot import snapshot
from revenue_evidence_custody import LocalEvidenceCustody
from revenue_identity_boundary import IdentityAssessment
from revenue_occ_export import export_occ_snapshot
from revenue_occ_checkpoint_store import LocalOCCCheckpointStore


class CheckpointStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.custody = LocalEvidenceCustody(base / "evidence.sqlite")
        self.store_path = base / "occ.sqlite"
        self.store = LocalOCCCheckpointStore(self.store_path)
        self.identity = IdentityAssessment("demo_001:01", "HOLD", ("identity_missing",))
        self.custody.append("demo_001:01", "agent_1", "engineering", b"first")
        self.first = self.export()

    def tearDown(self):
        self.temp.cleanup()

    def export(self):
        return export_occ_snapshot(snapshot(self.identity, self.custody))

    def accept(self, payload):
        return self.store.accept(payload, hashlib.sha256(payload).hexdigest())

    def test_restart_preserves_checkpoint(self):
        self.assertEqual(self.accept(self.first)[0], "READ_ONLY_STORED")
        reopened = LocalOCCCheckpointStore(self.store_path)
        self.assertEqual(reopened.read().sequence, 1)
        self.assertEqual(reopened.accept(self.first, hashlib.sha256(self.first).hexdigest())[0], "REJECT")

    def test_newer_report_advances(self):
        self.accept(self.first)
        self.custody.append("demo_001:02", "agent_1", "engineering", b"second")
        self.assertEqual(self.accept(self.export())[0], "READ_ONLY_STORED")
        self.assertEqual(self.store.read().sequence, 2)

    def test_stale_report_rejected(self):
        self.accept(self.first)
        self.custody.append("demo_001:02", "agent_1", "engineering", b"second")
        self.accept(self.export())
        self.assertEqual(self.accept(self.first)[0], "REJECT")

    def test_invalid_pin_does_not_advance(self):
        status, _ = self.store.accept(self.first, "f"*64)
        self.assertEqual(status, "REJECT")
        self.assertIsNone(self.store.read())

    def test_no_execution_permissions(self):
        self.assertEqual(self.accept(self.first)[0], "READ_ONLY_STORED")
        self.assertEqual(self.store.read().sequence, 1)


if __name__ == "__main__":
    unittest.main()

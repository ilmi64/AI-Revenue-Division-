import hashlib
import tempfile
import unittest
from pathlib import Path
from revenue_commissioning_snapshot import snapshot
from revenue_evidence_custody import LocalEvidenceCustody
from revenue_identity_boundary import IdentityAssessment
from revenue_occ_export import export_occ_snapshot
from revenue_occ_pinned_import import verify_pinned_import


class PinnedImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        custody = LocalEvidenceCustody(Path(self.tmp.name) / "journal.sqlite")
        custody.append("demo_001:01", "agent_1", "engineering", b"artifact")
        self.payload = export_occ_snapshot(snapshot(
            IdentityAssessment("demo_001:01", "HOLD", ("missing_identity",)), custody))
        self.digest = hashlib.sha256(self.payload).hexdigest()

    def tearDown(self):
        self.tmp.cleanup()

    def test_matching_pin_is_still_read_only(self):
        result = verify_pinned_import(self.payload, self.digest)
        self.assertEqual(result.status, "READ_ONLY_PIN_MATCH")
        self.assertFalse(result.launch_authorized)
        self.assertFalse(result.agent_execution_authorized)
        self.assertFalse(result.external_actions_authorized)

    def test_modified_payload_rejected(self):
        changed = self.payload.replace(b"missing_identity", b"other_identity")
        self.assertIn("pin_mismatch", verify_pinned_import(changed, self.digest).blockers)

    def test_wrong_pin_rejected(self):
        self.assertIn("pin_mismatch", verify_pinned_import(self.payload, "f"*64).blockers)

    def test_missing_pin_rejected(self):
        self.assertIn("pin_invalid", verify_pinned_import(self.payload, "").blockers)

    def test_pinned_malformed_json_rejected(self):
        bad = b"not-json"
        result = verify_pinned_import(bad, hashlib.sha256(bad).hexdigest())
        self.assertEqual(result.status, "REJECT")
        self.assertIn("json_invalid", result.blockers)


if __name__ == "__main__":
    unittest.main()

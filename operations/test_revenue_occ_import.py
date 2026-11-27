import json
import tempfile
import unittest
from pathlib import Path
from revenue_commissioning_snapshot import snapshot
from revenue_evidence_custody import LocalEvidenceCustody
from revenue_identity_boundary import IdentityAssessment
from revenue_occ_export import export_occ_snapshot
from revenue_occ_import import validate_occ_export


class OCCImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        custody = LocalEvidenceCustody(Path(self.tmp.name) / "journal.sqlite")
        custody.append("demo_001:01", "agent_1", "engineering", b"artifact")
        self.payload = export_occ_snapshot(snapshot(
            IdentityAssessment("demo_001:01", "HOLD", ("identity_missing",)), custody))

    def tearDown(self):
        self.tmp.cleanup()

    def changed(self, section, field, value):
        data = json.loads(self.payload)
        if section is None:
            data[field] = value
        else:
            data[section][field] = value
        return json.dumps(data).encode("ascii")

    def test_end_to_end_read_only_roundtrip(self):
        decision = validate_occ_export(self.payload)
        self.assertEqual(decision.status, "READ_ONLY_ACCEPTED")
        self.assertFalse(decision.launch_authorized)
        self.assertFalse(decision.agent_execution_authorized)

    def test_wrong_company_rejected(self):
        self.assertEqual(validate_occ_export(self.changed(None, "company", "Trading & Technology")).status, "REJECT")

    def test_permission_escalation_rejected(self):
        self.assertEqual(validate_occ_export(self.changed("permissions", "launch", True)).status, "REJECT")

    def test_fake_signature_rejected(self):
        self.assertEqual(validate_occ_export(self.changed("trust", "authenticated_signature", True)).status, "REJECT")

    def test_unknown_field_rejected(self):
        data = json.loads(self.payload)
        data["execute"] = True
        self.assertEqual(validate_occ_export(json.dumps(data).encode()).status, "REJECT")

    def test_malformed_json_rejected(self):
        self.assertEqual(validate_occ_export(b"{invalid").status, "REJECT")

    def test_oversized_payload_rejected(self):
        self.assertEqual(validate_occ_export(b"x" * 32769).status, "REJECT")


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from revenue_commissioning_snapshot import snapshot
from revenue_evidence_custody import LocalEvidenceCustody
from revenue_identity_boundary import IdentityAssessment
from revenue_occ_export import export_occ_snapshot


class OCCExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        custody = LocalEvidenceCustody(Path(self.temp.name) / "journal.sqlite")
        custody.append("demo_001:01", "agent_1", "engineering", b"artifact")
        self.report = snapshot(IdentityAssessment("demo_001:01", "HOLD", ("missing_identity",)), custody)

    def tearDown(self):
        self.temp.cleanup()

    def test_canonical_deterministic_output(self):
        first = export_occ_snapshot(self.report)
        self.assertEqual(first, export_occ_snapshot(self.report))
        self.assertEqual(json.loads(first)["schema"], "aevora.occ.commissioning.v1")

    def test_never_exports_release_authority(self):
        data = json.loads(export_occ_snapshot(self.report))
        self.assertFalse(any(data["permissions"].values()))
        self.assertFalse(data["trust"]["authenticated_signature"])

    def test_rejects_forged_authorization(self):
        with self.assertRaises(ValueError):
            export_occ_snapshot(replace(self.report, launch_authorized=True))

    def test_rejects_wrong_company(self):
        with self.assertRaises(ValueError):
            export_occ_snapshot(replace(self.report, company="Trading & Technology"))

    def test_rejects_invalid_digest(self):
        with self.assertRaises(ValueError):
            export_occ_snapshot(replace(self.report, evidence_head_sha256="bad"))


if __name__ == "__main__":
    unittest.main()

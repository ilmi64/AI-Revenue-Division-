import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from revenue_evidence_custody import LocalEvidenceCustody
from revenue_identity_boundary import IdentityAssessment
from revenue_release_gate import assess_release


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.custody = LocalEvidenceCustody(Path(self.temp.name) / "evidence.sqlite")
        self.custody.append("demo_001:01", "agent_1", "engineering", b"work")
        self.identity = IdentityAssessment("demo_001:01", "IDENTITY_EVIDENCE_REPORTED", ())

    def tearDown(self):
        self.temp.cleanup()

    def test_no_anchor_blocks(self):
        self.assertIn("external_anchor_missing", assess_release(self.identity, self.custody).blockers)

    def test_matching_self_supplied_anchor_never_authorizes(self):
        seq, digest = self.custody.head()
        result = assess_release(self.identity, self.custody, anchor_sequence=seq, anchor_digest=digest)
        self.assertEqual(result.status, "BLOCKED")
        self.assertFalse(result.execution_authorized)
        self.assertFalse(result.external_submission_authorized)

    def test_mismatched_anchor_blocks(self):
        result = assess_release(self.identity, self.custody, anchor_sequence=1, anchor_digest="f"*64)
        self.assertIn("external_anchor_mismatch", result.blockers)

    def test_spoofed_verified_flags_do_not_grant_release(self):
        forged = replace(self.identity, identity_verified=True, independent_custody_verified=True)
        seq, digest = self.custody.head()
        result = assess_release(forged, self.custody, anchor_sequence=seq, anchor_digest=digest)
        self.assertIn("release_authority_absent", result.blockers)
        self.assertFalse(result.deployment_authorized)
        self.assertFalse(result.spending_authorized)

    def test_hold_identity_blocks(self):
        identity = replace(self.identity, status="HOLD", blockers=("self_review",))
        self.assertIn("self_review", assess_release(identity, self.custody).blockers)


if __name__ == "__main__":
    unittest.main()

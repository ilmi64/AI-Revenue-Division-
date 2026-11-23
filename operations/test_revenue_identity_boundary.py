import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from revenue_evidence_custody import LocalEvidenceCustody
from revenue_identity_boundary import VerifiedPrincipal, assess_identity


class IdentityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        custody = LocalEvidenceCustody(Path(self.temp.name) / "evidence.sqlite")
        self.author = custody.append("demo_001:01", "agent_1", "engineering", b"work")
        self.reviewer = custody.append("demo_001:01", "reviewer_2", "quality", b"review")
        self.agent = VerifiedPrincipal("agent_1", "engineering", True, True, False, "worker")
        self.qa = VerifiedPrincipal("reviewer_2", "quality", True, True, False, "independent_qa")

    def tearDown(self):
        self.temp.cleanup()

    def check(self, **kwargs):
        return assess_identity(self.author, self.reviewer, kwargs.get("agent", self.agent),
                               kwargs.get("qa", self.qa),
                               trusted_registry_verified=kwargs.get("registry", True))

    def test_verified_claims_still_cannot_authorize_delivery(self):
        result = self.check()
        self.assertEqual(result.status, "IDENTITY_EVIDENCE_REPORTED")
        self.assertFalse(result.identity_verified)
        self.assertFalse(result.execution_authorized)
        self.assertFalse(result.external_delivery_authorized)

    def test_self_asserted_registry_fails_closed(self):
        self.assertIn("trusted_registry_not_verified", self.check(registry=False).blockers)

    def test_revoked_agent_fails_closed(self):
        self.assertIn("author_trust_unverified",
                      self.check(agent=replace(self.agent, revoked=True)).blockers)

    def test_missing_role_grant_fails_closed(self):
        self.assertIn("reviewer_trust_unverified",
                      self.check(qa=replace(self.qa, role_grant_verified=False)).blockers)

    def test_identity_mismatch_fails_closed(self):
        self.assertIn("reviewer_identity_mismatch",
                      self.check(qa=replace(self.qa, principal_id="other")).blockers)

    def test_same_trust_domain_fails_closed(self):
        self.assertIn("independence_boundary_missing",
                      self.check(qa=replace(self.qa, trust_domain="worker")).blockers)


if __name__ == "__main__":
    unittest.main()

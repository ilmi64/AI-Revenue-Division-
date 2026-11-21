"""Offline lifecycle tests using disposable synthetic fixture keys."""
import unittest

from identity_lifecycle_reference import (
    issue_identity, verify_identity, issue_owner_approval, verify_owner_approval,
)

ISSUER_KEY = b"synthetic-issuer-fixture-key-never-use-in-production-0001"
OWNER_KEY = b"synthetic-owner-fixture-key-never-use-in-production-0002"


class IdentityLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.identity = issue_identity(issuer_id="test-issuer", agent_id="agent-1",
            company_id="ai_revenue", role="researcher", issued_at=10, expires_at=500,
            issuer_key=ISSUER_KEY)

    def test_issuer_signed_identity_verifies(self):
        self.assertEqual(verify_identity(self.identity, issuer_id="test-issuer",
            company_id="ai_revenue", now=100, issuer_key=ISSUER_KEY)[0], True)

    def test_tampered_identity_denied(self):
        changed = {"claims": dict(self.identity["claims"]), "signature": self.identity["signature"]}
        changed["claims"]["role"] = "administrator"
        self.assertEqual(verify_identity(changed, issuer_id="test-issuer",
            company_id="ai_revenue", now=100, issuer_key=ISSUER_KEY)[1], "invalid_identity_signature")

    def test_wrong_issuer_key_denied(self):
        self.assertEqual(verify_identity(self.identity, issuer_id="test-issuer",
            company_id="ai_revenue", now=100, issuer_key=b"x" * 32)[1], "invalid_identity_signature")

    def test_wrong_company_denied(self):
        self.assertEqual(verify_identity(self.identity, issuer_id="test-issuer",
            company_id="trading_technology", now=100, issuer_key=ISSUER_KEY)[1], "identity_company_mismatch")

    def test_expired_identity_denied(self):
        self.assertEqual(verify_identity(self.identity, issuer_id="test-issuer",
            company_id="ai_revenue", now=500, issuer_key=ISSUER_KEY)[1], "identity_expired")

    def test_revoked_identity_denied(self):
        self.assertEqual(verify_identity(self.identity, issuer_id="test-issuer",
            company_id="ai_revenue", now=100, issuer_key=ISSUER_KEY,
            revoked_agents={"agent-1"})[1], "identity_revoked")

    def test_invalid_issuer_key_rejected_at_issue(self):
        with self.assertRaises(ValueError):
            issue_identity(issuer_id="i", agent_id="a", company_id="c", role="r",
                issued_at=1, expires_at=2, issuer_key=b"short")

    def test_agent_cannot_modify_signed_role(self):
        forged = {"claims": dict(self.identity["claims"]), "signature": self.identity["signature"]}
        forged["claims"]["company_id"] = "trading_technology"
        self.assertFalse(verify_identity(forged, issuer_id="test-issuer",
            company_id="trading_technology", now=100, issuer_key=ISSUER_KEY)[0])

    def test_owner_approval_exact_scope_verifies(self):
        approval = issue_owner_approval(owner_id="owner", company_id="ai_revenue",
            task_id="task-1", operation="report.publish", resource="reports/draft-1",
            nonce="nonce-1", issued_at=20, expires_at=200, owner_key=OWNER_KEY)
        self.assertTrue(verify_owner_approval(approval, owner_id="owner",
            company_id="ai_revenue", task_id="task-1", operation="report.publish",
            resource="reports/draft-1", nonce="nonce-1", now=100,
            owner_key=OWNER_KEY)[0])

    def test_approval_cannot_be_replayed(self):
        approval = issue_owner_approval(owner_id="owner", company_id="ai_revenue",
            task_id="task-1", operation="report.publish", resource="reports/draft-1",
            nonce="nonce-1", issued_at=20, expires_at=200, owner_key=OWNER_KEY)
        consumed = {"nonce-1"}
        self.assertEqual(verify_owner_approval(approval, owner_id="owner",
            company_id="ai_revenue", task_id="task-1", operation="report.publish",
            resource="reports/draft-1", nonce="nonce-1", now=100,
            owner_key=OWNER_KEY, consumed_nonces=consumed)[1], "approval_already_consumed")

    def test_approval_scope_is_exact(self):
        approval = issue_owner_approval(owner_id="owner", company_id="ai_revenue",
            task_id="task-1", operation="report.publish", resource="reports/draft-1",
            nonce="nonce-1", issued_at=20, expires_at=200, owner_key=OWNER_KEY)
        self.assertEqual(verify_owner_approval(approval, owner_id="owner",
            company_id="ai_revenue", task_id="task-1", operation="report.publish",
            resource="reports/other", nonce="nonce-1", now=100,
            owner_key=OWNER_KEY)[1], "approval_scope_mismatch")

    def test_approval_wrong_signer_denied(self):
        approval = issue_owner_approval(owner_id="owner", company_id="ai_revenue",
            task_id="task-1", operation="report.publish", resource="reports/draft-1",
            nonce="nonce-1", issued_at=20, expires_at=200, owner_key=OWNER_KEY)
        self.assertEqual(verify_owner_approval(approval, owner_id="owner",
            company_id="ai_revenue", task_id="task-1", operation="report.publish",
            resource="reports/draft-1", nonce="nonce-1", now=100,
            owner_key=b"z" * 48)[1], "invalid_approval_signature")

    def test_approval_expiry_denied(self):
        approval = issue_owner_approval(owner_id="owner", company_id="ai_revenue",
            task_id="task-1", operation="report.publish", resource="reports/draft-1",
            nonce="nonce-1", issued_at=20, expires_at=200, owner_key=OWNER_KEY)
        self.assertEqual(verify_owner_approval(approval, owner_id="owner",
            company_id="ai_revenue", task_id="task-1", operation="report.publish",
            resource="reports/draft-1", nonce="nonce-1", now=200,
            owner_key=OWNER_KEY)[1], "approval_expired")

    def test_approval_payload_tampering_denied(self):
        approval = issue_owner_approval(owner_id="owner", company_id="ai_revenue",
            task_id="task-1", operation="report.publish", resource="reports/draft-1",
            nonce="nonce-1", issued_at=20, expires_at=200, owner_key=OWNER_KEY)
        approval["claims"]["operation"] = "funds.transfer"
        self.assertEqual(verify_owner_approval(approval, owner_id="owner",
            company_id="ai_revenue", task_id="task-1", operation="funds.transfer",
            resource="reports/draft-1", nonce="nonce-1", now=100,
            owner_key=OWNER_KEY)[1], "invalid_approval_signature")


if __name__ == "__main__":
    unittest.main()

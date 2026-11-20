"""Contract tests for the PostgreSQL approval adapter using a DB-API fake."""
import unittest
from unittest.mock import MagicMock, call
from owner_approval_postgres_repository import (
    ApprovalRepositoryError, PostgresOwnerApprovalRepository,
)


class FakeConnection:
    def __init__(self):
        self.cursor_obj = MagicMock()
        self.commits = 0
        self.rollbacks = 0
        self.closed = 0
    def cursor(self):
        return self.cursor_obj
    def commit(self):
        self.commits += 1
    def rollback(self):
        self.rollbacks += 1
    def close(self):
        self.closed += 1


def valid_claims():
    return {
        "approval_id": "11111111-1111-4111-8111-111111111111",
        "owner_id": "owner-1", "company_id": "revenue-co", "stream_id": "sales",
        "agent_id": "agent-1", "session_id": "session-1", "task_id": "task-1",
        "operation": "crm.create_draft", "resource": "customer/123",
        "recipient": "customer-123", "intent_digest": "a" * 64,
        "amount_minor": None, "currency": None, "policy_version": "p1",
        "audience": "approval-service", "nonce": "nonce-1", "single_use": True,
        "issued_at": 100, "expires_at": 200, "signer_key_id": "owner-key-1",
        "signed_payload_digest": "b" * 64, "signature_digest": "c" * 64,
        "scope_digest": "d" * 64,
    }


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.conn = FakeConnection()
        self.repo = PostgresOwnerApprovalRepository(
            connection_factory=lambda: self.conn,
            company_id="revenue-co", audience="approval-service",
        )
        self.conn.cursor_obj.fetchone.return_value = {
            "last_sequence": 0, "head_hash": "0" * 64,
        }

    def test_issue_persists_and_audits_in_one_commit(self):
        receipt = self.repo.issue(
            claims=valid_claims(), signed_envelope={"signature": "opaque"},
            now=120,
        )
        self.assertEqual(receipt["company_id"], "revenue-co")
        self.assertEqual(self.conn.commits, 1)
        self.assertEqual(self.conn.rollbacks, 0)
        self.assertEqual(self.conn.closed, 1)
        sql = " ".join(str(c.args[0]) for c in self.conn.cursor_obj.execute.call_args_list)
        self.assertIn("INSERT INTO owner_approval_records", sql)
        self.assertIn("INSERT INTO owner_approval_audit_events", sql)

    def test_issue_rejects_wrong_company_before_database(self):
        claims = valid_claims()
        claims["company_id"] = "trading-co"
        with self.assertRaises(ApprovalRepositoryError):
            self.repo.issue(claims=claims, signed_envelope={"signature": "x"}, now=120)
        self.assertEqual(self.conn.cursor_obj.execute.call_count, 0)

    def test_issue_rejects_non_single_use(self):
        claims = valid_claims()
        claims["single_use"] = False
        with self.assertRaises(ApprovalRepositoryError):
            self.repo.issue(claims=claims, signed_envelope={"signature": "x"}, now=120)

    def test_issue_rolls_back_on_audit_failure(self):
        self.conn.cursor_obj.execute.side_effect = [None, None, None, RuntimeError("audit unavailable")]
        with self.assertRaises(RuntimeError):
            self.repo.issue(claims=valid_claims(), signed_envelope={"signature": "x"}, now=120)
        self.assertEqual(self.conn.commits, 0)
        self.assertEqual(self.conn.rollbacks, 1)

    def test_consume_uses_caller_transaction_without_commit(self):
        self.conn.cursor_obj.fetchone.return_value = {
            "company_id": "revenue-co", "stream_id": "sales", "owner_id": "owner-1",
            "principal_agent_id": "agent-1", "session_id": "session-1", "task_id": "task-1",
            "operation": "crm.create_draft", "resource": "customer/123",
            "recipient": "customer-123", "intent_digest": "a" * 64,
            "policy_version": "p1", "audience": "approval-service",
            "revoked_at": None, "expires_at": __import__("datetime").datetime.fromtimestamp(200, __import__("datetime").timezone.utc),
            "amount_minor": None, "currency": None, "nonce": "nonce-1",
        }
        result = self.repo.consume_in_transaction(
            self.conn, approval_id=valid_claims()["approval_id"], action_id="action-1",
            expected={
                "company_id": "revenue-co", "stream_id": "sales", "owner_id": "owner-1",
                "principal_agent_id": "agent-1", "session_id": "session-1", "task_id": "task-1",
                "operation": "crm.create_draft", "resource": "customer/123",
                "recipient": "customer-123", "intent_digest": "a" * 64,
                "policy_version": "p1", "audience": "approval-service",
                "amount_minor": None, "currency": None,
            }, now=120,
        )
        self.assertTrue(result["consumed"])
        self.assertEqual(self.conn.commits, 0)
        self.assertEqual(self.conn.rollbacks, 0)

    def test_consume_rejects_scope_mismatch_without_commit(self):
        self.conn.cursor_obj.fetchone.return_value = {"company_id": "revenue-co"}
        with self.assertRaises(ApprovalRepositoryError):
            self.repo.consume_in_transaction(
                self.conn, approval_id=valid_claims()["approval_id"], action_id="a",
                expected={"company_id": "revenue-co"}, now=120,
            )
        self.assertEqual(self.conn.commits, 0)

    def test_amount_currency_pair_is_enforced(self):
        claims = valid_claims()
        claims["amount_minor"] = 50
        with self.assertRaises(ApprovalRepositoryError):
            self.repo.issue(claims=claims, signed_envelope={"signature": "x"}, now=120)

    def test_digest_format_is_enforced(self):
        claims = valid_claims()
        claims["signature_digest"] = "not-a-digest"
        with self.assertRaises(ApprovalRepositoryError):
            self.repo.issue(claims=claims, signed_envelope={"signature": "x"}, now=120)


if __name__ == "__main__":
    unittest.main()

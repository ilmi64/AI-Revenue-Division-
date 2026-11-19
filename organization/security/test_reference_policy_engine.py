"""Offline tests for the synthetic policy decision reference."""
import unittest

from reference_policy_engine import authorize


class PolicyEngineTests(unittest.TestCase):
    def setUp(self):
        self.identity = {"agent_id": "synthetic-agent-01", "company_id": "ai_revenue",
                         "role": "researcher", "expires_at": 500}
        self.policy = {"available": True, "company_id": "ai_revenue", "emergency_stop": False,
                       "allowed_operations": ["research.read", "market_data.read", "report.write"],
                       "allowed_resource_prefixes": ["research/", "reports/"],
                       "cost_cap_cad": 0, "approval_required": False}
        self.request = {"task_id": "task-01", "company_id": "ai_revenue",
                        "operation": "research.read", "resource": "research/synthetic-fixture",
                        "nonce": "nonce-01", "cost_cad": 0}
        self.cache = set()

    def decide(self, **kwargs):
        return authorize(kwargs.pop("request", self.request),
                         kwargs.pop("identity", self.identity),
                         kwargs.pop("policy", self.policy), now=100,
                         replay_cache=self.cache, **kwargs)

    def test_scoped_synthetic_request_allowed(self):
        self.assertTrue(self.decide().allowed)

    def test_company_mismatch_denied(self):
        self.assertEqual(self.decide(request=dict(self.request, company_id="trading_technology")).reason,
                         "company_mismatch")

    def test_expired_identity_denied(self):
        self.assertEqual(self.decide(identity=dict(self.identity, expires_at=100)).reason,
                         "identity_expired")

    def test_revoked_identity_denied(self):
        self.assertEqual(self.decide(revoked_agents={"synthetic-agent-01"}).reason, "identity_revoked")

    def test_policy_outage_fails_closed(self):
        self.assertEqual(self.decide(policy=dict(self.policy, available=False)).reason, "policy_unavailable")

    def test_emergency_stop_denies(self):
        self.assertEqual(self.decide(policy=dict(self.policy, emergency_stop=True)).reason,
                         "emergency_stop_active")

    def test_unlisted_operation_denied(self):
        self.assertEqual(self.decide(request=dict(self.request, operation="external.publish")).reason,
                         "operation_not_allowlisted")

    def test_resource_scope_denied(self):
        self.assertEqual(self.decide(request=dict(self.request, resource="secrets/private")).reason,
                         "resource_out_of_scope")

    def test_nonzero_cost_denied(self):
        self.assertEqual(self.decide(request=dict(self.request, cost_cad=0.01)).reason,
                         "cost_cap_exceeded")

    def test_cancelled_task_denied(self):
        self.assertEqual(self.decide(cancelled_tasks={"task-01"}).reason, "task_cancelled")

    def test_replay_denied_after_first_allow(self):
        self.assertTrue(self.decide().allowed)
        self.assertEqual(self.decide().reason, "replayed_nonce")

    def test_exact_approval_required(self):
        r = dict(self.request, operation="report.write", resource="reports/draft", requires_approval=True)
        a = {"status": "approved", "company_id": "ai_revenue", "task_id": "task-01",
             "operation": "report.write", "resource": "reports/draft", "expires_at": 300,
             "single_use": True, "nonce": "nonce-01"}
        self.assertTrue(self.decide(request=r, approvals=[a]).allowed)
        self.assertEqual(self.decide(request=r, approvals=[a]).reason, "replayed_nonce")

    def test_mismatched_approval_denied(self):
        self.assertEqual(self.decide(request=dict(self.request, requires_approval=True)).reason,
                         "exact_owner_approval_missing_or_invalid")

    def test_trading_live_order_always_denied(self):
        i = dict(self.identity, company_id="trading_technology")
        p = dict(self.policy, company_id="trading_technology",
                 allowed_operations=["trade.live_order"], allowed_resource_prefixes=["orders/"])
        r = dict(self.request, company_id="trading_technology",
                 operation="trade.live_order", resource="orders/synthetic")
        self.assertEqual(self.decide(identity=i, policy=p, request=r).reason,
                         "live_financial_action_disabled")

    def test_trading_risk_controls_are_protected(self):
        i = dict(self.identity, company_id="trading_technology")
        p = dict(self.policy, company_id="trading_technology", allowed_operations=["risk.halt.change"])
        r = dict(self.request, company_id="trading_technology", operation="risk.halt.change")
        self.assertEqual(self.decide(identity=i, policy=p, request=r).reason,
                         "protected_control_plane_operation")

    def test_unverified_market_data_denied(self):
        self.assertEqual(self.decide(request=dict(self.request, operation="market_data.read")).reason,
                         "market_data_provenance_unverified")


if __name__ == "__main__":
    unittest.main()

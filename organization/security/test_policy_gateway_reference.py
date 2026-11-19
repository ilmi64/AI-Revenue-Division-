import unittest
from policy_gateway_reference import *

def setup(**kw):
 p=Principal("agent-1","revenue","operator","s-1",True,500)
 t=Task("task-1","revenue","agent-1",frozenset({"research.read","draft.create"}),
        frozenset({"market/public","draft/1"}),400,"v1")
 cfg=dict(identity_verifier=lambda p:True,approval_consumer=lambda *a:True,
          emergency_stop=lambda c:False,current_policy_version=lambda:"v1")
 cfg.update(kw)
 return PolicyGateway(**cfg),p,t
def req(**kw):
 d=dict(operation="research.read",resource="market/public",now=100,policy_version="v1")
 d.update(kw); return Request(**d)

class GatewayTests(unittest.TestCase):
 def test_allow_scoped_research(self):
  g,p,t=setup(); self.assertEqual(g.authorize(p,t,req()).outcome,"allow")
 def test_identity_unverified(self):
  g,p,t=setup(identity_verifier=lambda p:False)
  self.assertEqual(g.authorize(p,t,req()).reason,"identity_unverified")
 def test_inactive(self):
  g,p,t=setup(); p=Principal(p.agent_id,p.company_id,p.role,p.session_id,False,p.expires_at)
  self.assertEqual(g.authorize(p,t,req()).outcome,"deny")
 def test_expired_identity(self):
  g,p,t=setup(); self.assertEqual(g.authorize(p,t,req(now=500)).reason,"principal_inactive_or_expired")
 def test_expired_task(self):
  g,p,t=setup(); self.assertEqual(g.authorize(p,t,req(now=400)).reason,"task_expired")
 def test_cross_company(self):
  g,p,t=setup(); t=Task(t.task_id,"trading",t.assigned_agent_id,t.allowed_operations,t.allowed_resources,t.expires_at,"v1")
  self.assertEqual(g.authorize(p,t,req()).reason,"principal_task_company_mismatch")
 def test_wrong_assignee(self):
  g,p,t=setup(); t=Task(t.task_id,t.company_id,"agent-2",t.allowed_operations,t.allowed_resources,t.expires_at,"v1")
  self.assertEqual(g.authorize(p,t,req()).reason,"agent_not_assigned_to_task")
 def test_stale_policy(self):
  g,p,t=setup(); self.assertEqual(g.authorize(p,t,req(policy_version="old")).reason,"stale_policy_version")
 def test_emergency_stop(self):
  g,p,t=setup(emergency_stop=lambda c:True)
  self.assertEqual(g.authorize(p,t,req()).reason,"company_emergency_stop_active")
 def test_operation_escalation(self):
  g,p,t=setup(); self.assertEqual(g.authorize(p,t,req(operation="funds.transfer")).reason,"operation_outside_task_scope")
 def test_resource_escalation(self):
  g,p,t=setup(); self.assertEqual(g.authorize(p,t,req(resource="private/secret")).reason,"resource_outside_task_scope")
 def test_trading_live_order_denied_even_allowlisted(self):
  g,p,t=setup(); p=Principal("agent-1","trading","operator","s-1",True,500)
  t=Task("task-1","trading","agent-1",frozenset({"trade.live_order"}),frozenset({"account/1"}),400,"v1")
  self.assertEqual(g.authorize(p,t,req(operation="trade.live_order",resource="account/1")).reason,
                   "trading_live_or_risk_control_action_prohibited")
 def test_protected_policy_change_denied(self):
  g,p,t=setup(); self.assertEqual(g.authorize(p,t,req(operation="policy.modify")).reason,
                                  "protected_control_plane_operation")
 def test_approval_required(self):
  g,p,t=setup(approval_consumer=lambda *a:False)
  self.assertEqual(g.authorize(p,t,req(requires_owner_approval=True,approval_id="ap-1")).reason,
                   "owner_approval_invalid_or_unconsumed")
 def test_missing_approval(self):
  g,p,t=setup()
  self.assertEqual(g.authorize(p,t,req(requires_owner_approval=True)).reason,"owner_approval_missing")
 def test_dependency_failure_denies(self):
  g,p,t=setup(emergency_stop=lambda c:1/0)
  self.assertEqual(g.authorize(p,t,req()).reason,"policy_dependency_error_fail_closed")
if __name__=="__main__": unittest.main()

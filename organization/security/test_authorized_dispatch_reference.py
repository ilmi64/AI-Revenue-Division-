import json, unittest
from policy_gateway_reference import Principal, Task, Request, PolicyGateway
from outbox_dispatch_reference import Outbox, dispatch_one
from authorized_dispatch_reference import dispatch_authorized_one

class IntegrationTests(unittest.TestCase):
 def setUp(self):
  self.store=Outbox()
  self.principal=Principal("agent-1","revenue","operator","s-1",True,1000)
  self.task=Task("task-1","revenue","agent-1",frozenset({"draft.create"}),
                 frozenset({"draft/1"}),900,"v1")
  self.calls=[]; self.audits=[]
  self.gateway=PolicyGateway(identity_verifier=lambda p:True,
      approval_consumer=self.consume,emergency_stop=lambda c:False,
      current_policy_version=lambda:"v1")
 def consume(self,*args):
  self.calls.append("approval_consumed"); return True
 def payload(self, approved=False):
  return {"company_id":"revenue","agent_id":"agent-1","task_id":"task-1",
          "operation":"draft.create","resource":"draft/1","policy_version":"v1",
          "requires_owner_approval":approved,"approval_id":"ap-1" if approved else ""}
 def resolver(self, claim, payload, now):
  return (self.principal,self.task,Request(payload["operation"],payload["resource"],now,
      payload["policy_version"],payload["requires_owner_approval"],payload["approval_id"]))
 def run_one(self, payload, sender):
  self.store.enqueue("a1","idem-1",payload,10)
  return dispatch_authorized_one(store=self.store,worker="w1",now=20,
      gateway=self.gateway,context_resolver=self.resolver,sender=sender,
      dispatch_fn=dispatch_one,audit_fn=lambda *a:self.audits.append(a))
 def test_valid_action_consumes_approval_once_at_dispatch(self):
  sent=[]
  result=self.run_one(self.payload(True),lambda key,payload:sent.append((key,payload)) or {"ok":True})
  self.assertEqual(result,"sent_and_recorded")
  self.assertEqual(self.calls,["approval_consumed"])
  self.assertEqual(len(sent),1)
 def test_denial_never_calls_sender(self):
  self.gateway.emergency_stop=lambda c:True
  sent=[]
  result=self.run_one(self.payload(),lambda *a:sent.append(a))
  self.assertEqual(result,"denied_by_fresh_policy"); self.assertEqual(sent,[])
 def test_payload_identity_tamper_denied(self):
  payload=self.payload(); payload["agent_id"]="forged"
  sent=[]
  result=self.run_one(payload,lambda *a:sent.append(a))
  self.assertEqual(result,"denied_by_fresh_policy"); self.assertEqual(sent,[])
 def test_missing_fields_denied(self):
  payload=self.payload(); del payload["resource"]
  sent=[]
  result=self.run_one(payload,lambda *a:sent.append(a))
  self.assertEqual(result,"denied_by_fresh_policy"); self.assertEqual(sent,[])
 def test_approval_consumed_only_after_claim_and_at_gateway(self):
  self.assertEqual(self.run_one(self.payload(True),lambda *a:{"ok":True}),"sent_and_recorded")
  self.assertEqual(self.calls.count("approval_consumed"),1)
 def test_timeout_becomes_unknown_not_auto_retry(self):
  def timeout(*a): raise TimeoutError()
  result=self.run_one(self.payload(),timeout)
  self.assertEqual(result,"outcome_unknown_reconciliation_required")
  self.assertEqual(self.store.get("a1")["status"],"outcome_unknown")
 def test_audit_callback_failure_fails_closed(self):
  def broken_audit(*a): raise RuntimeError("audit down")
  self.store.enqueue("a2","idem-2",self.payload(),10)
  sent=[]
  result=dispatch_authorized_one(store=self.store,worker="w2",now=20,
      gateway=self.gateway,context_resolver=self.resolver,sender=lambda *a:sent.append(a),
      dispatch_fn=dispatch_one,audit_fn=broken_audit)
  self.assertEqual(result,"denied_by_fresh_policy"); self.assertEqual(sent,[])
 def tearDown(self): self.store.close()

if __name__=="__main__": unittest.main()

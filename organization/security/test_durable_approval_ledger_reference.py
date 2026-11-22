import os, tempfile, threading, unittest
from durable_approval_ledger_reference import DurableApprovalLedger

class LedgerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.path=os.path.join(self.tmp.name,"ledger.db")
  self.db=DurableApprovalLedger(self.path)
  self.db.issue(approval_id="ap1",nonce="n1",owner_id="owner",company_id="revenue",
   agent_id="agent",session_id="s1",task_id="t1",operation="draft.publish",
   resource="draft/7",policy_version="p1",expires_at=500,created_at=10,amount_limit_minor=2500)
 def kwargs(self,**over):
  d=dict(company_id="revenue",owner_id="owner",agent_id="agent",session_id="s1",
   task_id="t1",operation="draft.publish",resource="draft/7",policy_version="p1",
   action_id="act1",now=100,amount_minor=2000)
  d.update(over); return d
 def test_exact_scope_consumes_once_and_audits(self):
  r=self.db.consume("ap1",**self.kwargs())
  self.assertTrue(r.allowed); self.assertEqual(self.db.count_consumptions("ap1"),1)
  self.assertEqual(self.db.count_audit("revenue","approval_consumed"),1)
  self.assertTrue(self.db.verify_audit("revenue"))
 def test_replay_rejected(self):
  self.assertTrue(self.db.consume("ap1",**self.kwargs()).allowed)
  self.assertFalse(self.db.consume("ap1",**self.kwargs(action_id="act2")).allowed)
  self.assertEqual(self.db.count_consumptions("ap1"),1)
 def test_scope_mismatch(self):
  r=self.db.consume("ap1",**self.kwargs(company_id="trading"))
  self.assertEqual(r.reason,"approval_scope_mismatch")
 def test_expired(self):
  r=self.db.consume("ap1",**self.kwargs(now=500))
  self.assertEqual(r.reason,"approval_expired")
 def test_revoked(self):
  self.assertTrue(self.db.revoke("ap1",company_id="revenue",now=20))
  self.assertEqual(self.db.consume("ap1",**self.kwargs()).reason,"approval_revoked")
 def test_amount_ceiling(self):
  self.assertEqual(self.db.consume("ap1",**self.kwargs(amount_minor=2501)).reason,
                   "amount_limit_exceeded")
 def test_company_streams_are_separate(self):
  self.db.issue(approval_id="ap2",nonce="n2",owner_id="owner",company_id="trading",
   agent_id="agent",session_id="s2",task_id="t2",operation="research.read",
   resource="market/public",policy_version="p1",expires_at=500,created_at=11)
  self.assertTrue(self.db.verify_audit("revenue")); self.assertTrue(self.db.verify_audit("trading"))
 def test_two_connections_only_one_winner(self):
  other=DurableApprovalLedger(self.path); barrier=threading.Barrier(2); results=[]
  def run(db, action):
   barrier.wait()
   results.append(db.consume("ap1",**self.kwargs(action_id=action)))
  a=threading.Thread(target=run,args=(self.db,"act-a"))
  b=threading.Thread(target=run,args=(other,"act-b"))
  a.start(); b.start(); a.join(); b.join()
  self.assertEqual(sum(r.allowed for r in results),1)
  self.assertEqual(self.db.count_consumptions("ap1"),1)
  other.close()
 def test_restart_persists_consumption(self):
  self.assertTrue(self.db.consume("ap1",**self.kwargs()).allowed)
  self.db.close(); self.db=DurableApprovalLedger(self.path)
  self.assertEqual(self.db.consume("ap1",**self.kwargs(action_id="act2")).reason,
                   "approval_replay_or_action_duplicate")
 def test_revocation_audit_chain(self):
  self.db.revoke("ap1",company_id="revenue",now=20)
  self.assertEqual(self.db.count_audit("revenue","approval_revoked"),1)
  self.assertTrue(self.db.verify_audit("revenue"))
 def test_failed_audit_rolls_back_consumption(self):
  self.db.execute_for_test = None
  self.db.db.execute("CREATE TRIGGER fail_consume_audit BEFORE INSERT ON approval_audit "
                     "WHEN NEW.event_type='approval_consumed' BEGIN SELECT RAISE(ABORT,'audit unavailable'); END")
  with self.assertRaises(Exception):
   self.db.consume("ap1",**self.kwargs())
  self.assertEqual(self.db.count_consumptions("ap1"),0)
  self.assertTrue(self.db.verify_audit("revenue"))
 def tearDown(self):
  try:self.db.close()
  except:pass
  self.tmp.cleanup()

if __name__=="__main__": unittest.main()

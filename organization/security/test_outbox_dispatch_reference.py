import tempfile, os, unittest
from outbox_dispatch_reference import Outbox, dispatch_one

class OutboxTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.NamedTemporaryFile(delete=False); self.tmp.close()
  self.s=Outbox(self.tmp.name,max_attempts=2)
  self.s.enqueue("a1","idem-1",{"kind":"synthetic"},10)
 def tearDown(self):
  self.s.close(); os.unlink(self.tmp.name)
 def test_claim_and_complete_idempotently(self):
  c=self.s.claim("w1",11); self.assertEqual(c.attempt,1)
  self.assertEqual(self.s.complete("a1","w1",{"ok":True},12),"completed")
  self.assertEqual(self.s.complete("a1","w1",{"ok":True},13),"already_completed_same_result")
 def test_conflicting_intent_same_idempotency_key(self):
  with self.assertRaises(ValueError): self.s.enqueue("a2","idem-1",{"different":1},11)
 def test_expired_lease_not_reissued_blindly(self):
  self.s.claim("w1",11,lease_seconds=1)
  self.assertIsNone(self.s.claim("w2",99))
  self.assertEqual(self.s.get("a1")["status"],"leased")
 def test_wrong_worker_cannot_complete(self):
  self.s.claim("w1",11)
  with self.assertRaises(ValueError): self.s.complete("a1","w2",{},12)
 def test_timeout_enters_unknown(self):
  r=dispatch_one(self.s,"w1",11,lambda c:True,lambda k,p:(_ for _ in ()).throw(TimeoutError()))
  self.assertEqual(r,"outcome_unknown_reconciliation_required")
  self.assertEqual(self.s.get("a1")["status"],"outcome_unknown")
 def test_unknown_requires_evidence_before_retry(self):
  self.s.claim("w1",11); self.s.mark_uncertain("a1","w1",12,"crash")
  with self.assertRaises(ValueError): self.s.retry_after_confirmed_no_effect("a1",13,"")
  self.s.retry_after_confirmed_no_effect("a1",14,"recon-123")
  self.assertEqual(self.s.get("a1")["status"],"pending")
 def test_policy_rechecked_before_sender(self):
  called=[]
  r=dispatch_one(self.s,"w1",11,lambda c:False,lambda k,p:called.append(1))
  self.assertEqual(r,"denied_by_fresh_policy"); self.assertEqual(called,[])
  self.assertEqual(self.s.get("a1")["status"],"cancelled")
 def test_cancel_pending(self):
  self.assertTrue(self.s.cancel("a1",11)); self.assertFalse(self.s.cancel("a1",12))
 def test_persistent_restart(self):
  self.s.claim("w1",11); self.s.close()
  self.s=Outbox(self.tmp.name,max_attempts=2)
  self.assertEqual(self.s.get("a1")["status"],"leased")
 def test_retry_limit(self):
  self.s.claim("w1",11); self.s.mark_uncertain("a1","w1",12,"timeout")
  self.s.retry_after_confirmed_no_effect("a1",13,"proof-1")
  self.s.claim("w2",14); self.s.mark_uncertain("a1","w2",15,"timeout")
  self.s.retry_after_confirmed_no_effect("a1",16,"proof-2")
  self.assertEqual(self.s.get("a1")["status"],"failed")
if __name__=="__main__": unittest.main()

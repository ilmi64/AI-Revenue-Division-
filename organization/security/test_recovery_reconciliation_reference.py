import unittest
from recovery_reconciliation_reference import *

class FakeStore:
 def __init__(self):
  self.data={"x":{"status":"outcome_unknown","idempotency_key":"idem-x"}}
  self.resolved=[]
 def get(self,k): return self.data.get(k)
 def resolve_unknown(self,k,outcome,digest,now):
  self.resolved.append((k,outcome,digest,now))
  self.data[k]["status"]="resolved_"+outcome

def ev(**kw):
 d=dict(action_id="x",idempotency_key="idem-x",checked_at=100,source="receiver-ledger",
        outcome="confirmed_not_applied",evidence_digest="sha256:abc",authenticated=True)
 d.update(kw); return ReconciliationEvidence(**d)

class RecoveryTests(unittest.TestCase):
 def setUp(self): self.s=FakeStore()
 def test_authoritative_not_applied_closes_old_action(self):
  r=reconcile_unknown_action(store=self.s,action_id="x",evidence=ev(),now=110)
  self.assertEqual(r.status,"resolved_not_applied_new_intent_required")
  self.assertEqual(self.s.data["x"]["status"],"resolved_confirmed_not_applied")
 def test_applied_is_marked_not_resent(self):
  r=reconcile_unknown_action(store=self.s,action_id="x",evidence=ev(outcome="confirmed_applied"),now=110)
  self.assertEqual(r.status,"resolved_applied")
 def test_inconclusive_quarantined(self):
  self.assertEqual(reconcile_unknown_action(store=self.s,action_id="x",evidence=ev(outcome="inconclusive"),now=110).status,"quarantined")
 def test_unauthenticated_evidence_quarantined(self):
  self.assertEqual(reconcile_unknown_action(store=self.s,action_id="x",evidence=ev(authenticated=False),now=110).status,"quarantined")
 def test_wrong_idempotency_key_quarantined(self):
  self.assertEqual(reconcile_unknown_action(store=self.s,action_id="x",evidence=ev(idempotency_key="other"),now=110).status,"quarantined")
 def test_stale_evidence_quarantined(self):
  self.assertEqual(reconcile_unknown_action(store=self.s,action_id="x",evidence=ev(checked_at=1),now=500).status,"quarantined")
 def test_future_evidence_quarantined(self):
  self.assertEqual(reconcile_unknown_action(store=self.s,action_id="x",evidence=ev(checked_at=200),now=100).status,"quarantined")
 def test_already_resolved_not_replayed(self):
  self.s.data["x"]["status"]="sent_and_recorded"
  self.assertEqual(reconcile_unknown_action(store=self.s,action_id="x",evidence=ev(),now=110).reason,"action_not_in_unknown_state")
 def test_missing_action_denied(self):
  self.assertEqual(reconcile_unknown_action(store=self.s,action_id="missing",evidence=ev(action_id="missing"),now=110).status,"denied")
 def test_missing_digest_quarantined(self):
  self.assertEqual(reconcile_unknown_action(store=self.s,action_id="x",evidence=ev(evidence_digest=""),now=110).status,"quarantined")
 def test_store_error_quarantined(self):
  class Broken:
   def get(self,k): raise RuntimeError()
  self.assertEqual(reconcile_unknown_action(store=Broken(),action_id="x",evidence=ev(),now=110).status,"quarantined")
 def test_restore_manifest_checks_consumption(self):
  class Ledger:
   def verify_audit(self,c): return True
   def count_consumptions(self,a): return 1
  self.assertEqual(verify_backup_restore(restored_ledger=Ledger(),expected_company="revenue",
       expected_audit_valid=True,expected_consumed_approval_ids=["ap1"]).status,"passed")
 def test_restore_detects_missing_consumption(self):
  class Ledger:
   def verify_audit(self,c): return True
   def count_consumptions(self,a): return 0
  self.assertEqual(verify_backup_restore(restored_ledger=Ledger(),expected_company="revenue",
       expected_audit_valid=True,expected_consumed_approval_ids=["ap1"]).status,"failed")
if __name__=="__main__": unittest.main()

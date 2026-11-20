import hashlib, os, sqlite3, tempfile, threading, unittest
from atomic_evidence_reconciliation_reference import (
    SQLiteAtomicReconciliationStore, ReconciliationError, EvidenceReplayError)
from receiver_evidence_verifier_reference import ReceiverEvidenceVerifier

class AtomicEvidenceReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,"state.sqlite")
        self.store=SQLiteAtomicReconciliationStore(self.path)
        self.store.register_unknown_action(action_id="a1",company="coA",
            receiver_account="acct1",idempotency_key="idem1")
        self.verifier=ReceiverEvidenceVerifier(
            lambda issuer,payload,signature: issuer=="receiver-A" and
              signature==hashlib.sha256(payload).hexdigest(),
            {"receiver-A"},max_age_seconds=300,future_skew_seconds=30)
    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()
    def evidence(self, *, eid="ev1", nonce="n1", outcome="applied", **overrides):
        e={"evidence_id":eid,"issuer":"receiver-A","audience":"recovery-gateway",
           "company":"coA","action_id":"a1","receiver_account":"acct1",
           "idempotency_key":"idem1","outcome":outcome,"observed_at":100,
           "nonce":nonce,"signature":""}
        e.update(overrides)
        e["signature"]=hashlib.sha256(
            ReceiverEvidenceVerifier.canonical_signed_payload(e)).hexdigest()
        return e
    def verify(self,e):
        return self.verifier.verify(e,expected={"company":"coA","action_id":"a1",
            "receiver_account":"acct1","idempotency_key":"idem1",
            "audience":"recovery-gateway"},now=101)
    def reconcile(self,e):
        return self.store.reconcile(action_id="a1",evidence=e,verified=self.verify(e),now=102)
    def test_atomic_receipt_state_and_audit(self):
        self.assertEqual(self.reconcile(self.evidence()),"reconciled_applied")
        self.assertEqual(self.store.action_state("a1"),"reconciled_applied")
        self.assertTrue(self.store.verify_audit("coA"))
        self.assertEqual(self.store.db.execute("select count(*) from evidence_receipts").fetchone()[0],1)
    def test_retry_after_commit_is_idempotent(self):
        e=self.evidence()
        self.assertEqual(self.reconcile(e),"reconciled_applied")
        self.assertEqual(self.store.reconcile(action_id="a1",evidence=e,
            verified=self.verify(e),now=103),"duplicate_same_result")
        self.assertEqual(self.store.db.execute("select count(*) from audit").fetchone()[0],1)
    def test_audit_failure_rolls_back_receipt_and_state_then_retry_succeeds(self):
        e=self.evidence()
        self.store.db.execute("""CREATE TRIGGER reject_audit BEFORE INSERT ON audit
          BEGIN SELECT RAISE(ABORT,'audit unavailable'); END;""")
        with self.assertRaises(sqlite3.IntegrityError): self.reconcile(e)
        self.assertEqual(self.store.action_state("a1"),"outcome_unknown")
        self.assertEqual(self.store.db.execute("select count(*) from evidence_receipts").fetchone()[0],0)
        self.store.db.execute("DROP TRIGGER reject_audit")
        self.assertEqual(self.reconcile(e),"reconciled_applied")
    def test_nonce_replay_with_new_evidence_id_rejected(self):
        self.reconcile(self.evidence())
        e=self.evidence(eid="ev2",nonce="n1")
        with self.assertRaises(EvidenceReplayError): self.reconcile(e)
    def test_evidence_id_replay_with_new_nonce_rejected(self):
        self.reconcile(self.evidence())
        e=self.evidence(eid="ev1",nonce="n2")
        with self.assertRaises(EvidenceReplayError): self.reconcile(e)
    def test_same_evidence_cannot_be_rebound_to_other_action(self):
        self.reconcile(self.evidence())
        self.store.register_unknown_action(action_id="a2",company="coA",
            receiver_account="acct1",idempotency_key="idem2")
        e=self.evidence(eid="ev2",nonce="n2",action_id="a2",idempotency_key="idem2")
        v=self.verifier.verify(e,expected={"company":"coA","action_id":"a2",
            "receiver_account":"acct1","idempotency_key":"idem2",
            "audience":"recovery-gateway"},now=101)
        with self.assertRaises(EvidenceReplayError): self.store.reconcile(
            action_id="a2",evidence=self.evidence(eid="ev1",nonce="n1",action_id="a2",
              idempotency_key="idem2"),verified=v,now=102)
    def test_digest_mutation_between_verify_and_commit_rejected(self):
        e=self.evidence()
        v=self.verify(e)
        changed=dict(e,nonce="changed")
        with self.assertRaisesRegex(ReconciliationError,"digest_mismatch"):
            self.store.reconcile(action_id="a1",evidence=changed,verified=v,now=102)
    def test_verified_claim_cannot_be_swapped_between_payloads(self):
        e1=self.evidence()
        e2=self.evidence(eid="ev2",nonce="n2")
        with self.assertRaises(ReconciliationError):
            self.store.reconcile(action_id="a1",evidence=e2,verified=self.verify(e1),now=102)
    def test_scope_mismatch_rejected(self):
        e=self.evidence(receiver_account="other")
        with self.assertRaises(Exception): self.reconcile(e)
        self.assertEqual(self.store.action_state("a1"),"outcome_unknown")
    def test_inconclusive_quarantines_atomically(self):
        self.assertEqual(self.reconcile(self.evidence(outcome="inconclusive")),"quarantined")
        self.assertEqual(self.store.action_state("a1"),"quarantined")
        self.assertTrue(self.store.verify_audit("coA"))
    def test_not_applied_closes_old_action(self):
        self.assertEqual(self.reconcile(self.evidence(outcome="not_applied")),"reconciled_not_applied")
    def test_two_connections_only_one_reconciliation_commits(self):
        e=self.evidence()
        verified=self.verify(e)
        barrier=threading.Barrier(2)
        outcomes=[]
        def worker():
            db=SQLiteAtomicReconciliationStore(self.path)
            barrier.wait()
            try:
                outcomes.append(db.reconcile(action_id="a1",evidence=e,verified=verified,now=102))
            except (EvidenceReplayError,ReconciliationError):
                outcomes.append("denied")
            finally: db.close()
        threads=[threading.Thread(target=worker) for _ in range(2)]
        [t.start() for t in threads]
        [t.join(timeout=5) for t in threads]
        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertEqual(outcomes.count("reconciled_applied"),1)
        self.assertEqual(outcomes.count("duplicate_same_result"),1)
        self.assertEqual(self.store.db.execute("select count(*) from evidence_receipts").fetchone()[0],1)
        self.assertTrue(self.store.verify_audit("coA"))

if __name__=="__main__": unittest.main()

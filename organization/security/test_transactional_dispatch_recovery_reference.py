import hashlib, os, sqlite3, tempfile, threading, unittest
from transactional_dispatch_recovery_reference import DispatchStore
from receiver_evidence_verifier_reference import ReceiverEvidenceVerifier, EvidenceError

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,"state.db")
        self.s=DispatchStore(self.path)
        self.s.issue_approval(approval_id="ap1",company="coA",agent="ag1",task="t1",
          operation="publish",resource="listing/1",policy="v1",expires=1000,now=1)
        self.s.enqueue(action_id="ac1",company="coA",approval_id="ap1",
          idempotency_key="idem1",intent={"listing":"1","price_minor":1200,"receiver_account":"acct1"},now=2)
    def tearDown(self):
        self.s.close(); self.tmp.cleanup()
    @staticmethod
    def receiver_evidence(evidence_id, **overrides):
        evidence={"evidence_id":evidence_id,"company":"coA","action_id":"ac1",
                  "idempotency_key":"idem1","receiver_account":"acct1","audience":"recovery-gateway"}
        evidence.update(overrides)
        return evidence
    @staticmethod
    def fake_verifier(outcome):
        # Test double only: model the trusted verifier's exact action binding.
        def verify(evidence, *, expected, now):
            if any(evidence.get(key)!=value for key,value in expected.items()):
                return {"verified":False}
            return {"verified":True,"outcome":outcome,"evidence_id":evidence["evidence_id"],
                    "issuer":"test-receiver","observed_at":now,"payload_sha256":"0"*64}
        return verify
    def signed_receiver_evidence(self, evidence_id="ev-real", **overrides):
        evidence={"evidence_id":evidence_id,"issuer":"receiver-A","audience":"recovery-gateway",
          "company":"coA","action_id":"ac1","receiver_account":"acct1",
          "idempotency_key":"idem1","outcome":"applied","observed_at":5,
          "nonce":"nonce-"+evidence_id,"signature":""}
        evidence.update(overrides)
        evidence["signature"]=hashlib.sha256(
          ReceiverEvidenceVerifier.canonical_signed_payload(evidence)).hexdigest()
        return evidence
    @staticmethod
    def real_verifier():
        # Deterministic digest callback is a test fixture, not production cryptography.
        return ReceiverEvidenceVerifier(
          lambda issuer,payload,signature: issuer=="receiver-A" and
            signature==hashlib.sha256(payload).hexdigest(),
          {"receiver-A"},max_age_seconds=300,future_skew_seconds=30)

    def start(self):
        return self.s.authorize_and_start("ac1",company="coA",agent="ag1",task="t1",
          operation="publish",resource="listing/1",policy="v1",now=3)
    def test_atomic_start_consumes_once(self):
        self.assertTrue(self.start()["allowed"])
        self.assertEqual(self.s.action_state("ac1"),"dispatch_started")
        self.assertEqual(self.s.db.execute("select count(*) from consumed").fetchone()[0],1)
    def test_revoke_before_start_blocks(self):
        self.assertTrue(self.s.revoke("ap1",company="coA",now=3))
        self.assertEqual(self.start()["reason"],"approval_revoked")
        self.assertEqual(self.s.action_state("ac1"),"queued")
    def test_start_wins_then_revoke_cannot_undo_remote(self):
        self.assertTrue(self.start()["allowed"])
        self.assertTrue(self.s.revoke("ap1",company="coA",now=4))
        self.assertEqual(self.s.action_state("ac1"),"dispatch_started")
    def test_company_boundary(self):
        r=self.s.authorize_and_start("ac1",company="coB",agent="ag1",task="t1",
          operation="publish",resource="listing/1",policy="v1",now=3)
        self.assertFalse(r["allowed"])
    def test_scope_mismatch(self):
        r=self.s.authorize_and_start("ac1",company="coA",agent="ag1",task="other",
          operation="publish",resource="listing/1",policy="v1",now=3)
        self.assertEqual(r["reason"],"approval_scope_mismatch")
    def test_expired(self):
        r=self.s.authorize_and_start("ac1",company="coA",agent="ag1",task="t1",
          operation="publish",resource="listing/1",policy="v1",now=1000)
        self.assertEqual(r["reason"],"approval_expired")
    def test_duplicate_enqueue_is_idempotent(self):
        self.assertEqual(self.s.enqueue(action_id="ac1",company="coA",approval_id="ap1",
          idempotency_key="idem1",intent={"listing":"1","price_minor":1200},now=4),
          "duplicate_same_intent")
    def test_conflicting_idempotency_rejected(self):
        with self.assertRaises(ValueError):
            self.s.enqueue(action_id="ac2",company="coA",approval_id="ap1",
              idempotency_key="idem1",intent={"listing":"2"},now=4)
    def test_timeout_becomes_unknown(self):
        self.start()
        self.assertEqual(self.s.record_sender_result("ac1",result="timeout",now=4),"outcome_unknown")
    def test_unknown_cannot_be_restarted(self):
        self.start(); self.s.record_sender_result("ac1",result="timeout",now=4)
        self.assertEqual(self.start()["reason"],"action_not_queued")
    def test_applied_reconciliation_terminal(self):
        self.start(); self.s.record_sender_result("ac1",result="timeout",now=4)
        self.assertEqual(self.s.reconcile("ac1",evidence=self.receiver_evidence("ev1"),evidence_verifier=self.fake_verifier("applied"),now=6),"reconciled_applied")
    def test_not_applied_does_not_reuse_old_authorization(self):
        self.start(); self.s.record_sender_result("ac1",result="timeout",now=4)
        self.s.reconcile("ac1",evidence=self.receiver_evidence("ev2"),evidence_verifier=self.fake_verifier("not_applied"),now=6)
        self.assertEqual(self.start()["reason"],"action_not_queued")
    def test_inconclusive_quarantines(self):
        self.start(); self.s.record_sender_result("ac1",result="exception",now=4)
        self.assertEqual(self.s.reconcile("ac1",evidence=self.receiver_evidence("ev3"),evidence_verifier=self.fake_verifier("inconclusive"),now=6),"quarantined")
    def test_reconciliation_uses_real_verifier_object_and_receiver_binding(self):
        self.start()
        self.s.record_sender_result("ac1",result="timeout",now=4)
        verifier=self.real_verifier()
        self.assertEqual(self.s.reconcile("ac1",evidence=self.signed_receiver_evidence(),
          evidence_verifier=verifier,now=6),"reconciled_applied")

    def test_real_verifier_rejects_wrong_receiver_account(self):
        self.start()
        self.s.record_sender_result("ac1",result="timeout",now=4)
        verifier=self.real_verifier()
        wrong=self.signed_receiver_evidence("ev-wrong-account",receiver_account="acct-other")
        with self.assertRaises(EvidenceError):
            self.s.reconcile("ac1",evidence=wrong,evidence_verifier=verifier,now=6)
        self.assertEqual(self.s.action_state("ac1"),"outcome_unknown")

    def test_wrong_action_binding_is_rejected(self):
        self.start(); self.s.record_sender_result("ac1",result="timeout",now=4)
        wrong=self.receiver_evidence("ev-wrong",action_id="different-action")
        with self.assertRaisesRegex(ValueError,"receiver_evidence_not_verified"):
            self.s.reconcile("ac1",evidence=wrong,
                evidence_verifier=self.fake_verifier("applied"),now=6)

    def test_action_identity_rechecked_after_verification(self):
        self.start(); self.s.record_sender_result("ac1",result="timeout",now=4)
        valid=self.fake_verifier("applied")
        def mutate_then_verify(evidence, *, expected, now):
            # Simulate an identity change between pre-verification read and commit.
            self.s.db.execute("UPDATE actions SET idem='tampered-idem' WHERE id='ac1'")
            return valid(evidence,expected=expected,now=now)
        with self.assertRaisesRegex(ValueError,"action_identity_changed_during_verification"):
            self.s.reconcile("ac1",evidence=self.receiver_evidence("ev-race"),
                evidence_verifier=mutate_then_verify,now=6)
        self.assertEqual(self.s.action_state("ac1"),"outcome_unknown")

    def test_unauthenticated_evidence_rejected(self):
        self.start(); self.s.record_sender_result("ac1",result="timeout",now=4)
        with self.assertRaises(ValueError):
            self.s.reconcile("ac1",evidence=self.receiver_evidence("ev4"),evidence_verifier=lambda *a,**k: (_ for _ in ()).throw(ValueError("bad_signature")),now=6)
    def test_audit_and_online_backup_restore(self):
        self.start(); self.s.record_sender_result("ac1",result="accepted",now=4)
        backup=os.path.join(self.tmp.name,"backup.db")
        self.s.backup_to(backup)
        restored=DispatchStore(backup)
        try:
            self.assertTrue(restored.integrity_ok())
            self.assertTrue(restored.verify_audit("coA"))
            self.assertEqual(restored.action_state("ac1"),"sent")
        finally: restored.close()
    def test_audit_failure_rolls_back_approval_and_dispatch_state(self):
        self.s.db.execute("""CREATE TRIGGER reject_dispatch_audit
          BEFORE INSERT ON audit WHEN NEW.kind='dispatch_started'
          BEGIN SELECT RAISE(ABORT, 'audit unavailable'); END;""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.start()
        self.assertEqual(self.s.action_state("ac1"),"queued")
        self.assertEqual(self.s.db.execute("select count(*) from consumed").fetchone()[0],0)

    def test_two_workers_race_one_approval_exactly_one_wins(self):
        barrier=threading.Barrier(2)
        results=[]
        errors=[]
        def worker():
            store=None
            try:
                store=DispatchStore(self.path)  # create SQLite connection in owning thread
                barrier.wait()
                results.append(store.authorize_and_start("ac1",company="coA",agent="ag1",
                  task="t1",operation="publish",resource="listing/1",policy="v1",now=3))
            except Exception as exc:
                errors.append(exc)
            finally:
                if store is not None: store.close()
        threads=[threading.Thread(target=worker) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=5)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(errors,[])
        self.assertEqual(sum(1 for result in results if result["allowed"]),1)
        self.assertEqual(self.s.db.execute("select count(*) from consumed").fetchone()[0],1)
        self.assertEqual(self.s.action_state("ac1"),"dispatch_started")
        self.assertTrue(self.s.verify_audit("coA"))

    def test_revocation_and_dispatch_race_has_one_serialized_winner(self):
        barrier=threading.Barrier(2)
        outcomes=[]
        errors=[]
        def authorize():
            store=None
            try:
                store=DispatchStore(self.path)
                barrier.wait()
                outcomes.append(("authorize",store.authorize_and_start("ac1",company="coA",
                  agent="ag1",task="t1",operation="publish",resource="listing/1",
                  policy="v1",now=3)))
            except Exception as exc: errors.append(exc)
            finally:
                if store is not None: store.close()
        def revoke():
            store=None
            try:
                store=DispatchStore(self.path)
                barrier.wait()
                outcomes.append(("revoke",store.revoke("ap1",company="coA",now=3)))
            except Exception as exc: errors.append(exc)
            finally:
                if store is not None: store.close()
        threads=[threading.Thread(target=authorize),threading.Thread(target=revoke)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=5)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(errors,[])
        auth=dict(outcomes)["authorize"]
        revoked=dict(outcomes)["revoke"]
        if auth["allowed"]:
            self.assertEqual(self.s.action_state("ac1"),"dispatch_started")
            self.assertTrue(revoked)
            self.assertEqual(self.s.db.execute("select count(*) from consumed").fetchone()[0],1)
        else:
            self.assertEqual(auth["reason"],"approval_revoked")
            self.assertTrue(revoked)
            self.assertEqual(self.s.action_state("ac1"),"queued")
            self.assertEqual(self.s.db.execute("select count(*) from consumed").fetchone()[0],0)
        self.assertTrue(self.s.verify_audit("coA"))

    def test_audit_tamper_detected(self):
        self.start()
        self.s.db.execute("update audit set payload='{}' where kind='dispatch_started'")
        self.assertFalse(self.s.verify_audit("coA"))

if __name__=="__main__": unittest.main()

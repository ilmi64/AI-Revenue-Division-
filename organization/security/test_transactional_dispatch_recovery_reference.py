import os, sqlite3, tempfile, threading, unittest
from transactional_dispatch_recovery_reference import DispatchStore

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,"state.db")
        self.s=DispatchStore(self.path)
        self.s.issue_approval(approval_id="ap1",company="coA",agent="ag1",task="t1",
          operation="publish",resource="listing/1",policy="v1",expires=1000,now=1)
        self.s.enqueue(action_id="ac1",company="coA",approval_id="ap1",
          idempotency_key="idem1",intent={"listing":"1","price_minor":1200},now=2)
    def tearDown(self):
        self.s.close(); self.tmp.cleanup()
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
        self.assertEqual(self.s.reconcile("ac1",outcome="applied",evidence_id="ev1",
          source="receiver",observed_at=5,authenticated=True,now=6),"reconciled_applied")
    def test_not_applied_does_not_reuse_old_authorization(self):
        self.start(); self.s.record_sender_result("ac1",result="timeout",now=4)
        self.s.reconcile("ac1",outcome="not_applied",evidence_id="ev2",
          source="receiver",observed_at=5,authenticated=True,now=6)
        self.assertEqual(self.start()["reason"],"action_not_queued")
    def test_inconclusive_quarantines(self):
        self.start(); self.s.record_sender_result("ac1",result="exception",now=4)
        self.assertEqual(self.s.reconcile("ac1",outcome="inconclusive",evidence_id="ev3",
          source="receiver",observed_at=5,authenticated=True,now=6),"quarantined")
    def test_unauthenticated_evidence_rejected(self):
        self.start(); self.s.record_sender_result("ac1",result="timeout",now=4)
        with self.assertRaises(ValueError):
            self.s.reconcile("ac1",outcome="applied",evidence_id="ev4",
              source="unknown",observed_at=5,authenticated=False,now=6)
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
        second=DispatchStore(self.path)
        barrier=threading.Barrier(2)
        results=[]
        errors=[]
        def worker(store):
            try:
                barrier.wait()
                results.append(store.authorize_and_start("ac1",company="coA",agent="ag1",
                  task="t1",operation="publish",resource="listing/1",policy="v1",now=3))
            except Exception as exc:
                errors.append(exc)
        threads=[threading.Thread(target=worker,args=(store,)) for store in (self.s,second)]
        try:
            for thread in threads: thread.start()
            for thread in threads: thread.join(timeout=5)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(errors,[])
            self.assertEqual(sum(1 for result in results if result["allowed"]),1)
            self.assertEqual(self.s.db.execute("select count(*) from consumed").fetchone()[0],1)
            self.assertEqual(self.s.action_state("ac1"),"dispatch_started")
            self.assertTrue(self.s.verify_audit("coA"))
        finally:
            second.close()

    def test_audit_tamper_detected(self):
        self.start()
        self.s.db.execute("update audit set payload='{}' where kind='dispatch_started'")
        self.assertFalse(self.s.verify_audit("coA"))

if __name__=="__main__": unittest.main()

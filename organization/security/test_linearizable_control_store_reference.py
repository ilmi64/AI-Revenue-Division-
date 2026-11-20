"""Synthetic local tests for the unified recovery/dispatch transaction boundary."""
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from linearizable_control_store_reference import (
    ACTIVE, DISABLED, QUARANTINED, ControlStoreError, LinearizableControlStore
)


class Verifier:
    def __init__(self, claims): self.claims=claims
    def verify(self, document, *, expected, now):
        if document!="synthetic-signed-document": return {"verified":False}
        return {**expected,**self.claims,"verified":True}


class ControlStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/"control.sqlite")
        self.db=LinearizableControlStore(self.path)
        self.db.register_stream(company="co-a",stream="primary",now=1)
        self._release("bootstrap","a"*64,2)
        self._approval_and_action()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _release(self, incident, checkpoint, now):
        self.db.quarantine(company="co-a",stream="primary",incident_id=incident,
            reason="synthetic setup",checkpoint_digest=checkpoint,now=now)
        owner=Verifier({"approval_id":"owner-"+incident,"nonce":"nonce-"+incident,"expires_at":900})
        assessor=Verifier({"assessment_digest":"assessment-"+incident,"expires_at":900,
            "db_integrity":True,"audit_chain_valid":True,"checkpoint_match":True,
            "revocations_current":True,"emergency_stop_clear":True,"unknown_actions_reconciled":True})
        self.db.release_stream(company="co-a",stream="primary",incident_id=incident,
            checkpoint_digest=checkpoint,owner_approval="synthetic-signed-document",
            recovery_assessment="synthetic-signed-document",owner_verifier=owner,
            assessment_verifier=assessor,now=now+1)

    def _approval_and_action(self, aid="approval-1", action="action-1", idem="idem-1", task="task-1", now=3):
        self.db.issue_approval(approval_id=aid,company="co-a",stream="primary",agent="agent-a",
            task=task,operation="publish",resource="catalog/item",policy_version="v1",
            expires_at=1000,now=now)
        self.db.enqueue(action_id=action,company="co-a",stream="primary",approval_id=aid,
            idempotency_key=idem,intent={"receiver_account":"synthetic-sink","amount_minor":5},now=now)

    def _authorize(self, db=None, action="action-1", task="task-1", company="co-a"):
        db=db or self.db
        return db.authorize_and_start(action,company=company,stream="primary",agent="agent-a",
            task=task,operation="publish",resource="catalog/item",policy_version="v1",now=20)

    def test_approval_requires_registered_company_stream(self):
        with self.assertRaises(ControlStoreError):
            self.db.issue_approval(approval_id="orphan",company="co-missing",stream="missing",
                agent="agent-a",task="task-x",operation="publish",resource="catalog/item",
                policy_version="v1",expires_at=1000,now=3)

    def test_new_stream_defaults_disabled(self):
        self.db.register_stream(company="co-b",stream="new",now=1)
        self.assertEqual(self.db.stream_state("co-b","new")["status"],DISABLED)

    def test_valid_dispatch_consumes_approval_and_starts_action(self):
        self.assertTrue(self._authorize()["allowed"])
        self.assertEqual(self.db.action_state("action-1"),"dispatch_started")
        with self.assertRaises(ControlStoreError): self._authorize()

    def test_quarantine_blocks_dispatch(self):
        self.db.quarantine(company="co-a",stream="primary",incident_id="inc",reason="test",
            checkpoint_digest="b"*64,now=21)
        self.assertEqual(self._authorize()["reason"],"stream_not_active")
        self.assertEqual(self.db.action_state("action-1"),"queued")

    def test_quarantine_then_release_fences_old_action(self):
        self.db.quarantine(company="co-a",stream="primary",incident_id="inc",reason="test",
            checkpoint_digest="b"*64,now=21)
        self._release("inc","b"*64,22)
        self.assertEqual(self._authorize()["reason"],"stale_recovery_epoch")

    def test_enqueue_during_quarantine_is_fenced_after_release(self):
        self.db.quarantine(company="co-a",stream="primary",incident_id="inc",reason="test",
            checkpoint_digest="b"*64,now=21)
        self._approval_and_action("approval-2","action-2","idem-2","task-2",22)
        self._release("inc","b"*64,23)
        self.assertEqual(self._authorize(action="action-2",task="task-2")["reason"],"stale_recovery_epoch")

    def test_revocation_blocks_dispatch(self):
        self.db.revoke_approval("approval-1",company="co-a",now=19)
        self.assertEqual(self._authorize()["reason"],"approval_revoked")

    def test_expiry_blocks_dispatch(self):
        self.db.db.execute("UPDATE approvals SET expires_at=19 WHERE approval_id='approval-1'")
        self.assertEqual(self._authorize()["reason"],"approval_expired")

    def test_same_enqueue_is_idempotent(self):
        self.assertEqual(self.db.enqueue(action_id="action-1",company="co-a",stream="primary",
            approval_id="approval-1",idempotency_key="idem-1",
            intent={"receiver_account":"synthetic-sink","amount_minor":5},now=4),"duplicate_same_intent")

    def test_idempotency_conflict_is_rejected(self):
        with self.assertRaises(ControlStoreError):
            self.db.enqueue(action_id="action-x",company="co-a",stream="primary",
                approval_id="approval-1",idempotency_key="idem-1",
                intent={"receiver_account":"attacker"},now=4)

    def test_company_mismatch_denied(self):
        self.assertEqual(self._authorize(company="co-b")["reason"],"company_or_stream_mismatch")

    def test_audit_failure_rolls_back_dispatch_and_approval(self):
        self.db.db.execute("""CREATE TRIGGER fail_dispatch BEFORE INSERT ON audit
          WHEN NEW.event_type='dispatch_started' BEGIN SELECT RAISE(ABORT,'audit unavailable'); END""")
        with self.assertRaises(Exception): self._authorize()
        self.assertEqual(self.db.action_state("action-1"),"queued")
        row=self.db.db.execute("SELECT consumed_action_id FROM approvals WHERE approval_id='approval-1'").fetchone()
        self.assertIsNone(row[0])

    def test_quarantine_audit_failure_rolls_back_state_epoch_and_outbox(self):
        self.db.db.execute("""CREATE TRIGGER fail_quarantine BEFORE INSERT ON audit
          WHEN NEW.event_type='stream_quarantined' BEGIN SELECT RAISE(ABORT,'audit unavailable'); END""")
        before=self.db.stream_state("co-a","primary")
        before_outbox=self.db.db.execute("SELECT COUNT(*) FROM control_outbox").fetchone()[0]
        with self.assertRaises(Exception):
            self.db.quarantine(company="co-a",stream="primary",incident_id="x",reason="test",
                checkpoint_digest="c"*64,now=30)
        after=self.db.stream_state("co-a","primary")
        self.assertEqual((after["status"],after["epoch"]),(before["status"],before["epoch"]))
        self.assertEqual(before_outbox,
                         self.db.db.execute("SELECT COUNT(*) FROM control_outbox").fetchone()[0])

    def test_crash_after_commit_never_auto_resends(self):
        self.assertTrue(self._authorize()["allowed"])
        self.assertEqual(self.db.action_state("action-1"),"dispatch_started")
        with self.assertRaises(ControlStoreError): self._authorize()

    def test_timeout_is_unknown(self):
        self.assertTrue(self._authorize()["allowed"])
        self.assertEqual(self.db.record_sender_result("action-1",result="timeout",now=21),"outcome_unknown")

    def test_release_requires_both_verifiers(self):
        self.db.quarantine(company="co-a",stream="primary",incident_id="inc",reason="test",
            checkpoint_digest="d"*64,now=21)
        with self.assertRaises(ControlStoreError):
            self.db.release_stream(company="co-a",stream="primary",incident_id="inc",
                checkpoint_digest="d"*64,owner_approval="synthetic-signed-document",
                recovery_assessment="synthetic-signed-document",owner_verifier=object(),
                assessment_verifier=object(),now=22)

    def test_release_requires_all_assessment_checks(self):
        self.db.quarantine(company="co-a",stream="primary",incident_id="inc",reason="test",
            checkpoint_digest="d"*64,now=21)
        owner=Verifier({"approval_id":"o","nonce":"n","expires_at":900})
        assessor=Verifier({"assessment_digest":"d","expires_at":900,"db_integrity":True,
            "audit_chain_valid":False,"checkpoint_match":True,"revocations_current":True,
            "emergency_stop_clear":True,"unknown_actions_reconciled":True})
        with self.assertRaises(ControlStoreError):
            self.db.release_stream(company="co-a",stream="primary",incident_id="inc",
                checkpoint_digest="d"*64,owner_approval="synthetic-signed-document",
                recovery_assessment="synthetic-signed-document",owner_verifier=owner,
                assessment_verifier=assessor,now=22)
        self.assertEqual(self.db.stream_state("co-a","primary")["status"],QUARANTINED)

    def test_action_intent_is_immutable(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.db.execute("UPDATE actions SET intent_json='{}' WHERE action_id='action-1'")
        self.assertEqual(self.db.action_state("action-1"),"queued")

    def test_release_audit_failure_is_not_misclassified_as_replay(self):
        self.db.quarantine(company="co-a",stream="primary",incident_id="audit-inc",reason="test",
            checkpoint_digest="d"*64,now=21)
        owner=Verifier({"approval_id":"audit-owner","nonce":"audit-nonce","expires_at":900})
        assessor=Verifier({"assessment_digest":"audit-assessment","expires_at":900,"db_integrity":True,
            "audit_chain_valid":True,"checkpoint_match":True,"revocations_current":True,
            "emergency_stop_clear":True,"unknown_actions_reconciled":True})
        self.db.db.execute("""CREATE TRIGGER fail_release_audit BEFORE INSERT ON audit
          WHEN NEW.event_type='stream_released_by_owner' BEGIN SELECT RAISE(ABORT,'audit unavailable'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.release_stream(company="co-a",stream="primary",incident_id="audit-inc",
                checkpoint_digest="d"*64,owner_approval="synthetic-signed-document",
                recovery_assessment="synthetic-signed-document",owner_verifier=owner,
                assessment_verifier=assessor,now=22)
        self.assertEqual(self.db.stream_state("co-a","primary")["status"],QUARANTINED)
        self.assertEqual(self.db.db.execute(
            "SELECT COUNT(*) FROM release_consumptions WHERE approval_id='audit-owner'").fetchone()[0],0)

    def test_release_approval_nonce_cannot_be_reused(self):
        self.db.quarantine(company="co-a",stream="primary",incident_id="inc-1",reason="test",
            checkpoint_digest="d"*64,now=21)
        owner=Verifier({"approval_id":"single-use-owner-approval","nonce":"single-use-nonce","expires_at":900})
        assessor=Verifier({"assessment_digest":"assessment-1","expires_at":900,"db_integrity":True,
            "audit_chain_valid":True,"checkpoint_match":True,"revocations_current":True,
            "emergency_stop_clear":True,"unknown_actions_reconciled":True})
        self.db.release_stream(company="co-a",stream="primary",incident_id="inc-1",
            checkpoint_digest="d"*64,owner_approval="synthetic-signed-document",
            recovery_assessment="synthetic-signed-document",owner_verifier=owner,
            assessment_verifier=assessor,now=22)
        self.db.quarantine(company="co-a",stream="primary",incident_id="inc-2",reason="test",
            checkpoint_digest="e"*64,now=23)
        assessor2=Verifier({"assessment_digest":"assessment-2","expires_at":900,"db_integrity":True,
            "audit_chain_valid":True,"checkpoint_match":True,"revocations_current":True,
            "emergency_stop_clear":True,"unknown_actions_reconciled":True})
        with self.assertRaises(ControlStoreError):
            self.db.release_stream(company="co-a",stream="primary",incident_id="inc-2",
                checkpoint_digest="e"*64,owner_approval="synthetic-signed-document",
                recovery_assessment="synthetic-signed-document",owner_verifier=owner,
                assessment_verifier=assessor2,now=24)
        self.assertEqual(self.db.stream_state("co-a","primary")["status"],QUARANTINED)

    def test_dispatch_quarantine_race_serializes(self):
        barrier=threading.Barrier(2); results={}
        def dispatch():
            db=LinearizableControlStore(self.path)
            barrier.wait()
            try:
                results["dispatch"]=db.authorize_and_start("action-1",company="co-a",stream="primary",
                    agent="agent-a",task="task-1",operation="publish",resource="catalog/item",
                    policy_version="v1",now=40)
            finally: db.close()
        def quarantine():
            db=LinearizableControlStore(self.path)
            barrier.wait()
            try:
                db.quarantine(company="co-a",stream="primary",incident_id="race",reason="race",
                    checkpoint_digest="e"*64,now=40)
            finally: db.close()
        t1=threading.Thread(target=dispatch); t2=threading.Thread(target=quarantine)
        t1.start(); t2.start(); t1.join(); t2.join()
        self.assertEqual(self.db.stream_state("co-a","primary")["status"],QUARANTINED)
        if results["dispatch"]["allowed"]:
            self.assertEqual(self.db.action_state("action-1"),"dispatch_started")
        else:
            self.assertEqual(results["dispatch"]["reason"],"stream_not_active")
            self.assertEqual(self.db.action_state("action-1"),"queued")

    def test_company_epochs_are_isolated(self):
        self.db.register_stream(company="co-b",stream="primary",now=1)
        self.db.quarantine(company="co-b",stream="primary",incident_id="b",reason="test",
            checkpoint_digest="f"*64,now=2)
        self.assertEqual(self.db.stream_state("co-a","primary")["status"],ACTIVE)
        self.assertEqual(self.db.stream_state("co-b","primary")["status"],QUARANTINED)

    def test_audit_chain_valid_and_tamper_detected(self):
        self.assertTrue(self.db.verify_audit("co-a","primary"))
        self.db.db.execute("UPDATE audit SET payload_json='{}' WHERE event_type='action_queued'")
        self.assertFalse(self.db.verify_audit("co-a","primary"))


if __name__=="__main__":
    unittest.main()

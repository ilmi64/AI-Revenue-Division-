import tempfile, threading, unittest
from pathlib import Path
from sqlite_control_store import SQLiteControlStore

class SQLiteControlStoreTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.path=str(Path(self.tmp.name)/"control.db")
  self.s=SQLiteControlStore(self.path); self.s.add_task("task-1")
  self.s.add_approval(approval_id="approval-1",nonce="nonce-1",company_id="revenue",
   task_id="task-1",operation="publish.draft",resource="campaign/1",expires_at=9999)
 def tearDown(self): self.tmp.cleanup()
 def consume(self, store=None, **kw):
  return (store or self.s).consume_and_enqueue(approval_id="approval-1",nonce="nonce-1",
   company_id="revenue",task_id="task-1",operation="publish.draft",resource="campaign/1",
   now=100,idempotency_key="idem-1",**kw)
 def test_atomic_consume_and_outbox(self):
  ok,reason,row=self.consume(); self.assertTrue(ok); self.assertEqual(reason,"consumed_and_queued")
  self.assertEqual(len(self.s.outbox_rows()),1)
 def test_restart_persists_replay_block(self):
  self.consume(); reopened=SQLiteControlStore(self.path)
  result=reopened.consume_and_enqueue(approval_id="approval-1",nonce="nonce-1",company_id="revenue",
   task_id="task-1",operation="publish.draft",resource="campaign/1",now=100,idempotency_key="idem-2")
  self.assertFalse(result[0]); self.assertEqual(result[1],"replay_or_unique_constraint")
 def test_concurrent_race_exactly_one_wins(self):
  barrier=threading.Barrier(2); results=[]
  def run(key):
   s=SQLiteControlStore(self.path); barrier.wait()
   results.append(s.consume_and_enqueue(approval_id="approval-1",nonce="nonce-1",company_id="revenue",
    task_id="task-1",operation="publish.draft",resource="campaign/1",now=100,idempotency_key=key))
  ts=[threading.Thread(target=run,args=(f"idem-{i}",)) for i in range(2)]
  [t.start() for t in ts]; [t.join() for t in ts]
  self.assertEqual(sum(1 for r in results if r[0]),1)
  self.assertEqual(len(self.s.outbox_rows()),1)
 def test_revocation(self):
  self.s.revoke("approval-1")
  self.assertEqual(self.consume()[1],"approval_revoked")
 def test_cancellation(self):
  self.s.cancel_task("task-1")
  self.assertEqual(self.consume()[1],"task_missing_or_cancelled")
 def test_scope_mismatch(self):
  r=self.s.consume_and_enqueue(approval_id="approval-1",nonce="nonce-1",company_id="trading",
   task_id="task-1",operation="publish.draft",resource="campaign/1",now=100,idempotency_key="idem-x")
  self.assertEqual(r[1],"scope_mismatch")
 def test_expiry(self):
  self.assertEqual(self.s.consume_and_enqueue(approval_id="approval-1",nonce="nonce-1",company_id="revenue",
   task_id="task-1",operation="publish.draft",resource="campaign/1",now=9999,idempotency_key="idem-x")[1],"approval_expired")
 def test_audit_append_verify_and_restart(self):
  self.s.append_audit(stream_id="revenue-events",company_id="revenue",event_id="e1",
   occurred_at="2026-11-19T00:00:00Z",actor_id="agent-1",event_type="task.started",payload={"task":"t1"})
  self.assertEqual(self.s.verify_audit("revenue-events"),(True,"ok"))
  self.assertEqual(SQLiteControlStore(self.path).verify_audit("revenue-events"),(True,"ok"))
 def test_audit_tamper_detected(self):
  self.s.append_audit(stream_id="revenue-events",company_id="revenue",event_id="e1",
   occurred_at="2026-11-19T00:00:00Z",actor_id="agent-1",event_type="task.started",payload={"task":"t1"})
  import sqlite3
  c=sqlite3.connect(self.path); c.execute("UPDATE audit_events SET event_json=? WHERE event_id='e1'",('{"payload":{"task":"altered"}}',)); c.commit(); c.close()
  self.assertFalse(self.s.verify_audit("revenue-events")[0])
if __name__=="__main__": unittest.main()

"""SQLite durability/concurrency prototype. Local test harness only; not production authorization."""
from __future__ import annotations
import hashlib, json, sqlite3, time
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS approvals(
 approval_id TEXT PRIMARY KEY, nonce_hash TEXT NOT NULL UNIQUE, company_id TEXT NOT NULL,
 task_id TEXT NOT NULL, operation TEXT NOT NULL, resource TEXT NOT NULL,
 expires_at INTEGER NOT NULL, owner_approved INTEGER NOT NULL CHECK(owner_approved IN (0,1)),
 revoked INTEGER NOT NULL DEFAULT 0 CHECK(revoked IN (0,1))
);
CREATE TABLE IF NOT EXISTS tasks(
 task_id TEXT PRIMARY KEY, cancelled INTEGER NOT NULL DEFAULT 0 CHECK(cancelled IN (0,1))
);
CREATE TABLE IF NOT EXISTS consumed_approvals(
 approval_id TEXT PRIMARY KEY REFERENCES approvals(approval_id),
 nonce_hash TEXT NOT NULL UNIQUE, consumed_at INTEGER NOT NULL,
 idempotency_key TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS action_outbox(
 outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
 idempotency_key TEXT NOT NULL UNIQUE,
 approval_id TEXT NOT NULL UNIQUE REFERENCES consumed_approvals(approval_id),
 company_id TEXT NOT NULL, task_id TEXT NOT NULL, operation TEXT NOT NULL,
 resource TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending'
   CHECK(state IN ('pending','claimed','completed','failed','quarantined')),
 created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_stream_heads(
 stream_id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
 last_sequence INTEGER NOT NULL, last_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events(
 stream_id TEXT NOT NULL, sequence INTEGER NOT NULL, event_id TEXT NOT NULL UNIQUE,
 company_id TEXT NOT NULL, occurred_at TEXT NOT NULL, event_json TEXT NOT NULL,
 previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
 PRIMARY KEY(stream_id, sequence)
);
"""

def _canonical(d):
 return json.dumps(d, sort_keys=True, separators=(",",":"), ensure_ascii=False)

def _sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

class SQLiteControlStore:
 def __init__(self, path):
  self.path=str(path)
  with self._connect() as c:
   c.executescript(SCHEMA)
 def _connect(self):
  c=sqlite3.connect(self.path, timeout=15, isolation_level=None)
  c.row_factory=sqlite3.Row
  c.execute("PRAGMA foreign_keys=ON")
  c.execute("PRAGMA busy_timeout=15000")
  c.execute("PRAGMA journal_mode=WAL")
  c.execute("PRAGMA synchronous=FULL")
  return c
 def add_task(self, task_id):
  with self._connect() as c: c.execute("INSERT OR IGNORE INTO tasks(task_id) VALUES(?)",(task_id,))
 def add_approval(self, *, approval_id, nonce, company_id, task_id, operation, resource, expires_at, owner_approved=True):
  if not all(isinstance(x,str) and x for x in (approval_id,nonce,company_id,task_id,operation,resource)):
   raise ValueError("required approval fields must be non-empty strings")
  with self._connect() as c:
   c.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?,0)",
    (approval_id,_sha(nonce),company_id,task_id,operation,resource,int(expires_at),int(owner_approved)))
 def revoke(self, approval_id):
  with self._connect() as c: c.execute("UPDATE approvals SET revoked=1 WHERE approval_id=?",(approval_id,))
 def cancel_task(self, task_id):
  with self._connect() as c: c.execute("UPDATE tasks SET cancelled=1 WHERE task_id=?",(task_id,))
 def consume_and_enqueue(self, *, approval_id, nonce, company_id, task_id, operation, resource, now, idempotency_key):
  """Single SQLite write transaction. It queues intent; it never performs an external action."""
  if not idempotency_key: return False,"missing_idempotency_key",None
  c=self._connect()
  try:
   c.execute("BEGIN IMMEDIATE")
   a=c.execute("SELECT * FROM approvals WHERE approval_id=?",(approval_id,)).fetchone()
   if a is None: c.rollback(); return False,"approval_not_found",None
   if not a["owner_approved"]: c.rollback(); return False,"owner_approval_missing",None
   if a["revoked"]: c.rollback(); return False,"approval_revoked",None
   if int(now)>=a["expires_at"]: c.rollback(); return False,"approval_expired",None
   if a["nonce_hash"] != _sha(nonce): c.rollback(); return False,"nonce_mismatch",None
   if (a["company_id"],a["task_id"],a["operation"],a["resource"]) != (company_id,task_id,operation,resource):
    c.rollback(); return False,"scope_mismatch",None
   task=c.execute("SELECT cancelled FROM tasks WHERE task_id=?",(task_id,)).fetchone()
   if task is None or task["cancelled"]: c.rollback(); return False,"task_missing_or_cancelled",None
   existing=c.execute("SELECT outbox_id,state FROM action_outbox WHERE idempotency_key=?",(idempotency_key,)).fetchone()
   if existing:
    c.rollback(); return False,"idempotent_request_already_recorded",dict(existing)
   c.execute("INSERT INTO consumed_approvals VALUES(?,?,?,?)",
     (approval_id,a["nonce_hash"],int(now),idempotency_key))
   cur=c.execute("""INSERT INTO action_outbox(idempotency_key,approval_id,company_id,task_id,operation,resource,created_at)
                    VALUES(?,?,?,?,?,?,?)""",
     (idempotency_key,approval_id,company_id,task_id,operation,resource,int(now)))
   outbox_id=cur.lastrowid
   c.commit()
   return True,"consumed_and_queued",{"outbox_id":outbox_id,"state":"pending"}
  except sqlite3.IntegrityError:
   c.rollback(); return False,"replay_or_unique_constraint",None
  except Exception:
   c.rollback(); raise
  finally: c.close()
 def append_audit(self, *, stream_id, company_id, event_id, occurred_at, actor_id, event_type, payload):
  if not isinstance(payload,dict): raise ValueError("payload must be an object")
  body={"event_id":event_id,"company_id":company_id,"occurred_at":occurred_at,
        "actor_id":actor_id,"event_type":event_type,"payload":payload}
  encoded=_canonical(body)
  c=self._connect()
  try:
   c.execute("BEGIN IMMEDIATE")
   head=c.execute("SELECT * FROM audit_stream_heads WHERE stream_id=?",(stream_id,)).fetchone()
   if head and head["company_id"] != company_id: raise ValueError("stream company mismatch")
   seq=(head["last_sequence"]+1) if head else 1
   prev=head["last_hash"] if head else "0"*64
   digest=_sha(_canonical({"stream_id":stream_id,"sequence":seq,"body":body,"previous_hash":prev,"hash_algorithm":"sha256"}))
   c.execute("INSERT INTO audit_events VALUES(?,?,?,?,?,?,?,?)",
     (stream_id,seq,event_id,company_id,occurred_at,encoded,prev,digest))
   c.execute("""INSERT INTO audit_stream_heads VALUES(?,?,?,?)
     ON CONFLICT(stream_id) DO UPDATE SET last_sequence=excluded.last_sequence,last_hash=excluded.last_hash""",
     (stream_id,company_id,seq,digest))
   c.commit(); return {"sequence":seq,"hash":digest}
  except Exception: c.rollback(); raise
  finally: c.close()
 def verify_audit(self, stream_id):
  with self._connect() as c:
   rows=c.execute("SELECT * FROM audit_events WHERE stream_id=? ORDER BY sequence",(stream_id,)).fetchall()
   head=c.execute("SELECT * FROM audit_stream_heads WHERE stream_id=?",(stream_id,)).fetchone()
  prev="0"*64
  for i,r in enumerate(rows,1):
   if r["sequence"]!=i or r["previous_hash"]!=prev: return False,"sequence_or_link_failure"
   body=json.loads(r["event_json"])
   digest=_sha(_canonical({"stream_id":stream_id,"sequence":i,"body":body,"previous_hash":prev,"hash_algorithm":"sha256"}))
   if digest!=r["event_hash"]: return False,"event_hash_failure"
   prev=digest
  if (head is None and rows) or (head and (head["last_sequence"]!=len(rows) or head["last_hash"]!=prev)):
   return False,"head_mismatch"
  return True,"ok"
 def outbox_rows(self):
  with self._connect() as c:
   return [dict(r) for r in c.execute("SELECT * FROM action_outbox ORDER BY outbox_id")]

"""Offline SQLite outbox dispatcher reference. Never performs network or financial actions."""
import sqlite3, json, uuid
from dataclasses import dataclass

@dataclass(frozen=True)
class Claim:
    action_id: str
    idempotency_key: str
    payload_json: str
    attempt: int

class Outbox:
    def __init__(self, path=":memory:", max_attempts=3):
        self.db=sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.max_attempts=max_attempts
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS actions(
          action_id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL UNIQUE,
          payload_json TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN
          ('pending','leased','completed','failed','outcome_unknown','cancelled')),
          attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL,
          lease_owner TEXT, lease_until INTEGER, result_json TEXT,
          created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS action_events(
          event_id TEXT PRIMARY KEY, action_id TEXT NOT NULL REFERENCES actions(action_id),
          event_type TEXT NOT NULL, occurred_at INTEGER NOT NULL, detail_json TEXT NOT NULL);
        """)
    def enqueue(self, action_id, idempotency_key, payload, now):
        if not all(isinstance(x,str) and x for x in (action_id,idempotency_key)):
            raise ValueError("identifiers required")
        if not isinstance(payload,dict): raise ValueError("payload must be an object")
        raw=json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False)
        self.db.execute("INSERT OR IGNORE INTO actions VALUES(?,?,?,'pending',0,?,NULL,NULL,NULL,?,?)",
                        (action_id,idempotency_key,raw,self.max_attempts,now,now))
        row=self.db.execute("SELECT * FROM actions WHERE idempotency_key=?",(idempotency_key,)).fetchone()
        if row["action_id"] != action_id or row["payload_json"] != raw:
            raise ValueError("idempotency key reused with different intent")
        return action_id
    def claim(self, worker, now, lease_seconds=30):
        if not worker or lease_seconds <= 0: raise ValueError("invalid lease")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            # Expired leases are NOT automatically retried: the prior worker may have dispatched.
            row=self.db.execute("""SELECT * FROM actions WHERE status='pending'
                AND attempts < max_attempts ORDER BY created_at, action_id LIMIT 1""").fetchone()
            if row is None:
                self.db.execute("COMMIT"); return None
            cur=self.db.execute("""UPDATE actions SET status='leased', lease_owner=?,
                lease_until=?, attempts=attempts+1, updated_at=?
                WHERE action_id=? AND status='pending'""",
                (worker,now+lease_seconds,now,row["action_id"]))
            if cur.rowcount != 1: raise RuntimeError("claim race")
            self.db.execute("INSERT INTO action_events VALUES(?,?,?,?,?)",
                (str(uuid.uuid4()),row["action_id"],"claimed",now,json.dumps({"worker":worker})))
            self.db.execute("COMMIT")
            return Claim(row["action_id"],row["idempotency_key"],row["payload_json"],row["attempts"]+1)
        except:
            self.db.execute("ROLLBACK"); raise
    def complete(self, action_id, worker, result, now):
        raw=json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT * FROM actions WHERE action_id=?",(action_id,)).fetchone()
            if row is None: raise KeyError(action_id)
            if row["status"]=="completed":
                if row["result_json"]==raw: self.db.execute("COMMIT"); return "already_completed_same_result"
                raise ValueError("conflicting completion")
            if row["status"]!="leased" or row["lease_owner"]!=worker:
                raise ValueError("lease ownership/status mismatch")
            self.db.execute("""UPDATE actions SET status='completed',result_json=?,
                lease_owner=NULL,lease_until=NULL,updated_at=? WHERE action_id=?""",(raw,now,action_id))
            self.db.execute("INSERT INTO action_events VALUES(?,?,?,?,?)",
                (str(uuid.uuid4()),action_id,"completed",now,raw))
            self.db.execute("COMMIT"); return "completed"
        except:
            self.db.execute("ROLLBACK"); raise
    def mark_uncertain(self, action_id, worker, now, reason):
        cur=self.db.execute("""UPDATE actions SET status='outcome_unknown',lease_owner=NULL,
            lease_until=NULL,updated_at=? WHERE action_id=? AND status='leased' AND lease_owner=?""",
            (now,action_id,worker))
        if cur.rowcount != 1: raise ValueError("cannot mark uncertain")
        self.db.execute("INSERT INTO action_events VALUES(?,?,?,?,?)",
            (str(uuid.uuid4()),action_id,"outcome_unknown",now,json.dumps({"reason":reason})))
    def retry_after_confirmed_no_effect(self, action_id, now, evidence_ref):
        if not evidence_ref: raise ValueError("reconciliation evidence required")
        cur=self.db.execute("""UPDATE actions SET status=CASE WHEN attempts < max_attempts
            THEN 'pending' ELSE 'failed' END,updated_at=? WHERE action_id=? AND status='outcome_unknown'""",
            (now,action_id))
        if cur.rowcount != 1: raise ValueError("not awaiting reconciliation")
        self.db.execute("INSERT INTO action_events VALUES(?,?,?,?,?)",
            (str(uuid.uuid4()),action_id,"reconciled_no_effect",now,json.dumps({"evidence_ref":evidence_ref})))
    def cancel_claim_for_denial(self, action_id, worker, now):
        cur=self.db.execute("""UPDATE actions SET status='cancelled',lease_owner=NULL,
            lease_until=NULL,updated_at=? WHERE action_id=? AND status='leased' AND lease_owner=?""",
            (now,action_id,worker))
        if cur.rowcount != 1: raise ValueError("lease ownership/status mismatch")
        self.db.execute("INSERT INTO action_events VALUES(?,?,?,?,?)",
            (str(uuid.uuid4()),action_id,"policy_denied",now,"{}"))
    def cancel(self, action_id, now):
        cur=self.db.execute("""UPDATE actions SET status='cancelled',lease_owner=NULL,
            lease_until=NULL,updated_at=? WHERE action_id=? AND status='pending'""",(now,action_id))
        return cur.rowcount == 1
    def get(self, action_id):
        r=self.db.execute("SELECT * FROM actions WHERE action_id=?",(action_id,)).fetchone()
        return dict(r) if r else None
    def close(self): self.db.close()

def dispatch_one(store, worker, now, policy_check, sender):
    """Callbacks are test doubles. Recheck policy immediately before send.
    Sender MUST support the same idempotency key at the remote boundary.
    """
    claim=store.claim(worker,now)
    if claim is None: return "no_pending_action"
    try:
        if not policy_check(claim): 
            store.cancel_claim_for_denial(claim.action_id,worker,now)
            return "denied_by_fresh_policy"
        result=sender(claim.idempotency_key,json.loads(claim.payload_json))
        store.complete(claim.action_id,worker,result,now)
        return "sent_and_recorded"
    except TimeoutError:
        store.mark_uncertain(claim.action_id,worker,now,"sender_timeout")
        return "outcome_unknown_reconciliation_required"

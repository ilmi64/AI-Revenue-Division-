"""SQLite transactional approval ledger reference.

Synthetic/offline reference only. Uses a single SQLite database transaction to
consume a one-time approval and append its audit event atomically.
"""
from __future__ import annotations
import hashlib, json, sqlite3, uuid
from dataclasses import dataclass

GENESIS = "0" * 64

@dataclass(frozen=True)
class ConsumeResult:
    allowed: bool
    reason: str
    event_id: str = ""

class DurableApprovalLedger:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None,
                                  check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS approvals(
          approval_id TEXT PRIMARY KEY, nonce TEXT NOT NULL UNIQUE,
          owner_id TEXT NOT NULL, company_id TEXT NOT NULL,
          agent_id TEXT NOT NULL, session_id TEXT NOT NULL,
          task_id TEXT NOT NULL, operation TEXT NOT NULL, resource TEXT NOT NULL,
          policy_version TEXT NOT NULL, amount_limit_minor INTEGER,
          expires_at INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,
          created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approval_consumptions(
          approval_id TEXT PRIMARY KEY REFERENCES approvals(approval_id),
          nonce TEXT NOT NULL UNIQUE, action_id TEXT NOT NULL UNIQUE,
          consumed_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approval_audit(
          sequence INTEGER PRIMARY KEY AUTOINCREMENT,
          event_id TEXT NOT NULL UNIQUE, company_id TEXT NOT NULL,
          event_type TEXT NOT NULL, occurred_at INTEGER NOT NULL,
          payload_json TEXT NOT NULL, previous_hash TEXT NOT NULL,
          event_hash TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS approval_audit_company_seq
          ON approval_audit(company_id, sequence);
        """)
    @staticmethod
    def _canonical(obj):
        return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)
    def _append_audit_tx(self, company_id, event_type, now, payload):
        row = self.db.execute(
          "SELECT event_hash FROM approval_audit WHERE company_id=? ORDER BY sequence DESC LIMIT 1",
          (company_id,)).fetchone()
        previous = row["event_hash"] if row else GENESIS
        body = {"company_id":company_id,"event_type":event_type,"occurred_at":now,
                "payload":payload,"previous_hash":previous}
        digest = hashlib.sha256(self._canonical(body).encode("utf-8")).hexdigest()
        event_id = str(uuid.uuid4())
        self.db.execute("""INSERT INTO approval_audit
          (event_id,company_id,event_type,occurred_at,payload_json,previous_hash,event_hash)
          VALUES(?,?,?,?,?,?,?)""",
          (event_id,company_id,event_type,now,self._canonical(payload),previous,digest))
        return event_id
    def issue(self, *, approval_id, nonce, owner_id, company_id, agent_id,
              session_id, task_id, operation, resource, policy_version,
              expires_at, created_at, amount_limit_minor=None):
        fields=(approval_id,nonce,owner_id,company_id,agent_id,session_id,
                task_id,operation,resource,policy_version)
        if not all(isinstance(x,str) and x.strip() for x in fields):
            raise ValueError("approval_fields_required")
        if isinstance(expires_at,bool) or not isinstance(expires_at,int) or expires_at <= created_at:
            raise ValueError("invalid_expiry")
        if amount_limit_minor is not None and (
            isinstance(amount_limit_minor,bool) or not isinstance(amount_limit_minor,int)
            or amount_limit_minor < 0):
            raise ValueError("invalid_amount_limit_minor")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("""INSERT INTO approvals
              (approval_id,nonce,owner_id,company_id,agent_id,session_id,task_id,
               operation,resource,policy_version,amount_limit_minor,expires_at,created_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (approval_id,nonce,owner_id,company_id,agent_id,session_id,task_id,
               operation,resource,policy_version,amount_limit_minor,expires_at,created_at))
            self._append_audit_tx(company_id,"approval_issued",created_at,
                                  {"approval_id":approval_id,"task_id":task_id,
                                   "operation":operation,"resource":resource})
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK"); raise
    def revoke(self, approval_id, *, company_id, now):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            cur=self.db.execute("""UPDATE approvals SET revoked=1
              WHERE approval_id=? AND company_id=? AND revoked=0""",(approval_id,company_id))
            if cur.rowcount != 1:
                self.db.execute("ROLLBACK")
                return False
            self._append_audit_tx(company_id,"approval_revoked",now,{"approval_id":approval_id})
            self.db.execute("COMMIT")
            return True
        except Exception:
            self.db.execute("ROLLBACK"); raise
    def consume(self, approval_id, *, company_id, owner_id, agent_id,
                session_id, task_id, operation, resource, policy_version,
                action_id, now, amount_minor=None):
        """Atomic exact-scope consume. Owner signature verification is upstream."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT * FROM approvals WHERE approval_id=?",
                                (approval_id,)).fetchone()
            reason=None
            if row is None: reason="approval_not_found"
            elif row["revoked"]: reason="approval_revoked"
            elif now >= row["expires_at"]: reason="approval_expired"
            elif (row["company_id"],row["owner_id"],row["agent_id"],row["session_id"],
                  row["task_id"],row["operation"],row["resource"],row["policy_version"]) != (
                  company_id,owner_id,agent_id,session_id,task_id,operation,resource,policy_version):
                reason="approval_scope_mismatch"
            elif amount_minor is not None and (
                isinstance(amount_minor,bool) or not isinstance(amount_minor,int) or amount_minor < 0):
                reason="invalid_amount"
            elif row["amount_limit_minor"] is not None and (
                amount_minor is None or amount_minor > row["amount_limit_minor"]):
                reason="amount_limit_exceeded"
            if reason:
                self._append_audit_tx(company_id,"approval_consume_denied",now,
                                      {"approval_id":approval_id,"reason":reason,"action_id":action_id})
                self.db.execute("COMMIT")
                return ConsumeResult(False,reason)
            self.db.execute("""INSERT INTO approval_consumptions
              (approval_id,nonce,action_id,consumed_at) VALUES(?,?,?,?)""",
              (row["approval_id"],row["nonce"],action_id,now))
            event_id=self._append_audit_tx(company_id,"approval_consumed",now,
                {"approval_id":approval_id,"task_id":task_id,"operation":operation,
                 "resource":resource,"action_id":action_id})
            self.db.execute("COMMIT")
            return ConsumeResult(True,"consumed_once",event_id)
        except sqlite3.IntegrityError:
            self.db.execute("ROLLBACK")
            # Only classify as replay if the unique row exists after rollback.
            # Other integrity failures (including audit insertion failure) propagate.
            existing=self.db.execute("""SELECT 1 FROM approval_consumptions
              WHERE approval_id=? OR action_id=? LIMIT 1""",
              (approval_id,action_id)).fetchone()
            if existing:
                return ConsumeResult(False,"approval_replay_or_action_duplicate")
            raise
        except Exception:
            self.db.execute("ROLLBACK")
            raise
    def verify_audit(self, company_id):
        rows=self.db.execute("""SELECT * FROM approval_audit WHERE company_id=?
          ORDER BY sequence""",(company_id,)).fetchall()
        previous=GENESIS
        for row in rows:
            payload=json.loads(row["payload_json"])
            body={"company_id":company_id,"event_type":row["event_type"],
                  "occurred_at":row["occurred_at"],"payload":payload,
                  "previous_hash":previous}
            expected=hashlib.sha256(self._canonical(body).encode("utf-8")).hexdigest()
            if row["previous_hash"] != previous or row["event_hash"] != expected:
                return False
            previous=expected
        return True
    def count_consumptions(self, approval_id):
        return self.db.execute("SELECT COUNT(*) FROM approval_consumptions WHERE approval_id=?",
                               (approval_id,)).fetchone()[0]
    def count_audit(self, company_id, event_type):
        return self.db.execute("SELECT COUNT(*) FROM approval_audit WHERE company_id=? AND event_type=?",
                               (company_id,event_type)).fetchone()[0]
    def close(self):
        self.db.close()

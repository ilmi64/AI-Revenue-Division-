"""Offline reference for atomic approval + outbox dispatch boundary.

Not production software. SQLite serializes local state changes; the remote sender
remains outside the transaction and must enforce the same idempotency key.
"""
from __future__ import annotations
import hashlib, json, sqlite3, uuid

GENESIS = "0" * 64

class DispatchStore:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS approvals(
          id TEXT PRIMARY KEY, company TEXT NOT NULL, agent TEXT NOT NULL,
          task TEXT NOT NULL, operation TEXT NOT NULL, resource TEXT NOT NULL,
          policy TEXT NOT NULL, expires INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS actions(
          id TEXT PRIMARY KEY, company TEXT NOT NULL, approval_id TEXT NOT NULL,
          idem TEXT NOT NULL UNIQUE, intent_json TEXT NOT NULL, state TEXT NOT NULL,
          created INTEGER NOT NULL, updated INTEGER NOT NULL, evidence_json TEXT);
        CREATE TABLE IF NOT EXISTS consumed(
          approval_id TEXT PRIMARY KEY, action_id TEXT NOT NULL UNIQUE,
          consumed_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(
          seq INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT NOT NULL,
          kind TEXT NOT NULL, at INTEGER NOT NULL, payload TEXT NOT NULL,
          prev TEXT NOT NULL, hash TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS audit_company_seq ON audit(company,seq);
        """)
    @staticmethod
    def canon(x):
        return json.dumps(x, sort_keys=True, separators=(",",":"), allow_nan=False)
    def _event(self, company, kind, now, payload):
        r=self.db.execute("SELECT hash FROM audit WHERE company=? ORDER BY seq DESC LIMIT 1",(company,)).fetchone()
        prev=r["hash"] if r else GENESIS
        body={"company":company,"kind":kind,"at":now,"payload":payload,"prev":prev}
        digest=hashlib.sha256(self.canon(body).encode()).hexdigest()
        self.db.execute("INSERT INTO audit(company,kind,at,payload,prev,hash) VALUES(?,?,?,?,?,?)",
                        (company,kind,now,self.canon(payload),prev,digest))
    def issue_approval(self, *, approval_id, company, agent, task, operation,
                       resource, policy, expires, now):
        if not all(isinstance(x,str) and x.strip() for x in
                   (approval_id,company,agent,task,operation,resource,policy)):
            raise ValueError("required_fields")
        if isinstance(expires,bool) or not isinstance(expires,int) or expires <= now:
            raise ValueError("invalid_expiry")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?,0)",
                (approval_id,company,agent,task,operation,resource,policy,expires))
            self._event(company,"approval_issued",now,{"approval_id":approval_id})
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK"); raise
    def enqueue(self, *, action_id, company, approval_id, idempotency_key, intent, now):
        if not all(isinstance(x,str) and x.strip() for x in
                   (action_id,company,approval_id,idempotency_key)):
            raise ValueError("required_fields")
        encoded=self.canon(intent)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old=self.db.execute("SELECT * FROM actions WHERE id=? OR idem=?",
                                (action_id,idempotency_key)).fetchone()
            if old:
                if old["id"]==action_id and old["idem"]==idempotency_key and old["intent_json"]==encoded:
                    self.db.execute("COMMIT"); return "duplicate_same_intent"
                raise ValueError("action_or_idempotency_conflict")
            self.db.execute("""INSERT INTO actions
              (id,company,approval_id,idem,intent_json,state,created,updated)
              VALUES(?,?,?,?,?,'queued',?,?)""",
              (action_id,company,approval_id,idempotency_key,encoded,now,now))
            self._event(company,"action_queued",now,{"action_id":action_id,"approval_id":approval_id})
            self.db.execute("COMMIT"); return "queued"
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise
    def revoke(self, approval_id, *, company, now):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            c=self.db.execute("UPDATE approvals SET revoked=1 WHERE id=? AND company=? AND revoked=0",
                              (approval_id,company))
            if c.rowcount:
                self._event(company,"approval_revoked",now,{"approval_id":approval_id})
            self.db.execute("COMMIT"); return c.rowcount==1
        except Exception:
            self.db.execute("ROLLBACK"); raise
    def authorize_and_start(self, action_id, *, company, agent, task, operation,
                            resource, policy, now):
        """Linearization point: consume exact approval, set dispatch_started, audit."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            a=self.db.execute("SELECT * FROM actions WHERE id=?",(action_id,)).fetchone()
            reason=None
            if a is None: reason="action_not_found"
            elif a["company"] != company: reason="company_mismatch"
            elif a["state"] != "queued": reason="action_not_queued"
            p=self.db.execute("SELECT * FROM approvals WHERE id=?",(a["approval_id"],)).fetchone() if a else None
            if reason is None and p is None: reason="approval_not_found"
            if reason is None and p["revoked"]: reason="approval_revoked"
            if reason is None and now >= p["expires"]: reason="approval_expired"
            if reason is None and (p["company"],p["agent"],p["task"],p["operation"],p["resource"],p["policy"]) != (company,agent,task,operation,resource,policy):
                reason="approval_scope_mismatch"
            if reason:
                if a and a["company"]==company:
                    self._event(company,"dispatch_denied",now,{"action_id":action_id,"reason":reason})
                self.db.execute("COMMIT"); return {"allowed":False,"reason":reason}
            self.db.execute("INSERT INTO consumed VALUES(?,?,?)",(p["id"],action_id,now))
            self.db.execute("UPDATE actions SET state='dispatch_started',updated=? WHERE id=?",(now,action_id))
            self._event(company,"dispatch_started",now,{"action_id":action_id,"approval_id":p["id"],"idem":a["idem"]})
            self.db.execute("COMMIT")
            return {"allowed":True,"idempotency_key":a["idem"],"intent":json.loads(a["intent_json"])}
        except sqlite3.IntegrityError:
            self.db.execute("ROLLBACK")
            # Distinguish a genuine unique-consumption replay from an audit
            # constraint failure. Audit failure must propagate and fail closed.
            used=self.db.execute("SELECT 1 FROM consumed WHERE approval_id=? OR action_id=? LIMIT 1",
                                 (a["approval_id"] if a else "",action_id)).fetchone()
            if used:
                return {"allowed":False,"reason":"approval_or_action_replay"}
            raise
        except Exception:
            self.db.execute("ROLLBACK"); raise
    def record_sender_result(self, action_id, *, result, now):
        if result not in ("accepted","rejected","timeout","exception"):
            raise ValueError("invalid_sender_result")
        state={"accepted":"sent","rejected":"failed","timeout":"outcome_unknown",
               "exception":"outcome_unknown"}[result]
        self.db.execute("BEGIN IMMEDIATE")
        try:
            a=self.db.execute("SELECT * FROM actions WHERE id=?",(action_id,)).fetchone()
            if not a or a["state"]!="dispatch_started":
                raise ValueError("not_dispatch_started")
            self.db.execute("UPDATE actions SET state=?,updated=? WHERE id=?",(state,now,action_id))
            self._event(a["company"],"sender_result",now,{"action_id":action_id,"state":state})
            self.db.execute("COMMIT"); return state
        except Exception:
            self.db.execute("ROLLBACK"); raise
    def reconcile(self, action_id, *, evidence, evidence_verifier, now):
        """Verify raw receiver evidence through trusted infrastructure before recording it."""
        if not callable(evidence_verifier):
            raise ValueError("trusted_evidence_verifier_required")
        if not isinstance(evidence,dict):
            raise ValueError("evidence_required")
        # Read immutable action identity before external verification. The trusted
        # verifier must bind the signed evidence to this exact action and audience.
        action=self.db.execute("SELECT company,id,idem FROM actions WHERE id=?",(action_id,)).fetchone()
        if not action:
            raise ValueError("action_not_found")
        expected={"company":action["company"],"action_id":action["id"],
                  "idempotency_key":action["idem"],"audience":"recovery-gateway"}
        verified=evidence_verifier(evidence, expected=expected, now=now)
        if not isinstance(verified,dict) or verified.get("verified") is not True:
            raise ValueError("receiver_evidence_not_verified")
        outcome=verified.get("outcome")
        if outcome not in ("applied","not_applied","inconclusive"):
            raise ValueError("invalid_verified_outcome")
        evidence_id=verified.get("evidence_id")
        if not isinstance(evidence_id,str) or not evidence_id.strip():
            raise ValueError("verified_evidence_id_required")
        source=verified.get("issuer")
        observed_at=verified.get("observed_at")
        if not isinstance(source,str) or isinstance(observed_at,bool) or not isinstance(observed_at,int):
            raise ValueError("verified_evidence_metadata_required")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            a=self.db.execute("SELECT * FROM actions WHERE id=?",(action_id,)).fetchone()
            if not a:
                raise ValueError("action_not_found")
            # Recheck identity under the write lock: verification happened outside
            # the transaction to avoid holding a DB lock across external code.
            if (a["company"],a["id"],a["idem"]) != (
                expected["company"],expected["action_id"],expected["idempotency_key"]):
                raise ValueError("action_identity_changed_during_verification")
            if a["state"]!="outcome_unknown":
                raise ValueError("action_not_unknown")
            evidence_record={"outcome":outcome,"evidence_id":evidence_id,"source":source,
                      "observed_at":observed_at,"payload_sha256":verified.get("payload_sha256")}
            state={"applied":"reconciled_applied","not_applied":"reconciled_not_applied",
                   "inconclusive":"quarantined"}[outcome]
            self.db.execute("UPDATE actions SET state=?,updated=?,evidence_json=? WHERE id=?",
                            (state,now,self.canon(evidence_record),action_id))
            self._event(a["company"],"action_reconciled",now,{"action_id":action_id,**evidence_record,"state":state})
            self.db.execute("COMMIT"); return state
        except Exception:
            self.db.execute("ROLLBACK"); raise
    def verify_audit(self, company):
        rows=self.db.execute("SELECT * FROM audit WHERE company=? ORDER BY seq",(company,)).fetchall()
        prev=GENESIS
        for r in rows:
            body={"company":company,"kind":r["kind"],"at":r["at"],
                  "payload":json.loads(r["payload"]),"prev":prev}
            digest=hashlib.sha256(self.canon(body).encode()).hexdigest()
            if r["prev"]!=prev or r["hash"]!=digest: return False
            prev=digest
        return True
    def action_state(self, action_id):
        r=self.db.execute("SELECT state FROM actions WHERE id=?",(action_id,)).fetchone()
        return r["state"] if r else None
    def backup_to(self, destination):
        """Use SQLite online backup API; destination must be a new/controlled path."""
        target=sqlite3.connect(destination)
        try: self.db.backup(target)
        finally: target.close()
    def integrity_ok(self):
        return self.db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    def close(self): self.db.close()

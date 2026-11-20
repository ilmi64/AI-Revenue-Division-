"""Offline synthetic single-transaction recovery/dispatch control-store reference.

No network, sender, broker, wallet, payment, signing, or live financial actions.
SQLite demonstrates a local transaction boundary only; it is not production.
"""
import hashlib
import json
import sqlite3
import uuid

GENESIS = "0" * 64
ACTIVE, DISABLED, QUARANTINED = "active", "dispatch_disabled", "quarantined"


class ControlStoreError(ValueError):
    pass


class LinearizableControlStore:
    """One database for stream state, approvals, action intents, dispatch and audit."""

    def __init__(self, path):
        self.db = sqlite3.connect(str(path), timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS streams(
          company TEXT NOT NULL, stream TEXT NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('dispatch_disabled','quarantined','active')),
          epoch INTEGER NOT NULL CHECK(epoch>=0), incident_id TEXT,
          checkpoint_digest TEXT, updated_at INTEGER NOT NULL,
          PRIMARY KEY(company,stream));
        CREATE TABLE IF NOT EXISTS approvals(
          approval_id TEXT PRIMARY KEY, company TEXT NOT NULL, stream TEXT NOT NULL,
          agent TEXT NOT NULL, task TEXT NOT NULL, operation TEXT NOT NULL,
          resource TEXT NOT NULL, policy_version TEXT NOT NULL, amount_limit_minor INTEGER,
          expires_at INTEGER NOT NULL,
          revoked INTEGER NOT NULL DEFAULT 0, consumed_action_id TEXT UNIQUE, consumed_at INTEGER);
        CREATE TABLE IF NOT EXISTS actions(
          action_id TEXT PRIMARY KEY, company TEXT NOT NULL, stream TEXT NOT NULL,
          approval_id TEXT NOT NULL REFERENCES approvals(approval_id),
          idempotency_key TEXT NOT NULL UNIQUE, intent_json TEXT NOT NULL,
          enqueue_epoch INTEGER NOT NULL,
          state TEXT NOT NULL CHECK(state IN
          ('queued','dispatch_started','sent','failed','outcome_unknown','reconciled_applied',
           'reconciled_not_applied','quarantined','cancelled')),
          created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(
          sequence INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT NOT NULL, stream TEXT NOT NULL,
          event_type TEXT NOT NULL, occurred_at INTEGER NOT NULL, payload_json TEXT NOT NULL,
          previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS audit_scope ON audit(company,stream,sequence);
        CREATE TABLE IF NOT EXISTS control_outbox(
          event_id TEXT PRIMARY KEY, company TEXT NOT NULL, stream TEXT NOT NULL,
          epoch INTEGER NOT NULL, event_type TEXT NOT NULL, payload_json TEXT NOT NULL,
          created_at INTEGER NOT NULL, delivered_at INTEGER);
        CREATE TABLE IF NOT EXISTS release_consumptions(
          approval_id TEXT PRIMARY KEY, nonce TEXT NOT NULL UNIQUE,
          company TEXT NOT NULL, stream TEXT NOT NULL, incident_id TEXT NOT NULL,
          checkpoint_digest TEXT NOT NULL, consumed_at INTEGER NOT NULL);
        CREATE TRIGGER IF NOT EXISTS immutable_action_intent
          BEFORE UPDATE OF action_id,company,stream,approval_id,idempotency_key,intent_json,enqueue_epoch
          ON actions BEGIN SELECT RAISE(ABORT,'immutable_action_intent'); END;
        """)

    @staticmethod
    def canon(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)

    @staticmethod
    def required(*values):
        return all(isinstance(v, str) and v.strip() for v in values)

    def _audit(self, company, stream, event_type, now, payload):
        row = self.db.execute(
            "SELECT event_hash FROM audit WHERE company=? AND stream=? ORDER BY sequence DESC LIMIT 1",
            (company, stream)).fetchone()
        previous = row["event_hash"] if row else GENESIS
        body = {"company":company,"stream":stream,"event_type":event_type,
                "occurred_at":now,"payload":payload,"previous_hash":previous}
        digest = hashlib.sha256(self.canon(body).encode("utf-8")).hexdigest()
        self.db.execute(
            "INSERT INTO audit(company,stream,event_type,occurred_at,payload_json,previous_hash,event_hash) "
            "VALUES(?,?,?,?,?,?,?)",
            (company,stream,event_type,now,self.canon(payload),previous,digest))

    def register_stream(self, *, company, stream, now):
        if not self.required(company,stream) or isinstance(now,bool) or not isinstance(now,int):
            raise ControlStoreError("invalid_stream_registration")
        self.db.execute(
            "INSERT INTO streams(company,stream,status,epoch,updated_at) VALUES(?,?,?,0,?)",
            (company,stream,DISABLED,now))

    def issue_approval(self, *, approval_id, company, stream, agent, task,
                       operation, resource, policy_version, expires_at, now, amount_limit_minor=None):
        if not self.required(approval_id,company,stream,agent,task,operation,resource,policy_version):
            raise ControlStoreError("approval_fields_required")
        if (isinstance(now,bool) or not isinstance(now,int) or isinstance(expires_at,bool)
            or not isinstance(expires_at,int) or expires_at<=now):
            raise ControlStoreError("invalid_approval_expiry")
        if amount_limit_minor is not None and (
            isinstance(amount_limit_minor,bool) or not isinstance(amount_limit_minor,int)
            or amount_limit_minor<0):
            raise ControlStoreError("invalid_amount_limit_minor")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if self.db.execute("SELECT 1 FROM streams WHERE company=? AND stream=?",
                               (company,stream)).fetchone() is None:
                raise ControlStoreError("stream_not_registered")
            self.db.execute(
                "INSERT INTO approvals(approval_id,company,stream,agent,task,operation,resource,"
                "policy_version,amount_limit_minor,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (approval_id,company,stream,agent,task,operation,resource,policy_version,
                 amount_limit_minor,expires_at))
            self._audit(company,stream,"approval_issued",now,
                        {"approval_id":approval_id,"task":task,"operation":operation})
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def enqueue(self, *, action_id, company, stream, approval_id, idempotency_key, intent, now):
        if not self.required(action_id,company,stream,approval_id,idempotency_key) or not isinstance(intent,dict):
            raise ControlStoreError("action_fields_required")
        if isinstance(now,bool) or not isinstance(now,int):
            raise ControlStoreError("invalid_time")
        encoded = self.canon(intent)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.db.execute(
                "SELECT * FROM actions WHERE action_id=? OR idempotency_key=?",
                (action_id,idempotency_key)).fetchone()
            if old:
                same = (old["action_id"],old["company"],old["stream"],old["approval_id"],
                        old["idempotency_key"],old["intent_json"]) == (
                        action_id,company,stream,approval_id,idempotency_key,encoded)
                if same:
                    self.db.execute("COMMIT")
                    return "duplicate_same_intent"
                raise ControlStoreError("action_or_idempotency_conflict")
            s = self.db.execute(
                "SELECT epoch FROM streams WHERE company=? AND stream=?",(company,stream)).fetchone()
            if s is None: raise ControlStoreError("stream_not_registered")
            self.db.execute(
                "INSERT INTO actions(action_id,company,stream,approval_id,idempotency_key,intent_json,"
                "enqueue_epoch,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,'queued',?,?)",
                (action_id,company,stream,approval_id,idempotency_key,encoded,s["epoch"],now,now))
            self._audit(company,stream,"action_queued",now,
                        {"action_id":action_id,"approval_id":approval_id,
                         "idempotency_key":idempotency_key,"enqueue_epoch":s["epoch"]})
            self.db.execute("COMMIT")
            return "queued"
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def revoke_approval(self, approval_id, *, company, now):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT stream FROM approvals WHERE approval_id=? AND company=?",
                (approval_id,company)).fetchone()
            if row is None:
                self.db.execute("COMMIT")
                return False
            cur = self.db.execute(
                "UPDATE approvals SET revoked=1 WHERE approval_id=? AND company=? AND revoked=0",
                (approval_id,company))
            if cur.rowcount:
                self._audit(company,row["stream"],"approval_revoked",now,{"approval_id":approval_id})
            self.db.execute("COMMIT")
            return cur.rowcount == 1
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def quarantine(self, *, company, stream, incident_id, reason, checkpoint_digest, now):
        if not self.required(company,stream,incident_id,reason,checkpoint_digest):
            raise ControlStoreError("quarantine_fields_required")
        if isinstance(now,bool) or not isinstance(now,int):
            raise ControlStoreError("invalid_time")
        if len(checkpoint_digest)!=64 or any(c not in "0123456789abcdef" for c in checkpoint_digest):
            raise ControlStoreError("checkpoint_digest_invalid")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT * FROM streams WHERE company=? AND stream=?",(company,stream)).fetchone()
            if row is None: raise ControlStoreError("stream_not_registered")
            if (row["status"]==QUARANTINED and row["incident_id"]==incident_id
                and row["checkpoint_digest"]==checkpoint_digest):
                self.db.execute("COMMIT")
                return row["epoch"]
            epoch = row["epoch"]+1
            self.db.execute(
                "UPDATE streams SET status=?,epoch=?,incident_id=?,checkpoint_digest=?,updated_at=? "
                "WHERE company=? AND stream=?",
                (QUARANTINED,epoch,incident_id,checkpoint_digest,now,company,stream))
            payload={"incident_id":incident_id,"reason":reason,
                     "checkpoint_digest":checkpoint_digest,"epoch":epoch}
            self._audit(company,stream,"stream_quarantined",now,payload)
            self.db.execute("INSERT INTO control_outbox VALUES(?,?,?,?,?,?,?,NULL)",
                (str(uuid.uuid4()),company,stream,epoch,"stream_quarantined",self.canon(payload),now))
            self.db.execute("COMMIT")
            return epoch
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def release_stream(self, *, company, stream, incident_id, checkpoint_digest,
                       owner_approval, recovery_assessment, owner_verifier,
                       assessment_verifier, now):
        if isinstance(now,bool) or not isinstance(now,int):
            raise ControlStoreError("invalid_time")
        if not callable(getattr(owner_verifier,"verify",None)) or not callable(
            getattr(assessment_verifier,"verify",None)):
            raise ControlStoreError("trusted_release_verifiers_required")
        if not isinstance(owner_approval,dict) or not isinstance(recovery_assessment,dict):
            raise ControlStoreError("signed_release_documents_required")
        row=self.db.execute("SELECT * FROM streams WHERE company=? AND stream=?",
                            (company,stream)).fetchone()
        if row is None or row["status"]!=QUARANTINED: raise ControlStoreError("stream_not_quarantined")
        if row["incident_id"]!=incident_id or row["checkpoint_digest"]!=checkpoint_digest:
            raise ControlStoreError("quarantine_scope_mismatch")
        expected={"company":company,"stream":stream,"incident_id":incident_id,
                  "checkpoint_digest":checkpoint_digest,"action":"release_quarantine",
                  "audience":"recovery-authority"}
        try:
            approval=owner_verifier.verify(owner_approval,expected=expected,now=now)
            assessment=assessment_verifier.verify(
                recovery_assessment,expected={k:v for k,v in expected.items() if k!="action"},now=now)
        except Exception as exc:
            raise ControlStoreError("release_verification_failed") from exc
        if not isinstance(approval,dict) or approval.get("verified") is not True:
            raise ControlStoreError("owner_approval_not_verified")
        if not isinstance(assessment,dict) or assessment.get("verified") is not True:
            raise ControlStoreError("assessment_not_verified")
        required=("db_integrity","audit_chain_valid","checkpoint_match","revocations_current",
                  "emergency_stop_clear","unknown_actions_reconciled")
        if any(assessment.get(k) is not True for k in required):
            raise ControlStoreError("assessment_controls_incomplete")
        for k,v in expected.items():
            if approval.get(k)!=v or (k!="action" and assessment.get(k)!=v):
                raise ControlStoreError("release_scope_mismatch")
        aid,nonce,digest=approval.get("approval_id"),approval.get("nonce"),assessment.get("assessment_digest")
        if not self.required(aid,nonce,digest): raise ControlStoreError("release_claims_missing")
        for doc,label in ((approval,"owner_approval"),(assessment,"assessment")):
            if (isinstance(doc.get("expires_at"),bool) or not isinstance(doc.get("expires_at"),int)
                or now>=doc["expires_at"]):
                raise ControlStoreError(label+"_expired")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            cur=self.db.execute("SELECT * FROM streams WHERE company=? AND stream=?",(company,stream)).fetchone()
            if (cur is None or cur["status"]!=QUARANTINED or cur["incident_id"]!=incident_id
                or cur["checkpoint_digest"]!=checkpoint_digest or cur["epoch"]!=row["epoch"]):
                raise ControlStoreError("quarantine_changed_during_verification")
            self.db.execute(
                "INSERT INTO release_consumptions VALUES(?,?,?,?,?,?,?)",
                (aid,nonce,company,stream,incident_id,checkpoint_digest,now))
            epoch=cur["epoch"]+1
            self.db.execute("UPDATE streams SET status=?,epoch=?,updated_at=? WHERE company=? AND stream=?",
                            (ACTIVE,epoch,now,company,stream))
            payload={"incident_id":incident_id,"checkpoint_digest":checkpoint_digest,
                     "approval_id":aid,"nonce":nonce,"assessment_digest":digest,"epoch":epoch}
            self._audit(company,stream,"stream_released_by_owner",now,payload)
            self.db.execute("INSERT INTO control_outbox VALUES(?,?,?,?,?,?,?,NULL)",
                (str(uuid.uuid4()),company,stream,epoch,"stream_released",self.canon(payload),now))
            self.db.execute("COMMIT")
            return epoch
        except sqlite3.IntegrityError as exc:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            used=self.db.execute(
                "SELECT 1 FROM release_consumptions WHERE approval_id=? OR nonce=? LIMIT 1",
                (aid,nonce)).fetchone()
            if used:
                raise ControlStoreError("release_replay_or_conflict") from exc
            raise
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def authorize_and_start(self, action_id, *, company, stream, agent, task,
                            operation, resource, policy_version, now):
        """Authorization linearization point. The sender is deliberately absent."""
        if isinstance(now,bool) or not isinstance(now,int):
            raise ControlStoreError("invalid_time")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            a=self.db.execute("SELECT * FROM actions WHERE action_id=?",(action_id,)).fetchone()
            reason=None
            if a is None: reason="action_not_found"
            elif (a["company"],a["stream"])!=(company,stream): reason="company_or_stream_mismatch"
            elif a["state"]!="queued": reason="action_not_queued"
            s=self.db.execute("SELECT * FROM streams WHERE company=? AND stream=?",(company,stream)).fetchone()
            if reason is None and s is None: reason="stream_not_registered"
            if reason is None and s["status"]!=ACTIVE: reason="stream_not_active"
            if reason is None and a["enqueue_epoch"]!=s["epoch"]: reason="stale_recovery_epoch"
            p=self.db.execute("SELECT * FROM approvals WHERE approval_id=?",(a["approval_id"],)).fetchone() if a else None
            if reason is None and p is None: reason="approval_not_found"
            if reason is None and p["revoked"]: reason="approval_revoked"
            if reason is None and now>=p["expires_at"]: reason="approval_expired"
            if reason is None and (p["company"],p["stream"],p["agent"],p["task"],p["operation"],
                p["resource"],p["policy_version"])!=(company,stream,agent,task,operation,resource,policy_version):
                reason="approval_scope_mismatch"
            if reason is None:
                amount=json.loads(a["intent_json"]).get("amount_minor")
                if amount is not None and (isinstance(amount,bool) or not isinstance(amount,int) or amount<0):
                    reason="invalid_action_amount"
                elif p["amount_limit_minor"] is not None and (
                    amount is None or amount>p["amount_limit_minor"]):
                    reason="amount_limit_exceeded"
            if reason:
                if a and a["company"]==company and a["stream"]==stream:
                    self._audit(company,stream,"dispatch_denied",now,{"action_id":action_id,"reason":reason})
                self.db.execute("COMMIT")
                return {"allowed":False,"reason":reason}
            self.db.execute(
                "UPDATE approvals SET consumed_action_id=?,consumed_at=? "
                "WHERE approval_id=? AND consumed_action_id IS NULL AND revoked=0",
                (action_id,now,p["approval_id"]))
            if self.db.execute("SELECT changes()").fetchone()[0]!=1:
                raise ControlStoreError("approval_already_consumed")
            self.db.execute("UPDATE actions SET state='dispatch_started',updated_at=? "
                            "WHERE action_id=? AND state='queued'",(now,action_id))
            if self.db.execute("SELECT changes()").fetchone()[0]!=1:
                raise ControlStoreError("action_state_race")
            self._audit(company,stream,"dispatch_started",now,
                {"action_id":action_id,"approval_id":p["approval_id"],
                 "idempotency_key":a["idempotency_key"],"recovery_epoch":s["epoch"]})
            result={"allowed":True,"action_id":action_id,"idempotency_key":a["idempotency_key"],
                    "intent":json.loads(a["intent_json"]),"recovery_epoch":s["epoch"]}
            self.db.execute("COMMIT")
            return result
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def record_sender_result(self, action_id, *, result, now):
        states={"accepted":"sent","rejected":"failed","timeout":"outcome_unknown",
                "exception":"outcome_unknown"}
        if result not in states: raise ControlStoreError("invalid_sender_result")
        if isinstance(now,bool) or not isinstance(now,int):
            raise ControlStoreError("invalid_time")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            a=self.db.execute("SELECT * FROM actions WHERE action_id=?",(action_id,)).fetchone()
            if a is None or a["state"]!="dispatch_started":
                raise ControlStoreError("action_not_dispatch_started")
            state=states[result]
            self.db.execute("UPDATE actions SET state=?,updated_at=? WHERE action_id=?",
                            (state,now,action_id))
            self._audit(a["company"],a["stream"],"sender_result",now,
                        {"action_id":action_id,"state":state})
            self.db.execute("COMMIT")
            return state
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def action_state(self, action_id):
        r=self.db.execute("SELECT state FROM actions WHERE action_id=?",(action_id,)).fetchone()
        return r["state"] if r else None

    def stream_state(self, company, stream):
        r=self.db.execute("SELECT * FROM streams WHERE company=? AND stream=?",(company,stream)).fetchone()
        return dict(r) if r else None

    def verify_audit(self, company, stream):
        rows=self.db.execute("SELECT * FROM audit WHERE company=? AND stream=? ORDER BY sequence",
                             (company,stream)).fetchall()
        previous=GENESIS
        for r in rows:
            body={"company":company,"stream":stream,"event_type":r["event_type"],
                  "occurred_at":r["occurred_at"],"payload":json.loads(r["payload_json"]),
                  "previous_hash":previous}
            digest=hashlib.sha256(self.canon(body).encode("utf-8")).hexdigest()
            if r["previous_hash"]!=previous or r["event_hash"]!=digest: return False
            previous=digest
        return True

    def close(self):
        self.db.close()

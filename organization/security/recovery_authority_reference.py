"""Owner-gated recovery authority and quarantine reference.

Offline SQLite prototype only. Trusted signature verifiers are injected by
application wiring. No dispatch, broker, wallet, or external side effects.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3

GENESIS="0"*64

class RecoveryAuthorityError(ValueError):
    pass

class SQLiteRecoveryAuthority:
    def __init__(self,path,*,owner_approval_verifier,recovery_assessment_verifier):
        if not callable(getattr(owner_approval_verifier,"verify",None)):
            raise RecoveryAuthorityError("trusted_owner_approval_verifier_required")
        if not callable(getattr(recovery_assessment_verifier,"verify",None)):
            raise RecoveryAuthorityError("trusted_recovery_assessment_verifier_required")
        self._owner_verifier=owner_approval_verifier
        self._assessment_verifier=recovery_assessment_verifier
        self.db=sqlite3.connect(str(path),timeout=10,isolation_level=None)
        self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS recovery_streams(
          company TEXT NOT NULL, stream TEXT NOT NULL, status TEXT NOT NULL
            CHECK(status IN ('dispatch_disabled','quarantined','active')),
          incident_id TEXT, reason TEXT, checkpoint_digest TEXT,
          last_approval_id TEXT, last_assessment_digest TEXT,
          updated_at INTEGER NOT NULL,
          PRIMARY KEY(company,stream));
        CREATE TABLE IF NOT EXISTS release_consumptions(
          approval_id TEXT PRIMARY KEY, nonce TEXT NOT NULL UNIQUE,
          company TEXT NOT NULL, stream TEXT NOT NULL, incident_id TEXT NOT NULL,
          checkpoint_digest TEXT NOT NULL, consumed_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS recovery_audit(
          seq INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT NOT NULL,
          stream TEXT NOT NULL, kind TEXT NOT NULL, at INTEGER NOT NULL,
          payload TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS recovery_audit_scope
          ON recovery_audit(company,stream,seq);
        """)

    @staticmethod
    def canon(value):
        return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)

    def register_stream(self,*,company,stream,now):
        if any(not isinstance(x,str) or not x.strip() for x in (company,stream)):
            raise RecoveryAuthorityError("invalid_stream_identity")
        if isinstance(now,bool) or not isinstance(now,int):
            raise RecoveryAuthorityError("invalid_time")
        self.db.execute("INSERT INTO recovery_streams VALUES(?,?,'dispatch_disabled',NULL,NULL,NULL,NULL,NULL,?)",
                        (company,stream,now))

    def _append(self,company,stream,kind,now,payload):
        row=self.db.execute("""SELECT hash FROM recovery_audit
          WHERE company=? AND stream=? ORDER BY seq DESC LIMIT 1""",(company,stream)).fetchone()
        prev=row["hash"] if row else GENESIS
        body={"company":company,"stream":stream,"kind":kind,"at":now,"payload":payload,"prev":prev}
        digest=hashlib.sha256(self.canon(body).encode()).hexdigest()
        self.db.execute("""INSERT INTO recovery_audit
          (company,stream,kind,at,payload,prev,hash) VALUES(?,?,?,?,?,?,?)""",
          (company,stream,kind,now,self.canon(payload),prev,digest))

    def quarantine(self,*,company,stream,incident_id,reason,checkpoint_digest,now):
        fields=(company,stream,incident_id,reason,checkpoint_digest)
        if any(not isinstance(x,str) or not x.strip() for x in fields):
            raise RecoveryAuthorityError("quarantine_fields_invalid")
        if len(checkpoint_digest)!=64 or any(c not in "0123456789abcdef" for c in checkpoint_digest):
            raise RecoveryAuthorityError("checkpoint_digest_invalid")
        if isinstance(now,bool) or not isinstance(now,int):
            raise RecoveryAuthorityError("invalid_time")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT * FROM recovery_streams WHERE company=? AND stream=?",
                                (company,stream)).fetchone()
            if row is None: raise RecoveryAuthorityError("stream_not_registered")
            if row["status"]=="quarantined" and row["incident_id"]==incident_id and row["checkpoint_digest"]==checkpoint_digest:
                self.db.execute("COMMIT"); return "duplicate_quarantine"
            self.db.execute("""UPDATE recovery_streams SET status='quarantined',incident_id=?,
              reason=?,checkpoint_digest=?,last_approval_id=NULL,last_assessment_digest=NULL,
              updated_at=? WHERE company=? AND stream=?""",
              (incident_id,reason,checkpoint_digest,now,company,stream))
            self._append(company,stream,"stream_quarantined",now,
              {"incident_id":incident_id,"reason":reason,"checkpoint_digest":checkpoint_digest})
            self.db.execute("COMMIT"); return "quarantined"
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def release(self,*,company,stream,incident_id,checkpoint_digest,
                owner_approval,recovery_assessment,now):
        """Require independently verified assessment AND exact one-time owner approval."""
        if isinstance(now,bool) or not isinstance(now,int):
            raise RecoveryAuthorityError("invalid_time")
        row=self.db.execute("SELECT * FROM recovery_streams WHERE company=? AND stream=?",
                            (company,stream)).fetchone()
        if row is None: raise RecoveryAuthorityError("stream_not_registered")
        if row["status"]=="active":
            if (row["last_approval_id"]==owner_approval.get("approval_id") and
                row["last_assessment_digest"]==recovery_assessment.get("assessment_digest") and
                row["incident_id"]==incident_id and row["checkpoint_digest"]==checkpoint_digest):
                return "duplicate_same_release"
            raise RecoveryAuthorityError("stream_not_quarantined")
        if row["status"]!="quarantined": raise RecoveryAuthorityError("stream_not_quarantined")
        if row["incident_id"]!=incident_id or row["checkpoint_digest"]!=checkpoint_digest:
            raise RecoveryAuthorityError("quarantine_scope_mismatch")

        expected={"company":company,"stream":stream,"incident_id":incident_id,
                  "checkpoint_digest":checkpoint_digest,"action":"release_quarantine",
                  "audience":"recovery-authority"}
        try:
            approval=self._owner_verifier.verify(owner_approval,expected=expected,now=now)
            assessment=self._assessment_verifier.verify(recovery_assessment,
                expected={"company":company,"stream":stream,"incident_id":incident_id,
                          "checkpoint_digest":checkpoint_digest,"audience":"recovery-authority"},
                now=now)
        except Exception as exc:
            raise RecoveryAuthorityError("trusted_release_verification_failed") from exc

        if not isinstance(approval,dict) or approval.get("verified") is not True:
            raise RecoveryAuthorityError("owner_approval_not_verified")
        if not isinstance(assessment,dict) or assessment.get("verified") is not True:
            raise RecoveryAuthorityError("recovery_assessment_not_verified")
        required=("db_integrity","audit_chain_valid","checkpoint_match",
                  "revocations_current","emergency_stop_clear","unknown_actions_reconciled")
        if any(assessment.get(k) is not True for k in required):
            raise RecoveryAuthorityError("recovery_assessment_controls_incomplete")
        for key,value in expected.items():
            if approval.get(key)!=value:
                raise RecoveryAuthorityError("owner_approval_scope_mismatch:"+key)
            if key!="action" and assessment.get(key)!=value:
                raise RecoveryAuthorityError("recovery_assessment_scope_mismatch:"+key)
        for claim,key in ((approval,"approval_id"),(approval,"nonce"),
                          (assessment,"assessment_digest")):
            if not isinstance(claim.get(key),str) or not claim[key].strip():
                raise RecoveryAuthorityError("verified_release_claim_missing:"+key)
        if (isinstance(approval.get("expires_at"),bool) or
            not isinstance(approval.get("expires_at"),int) or now>=approval["expires_at"]):
            raise RecoveryAuthorityError("owner_approval_expired")
        if (isinstance(assessment.get("expires_at"),bool) or
            not isinstance(assessment.get("expires_at"),int) or now>=assessment["expires_at"]):
            raise RecoveryAuthorityError("recovery_assessment_expired")

        self.db.execute("BEGIN IMMEDIATE")
        try:
            current=self.db.execute("SELECT * FROM recovery_streams WHERE company=? AND stream=?",
                                    (company,stream)).fetchone()
            if (current is None or current["status"]!="quarantined" or
                current["incident_id"]!=incident_id or
                current["checkpoint_digest"]!=checkpoint_digest):
                raise RecoveryAuthorityError("quarantine_changed_during_verification")
            self.db.execute("""INSERT INTO release_consumptions
              (approval_id,nonce,company,stream,incident_id,checkpoint_digest,consumed_at)
              VALUES(?,?,?,?,?,?,?)""",
              (approval["approval_id"],approval["nonce"],company,stream,incident_id,checkpoint_digest,now))
            self.db.execute("""UPDATE recovery_streams SET status='active',last_approval_id=?,
              last_assessment_digest=?,updated_at=? WHERE company=? AND stream=? AND status='quarantined'""",
              (approval["approval_id"],assessment["assessment_digest"],now,company,stream))
            if self.db.execute("SELECT changes()").fetchone()[0]!=1:
                raise RecoveryAuthorityError("release_state_race")
            self._append(company,stream,"stream_released_by_owner",now,
              {"incident_id":incident_id,"checkpoint_digest":checkpoint_digest,
               "approval_id":approval["approval_id"],"assessment_digest":assessment["assessment_digest"]})
            self.db.execute("COMMIT")
            return "released"
        except sqlite3.IntegrityError as exc:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise RecoveryAuthorityError("owner_approval_replay_or_release_conflict") from exc
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def status(self,company,stream):
        row=self.db.execute("SELECT status FROM recovery_streams WHERE company=? AND stream=?",
                            (company,stream)).fetchone()
        return row["status"] if row else None

    def verify_audit(self,company,stream):
        rows=self.db.execute("""SELECT * FROM recovery_audit
          WHERE company=? AND stream=? ORDER BY seq""",(company,stream)).fetchall()
        prev=GENESIS
        for row in rows:
            body={"company":company,"stream":stream,"kind":row["kind"],"at":row["at"],
                  "payload":json.loads(row["payload"]),"prev":prev}
            digest=hashlib.sha256(self.canon(body).encode()).hexdigest()
            if row["prev"]!=prev or row["hash"]!=digest: return False
            prev=digest
        return True

    def close(self):
        self.db.close()

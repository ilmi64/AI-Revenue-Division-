"""Atomic evidence receipt + reconciliation prototype.

Offline SQLite reference only. Signature verification is performed by the
trusted ReceiverEvidenceVerifier before this method is called. The verified
claim's digest is recomputed here so the raw nonce/evidence identity cannot be
swapped between verification and durable recording.
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3

GENESIS = "0" * 64
HEX64 = re.compile(r"^[0-9a-f]{64}$")

class ReconciliationError(ValueError):
    pass

class EvidenceReplayError(ReconciliationError):
    pass

class SQLiteAtomicReconciliationStore:
    """Single-host reference; replay receipt, state transition and audit are atomic."""
    def __init__(self, path, *, trusted_verifier):
        if not callable(getattr(trusted_verifier, "verify_for_atomic_reconciliation", None)):
            raise ReconciliationError("trusted_receiver_verifier_required")
        self._trusted_verifier = trusted_verifier
        self.db = sqlite3.connect(str(path), timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS actions(
          action_id TEXT PRIMARY KEY, company TEXT NOT NULL,
          receiver_account TEXT NOT NULL, idempotency_key TEXT NOT NULL,
          state TEXT NOT NULL CHECK(state IN
            ('outcome_unknown','reconciled_applied','reconciled_not_applied','quarantined')),
          evidence_id TEXT, payload_sha256 TEXT);
        CREATE TABLE IF NOT EXISTS evidence_receipts(
          issuer TEXT NOT NULL, nonce TEXT NOT NULL, evidence_id TEXT NOT NULL,
          payload_sha256 TEXT NOT NULL, action_id TEXT NOT NULL,
          company TEXT NOT NULL, outcome TEXT NOT NULL,
          observed_at INTEGER NOT NULL, accepted_at INTEGER NOT NULL,
          PRIMARY KEY(issuer,nonce), UNIQUE(issuer,evidence_id),
          FOREIGN KEY(action_id) REFERENCES actions(action_id));
        CREATE TABLE IF NOT EXISTS audit(
          seq INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT NOT NULL,
          kind TEXT NOT NULL, at INTEGER NOT NULL, payload TEXT NOT NULL,
          prev TEXT NOT NULL, hash TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS audit_company_seq ON audit(company,seq);
        """)

    @staticmethod
    def canon(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def register_unknown_action(self, *, action_id, company, receiver_account, idempotency_key):
        fields=(action_id,company,receiver_account,idempotency_key)
        if any(not isinstance(x,str) or not x.strip() for x in fields):
            raise ReconciliationError("invalid_action_identity")
        self.db.execute("INSERT INTO actions VALUES(?,?,?,?,'outcome_unknown',NULL,NULL)", fields)

    def _append_audit(self, company, kind, now, payload):
        last=self.db.execute("SELECT hash FROM audit WHERE company=? ORDER BY seq DESC LIMIT 1",
                             (company,)).fetchone()
        prev=last["hash"] if last else GENESIS
        body={"company":company,"kind":kind,"at":now,"payload":payload,"prev":prev}
        digest=hashlib.sha256(self.canon(body).encode("utf-8")).hexdigest()
        self.db.execute("INSERT INTO audit(company,kind,at,payload,prev,hash) VALUES(?,?,?,?,?,?)",
                        (company,kind,now,self.canon(payload),prev,digest))

    def reconcile(self, *, action_id, evidence, now):
        """Verify with the store-bound trusted verifier, then atomically consume replay.

        Signature verification occurs before the write transaction. Durable replay
        consumption is exclusively the unique receipt insert inside the transaction.
        The action's immutable identity is reloaded and compared after BEGIN IMMEDIATE.
        """
        if not isinstance(evidence,dict):
            raise ReconciliationError("evidence_object_required")
        if isinstance(now,bool) or not isinstance(now,int):
            raise ReconciliationError("invalid_now")
        action_before=self.db.execute("SELECT * FROM actions WHERE action_id=?",
                                      (action_id,)).fetchone()
        if action_before is None:
            raise ReconciliationError("action_not_found")
        expected={"company":action_before["company"],"action_id":action_id,
                  "receiver_account":action_before["receiver_account"],
                  "idempotency_key":action_before["idempotency_key"],
                  "audience":"recovery-gateway"}
        try:
            verified=self._trusted_verifier.verify_for_atomic_reconciliation(
                evidence,expected=expected,now=now)
            from receiver_evidence_verifier_reference import ReceiverEvidenceVerifier
            payload=ReceiverEvidenceVerifier.canonical_signed_payload(evidence)
        except Exception as exc:
            raise ReconciliationError("trusted_evidence_verification_failed") from exc
        digest=hashlib.sha256(payload).hexdigest()
        if (not isinstance(verified,dict) or verified.get("verified") is not True or
            verified.get("payload_sha256") != digest or
            verified.get("issuer") != evidence.get("issuer") or
            verified.get("nonce") != evidence.get("nonce") or
            verified.get("evidence_id") != evidence.get("evidence_id") or
            verified.get("outcome") != evidence.get("outcome") or
            verified.get("observed_at") != evidence.get("observed_at")):
            raise ReconciliationError("trusted_verifier_claim_mismatch")

        state={"applied":"reconciled_applied","not_applied":"reconciled_not_applied",
               "inconclusive":"quarantined"}[evidence["outcome"]]
        issuer,nonce,eid=evidence["issuer"],evidence["nonce"],evidence["evidence_id"]
        self.db.execute("BEGIN IMMEDIATE")
        try:
            action=self.db.execute("SELECT * FROM actions WHERE action_id=?",(action_id,)).fetchone()
            if action is None:
                raise ReconciliationError("action_not_found")
            identity_before=(action_before["company"],action_before["receiver_account"],
                             action_before["idempotency_key"])
            identity_now=(action["company"],action["receiver_account"],action["idempotency_key"])
            if identity_before != identity_now:
                raise ReconciliationError("action_identity_changed_during_verification")
            by_nonce=self.db.execute(
              "SELECT * FROM evidence_receipts WHERE issuer=? AND nonce=?",
              (issuer,nonce)).fetchone()
            by_id=self.db.execute(
              "SELECT * FROM evidence_receipts WHERE issuer=? AND evidence_id=?",
              (issuer,eid)).fetchone()
            if by_nonce and by_id and by_nonce["nonce"] != by_id["nonce"]:
                raise EvidenceReplayError("evidence_nonce_and_id_conflict")
            prior=by_nonce or by_id
            if prior:
                same=(prior["issuer"],prior["nonce"],prior["evidence_id"],prior["payload_sha256"],
                      prior["action_id"],prior["company"],prior["outcome"],prior["observed_at"]) == (
                      issuer,nonce,eid,digest,action_id,action["company"],evidence["outcome"],
                      evidence["observed_at"])
                if not same:
                    raise EvidenceReplayError("evidence_replay_or_identity_conflict")
                if (action["state"] == state and action["evidence_id"] == eid and
                    action["payload_sha256"] == digest):
                    self.db.execute("COMMIT")
                    return "duplicate_same_result"
                raise ReconciliationError("receipt_state_invariant_violation")

            if action["state"] != "outcome_unknown":
                raise ReconciliationError("action_not_unknown")
            self.db.execute("""INSERT INTO evidence_receipts
              (issuer,nonce,evidence_id,payload_sha256,action_id,company,outcome,observed_at,accepted_at)
              VALUES(?,?,?,?,?,?,?,?,?)""",
              (issuer,nonce,eid,digest,action_id,action["company"],evidence["outcome"],
               evidence["observed_at"],now))
            self.db.execute("""UPDATE actions SET state=?,evidence_id=?,payload_sha256=?
              WHERE action_id=? AND state='outcome_unknown'""",(state,eid,digest,action_id))
            if self.db.execute("SELECT changes()").fetchone()[0] != 1:
                raise ReconciliationError("action_state_race")
            self._append_audit(action["company"],"action_reconciled",now,
              {"action_id":action_id,"evidence_id":eid,"payload_sha256":digest,"state":state})
            self.db.execute("COMMIT")
            return state
        except sqlite3.IntegrityError as exc:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            collision=self.db.execute("""SELECT 1 FROM evidence_receipts
              WHERE (issuer=? AND nonce=?) OR (issuer=? AND evidence_id=?) LIMIT 1""",
              (issuer,nonce,issuer,eid)).fetchone()
            if collision:
                raise EvidenceReplayError("evidence_unique_constraint_conflict") from exc
            raise
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def action_state(self, action_id):
        row=self.db.execute("SELECT state FROM actions WHERE action_id=?",(action_id,)).fetchone()
        return row["state"] if row else None

    def verify_audit(self, company):
        rows=self.db.execute("SELECT * FROM audit WHERE company=? ORDER BY seq",(company,)).fetchall()
        prev=GENESIS
        for row in rows:
            body={"company":company,"kind":row["kind"],"at":row["at"],
                  "payload":json.loads(row["payload"]),"prev":prev}
            digest=hashlib.sha256(self.canon(body).encode("utf-8")).hexdigest()
            if row["prev"] != prev or row["hash"] != digest: return False
            prev=digest
        return True

    def close(self):
        self.db.close()

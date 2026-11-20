"""Signed audit checkpoint verification and monotonic registry prototype.

Offline reference only. Real asymmetric signing, KMS/HSM and independent WORM
storage are injected production responsibilities and are not implemented here.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3

GENESIS = "0" * 64

class CheckpointError(ValueError):
    pass

def canonical_payload(checkpoint):
    return json.dumps({k:v for k,v in checkpoint.items() if k != "signature"},
                      sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

def checkpoint_digest(checkpoint):
    return hashlib.sha256(canonical_payload(checkpoint)).hexdigest()

def build_checkpoint(*, company_id, stream_id, sequence, event_hash, checkpoint_time,
                     schema_version, policy_version, signer_key_id, previous_checkpoint_digest,
                     signer):
    fields=(company_id,stream_id,schema_version,policy_version,signer_key_id,
            previous_checkpoint_digest,event_hash)
    if any(not isinstance(x,str) or not x.strip() for x in fields):
        raise CheckpointError("checkpoint_string_field_invalid")
    if isinstance(sequence,bool) or not isinstance(sequence,int) or sequence < 1:
        raise CheckpointError("checkpoint_sequence_invalid")
    if isinstance(checkpoint_time,bool) or not isinstance(checkpoint_time,int) or checkpoint_time < 0:
        raise CheckpointError("checkpoint_time_invalid")
    if len(event_hash)!=64 or any(c not in "0123456789abcdef" for c in event_hash):
        raise CheckpointError("event_hash_invalid")
    if len(previous_checkpoint_digest)!=64 or any(c not in "0123456789abcdef" for c in previous_checkpoint_digest):
        raise CheckpointError("previous_checkpoint_digest_invalid")
    if not callable(signer):
        raise CheckpointError("trusted_signer_required")
    checkpoint={"company_id":company_id,"stream_id":stream_id,"sequence":sequence,
      "event_hash":event_hash,"checkpoint_time":checkpoint_time,
      "schema_version":schema_version,"policy_version":policy_version,
      "signer_key_id":signer_key_id,
      "previous_checkpoint_digest":previous_checkpoint_digest}
    signature=signer(signer_key_id,canonical_payload(checkpoint))
    if not isinstance(signature,str) or not signature.strip():
        raise CheckpointError("signer_returned_invalid_signature")
    checkpoint["signature"]=signature
    return checkpoint

def verify_checkpoint(checkpoint, *, trusted_key_ids, signature_verifier,
                      expected_company, expected_stream, now,
                      max_age_seconds=86400, future_skew_seconds=30):
    required=("company_id","stream_id","sequence","event_hash","checkpoint_time",
      "schema_version","policy_version","signer_key_id",
      "previous_checkpoint_digest","signature")
    if not isinstance(checkpoint,dict) or any(k not in checkpoint for k in required):
        raise CheckpointError("checkpoint_fields_missing")
    for key in ("company_id","stream_id","event_hash","schema_version","policy_version",
                "signer_key_id","previous_checkpoint_digest","signature"):
        if not isinstance(checkpoint[key],str) or not checkpoint[key].strip():
            raise CheckpointError("checkpoint_field_invalid:"+key)
    if checkpoint["company_id"] != expected_company or checkpoint["stream_id"] != expected_stream:
        raise CheckpointError("checkpoint_scope_mismatch")
    seq=checkpoint["sequence"]
    stamp=checkpoint["checkpoint_time"]
    if isinstance(seq,bool) or not isinstance(seq,int) or seq < 1:
        raise CheckpointError("checkpoint_sequence_invalid")
    if isinstance(stamp,bool) or not isinstance(stamp,int):
        raise CheckpointError("checkpoint_time_invalid")
    if isinstance(now,bool) or not isinstance(now,int):
        raise CheckpointError("trusted_now_invalid")
    if stamp > now + future_skew_seconds:
        raise CheckpointError("checkpoint_from_future")
    if now-stamp > max_age_seconds:
        raise CheckpointError("checkpoint_stale")
    if checkpoint["signer_key_id"] not in set(trusted_key_ids):
        raise CheckpointError("checkpoint_signer_untrusted")
    if len(checkpoint["event_hash"])!=64 or any(c not in "0123456789abcdef" for c in checkpoint["event_hash"]):
        raise CheckpointError("event_hash_invalid")
    if len(checkpoint["previous_checkpoint_digest"])!=64 or any(
        c not in "0123456789abcdef" for c in checkpoint["previous_checkpoint_digest"]):
        raise CheckpointError("previous_checkpoint_digest_invalid")
    if not callable(signature_verifier):
        raise CheckpointError("trusted_signature_verifier_required")
    payload=canonical_payload(checkpoint)
    try:
        valid=signature_verifier(checkpoint["signer_key_id"],payload,checkpoint["signature"])
    except Exception as exc:
        raise CheckpointError("checkpoint_signature_verifier_failure") from exc
    if valid is not True:
        raise CheckpointError("checkpoint_signature_invalid")
    return {"verified":True,"digest":hashlib.sha256(payload).hexdigest(),
            "company_id":checkpoint["company_id"],"stream_id":checkpoint["stream_id"],
            "sequence":seq,"event_hash":checkpoint["event_hash"],
            "previous_checkpoint_digest":checkpoint["previous_checkpoint_digest"]}

class SQLiteCheckpointRegistry:
    """Local monotonic checkpoint ledger; not an independent WORM authority."""
    def __init__(self,path):
        self.db=sqlite3.connect(str(path),timeout=10,isolation_level=None)
        self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS checkpoints(
          company_id TEXT NOT NULL, stream_id TEXT NOT NULL, sequence INTEGER NOT NULL,
          digest TEXT NOT NULL, previous_digest TEXT NOT NULL, event_hash TEXT NOT NULL,
          payload_json TEXT NOT NULL, signature TEXT NOT NULL,
          PRIMARY KEY(company_id,stream_id,sequence),
          UNIQUE(company_id,stream_id,digest));
        CREATE TABLE IF NOT EXISTS checkpoint_heads(
          company_id TEXT NOT NULL, stream_id TEXT NOT NULL,
          sequence INTEGER NOT NULL, digest TEXT NOT NULL,
          PRIMARY KEY(company_id,stream_id));
        """)

    def accept(self,checkpoint, *, trusted_key_ids, signature_verifier, now,
               max_age_seconds=86400,future_skew_seconds=30):
        if not isinstance(checkpoint,dict):
            raise CheckpointError("checkpoint_object_required")
        verified=verify_checkpoint(checkpoint,trusted_key_ids=trusted_key_ids,
          signature_verifier=signature_verifier,expected_company=checkpoint.get("company_id"),
          expected_stream=checkpoint.get("stream_id"),now=now,
          max_age_seconds=max_age_seconds,future_skew_seconds=future_skew_seconds)
        digest=verified["digest"]
        company,stream=verified["company_id"],verified["stream_id"]
        self.db.execute("BEGIN IMMEDIATE")
        try:
            head=self.db.execute("SELECT * FROM checkpoint_heads WHERE company_id=? AND stream_id=?",
                                 (company,stream)).fetchone()
            if head:
                if verified["sequence"] == head["sequence"] and digest == head["digest"]:
                    self.db.execute("COMMIT")
                    return "duplicate_same_checkpoint"
                if verified["sequence"] <= head["sequence"]:
                    raise CheckpointError("checkpoint_rollback_or_same_sequence_conflict")
                if verified["previous_checkpoint_digest"] != head["digest"]:
                    raise CheckpointError("checkpoint_chain_link_mismatch")
            elif verified["previous_checkpoint_digest"] != GENESIS:
                raise CheckpointError("checkpoint_genesis_link_mismatch")
            self.db.execute("""INSERT INTO checkpoints
              (company_id,stream_id,sequence,digest,previous_digest,event_hash,payload_json,signature)
              VALUES(?,?,?,?,?,?,?,?)""",
              (company,stream,verified["sequence"],digest,
               verified["previous_checkpoint_digest"],verified["event_hash"],
               json.dumps(checkpoint,sort_keys=True,separators=(",",":")),checkpoint["signature"]))
            self.db.execute("""INSERT INTO checkpoint_heads(company_id,stream_id,sequence,digest)
              VALUES(?,?,?,?) ON CONFLICT(company_id,stream_id) DO UPDATE SET
              sequence=excluded.sequence,digest=excluded.digest""",
              (company,stream,verified["sequence"],digest))
            self.db.execute("COMMIT")
            return "accepted"
        except sqlite3.IntegrityError as exc:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise CheckpointError("checkpoint_registry_integrity_conflict") from exc
        except Exception:
            if self.db.in_transaction: self.db.execute("ROLLBACK")
            raise

    def verify_restore(self, *, company_id, stream_id, restored_sequence, restored_event_hash):
        head=self.db.execute("SELECT * FROM checkpoint_heads WHERE company_id=? AND stream_id=?",
                             (company_id,stream_id)).fetchone()
        if head is None:
            return False
        return (restored_sequence == head["sequence"] and
                restored_event_hash == self.db.execute(
                  "SELECT event_hash FROM checkpoints WHERE company_id=? AND stream_id=? AND sequence=?",
                  (company_id,stream_id,head["sequence"])).fetchone()["event_hash"])

    def close(self):
        self.db.close()

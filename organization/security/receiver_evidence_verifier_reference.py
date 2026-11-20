"""Trusted receiver-evidence verification boundary (offline reference).

Cryptographic signature verification is injected by a trusted host adapter.
This module deliberately does not accept a caller-supplied authenticated=True flag.
"""
from __future__ import annotations
import hashlib, json

class EvidenceError(ValueError):
    pass

class ReceiverEvidenceVerifier:
    REQUIRED = ("evidence_id","issuer","audience","company","action_id",
                "receiver_account","idempotency_key","outcome","observed_at",
                "nonce","signature")
    OUTCOMES = {"applied","not_applied","inconclusive"}

    def __init__(self, signature_verifier, trusted_issuers, *, max_age_seconds=300,
                 future_skew_seconds=30):
        if not callable(signature_verifier):
            raise ValueError("trusted_signature_verifier_required")
        if not trusted_issuers:
            raise ValueError("trusted_issuer_registry_required")
        self._verify_signature = signature_verifier
        self._issuers = frozenset(trusted_issuers)
        self.max_age = max_age_seconds
        self.future_skew = future_skew_seconds
        self._seen = set()  # prototype only; production requires durable shared replay store

    @staticmethod
    def canonical_signed_payload(evidence):
        payload={k:v for k,v in evidence.items() if k!="signature"}
        return json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

    def verify(self, evidence, *, expected, now):
        if not isinstance(evidence,dict) or any(k not in evidence for k in self.REQUIRED):
            raise EvidenceError("missing_evidence_fields")
        if evidence["issuer"] not in self._issuers:
            raise EvidenceError("untrusted_issuer")
        if evidence["outcome"] not in self.OUTCOMES:
            raise EvidenceError("invalid_outcome")
        for key in ("evidence_id","issuer","audience","company","action_id",
                    "receiver_account","idempotency_key","nonce","signature"):
            if not isinstance(evidence[key],str) or not evidence[key].strip():
                raise EvidenceError("invalid_string_field:"+key)
        observed=evidence["observed_at"]
        if isinstance(observed,bool) or not isinstance(observed,int):
            raise EvidenceError("invalid_observed_at")
        if observed > now + self.future_skew:
            raise EvidenceError("evidence_from_future")
        if now-observed > self.max_age:
            raise EvidenceError("stale_evidence")
        for key,value in expected.items():
            if evidence.get(key) != value:
                raise EvidenceError("evidence_scope_mismatch:"+key)
        replay=(evidence["issuer"],evidence["nonce"])
        if replay in self._seen:
            raise EvidenceError("evidence_replay")
        signed=self.canonical_signed_payload(evidence)
        if not self._verify_signature(evidence["issuer"],signed,evidence["signature"]):
            raise EvidenceError("invalid_signature")
        self._seen.add(replay)
        digest=hashlib.sha256(signed).hexdigest()
        return {"verified":True,"evidence_id":evidence["evidence_id"],
                "outcome":evidence["outcome"],"payload_sha256":digest,
                "issuer":evidence["issuer"],"observed_at":observed}


import hashlib, unittest
from receiver_evidence_verifier_reference import ReceiverEvidenceVerifier, EvidenceError

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        self.v=ReceiverEvidenceVerifier(
          lambda issuer,payload,signature: self._signature(issuer,payload,signature),
          {"receiver-A"},max_age_seconds=300,future_skew_seconds=30)
        self.e={"evidence_id":"ev1","issuer":"receiver-A","audience":"recovery-gateway",
          "company":"coA","action_id":"act1","receiver_account":"acct1",
          "idempotency_key":"idem1","outcome":"applied","observed_at":950,
          "nonce":"n1","signature":""}\n        self.e["signature"]=hashlib.sha256(self.v.canonical_signed_payload(self.e)).hexdigest()
        self.expected={"audience":"recovery-gateway","company":"coA","action_id":"act1",
          "receiver_account":"acct1","idempotency_key":"idem1"}
    def _signature(self,issuer,payload,signature):
        self.calls.append((issuer,payload,signature))
        return signature==hashlib.sha256(payload).hexdigest() and issuer=="receiver-A"
    def test_valid_bound_evidence(self):
        result=self.v.verify(self.e,expected=self.expected,now=1000)
        self.assertTrue(result["verified"])
        self.assertEqual(result["outcome"],"applied")
    def test_bad_signature_rejected(self):
        e=dict(self.e,signature="forged")
        with self.assertRaises(EvidenceError): self.v.verify(e,expected=self.expected,now=1000)
    def test_untrusted_issuer_rejected(self):
        e=dict(self.e,issuer="unknown")
        with self.assertRaises(EvidenceError): self.v.verify(e,expected=self.expected,now=1000)
    def test_action_or_account_mismatch_rejected(self):
        with self.assertRaises(EvidenceError):
            self.v.verify(self.e,expected=dict(self.expected,action_id="other"),now=1000)
    def test_stale_evidence_rejected(self):
        e=dict(self.e,observed_at=600,nonce="n2")
        with self.assertRaises(EvidenceError): self.v.verify(e,expected=self.expected,now=1000)
    def test_future_evidence_rejected(self):
        e=dict(self.e,observed_at=1031,nonce="n2")
        with self.assertRaises(EvidenceError): self.v.verify(e,expected=self.expected,now=1000)
    def test_replay_rejected(self):
        self.v.verify(self.e,expected=self.expected,now=1000)
        with self.assertRaises(EvidenceError): self.v.verify(self.e,expected=self.expected,now=1000)
    def test_missing_fields_rejected(self):
        e=dict(self.e); del e["signature"]
        with self.assertRaises(EvidenceError): self.v.verify(e,expected=self.expected,now=1000)
    def test_signature_binds_payload(self):
        e=dict(self.e,outcome="not_applied")
        with self.assertRaises(EvidenceError): self.v.verify(e,expected=self.expected,now=1000)
    def test_no_verifier_no_instance(self):
        with self.assertRaises(ValueError): ReceiverEvidenceVerifier(None,{"receiver-A"})
if __name__=="__main__": unittest.main()

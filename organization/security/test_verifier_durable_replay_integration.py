import hashlib, json, os, tempfile, unittest
from durable_replay_store_reference import SQLiteReplayStore, ReplayError, ReplayConflict, ReplayStoreUnavailable
from receiver_evidence_verifier_reference import ReceiverEvidenceVerifier, EvidenceError

class VerifierDurableReplayIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,"replay.sqlite")
        self.store=SQLiteReplayStore(self.path)
        self.verifier=self.make_verifier(self.store)
    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()
    @staticmethod
    def make_verifier(store):
        return ReceiverEvidenceVerifier(
          lambda issuer,payload,signature: issuer=="receiver-A" and
            signature==hashlib.sha256(payload).hexdigest(),
          {"receiver-A"},max_age_seconds=300,future_skew_seconds=30,
          replay_store=store)
    def evidence(self):
        e={"evidence_id":"e-1","issuer":"receiver-A","audience":"recovery-gateway",
          "company":"coA","action_id":"a1","receiver_account":"acct1",
          "idempotency_key":"idem1","outcome":"applied","observed_at":100,
          "nonce":"nonce-1","signature":""}
        e["signature"]=hashlib.sha256(
          ReceiverEvidenceVerifier.canonical_signed_payload(e)).hexdigest()
        return e
    def test_verified_evidence_claims_durable_nonce(self):
        result=self.verifier.verify(self.evidence(),expected={
          "company":"coA","action_id":"a1","receiver_account":"acct1",
          "idempotency_key":"idem1","audience":"recovery-gateway"},now=101)
        self.assertTrue(result["verified"])
    def test_replay_rejected_after_verifier_restart(self):
        e=self.evidence()
        self.verifier.verify(e,expected={"company":"coA","action_id":"a1",
          "receiver_account":"acct1","idempotency_key":"idem1",
          "audience":"recovery-gateway"},now=101)
        self.verifier= self.make_verifier(self.store)
        with self.assertRaises(EvidenceError):
            self.verifier.verify(e,expected={"company":"coA","action_id":"a1",
              "receiver_account":"acct1","idempotency_key":"idem1",
              "audience":"recovery-gateway"},now=101)
    def test_invalid_signature_does_not_consume_nonce(self):
        e=self.evidence()
        e["signature"]="bad"
        with self.assertRaises(EvidenceError):
            self.verifier.verify(e,expected={"company":"coA","action_id":"a1",
              "receiver_account":"acct1","idempotency_key":"idem1",
              "audience":"recovery-gateway"},now=101)
        good=self.evidence()
        self.assertTrue(self.verifier.verify(good,expected={"company":"coA",
          "action_id":"a1","receiver_account":"acct1","idempotency_key":"idem1",
          "audience":"recovery-gateway"},now=101)["verified"])

    def test_replay_conflict_is_distinguished_from_store_outage(self):
        e=self.evidence()
        expected={"company":"coA","action_id":"a1","receiver_account":"acct1",
          "idempotency_key":"idem1","audience":"recovery-gateway"}
        self.verifier.verify(e,expected=expected,now=101)
        with self.assertRaisesRegex(EvidenceError,"evidence_replay"):
            self.verifier.verify(e,expected=expected,now=101)

    def test_storage_integrity_failure_is_not_reported_as_replay(self):
        self.store.db.execute("""CREATE TRIGGER reject_insert BEFORE INSERT ON receiver_evidence_replay
          BEGIN SELECT RAISE(ABORT,'storage write unavailable'); END;""")
        with self.assertRaisesRegex(EvidenceError,"replay_store_unavailable"):
            self.verifier.verify(self.evidence(),expected={"company":"coA","action_id":"a1",
              "receiver_account":"acct1","idempotency_key":"idem1",
              "audience":"recovery-gateway"},now=101)

if __name__=="__main__":
    unittest.main()

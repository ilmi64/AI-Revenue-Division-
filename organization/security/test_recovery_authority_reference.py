import hashlib, os, tempfile, unittest
from recovery_authority_reference import SQLiteRecoveryAuthority, RecoveryAuthorityError

class FakeOwnerVerifier:
    def verify(self,doc,*,expected,now):
        if doc.get("signature")!="valid-owner": raise ValueError("bad signature")
        if any(doc.get(k)!=v for k,v in expected.items()): raise ValueError("scope")
        return {"verified":True,**expected,"approval_id":doc["approval_id"],
                "nonce":doc["nonce"],"expires_at":doc["expires_at"]}

class FakeAssessmentVerifier:
    def verify(self,doc,*,expected,now):
        if doc.get("signature")!="valid-assessor": raise ValueError("bad signature")
        if any(doc.get(k)!=v for k,v in expected.items()): raise ValueError("scope")
        return {"verified":True,**expected,"assessment_digest":doc["assessment_digest"],
          "expires_at":doc["expires_at"],**{k:doc.get(k) for k in (
            "db_integrity","audit_chain_valid","checkpoint_match","revocations_current",
            "emergency_stop_clear","unknown_actions_reconciled")}}

class RecoveryAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,"recovery.sqlite")
        self.authority=SQLiteRecoveryAuthority(self.path,
          owner_approval_verifier=FakeOwnerVerifier(),
          recovery_assessment_verifier=FakeAssessmentVerifier())
        self.authority.register_stream(company="coA",stream="main",now=1)
        self.digest="a"*64
        self.authority.quarantine(company="coA",stream="main",incident_id="inc1",
          reason="restore_mismatch",checkpoint_digest=self.digest,now=2)
    def tearDown(self):
        self.authority.close()
        self.tmp.cleanup()
    def approval(self,**kw):
        d={"company":"coA","stream":"main","incident_id":"inc1",
          "checkpoint_digest":self.digest,"action":"release_quarantine",
          "audience":"recovery-authority","approval_id":"ap1","nonce":"n1",
          "expires_at":200,"signature":"valid-owner"}
        d.update(kw); return d
    def assessment(self,**kw):
        d={"company":"coA","stream":"main","incident_id":"inc1",
          "checkpoint_digest":self.digest,"audience":"recovery-authority",
          "assessment_digest":"b"*64,"expires_at":200,"signature":"valid-assessor",
          "db_integrity":True,"audit_chain_valid":True,"checkpoint_match":True,
          "revocations_current":True,"emergency_stop_clear":True,
          "unknown_actions_reconciled":True}
        d.update(kw); return d
    def release(self,approval=None,assessment=None):
        return self.authority.release(company="coA",stream="main",incident_id="inc1",
          checkpoint_digest=self.digest,owner_approval=approval or self.approval(),
          recovery_assessment=assessment or self.assessment(),now=10)
    def test_stream_starts_dispatch_disabled(self):
        self.assertEqual(self.authority.status("coA","main"),"quarantined")
    def test_quarantine_is_idempotent(self):
        self.assertEqual(self.authority.quarantine(company="coA",stream="main",
          incident_id="inc1",reason="restore_mismatch",checkpoint_digest=self.digest,now=3),
          "duplicate_quarantine")
    def test_release_requires_owner_and_assessor_signatures(self):
        self.assertEqual(self.release(),"released")
        self.assertEqual(self.authority.status("coA","main"),"active")
        self.assertTrue(self.authority.verify_audit("coA","main"))
    def test_invalid_owner_signature_denied(self):
        with self.assertRaises(RecoveryAuthorityError): self.release(approval=self.approval(signature="bad"))
        self.assertEqual(self.authority.status("coA","main"),"quarantined")
    def test_invalid_assessor_signature_denied(self):
        with self.assertRaises(RecoveryAuthorityError): self.release(assessment=self.assessment(signature="bad"))
        self.assertEqual(self.authority.status("coA","main"),"quarantined")
    def test_missing_recovery_control_denied(self):
        with self.assertRaisesRegex(RecoveryAuthorityError,"controls_incomplete"):
            self.release(assessment=self.assessment(checkpoint_match=False))
    def test_wrong_incident_or_checkpoint_denied(self):
        with self.assertRaises(RecoveryAuthorityError):
            self.authority.release(company="coA",stream="main",incident_id="other",
              checkpoint_digest=self.digest,owner_approval=self.approval(incident_id="other"),
              recovery_assessment=self.assessment(incident_id="other"),now=10)
    def test_expired_owner_approval_denied(self):
        with self.assertRaisesRegex(RecoveryAuthorityError,"approval_expired"):
            self.release(approval=self.approval(expires_at=10))
    def test_expired_assessment_denied(self):
        with self.assertRaisesRegex(RecoveryAuthorityError,"assessment_expired"):
            self.release(assessment=self.assessment(expires_at=10))
    def test_approval_nonce_consumed_once(self):
        self.release()
        self.authority.quarantine(company="coA",stream="main",incident_id="inc2",
          reason="new_incident",checkpoint_digest="c"*64,now=11)
        with self.assertRaises(RecoveryAuthorityError):
            self.authority.release(company="coA",stream="main",incident_id="inc2",
              checkpoint_digest="c"*64,owner_approval=self.approval(incident_id="inc2",
              checkpoint_digest="c"*64),recovery_assessment=self.assessment(incident_id="inc2",
              checkpoint_digest="c"*64),now=12)
        self.assertEqual(self.authority.status("coA","main"),"quarantined")
    def test_duplicate_release_retry_is_idempotent(self):
        self.assertEqual(self.release(),"released")
        self.assertEqual(self.release(),"duplicate_same_release")
    def test_other_company_cannot_read_or_release_stream(self):
        self.assertIsNone(self.authority.status("coB","main"))
        with self.assertRaises(RecoveryAuthorityError):
            self.authority.release(company="coB",stream="main",incident_id="inc1",
              checkpoint_digest=self.digest,owner_approval=self.approval(company="coB"),
              recovery_assessment=self.assessment(company="coB"),now=10)
    def test_audit_tampering_detected(self):
        self.authority.db.execute("UPDATE recovery_audit SET reason='tampered' WHERE seq=1")
        self.assertFalse(self.authority.verify_audit("coA","main"))

if __name__=="__main__": unittest.main()

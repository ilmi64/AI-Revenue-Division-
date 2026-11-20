import hashlib, os, tempfile, unittest
from signed_audit_checkpoint_reference import (
    build_checkpoint, verify_checkpoint, SQLiteCheckpointRegistry,
    CheckpointError, GENESIS)

def sign(key_id,payload):
    return hashlib.sha256(key_id.encode()+b":" + payload).hexdigest()

def verify(key_id,payload,signature):
    return signature == sign(key_id,payload)

class SignedCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,"checkpoints.sqlite")
        self.registry=SQLiteCheckpointRegistry(self.path)
    def tearDown(self):
        self.registry.close()
        self.tmp.cleanup()
    def make(self,seq=1,event="a"*64,prev=GENESIS,stamp=100,**kw):
        return build_checkpoint(company_id="coA",stream_id="audit-main",sequence=seq,
          event_hash=event,checkpoint_time=stamp,schema_version="1",policy_version="p1",
          signer_key_id="key-A",previous_checkpoint_digest=prev,signer=sign)
    def accept(self,c,now=101):
        return self.registry.accept(c,trusted_key_ids={"key-A"},
          signature_verifier=verify,now=now,max_age_seconds=300)
    def test_valid_signed_checkpoint_accepted(self):
        c=self.make()
        self.assertEqual(self.accept(c),"accepted")
    def test_invalid_signature_rejected(self):
        c=self.make()
        c["signature"]="forged"
        with self.assertRaisesRegex(CheckpointError,"signature_invalid"): self.accept(c)
    def test_wrong_company_or_stream_rejected(self):
        c=self.make()
        with self.assertRaisesRegex(CheckpointError,"scope_mismatch"):
            verify_checkpoint(c,trusted_key_ids={"key-A"},signature_verifier=verify,
              expected_company="coB",expected_stream="audit-main",now=101)
    def test_stale_checkpoint_rejected(self):
        with self.assertRaisesRegex(CheckpointError,"stale"): self.accept(self.make(stamp=1),now=1000)
    def test_future_checkpoint_rejected(self):
        with self.assertRaisesRegex(CheckpointError,"future"): self.accept(self.make(stamp=200),now=101)
    def test_exact_duplicate_is_idempotent(self):
        c=self.make()
        self.assertEqual(self.accept(c),"accepted")
        self.assertEqual(self.accept(c),"duplicate_same_checkpoint")
    def test_lower_sequence_rollback_rejected(self):
        c1=self.make()
        self.accept(c1)
        c2=self.make(seq=2,event="b"*64,prev=hashlib.sha256(
            __import__("signed_audit_checkpoint_reference").canonical_payload(c1)).hexdigest())
        self.accept(c2)
        with self.assertRaisesRegex(CheckpointError,"rollback"):
            self.accept(c1)
    def test_same_sequence_different_hash_rejected(self):
        c1=self.make()
        self.accept(c1)
        c2=self.make(seq=1,event="b"*64)
        with self.assertRaisesRegex(CheckpointError,"rollback"):
            self.accept(c2)
    def test_wrong_previous_checkpoint_link_rejected(self):
        self.accept(self.make())
        c2=self.make(seq=2,event="b"*64,prev="f"*64)
        with self.assertRaisesRegex(CheckpointError,"chain_link"):
            self.accept(c2)
    def test_restore_requires_exact_latest_sequence_and_hash(self):
        c=self.make()
        self.accept(c)
        self.assertTrue(self.registry.verify_restore(company_id="coA",stream_id="audit-main",
          restored_sequence=1,restored_event_hash="a"*64))
        self.assertFalse(self.registry.verify_restore(company_id="coA",stream_id="audit-main",
          restored_sequence=0,restored_event_hash="a"*64))
        self.assertFalse(self.registry.verify_restore(company_id="coA",stream_id="audit-main",
          restored_sequence=1,restored_event_hash="b"*64))
    def test_unknown_signer_rejected(self):
        c=self.make()
        with self.assertRaisesRegex(CheckpointError,"signer_untrusted"):
            self.registry.accept(c,trusted_key_ids={"other"},signature_verifier=verify,now=101)
    def test_first_checkpoint_requires_genesis_link(self):
        c=self.make(prev="f"*64)
        with self.assertRaisesRegex(CheckpointError,"genesis_link"):
            self.accept(c)
    def test_registry_insert_failure_does_not_advance_head(self):
        c=self.make()
        self.registry.db.execute("""CREATE TRIGGER reject_checkpoint
          BEFORE INSERT ON checkpoints BEGIN SELECT RAISE(ABORT,'storage unavailable'); END;""")
        with self.assertRaisesRegex(CheckpointError,"integrity_conflict"):
            self.accept(c)
        self.assertIsNone(self.registry.db.execute(
          "SELECT 1 FROM checkpoint_heads WHERE company_id='coA' AND stream_id='audit-main'").fetchone())
        self.registry.db.execute("DROP TRIGGER reject_checkpoint")
        self.assertEqual(self.accept(c),"accepted")

if __name__=="__main__": unittest.main()

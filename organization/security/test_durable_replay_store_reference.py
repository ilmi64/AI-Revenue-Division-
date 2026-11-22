import os, tempfile, threading, unittest
from durable_replay_store_reference import SQLiteReplayStore, ReplayError, ReplayConflict, ReplayStoreUnavailable

class DurableReplayStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,"replay.sqlite")
        self.store=SQLiteReplayStore(self.path)
    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()
    def claim(self, nonce="n1", evidence_id="e1"):
        return self.store.claim(issuer="receiver-A",nonce=nonce,evidence_id=evidence_id,
          payload_sha256="a"*64,observed_at=100,accepted_at=101)
    def test_first_claim_succeeds(self):
        self.assertTrue(self.claim())
    def test_nonce_replay_rejected(self):
        self.claim()
        with self.assertRaisesRegex(ReplayConflict,"replayed"):
            self.claim(evidence_id="e2")
    def test_evidence_id_replay_rejected(self):
        self.claim()
        with self.assertRaisesRegex(ReplayConflict,"replayed"):
            self.claim(nonce="n2")
    def test_restart_persistence(self):
        self.claim()
        self.store.close()
        self.store=SQLiteReplayStore(self.path)
        with self.assertRaises(ReplayError):
            self.claim()
    def test_different_issuers_have_separate_nonce_namespaces(self):
        self.claim()
        self.store.claim(issuer="receiver-B",nonce="n1",evidence_id="e1",
          payload_sha256="b"*64,observed_at=100,accepted_at=101)
    def test_two_connection_race_has_one_winner(self):
        self.store.close()
        barrier=threading.Barrier(2)
        results=[]
        def worker():
            db=SQLiteReplayStore(self.path)
            barrier.wait()
            try:
                db.claim(issuer="receiver-A",nonce="race",evidence_id="race-e",
                  payload_sha256="c"*64,observed_at=100,accepted_at=101)
                results.append("accepted")
            except ReplayError:
                results.append("replay")
            finally:
                db.close()
        threads=[threading.Thread(target=worker) for _ in range(2)]
        [x.start() for x in threads]
        [x.join() for x in threads]
        self.assertCountEqual(results,["accepted","replay"])
    def test_invalid_claim_rejected(self):
        with self.assertRaises(ReplayError):
            self.store.claim(issuer="",nonce="n",evidence_id="e",
              payload_sha256="x",observed_at=1,accepted_at=2)
    def test_non_duplicate_integrity_failure_is_store_unavailable(self):
        self.store.db.execute("""CREATE TRIGGER reject_insert BEFORE INSERT ON receiver_evidence_replay
          BEGIN SELECT RAISE(ABORT,'storage write unavailable'); END;""")
        with self.assertRaises(ReplayStoreUnavailable):
            self.claim()
        self.assertEqual(self.store.db.execute(
          "SELECT count(*) FROM receiver_evidence_replay").fetchone()[0],0)
    def test_conflicting_nonce_and_id_are_replay_conflict(self):
        self.claim()
        with self.assertRaises(ReplayConflict):
            self.store.claim(issuer="receiver-A",nonce="n1",evidence_id="e2",
              payload_sha256="b"*64,observed_at=100,accepted_at=101)

if __name__=="__main__":
    unittest.main()

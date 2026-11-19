import unittest
from audit_chain_reference import InMemoryAuditChain, verify_chain, AuditError

def sample():
    c=InMemoryAuditChain()
    c.append(event_id="e1", occurred_at="2026-11-19T00:00:00Z", company_id="revenue",
             actor_id="agent-1", event_type="task.started", payload={"task_id":"t1"})
    c.append(event_id="e2", occurred_at="2026-11-19T00:00:01Z", company_id="revenue",
             actor_id="agent-1", event_type="task.completed", payload={"result":"ok"})
    return c.export()

class AuditChainTests(unittest.TestCase):
    def test_valid_chain(self): self.assertEqual(verify_chain(sample()), (True,"ok"))
    def test_payload_tamper(self):
        x=sample(); x[0]["payload"]["task_id"]="changed"
        self.assertFalse(verify_chain(x)[0])
    def test_hash_tamper(self):
        x=sample(); x[1]["hash"]="f"*64
        self.assertFalse(verify_chain(x)[0])
    def test_deletion(self): self.assertFalse(verify_chain(sample()[1:])[0])
    def test_reorder(self): self.assertFalse(verify_chain(list(reversed(sample()))[0:])[0])
    def test_duplicate_id(self):
        x=sample(); x[1]["event_id"]=x[0]["event_id"]
        self.assertFalse(verify_chain(x)[0])
    def test_duplicate_sequence(self):
        x=sample(); x[1]["sequence"]=1
        self.assertFalse(verify_chain(x)[0])
    def test_secret_field_rejected(self):
        c=InMemoryAuditChain()
        with self.assertRaises(AuditError):
            c.append(event_id="x", occurred_at="now", company_id="c", actor_id="a",
                     event_type="test", payload={"api_key":"do-not-log"})
    def test_float_rejected(self):
        c=InMemoryAuditChain()
        with self.assertRaises(AuditError):
            c.append(event_id="x", occurred_at="now", company_id="c", actor_id="a",
                     event_type="test", payload={"amount":1.25})
    def test_non_object_payload_rejected(self):
        c=InMemoryAuditChain()
        with self.assertRaises(AuditError):
            c.append(event_id="x", occurred_at="now", company_id="c", actor_id="a",
                     event_type="test", payload=["bad"])
    def test_non_string_payload_key_rejected(self):
        c=InMemoryAuditChain()
        with self.assertRaises(AuditError):
            c.append(event_id="x", occurred_at="now", company_id="c", actor_id="a",
                     event_type="test", payload={1:"bad"})
    def test_non_mapping_event_fails_closed(self):
        self.assertFalse(verify_chain(["not-an-event"])[0])

if __name__ == "__main__": unittest.main()

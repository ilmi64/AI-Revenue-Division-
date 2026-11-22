"""Run from repository root: python -m unittest discover -s operations -p 'test_*.py'"""
import unittest
from delivery_gate import decide

def record():
    return {
        "opportunity": {
            "id": "opp-1", "kind": "coding", "title": "Fix code",
            "source_url": "https://example.org/task", "scope_authorized": True,
            "cost_cad": 0, "requires_credentials": False,
            "external_action": False, "deadline_utc": None,
        },
        "evidence": {
            "task_owner": "agent-reviewer", "source_commit": "a" * 40,
            "tests_passed": True, "test_command": "python -m unittest",
            "test_log_ref": "local:test-output.txt",
        },
        "approvals": {"delivery_authorized": True, "scope_reviewed": True},
    }

class DeliveryGateTests(unittest.TestCase):
    def test_ready_still_requires_manual_delivery(self):
        result = decide(record())
        self.assertEqual(result["status"], "ready_for_manual_delivery")
        self.assertFalse(result["external_actions_performed"])
    def test_missing_approval_blocks(self):
        item = record()
        item["approvals"]["delivery_authorized"] = False
        self.assertIn("delivery_not_authorized", decide(item)["reasons"])
    def test_missing_scope_review_blocks(self):
        item = record()
        item["approvals"]["scope_reviewed"] = False
        self.assertEqual(decide(item)["status"], "blocked")
    def test_failed_tests_block(self):
        item = record()
        item["evidence"]["tests_passed"] = False
        self.assertIn("qa_not_passed", decide(item)["reasons"])
    def test_missing_log_blocks(self):
        item = record()
        item["evidence"]["test_log_ref"] = ""
        self.assertIn("missing_test_evidence", decide(item)["reasons"])
    def test_invalid_commit_blocks(self):
        item = record()
        item["evidence"]["source_commit"] = "not-a-sha"
        self.assertIn("invalid_source_commit", decide(item)["reasons"])
    def test_paid_opportunity_blocks(self):
        item = record()
        item["opportunity"]["cost_cad"] = 5
        self.assertIn("intake_not_review_ready", decide(item)["reasons"])
    def test_malformed_input_blocks(self):
        self.assertEqual(decide(None)["status"], "blocked")

if __name__ == "__main__":
    unittest.main()

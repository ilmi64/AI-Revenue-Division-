import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_incident_register import validate

class IncidentRegisterTests(unittest.TestCase):
    def setUp(self):
        self.risks = {"records": [{"id": "R-1"}]}
        self.decisions = {"records": [{"id": "D-1", "status": "pending", "owner_outcome_evidence": []}]}
        self.queue = {"tasks": [{"id": "T-1"}]}
        self.registry = {"divisions": [{"id": "technology"}]}
        self.incident = {
            "id": "INC-1", "summary": "Test incident", "severity": "high", "status": "recovering",
            "affected_division_id": "technology", "containment_recommendation": "Pause affected workflow pending review",
            "owner_assignment": "unassigned_pending_owner_confirmation", "detection_evidence": ["test:evidence"],
            "related_risk_ids": ["R-1"], "related_task_ids": ["T-1"], "related_decision_ids": ["D-1"],
            "corrective_actions": [{"id": "CA-1", "description": "Restore validated configuration",
                "status": "proposed", "owner_assignment": "unassigned_pending_owner_confirmation", "completion_evidence": []}]
        }
    def check(self, incident):
        return validate({"records": [incident]}, self.risks, self.decisions, self.queue, self.registry)
    def test_evidence_backed_open_incident_is_valid(self):
        self.assertEqual(self.check(self.incident), [])
    def test_empty_register_is_valid(self):
        self.assertEqual(validate({"records": []}, self.risks, self.decisions, self.queue, self.registry), [])
    def test_incident_requires_detection_evidence(self):
        item = dict(self.incident); item["detection_evidence"] = []
        self.assertTrue(any("detection_evidence" in e for e in self.check(item)))
    def test_dangling_links_are_rejected(self):
        item = dict(self.incident); item["related_task_ids"] = ["MISSING"]
        self.assertTrue(any("unknown task MISSING" in e for e in self.check(item)))
    def test_in_progress_action_requires_confirmed_owner(self):
        item = dict(self.incident); item["corrective_actions"] = [dict(self.incident["corrective_actions"][0], status="in_progress")]
        self.assertTrue(any("requires confirmed owner assignment" in e for e in self.check(item)))
    def test_completed_action_requires_owner_and_evidence(self):
        item = dict(self.incident); item["corrective_actions"] = [dict(self.incident["corrective_actions"][0], status="completed", owner_assignment="owner-confirmed")]
        self.assertTrue(any("requires completion evidence" in e for e in self.check(item)))
    def test_deferred_action_requires_pending_owner_decision(self):
        item = dict(self.incident); item["corrective_actions"] = [dict(self.incident["corrective_actions"][0], status="deferred_pending_owner_approval", owner_decision_id="D-1")]
        self.assertEqual(self.check(item), [])
    def test_closure_requires_review_completed_actions_and_approval(self):
        item = dict(self.incident); item["status"] = "closed"; item["post_incident_review_evidence"] = ["review:evidence"]
        errs = self.check(item)
        self.assertTrue(any("every corrective action" in e for e in errs))
        self.assertTrue(any("approved owner decision" in e for e in errs))
    def test_malformed_register_does_not_crash(self):
        self.assertTrue(validate("bad", self.risks, self.decisions, self.queue, self.registry))
        item = dict(self.incident); item["corrective_actions"] = [None]
        self.assertTrue(self.check(item))

if __name__ == "__main__":
    unittest.main()

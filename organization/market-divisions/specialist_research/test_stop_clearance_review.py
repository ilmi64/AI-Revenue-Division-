import tempfile
import unittest
from pathlib import Path

from specialist_research.incident_event_ledger import append_event, read_events
from specialist_research.stop_clearance_review import assess_stop_clearance

NOW = "2026-11-17T20:30:00Z"


def event(event_id, kind, actor, subject="incident-1", details=None):
    evidence = [] if kind in {"incident_opened", "incident_closed"} else [f"evidence:{event_id}"]
    return {
        "event_id": event_id, "event_type": kind,
        "occurred_at_utc": NOW, "recorded_at_utc": NOW,
        "actor_id": actor, "subject_id": subject,
        "summary": f"Synthetic {kind}", "evidence_refs": evidence,
        "details": details or {},
    }


class StopClearanceReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "events.jsonl"
        self.stop_id = "stop-A"

    def tearDown(self):
        self.tmp.cleanup()

    def append(self, value):
        append_event(self.path, value)

    def seed_recovery(self):
        self.append(event("stop-raised", "stop_raised", "risk",
                          details={"stop_id": self.stop_id}))
        self.append(event("recovery-1", "recovery_evidence_added", "operator",
                          details={"stop_id": self.stop_id}))
        self.append(event("corrective-1", "corrective_action_verified", "verifier",
                          details={"stop_id": self.stop_id}))

    def request(self, actor="operator"):
        self.append(event("request-1", "stop_clearance_requested", actor,
                          details={
                              "stop_id": self.stop_id, "incident_id": "incident-1",
                              "requestor_id": actor, "approval_status": "pending",
                              "recovery_evidence_event_ids": ["recovery-1"],
                              "corrective_action_event_ids": ["corrective-1"],
                          }))

    def review(self, event_id, actor, role, decision="eligible"):
        self.append(event(event_id, "stop_clearance_reviewed", actor,
                          details={
                              "request_event_id": "request-1", "stop_id": self.stop_id,
                              "reviewer_id": actor, "reviewer_role": role,
                              "decision": decision, "reason": "Synthetic independent review",
                          }))

    def audit(self):
        return assess_stop_clearance(read_events(self.path))

    def test_two_distinct_independent_reviews_make_request_eligible_but_stop_stays_active(self):
        self.seed_recovery()
        self.request()
        self.review("review-risk", "risk-reviewer", "independent_risk")
        self.review("review-occ", "occ-reviewer", "occ")
        result = self.audit()
        self.assertTrue(result["valid"])
        self.assertTrue(result["global_stop_active"])
        self.assertFalse(result["clearance_performed"])
        self.assertEqual(result["stops"][0]["status"], "eligible_for_separate_occ_decision")
        self.assertTrue(result["stops"][0]["stop_remains_active"])
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])

    def test_no_request_keeps_stop_in_review_pending_state(self):
        self.seed_recovery()
        result = self.audit()
        self.assertEqual(result["stops"][0]["status"], "review_pending_or_incomplete")
        self.assertTrue(result["global_stop_active"])

    def test_missing_recovery_link_blocks_eligibility(self):
        self.append(event("stop-raised", "stop_raised", "risk", details={"stop_id": self.stop_id}))
        self.append(event("corrective-1", "corrective_action_verified", "verifier",
                          details={"stop_id": self.stop_id}))
        self.append(event("request-1", "stop_clearance_requested", "operator",
                          details={"stop_id": self.stop_id, "incident_id": "incident-1",
                                   "requestor_id": "operator", "approval_status": "pending",
                                   "recovery_evidence_event_ids": ["missing"],
                                   "corrective_action_event_ids": ["corrective-1"]}))
        self.review("review-risk", "risk-reviewer", "independent_risk")
        self.review("review-occ", "occ-reviewer", "occ")
        result = self.audit()
        self.assertEqual(result["stops"][0]["status"], "review_pending_or_incomplete")
        self.assertTrue(any("recovery_evidence_added" in x for x in result["stops"][0]["requests"][0]["errors"]))

    def test_wrong_stop_or_incident_link_blocks_request(self):
        self.seed_recovery()
        self.append(event("request-1", "stop_clearance_requested", "operator",
                          details={"stop_id": self.stop_id, "incident_id": "other-incident",
                                   "requestor_id": "operator", "approval_status": "pending",
                                   "recovery_evidence_event_ids": ["recovery-1"],
                                   "corrective_action_event_ids": ["corrective-1"]}))
        self.review("review-risk", "risk-reviewer", "independent_risk")
        self.review("review-occ", "occ-reviewer", "occ")
        self.assertEqual(self.audit()["stops"][0]["status"], "review_pending_or_incomplete")

    def test_same_reviewer_cannot_satisfy_dual_control(self):
        self.seed_recovery()
        self.request()
        self.review("review-risk", "same-person", "independent_risk")
        self.review("review-occ", "same-person", "occ")
        result = self.audit()
        self.assertEqual(result["stops"][0]["status"], "review_pending_or_incomplete")
        self.assertTrue(any("distinct people" in x for x in result["stops"][0]["requests"][0]["errors"]))

    def test_requestor_cannot_review_own_request(self):
        self.seed_recovery()
        self.request(actor="operator")
        self.review("review-risk", "operator", "independent_risk")
        self.review("review-occ", "occ-reviewer", "occ")
        result = self.audit()
        self.assertEqual(result["stops"][0]["status"], "review_pending_or_incomplete")
        self.assertTrue(any("not independent" in x for x in result["stops"][0]["requests"][0]["errors"]))

    def test_rejected_review_blocks_eligibility(self):
        self.seed_recovery()
        self.request()
        self.review("review-risk", "risk-reviewer", "independent_risk")
        self.review("review-occ", "occ-reviewer", "occ", decision="rejected")
        result = self.audit()
        self.assertEqual(result["stops"][0]["status"], "review_pending_or_incomplete")

    def test_rejected_clearance_request_cannot_become_eligible(self):
        self.seed_recovery()
        self.append(event("request-1", "stop_clearance_requested", "operator",
                          details={"stop_id": self.stop_id, "incident_id": "incident-1",
                                   "requestor_id": "operator", "approval_status": "rejected",
                                   "recovery_evidence_event_ids": ["recovery-1"],
                                   "corrective_action_event_ids": ["corrective-1"]}))
        self.review("review-risk", "risk-reviewer", "independent_risk")
        self.review("review-occ", "occ-reviewer", "occ")
        result = self.audit()
        self.assertNotEqual(result["stops"][0]["status"], "eligible_for_separate_occ_decision")
        self.assertTrue(any("marked rejected" in x for x in result["stops"][0]["requests"][0]["errors"]))

    def test_duplicate_stop_id_raises_fail_closed_review(self):
        self.seed_recovery()
        self.append(event("stop-raised-again", "stop_raised", "risk-2",
                          details={"stop_id": self.stop_id}))
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "HALT_REVIEW")
        self.assertTrue(result["global_stop_active"])

    def test_unknown_request_review_is_reported(self):
        self.seed_recovery()
        self.append(event("orphan-review", "stop_clearance_reviewed", "occ-reviewer",
                          details={"request_event_id": "missing", "stop_id": self.stop_id,
                                   "reviewer_id": "occ-reviewer", "reviewer_role": "occ",
                                   "decision": "eligible", "reason": "orphan"}))
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown clearance request" in x for x in result["errors"]))

    def test_invalid_ledger_fails_closed(self):
        self.seed_recovery()
        rows = read_events(self.path)
        rows[0]["event"]["summary"] = "tampered"
        self.path.write_text("".join(__import__("json").dumps(x) + "\n" for x in rows))
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "HALT_REVIEW")
        self.assertTrue(result["global_stop_active"])

    def test_request_event_requires_structured_recovery_evidence(self):
        with self.assertRaises(ValueError):
            self.append(event("request-1", "stop_clearance_requested", "operator",
                              details={"approval_status": "pending"}))

    def test_review_event_requires_allowed_role_and_decision(self):
        with self.assertRaises(ValueError):
            self.append(event("review-1", "stop_clearance_reviewed", "reviewer",
                              details={"request_event_id": "request-1", "stop_id": self.stop_id,
                                       "reviewer_id": "reviewer", "reviewer_role": "desk_owner",
                                       "decision": "eligible", "reason": "test"}))


if __name__ == "__main__":
    unittest.main()

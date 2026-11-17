import unittest

from capital_flow_history import HistoryError, project_history

EVENT = {"event_id":"event-1","event_type":"large_wallet_transfer","review_status":"unverified"}

def review(sequence, status=None, action="review"):
    return {"sequence":sequence,"event_id":"event-1","review_status":status,
            "action":action,"reviewer_id":"analyst","reason":"Evidence checked"}

class HistoryProjectionTests(unittest.TestCase):
    def test_projects_review_timeline_without_mutating_source_event(self):
        original = dict(EVENT)
        rows = project_history([EVENT], [review(1, "research"), review(2, "corroborated", "corroborate")])
        self.assertEqual(rows[0]["current_review_status"], "corroborated")
        self.assertEqual(rows[0]["review_count"], 2)
        self.assertEqual(EVENT, original)
        self.assertEqual(rows[0]["event"]["review_status"], "unverified")

    def test_status_without_new_decision_preserves_previous_status(self):
        rows = project_history([EVENT], [review(1, "research"), review(2, None, "challenge")])
        self.assertEqual(rows[0]["current_review_status"], "research")

    def test_rejects_duplicate_event_ids(self):
        with self.assertRaises(HistoryError):
            project_history([EVENT, EVENT], [])

    def test_rejects_orphan_review(self):
        orphan = dict(review(1, "research"), event_id="missing")
        with self.assertRaises(HistoryError):
            project_history([EVENT], [orphan])

    def test_empty_review_history_uses_event_baseline(self):
        rows = project_history([EVENT], [])
        self.assertEqual(rows[0]["current_review_status"], "unverified")
        self.assertIsNone(rows[0]["latest_review"])

if __name__ == "__main__":
    unittest.main()

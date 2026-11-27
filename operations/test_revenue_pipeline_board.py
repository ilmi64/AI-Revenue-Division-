import unittest
from revenue_intake_sandbox import Opportunity
from revenue_pipeline_board import build_board

def item(reference, kind="coding", revenue=500, authorization=True, payout=True, sanctions=True, contact=True, upfront=0):
    return Opportunity(reference, kind, "CA", revenue, upfront, authorization, payout, sanctions, contact)

class PipelineBoardTests(unittest.TestCase):
    def test_ready_has_plan_but_no_execution(self):
        board = build_board((item("job1"),))
        self.assertEqual(board.review_ready_count, 1)
        self.assertEqual(board.rows[0].planned_tasks[0], "reproduce_issue_in_sandbox")
        self.assertFalse(board.rows[0].agent_execution_authorized)
        self.assertFalse(board.rows[0].external_contact_authorized)

    def test_hold_has_no_delivery_tasks(self):
        board = build_board((item("job2", authorization=False),))
        self.assertEqual(board.held_count, 1)
        self.assertEqual(board.rows[0].planned_tasks, ())

    def test_spending_rejected(self):
        board = build_board((item("job3", upfront=1),))
        self.assertEqual(board.rejected_count, 1)

    def test_estimate_is_not_booked_revenue(self):
        board = build_board((item("job4", revenue=900),))
        self.assertEqual(board.estimated_review_ready_cad, 900)
        self.assertEqual(board.booked_revenue_cad, 0)
        self.assertEqual(board.realized_revenue_cad, 0)

    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            build_board((item("dup"), item("dup")))

    def test_deterministic_priority(self):
        board = build_board((item("held", authorization=False), item("small", revenue=10), item("large", revenue=100)))
        self.assertEqual(tuple(row.reference for row in board.rows), ("large", "small", "held"))

    def test_empty_board(self):
        self.assertEqual(build_board(()).rows, ())

if __name__ == "__main__":
    unittest.main()

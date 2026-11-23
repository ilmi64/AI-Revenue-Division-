import unittest
from dataclasses import replace

from revenue_agent_queue import prepare_queue
from revenue_delivery_plan import DeliveryPlan, plan_delivery
from revenue_intake_sandbox import Opportunity


def opportunity(kind="coding", **changes):
    fields = dict(reference="demo_001", kind=kind, country="CA", expected_revenue_cad=300,
                  upfront_cost_cad=0, authorization_evidence=True, payout_confirmed=True,
                  sanctions_reviewed=True, customer_contact_allowed=True)
    fields.update(changes)
    return Opportunity(**fields)


class AgentQueueTests(unittest.TestCase):
    def test_all_service_lines_have_bounded_queue(self):
        for kind in ("coding", "authorized_bug_bounty", "app_build", "ai_setup", "research"):
            with self.subTest(kind=kind):
                tasks = prepare_queue(plan_delivery(opportunity(kind)))
                self.assertEqual(len(tasks), 4)
                self.assertEqual([t.sequence for t in tasks], [1, 2, 3, 4])
                self.assertEqual(len({t.task_id for t in tasks}), 4)
                self.assertTrue(all(t.state == "AWAITING_INTERNAL_REVIEW" for t in tasks))
                self.assertTrue(all(not t.execution_authorized and not t.spending_authorized
                                    and not t.external_delivery_authorized for t in tasks))

    def test_unqualified_opportunity_has_no_queue(self):
        self.assertEqual(prepare_queue(plan_delivery(opportunity(payout_confirmed=False))), ())

    def test_elevated_execution_rejected(self):
        plan = plan_delivery(opportunity())
        with self.assertRaises(ValueError):
            prepare_queue(replace(plan, agent_execution_authorized=True))

    def test_external_contact_permission_rejected(self):
        plan = plan_delivery(opportunity())
        with self.assertRaises(ValueError):
            prepare_queue(replace(plan, customer_contact_authorized=True))

    def test_unknown_task_rejected(self):
        plan = plan_delivery(opportunity())
        with self.assertRaises(ValueError):
            prepare_queue(replace(plan, tasks=("unknown",) + plan.tasks[1:]))

    def test_reference_validation(self):
        plan = plan_delivery(opportunity())
        with self.assertRaises(ValueError):
            prepare_queue(replace(plan, reference="../bad"))


if __name__ == "__main__":
    unittest.main()

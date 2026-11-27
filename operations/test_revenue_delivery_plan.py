import unittest

from revenue_delivery_plan import plan_delivery
from revenue_intake_sandbox import Opportunity


def opportunity(kind="coding", **changes):
    fields = dict(reference="demo_001", kind=kind, country="CA", expected_revenue_cad=300,
                  upfront_cost_cad=0, authorization_evidence=True, payout_confirmed=True,
                  sanctions_reviewed=True, customer_contact_allowed=True)
    fields.update(changes)
    return Opportunity(**fields)


class DeliveryPlanTests(unittest.TestCase):
    def test_all_service_lines_generate_bounded_internal_plans(self):
        for kind in ("coding", "authorized_bug_bounty", "app_build", "ai_setup", "research"):
            with self.subTest(kind=kind):
                result = plan_delivery(opportunity(kind))
                self.assertEqual(result.classification, "INTERNAL_PLAN_ONLY")
                self.assertEqual(len(result.tasks), 4)
                self.assertTrue(result.human_review_required)
                self.assertFalse(result.customer_contact_authorized)
                self.assertFalse(result.external_submission_authorized)
                self.assertFalse(result.agent_execution_authorized)
                self.assertFalse(result.spending_authorized)

    def test_missing_scope_prevents_work_plan(self):
        result = plan_delivery(opportunity("authorized_bug_bounty", authorization_evidence=False))
        self.assertEqual(result.classification, "HOLD")
        self.assertEqual(result.tasks, ())

    def test_paid_dependency_prevents_work_plan(self):
        result = plan_delivery(opportunity("app_build", upfront_cost_cad=1))
        self.assertEqual(result.classification, "REJECT")
        self.assertEqual(result.tasks, ())

    def test_external_contact_flag_is_not_permission_to_contact(self):
        result = plan_delivery(opportunity(customer_contact_allowed=True))
        self.assertFalse(result.customer_contact_authorized)


if __name__ == "__main__":
    unittest.main()

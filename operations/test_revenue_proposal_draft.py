import unittest
from revenue_intake_sandbox import Opportunity
from revenue_proposal_draft import draft_proposal

def opportunity(**overrides):
    data = dict(reference="example_01", kind="coding", country="CA",
                expected_revenue_cad=750, upfront_cost_cad=0,
                authorization_evidence=True, payout_confirmed=True,
                sanctions_reviewed=True, customer_contact_allowed=True)
    data.update(overrides)
    return Opportunity(**data)

class ProposalDraftTests(unittest.TestCase):
    def test_ready_proposal_is_internal(self):
        result = draft_proposal(opportunity())
        self.assertEqual(result.status, "INTERNAL_DRAFT")
        self.assertIn("Software bug fixing", result.markdown)
        self.assertIn("CAD 750", result.markdown)
        self.assertFalse(result.submission_authorized)
        self.assertFalse(result.client_contact_authorized)

    def test_hold_never_produces_proposal(self):
        result = draft_proposal(opportunity(authorization_evidence=False))
        self.assertEqual(result.status, "HOLD")
        self.assertEqual(result.markdown, "")

    def test_spending_rejected(self):
        result = draft_proposal(opportunity(upfront_cost_cad=5))
        self.assertEqual(result.markdown, "")

    def test_all_service_lines(self):
        for kind in ("coding", "authorized_bug_bounty", "app_build", "ai_setup", "research"):
            with self.subTest(kind=kind):
                result = draft_proposal(opportunity(kind=kind))
                self.assertEqual(result.status, "INTERNAL_DRAFT")
                self.assertIn("human review", result.markdown.lower())

    def test_deterministic_output(self):
        self.assertEqual(draft_proposal(opportunity()), draft_proposal(opportunity()))

    def test_no_earnings_guarantee(self):
        self.assertIn("No guarantee", draft_proposal(opportunity()).markdown)

if __name__ == "__main__":
    unittest.main()

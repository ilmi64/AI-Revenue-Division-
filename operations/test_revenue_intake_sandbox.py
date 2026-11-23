import unittest

from revenue_intake_sandbox import Opportunity, qualify


def candidate(**overrides):
    values = dict(reference="demo_001", kind="coding", country="CA",
                  expected_revenue_cad=250, upfront_cost_cad=0,
                  authorization_evidence=True, payout_confirmed=True,
                  sanctions_reviewed=True, customer_contact_allowed=True)
    values.update(overrides)
    return Opportunity(**values)


class IntakeTests(unittest.TestCase):
    def test_qualified_remains_review_only(self):
        d = qualify(candidate())
        self.assertEqual(d.status, "REVIEW_READY")
        self.assertFalse(d.submission_authorized)
        self.assertFalse(d.spending_authorized)
        self.assertFalse(d.execution_authorized)

    def test_no_upfront_spend(self):
        self.assertEqual(qualify(candidate(upfront_cost_cad=1)).status, "REJECT")

    def test_bug_bounty_requires_scope(self):
        d = qualify(candidate(kind="authorized_bug_bounty", authorization_evidence=False))
        self.assertEqual(d.status, "HOLD")
        self.assertIn("scope_authorization_unverified", d.reasons)

    def test_payout_and_jurisdiction_review(self):
        d = qualify(candidate(payout_confirmed=False, sanctions_reviewed=False))
        self.assertEqual(d.status, "HOLD")
        self.assertEqual(len(d.reasons), 2)

    def test_contact_requires_approval(self):
        self.assertEqual(qualify(candidate(customer_contact_allowed=False)).status, "HOLD")

    def test_no_revenue_estimate(self):
        self.assertEqual(qualify(candidate(expected_revenue_cad=0)).status, "HOLD")

    def test_reject_unsupported_kind(self):
        self.assertEqual(qualify(candidate(kind="unauthorized_testing")).status, "REJECT")

    def test_reject_invalid_financial_types(self):
        for value in (True, -1, 1.5, 1000001):
            with self.subTest(value=value):
                self.assertEqual(qualify(candidate(expected_revenue_cad=value)).status, "REJECT")

    def test_reject_invalid_flags(self):
        self.assertEqual(qualify(candidate(payout_confirmed="yes")).status, "REJECT")

    def test_reject_reference_injection(self):
        for value in ("", "../etc", "test\nsecret", "é"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                qualify(candidate(reference=value))


if __name__ == "__main__":
    unittest.main()

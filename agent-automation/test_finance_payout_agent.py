import unittest
from finance_payout_agent import assess, build_report, render_markdown

class FinancePayoutAgentTests(unittest.TestCase):
    def test_lead_is_not_misrepresented_as_earnings(self):
        result = assess({"title": "Possible bounty", "url": "https://github.com/a/b/issues/1"})
        self.assertEqual(result["commercial_status"], "unverified_lead")
        self.assertIsNone(result["reward_amount"])
        self.assertEqual(result["canada_eligibility"], "unverified")
        self.assertEqual(result["escrow_status"], "unverified")

    def test_report_recognizes_no_verified_paid_work(self):
        report = build_report({"results": [{"title": "Lead", "url": "https://github.com/a/b/issues/1"}]})
        self.assertEqual(report["verified_paid_opportunities"], 0)
        self.assertIn("not earnings", render_markdown(report))

    def test_non_github_https_lead_is_supported(self):
        result = assess({"title": "Contract", "url": "https://example.com/work",
                         "lane": "freelance_services", "source_name": "Example"})
        self.assertEqual(result["lane"], "freelance_services")
        self.assertEqual(result["commercial_status"], "unverified_lead")

    def test_preserves_canadian_eligibility_hint_without_verifying_it(self):
        result = assess({"title":"Role","url":"https://jobicy.com/jobs/1",
                         "lane":"remote_employment","source_name":"Jobicy",
                         "eligibility_hint":"canada_or_worldwide_listed_check_full_terms"})
        self.assertEqual(result["eligibility_hint"], "canada_or_worldwide_listed_check_full_terms")
        self.assertEqual(result["canada_eligibility"], "unverified")

    def test_invalid_results_type_fails_closed(self):
        with self.assertRaises(ValueError):
            build_report({"results": {}})

    def test_missing_url_remains_unverified(self):
        result = assess({"title": "Unknown"})
        self.assertTrue(any("invalid" in finding for finding in result["findings"]))

if __name__ == "__main__":
    unittest.main()

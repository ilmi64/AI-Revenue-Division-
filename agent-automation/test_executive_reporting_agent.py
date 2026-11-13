import unittest
from executive_reporting_agent import build_report, render_markdown

class ExecutiveReportingAgentTests(unittest.TestCase):
    def test_missing_artifacts_means_incomplete(self):
        report = build_report(None, None, None, None)
        self.assertEqual(report["readiness"], "incomplete")
        self.assertEqual(len(report["artifacts_missing"]), 4)

    def test_complete_artifact_set_still_requires_human_review(self):
        report = build_report({"results": []}, {"lead_count": 0},
                              {"reviewed_count": 0}, {"opportunities_reviewed": 0})
        self.assertEqual(report["readiness"], "human_review_required")
        self.assertEqual(report["verified_paid_opportunities"], 0)
        self.assertEqual(report["cash_received"], 0)

    def test_report_never_calls_leads_earnings(self):
        report = build_report({"results": [{"title": "Lead"}]}, {"lead_count": 1},
                              {"reviewed_count": 1}, {"opportunities_reviewed": 1})
        text = render_markdown(report)
        self.assertIn("do not represent earnings", text)
        self.assertIn("No external action is authorized", text)

if __name__ == "__main__":
    unittest.main()

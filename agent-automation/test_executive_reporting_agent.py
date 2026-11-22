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

    def test_division_feed_counts_are_available(self):
        report = build_report({"results": [{"lane": "ai_development"}]}, {"lead_count": 1},
                              {"reviewed_count": 1}, {"opportunities_reviewed": 1})
        self.assertEqual(report["counts"]["discovered"], 1)

    def test_report_never_calls_leads_earnings(self):
        report = build_report({"results": [{"title": "Lead"}]}, {"lead_count": 1},
                              {"reviewed_count": 1}, {"opportunities_reviewed": 1})
        text = render_markdown(report)
        self.assertIn("do not represent earnings", text)
        self.assertIn("No external action is authorized", text)

    def test_lane_coverage_flows_into_executive_report(self):
        registry = {"registry_valid": True, "source_count": 10, "lane_count": 9,
                    "covered_lane_count": 8, "research_gap_count": 1,
                    "external_accounts_connected": False,
                    "coverage": [{"label": "AI evaluation", "coverage_status": "candidate_sources_listed", "source_count": 2}]}
        report = build_report({"results": []}, {"lead_count": 0},
                              {"reviewed_count": 0}, {"opportunities_reviewed": 0}, registry)
        self.assertEqual(report["revenue_lane_coverage"]["covered_lane_count"], 8)
        self.assertIn("Revenue lane coverage", render_markdown(report))
        self.assertIn("External accounts connected by registry: no", render_markdown(report))

if __name__ == "__main__":
    unittest.main()

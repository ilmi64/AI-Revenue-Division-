import unittest
from risk_review_agent import review_brief, review_report

class RiskReviewAgentTests(unittest.TestCase):
    def valid_brief(self):
        return {"title": "Paid issue", "url": "https://github.com/org/repo/issues/1",
                "verified_scope": False, "verified_effort": False,
                "verified_acceptance_criteria": False, "do_not": ["Do not submit"],
                "triage_score": 4}

    def test_valid_structure_still_requires_human_review(self):
        result = review_brief(self.valid_brief())
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["findings"][0]["code"], "STRUCTURE_CHECK_PASSED")

    def test_missing_safety_flag_blocks(self):
        brief = self.valid_brief()
        brief["verified_effort"] = True
        self.assertEqual(review_brief(brief)["status"], "blocked")

    def test_bad_source_blocks(self):
        brief = self.valid_brief()
        brief["url"] = "https://example.com"
        self.assertEqual(review_brief(brief)["status"], "blocked")

    def test_report_counts_blocked_records(self):
        brief = self.valid_brief()
        brief["do_not"] = []
        report = review_report({"briefs": [brief]})
        self.assertEqual(report["blocked_count"], 1)
        self.assertEqual(report["overall_status"], "blocked")

    def test_bad_briefs_type_fails_closed(self):
        with self.assertRaises(ValueError):
            review_report({"briefs": {}})

if __name__ == "__main__":
    unittest.main()

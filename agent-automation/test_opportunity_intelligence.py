import unittest
from opportunity_intelligence import collect, normalize, render_markdown

class OpportunityIntelligenceTests(unittest.TestCase):
    def test_normalize_never_marks_funding_verified(self):
        item = {"title": "Paid bounty for beginner bug fix", "html_url": "https://github.com/a/b/issues/1",
                "repository_url": "https://api.github.com/repos/a/b", "state": "open",
                "labels": [{"name": "bounty"}], "updated_at": "2026-01-01"}
        result = normalize(item)
        self.assertFalse(result["funding_verified"])
        self.assertIn("bounty_keyword", result["signals"])
        self.assertEqual(result["repository"], "b")

    def test_collect_deduplicates_and_survives_query_error(self):
        item = {"title": "Bounty", "html_url": "https://github.com/a/b/issues/1",
                "repository_url": "https://api.github.com/repos/a/b", "labels": [], "updated_at": "2026"}
        calls = []
        def fake(query):
            calls.append(query)
            if len(calls) == 2: raise RuntimeError("temporary")
            return [item]
        results, errors = collect(fake)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)

    def test_report_warns_about_unverified_leads(self):
        report = render_markdown([], "2026-01-01T00:00:00+00:00", [])
        self.assertIn("not verified paid work", report)
        self.assertIn("Canadian eligibility", report)
        self.assertIn("Never submit", report)

if __name__ == "__main__":
    unittest.main()

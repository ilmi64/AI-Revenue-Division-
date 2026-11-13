import unittest
from development_task_agent import triage, build_report, render_markdown

class DevelopmentTaskAgentTests(unittest.TestCase):
    def test_paid_bounty_signals_are_prioritised_but_unverified(self):
        result = triage({"title": "Paid bounty", "url": "https://github.com/org/repo/issues/7",
                         "signals": ["bounty_keyword", "payment_keyword"]})
        self.assertEqual(result["priority"], "review_first")
        self.assertFalse(result["verified_scope"])
        self.assertFalse(result["verified_effort"])

    def test_invalid_url_is_held(self):
        result = triage({"title": "Potential work", "url": "http://example.com/task",
                         "signals": ["payment_keyword"]})
        self.assertEqual(result["priority"], "hold")
        self.assertEqual(result["triage_score"], 0)

    def test_external_source_relevance_is_only_a_review_signal(self):
        result = triage({"title":"Python role","url":"https://jobicy.com/jobs/1",
                         "lane":"remote_employment","source_name":"Jobicy",
                         "signals":["source_relevance_keyword"]})
        self.assertEqual(result["triage_score"], 1)
        self.assertEqual(result["priority"], "review_later")
        self.assertEqual(result["source_name"], "Jobicy")
        self.assertFalse(result["verified_scope"])

    def test_report_handles_empty_results(self):
        report = build_report({"results": []})
        self.assertEqual(report["lead_count"], 0)
        self.assertIn("not a verified job", render_markdown(report))

    def test_bad_results_type_fails_closed(self):
        with self.assertRaises(ValueError):
            build_report({"results": "not-a-list"})

if __name__ == "__main__":
    unittest.main()

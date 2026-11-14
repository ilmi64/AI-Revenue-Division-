import unittest
from boss_bounty_sources import inspect_comments, normalize_issue

class BossBountySourceTests(unittest.TestCase):
    def issue(self):
        return {
            "node_id": "I_test", "title": "Example paid task",
            "html_url": "https://github.com/example/project/issues/1",
            "repository_url": "https://api.github.com/repos/example/project",
            "updated_at": "2026-11-14T00:00:00Z", "state": "open",
            "body": '<a href="https://www.boss.dev/issue/github/I_test"><img src="https://api.boss.dev/badge/bounty?gid=boss%2Fabc" /></a>',
            "comments": 1,
        }

    def test_marker_is_recorded_but_not_verified(self):
        item = normalize_issue(self.issue(), [])
        self.assertEqual(item["source_name"], "BOSS-marked GitHub issue")
        self.assertFalse(item["funding_verified"])
        self.assertFalse(item["payout_verified"])
        self.assertEqual(item["commercial_status"], "unverified_lead")

    def test_warning_in_comments_blocks_assumption_of_payability(self):
        comments = [{"user": {"login": "maintainer"}, "body": "The bounty link is broken and the integration was disabled."}]
        result = inspect_comments(comments)
        self.assertEqual(result["platform_status"], "warning_detected_review_required")
        self.assertEqual(len(result["platform_warnings"]), 1)

    def test_bot_summary_is_not_payment_verification(self):
        comments = [{"user": {"login": "boss-bounty[bot]"}, "body": "Total Bounty: **$250**"}]
        result = inspect_comments(comments)
        self.assertEqual(result["platform_status"], "summary_seen_not_payment_verified")
        self.assertEqual(result["claim_or_champion_comment_count"], 0)

    def test_claim_activity_is_counted_not_claimed(self):
        comments = [{"user": {"login": "contributor"}, "body": "/claim 1"}]
        self.assertEqual(inspect_comments(comments)["claim_or_champion_comment_count"], 1)

    def test_rejects_issue_without_boss_marker(self):
        issue = self.issue()
        issue["body"] = "Ordinary issue"
        with self.assertRaises(ValueError):
            normalize_issue(issue, [])

if __name__ == "__main__":
    unittest.main()

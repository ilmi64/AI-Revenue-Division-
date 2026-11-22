"""Run: python -m unittest discover -s operations -p 'test_*.py'"""
import unittest
from datetime import datetime, timezone
from opportunity_intake import assess, evaluate

NOW = datetime(2026, 11, 22, tzinfo=timezone.utc)

def fixture(**changes):
    value = dict(id="test-1", kind="coding", title="Fix a bug",
                 source_url="https://example.org/task", scope_authorized=True,
                 cost_cad=0, requires_credentials=False, external_action=False,
                 deadline_utc="2027-01-10T00:00:00Z")
    value.update(changes)
    return value

class IntakeTests(unittest.TestCase):
    def test_review_ready_is_not_permission_to_execute(self):
        result = assess(fixture(), NOW)
        self.assertEqual(result["status"], "review_ready")
        self.assertEqual(result["next_action"], "human_review_only")

    def test_bounty_requires_authorized_scope(self):
        self.assertEqual(assess(fixture(kind="bug_bounty", scope_authorized=False), NOW)["status"], "hold")

    def test_no_paid_workflows(self):
        self.assertIn("upfront_cost_or_invalid_cost", assess(fixture(cost_cad=1), NOW)["reasons"])

    def test_credentials_require_approval(self):
        self.assertEqual(assess(fixture(requires_credentials=True), NOW)["status"], "hold")

    def test_external_actions_require_approval(self):
        self.assertEqual(assess(fixture(external_action=True), NOW)["status"], "hold")

    def test_expired_deadline(self):
        self.assertIn("expired", assess(fixture(deadline_utc="2026-01-01T00:00:00Z"), NOW)["reasons"])

    def test_naive_deadline_invalid(self):
        self.assertIn("invalid_deadline", assess(fixture(deadline_utc="2027-01-10"), NOW)["reasons"])

    def test_missing_field(self):
        item = fixture()
        del item["scope_authorized"]
        self.assertEqual(assess(item, NOW)["status"], "rejected")

    def test_duplicate_ids(self):
        self.assertEqual(evaluate([fixture(), fixture()], NOW)[1]["status"], "rejected")

    def test_invalid_url(self):
        self.assertEqual(assess(fixture(source_url="http://example.org"), NOW)["status"], "hold")

    def test_control_characters_in_url_are_rejected(self):
        for char in (chr(0), chr(1), chr(31), chr(127)):
            with self.subTest(codepoint=ord(char)):
                result = assess(fixture(source_url="https://exam" + char + "ple.org/task"), NOW)
                self.assertIn("unverified_source_url", result["reasons"])

    def test_non_list_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({"id": "wrong"}, NOW)

    def test_unhashable_kind_fails_closed(self):
        self.assertIn("unsupported_kind", assess(fixture(kind=["coding"]), NOW)["reasons"])

    def test_url_missing_hostname_fails_closed(self):
        self.assertIn("unverified_source_url", assess(fixture(source_url="https://"), NOW)["reasons"])

    def test_malformed_url_port_fails_closed(self):
        self.assertIn("unverified_source_url", assess(fixture(source_url="https://example.org:bad/path"), NOW)["reasons"])

    def test_unhashable_id_does_not_crash_batch(self):
        result = evaluate([fixture(id=["bad"])], NOW)
        self.assertEqual(result[0]["status"], "hold")

if __name__ == "__main__":
    unittest.main()

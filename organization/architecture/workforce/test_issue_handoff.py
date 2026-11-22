"""Offline synthetic-only checks for the issue handoff validator."""
import unittest
from dataclasses import replace

from issue_handoff import Company, Handoff, TestStatus, handoff_blockers


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.good = Handoff(
            company=Company.AI_REVENUE,
            issue_url="https://github.com/ilmi64/AI-Revenue-Division-/issues/26",
            issue_number=26,
            source_sha="a" * 40,
            task_branch="implementation/issue-handoff-validator-v1",
            allowed_operations=frozenset({"READ_SOURCE", "OFFLINE_SYNTHETIC_TEST"}),
            test_status=TestStatus.NOT_VERIFIED,
            evidence_refs=(),
        )

    def test_valid_record_is_not_authorization(self):
        self.assertEqual(handoff_blockers(self.good), ())
        self.assertTrue(self.good.human_approval_required)

    def test_malformed_object_fails_closed(self):
        self.assertEqual(handoff_blockers({}), ("invalid_handoff",))

    def test_wrong_company_issue_fails(self):
        self.assertIn("issue_scope_mismatch", handoff_blockers(replace(
            self.good, company=Company.TRADING_TECHNOLOGY)))

    def test_missing_source_pin_fails(self):
        self.assertIn("invalid_source_pin", handoff_blockers(replace(
            self.good, source_sha="main")))

    def test_forbidden_operations_fail(self):
        for operation in ("LIVE_TRADE", "DEPLOY", "RUN_CI", "PAID_API", "MERGE", "CUSTOMER_OUTREACH"):
            with self.subTest(operation=operation):
                record = replace(self.good, allowed_operations=frozenset({"READ_SOURCE", operation}))
                self.assertIn("unauthorized_operations", handoff_blockers(record))

    def test_wrong_status_and_approval_fail(self):
        record = replace(self.good, test_status="PASS", human_approval_required=False)
        self.assertIn("invalid_test_status", handoff_blockers(record))
        self.assertIn("human_approval_missing", handoff_blockers(record))

    def test_issue_number_and_url_strict(self):
        for url in ("http://github.com/ilmi64/AI-Revenue-Division-/issues/26",
                    "https://github.com.evil.test/ilmi64/AI-Revenue-Division-/issues/26",
                    "https://github.com/ilmi64/AI-Revenue-Division-/issues/26?run=true"):
            with self.subTest(url=url):
                self.assertIn("issue_scope_mismatch", handoff_blockers(replace(self.good, issue_url=url)))

    def test_branch_traversal_fails(self):
        self.assertIn("invalid_task_branch", handoff_blockers(replace(
            self.good, task_branch="implementation/../main")))


if __name__ == "__main__":
    unittest.main()

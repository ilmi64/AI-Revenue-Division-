"""Synthetic offline issue-gate tests; no GitHub/Codex calls."""
import unittest
from dataclasses import replace
from issue_dispatch_gate import DispatchState, plan_dispatch, validate_issue_payload

REPO = "ilmi64/AI-Revenue-Division-"
GOOD = {
    "number": 24,
    "title": "Offline QA verification",
    "body": (
        "## Starting points\n`organization/architecture/ai_revenue/mini_review_evidence.py`\n"
        "Source SHA: " + "a" * 40 + "\n"
        "## Authorized implementation\nRun offline tests.\n"
        "## Acceptance criteria\nReport actual test evidence. Stop and request explicit approval.\n"
    ),
}


class IssueGateTests(unittest.TestCase):
    def test_complete_payload_is_manual_ready(self):
        result = plan_dispatch(GOOD, REPO, explicit_approval=True)
        self.assertEqual(result.state, DispatchState.READY_FOR_MANUAL_START)
        self.assertIn("#24", result.manual_instruction)

    def test_no_approval_blocks(self):
        self.assertIn("explicit_approval_required",
                      plan_dispatch(GOOD, REPO, explicit_approval=False).blockers)

    def test_missing_source_pin_blocks(self):
        payload = {**GOOD, "body": GOOD["body"].replace("a" * 40, "main")}
        self.assertIn("missing_immutable_source_sha", validate_issue_payload(payload, REPO))

    def test_missing_acceptance_blocks(self):
        payload = {**GOOD, "body": GOOD["body"].replace("## Acceptance criteria", "## Notes")}
        self.assertIn("missing_acceptance_section", validate_issue_payload(payload, REPO))

    def test_missing_scoped_target_blocks(self):
        payload = {**GOOD, "body": GOOD["body"].replace(
            "`organization/architecture/ai_revenue/mini_review_evidence.py`", "some files")}
        self.assertIn("missing_scoped_module_targets", validate_issue_payload(payload, REPO))

    def test_missing_stop_blocks(self):
        payload = {**GOOD, "body": GOOD["body"].replace("Stop and request explicit approval.", "Finished.")}
        self.assertIn("missing_stop_or_escalation", validate_issue_payload(payload, REPO))

    def test_claimed_launcher_never_starts_cloud(self):
        result = plan_dispatch(GOOD, REPO, explicit_approval=True, supported_cloud_launcher=True)
        self.assertEqual(result.state, DispatchState.READY_FOR_MANUAL_START)

    def test_wrong_repo_blocks(self):
        self.assertIn("unknown_repository", validate_issue_payload(GOOD, "some/other-repo"))


if __name__ == "__main__":
    unittest.main()

"""Offline negative and end-to-end tests for the role-separated fixture mediator."""
from dataclasses import replace
import json
import unittest
from unittest.mock import patch

from evidence_verifier import VerificationBlocked
from revenue_agent_queue import prepare_queue
from revenue_delivery_plan import plan_delivery
from revenue_fixture_dispatch import PROFILES, canonical, dispatch_fixture, fixture_ticket
from revenue_runtime_mediation import FixtureDelegation, FixtureMediation
from revenue_workflow_demo import _FIXTURE, run_demo


class RevenueRuntimeMediationTests(unittest.TestCase):
    def fixture(self):
        profile = PROFILES["coding"]
        item = replace(_FIXTURE, kind="coding", reference=profile.reference, country=profile.country)
        task = next(task for task in prepare_queue(plan_delivery(item)) if task.task == profile.task)
        return FixtureDelegation(fixture_ticket("coding", task)), task

    def test_delegator_worker_qa_and_anchor_order_ends_in_internal_review_only(self):
        report = run_demo(mode="anchored", service="coding")
        audit = report["private_audit"]
        self.assertEqual([event["stage"] for event in audit], [
            "fixture_delegated", "worker_attempt", "independent_fixture_qa",
            "known_answer_checked", "anchored_receipt_readback",
        ])
        self.assertEqual(len({
            audit[0]["delegator_role"], audit[0]["worker_role"], audit[2]["role"],
        }), 3)
        self.assertEqual(report["private_runtime"]["state"], "REVIEW_READY")
        self.assertEqual(report["private_runtime"]["commissioning"]["status"], "HOLD")
        self.assertIs(report["receipt"]["release_authorized"], False)
        self.assertIs(report["agent_execution_authorized"], False)
        self.assertIs(report["external_actions_performed"], False)
        for private in ("fixture_delegated", "commissioning", "artifact_sha256", "ar_qa_reviewer"):
            self.assertNotIn(private, json.dumps(report["occ"]))

    def test_transient_local_failure_retries_once_with_same_scope_before_qa(self):
        delegation, task = self.fixture()
        valid = dispatch_fixture(delegation.ticket, task)
        with patch(
            "revenue_runtime_mediation.dispatch_fixture",
            side_effect=[VerificationBlocked("offline_worker_evidence_unavailable"), valid],
        ) as worker:
            report = run_demo(mode="anchored", service="coding")
        self.assertEqual(worker.call_count, 2)
        self.assertEqual(worker.call_args_list[0], worker.call_args_list[1])
        self.assertTrue(report["private_audit"][2]["retrying_same_scope"])
        self.assertEqual(report["private_test_log"]["fixture_runtime_events"][2],
                         report["private_audit"][2])
        self.assertIsNone(report["private_runtime"]["supervisor_escalation"])
        self.assertIs(report["receipt"]["release_authorized"], False)

    def test_exhausted_and_invalid_results_escalate_without_qa_or_anchor(self):
        for reason, attempts in (
            ("offline_worker_evidence_unavailable", 2), ("malformed_offline_worker_output", 1),
        ):
            with self.subTest(reason=reason), patch(
                "revenue_runtime_mediation.dispatch_fixture", side_effect=VerificationBlocked(reason),
            ) as worker, patch("revenue_runtime_mediation.review_evidence") as qa, patch(
                "revenue_runtime_mediation._verify_anchored_fixture",
            ) as anchor:
                report = run_demo(mode="anchored", service="coding")
                self.assertEqual(worker.call_count, attempts)
                qa.assert_not_called()
                anchor.assert_not_called()
            self.assertIsNone(report["receipt"])
            self.assertEqual(report["private_runtime"]["state"], "HOLD")
            self.assertEqual(report["private_runtime"]["supervisor_escalation"]["role"], "ar_cto")
            self.assertFalse(report["private_runtime"]["supervisor_escalation"]["automatic_resume_authorized"])
            self.assertEqual(report["occ"]["counts"]["blocked"], 1)

    def test_anchor_failure_escalates_and_never_retries(self):
        for failure, reason in (
            (VerificationBlocked("anchor_or_audit_unavailable"), "anchor_or_audit_unavailable"),
            (OSError("anchor fixture I/O error"), "offline_anchor_evidence_unavailable"),
        ):
            with self.subTest(reason=reason), patch(
                "revenue_runtime_mediation._verify_anchored_fixture", side_effect=failure,
            ) as anchor:
                report = run_demo(mode="anchored", service="coding")
                anchor.assert_called_once()
            self.assertIsNone(report["receipt"])
            self.assertEqual(report["private_task_review"]["status"], "EVIDENCE_REVIEWED")
            self.assertEqual(report["private_runtime"]["supervisor_escalation"]["reason"], reason)
            self.assertEqual(report["occ"]["counts"]["blocked"], 1)

    def test_ticket_expansion_qa_collusion_and_arbitrary_runtime_denied(self):
        delegation, task = self.fixture()
        for invalid in (
            None, replace(delegation, runtime="custom-command"),
            replace(delegation, reviewer_role=delegation.ticket.role_id),
            replace(delegation, supervisor_role="trading_supervisor"),
            replace(delegation, max_worker_attempts=3),
            replace(delegation, ticket=replace(delegation.ticket, company_id="trading_technology")),
            replace(delegation, ticket=replace(delegation.ticket, maximum_cost_cad=10)),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(VerificationBlocked):
                FixtureMediation(invalid, task)

    def test_out_of_order_steps_and_artifact_replacement_cannot_anchor(self):
        delegation, task = self.fixture()
        mediation = FixtureMediation(delegation, task)
        with self.assertRaisesRegex(VerificationBlocked, "stage_precondition"):
            mediation.anchor(anchor_available=True)
        with self.assertRaisesRegex(VerificationBlocked, "stage_precondition"):
            mediation.review_artifact(b"{}")
        mediation.run_worker()
        valid = run_demo(mode="anchored", service="coding")["private_artifact"]["contents"]
        valid["deliverable"]["total_cents"] += 1
        with self.assertRaisesRegex(VerificationBlocked, "artifact_scope_mismatch"):
            mediation.review_artifact(canonical(valid))
        with self.assertRaisesRegex(VerificationBlocked, "stage_precondition"):
            mediation.run_worker()
        with self.assertRaisesRegex(VerificationBlocked, "stage_precondition"):
            mediation.anchor(anchor_available=True)

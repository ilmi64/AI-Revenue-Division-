"""Synthetic commercial scope and static defensive-intake acceptance tests."""
from dataclasses import replace
import json
import unittest
from unittest.mock import patch

from evidence_verifier import VerificationBlocked
from revenue_agent_queue import prepare_queue
from revenue_commercial_scope import fixed_review_scope
from revenue_delivery_plan import plan_delivery
from revenue_fixture_dispatch import PROFILES, canonical, dispatch_fixture, fixture_ticket
from revenue_runtime_mediation import FixtureDelegation, FixtureMediation
from revenue_workflow_demo import _FIXTURE, run_demo


class RevenueCommercialScopeTests(unittest.TestCase):
    def test_four_service_briefs_bind_exact_internal_scope_and_still_deny_release(self):
        for service in PROFILES:
            with self.subTest(service=service):
                report = run_demo(mode="anchored", service=service)
                commercial = report["private_commercial_review"]
                self.assertEqual(commercial["status"], "INTERNAL_EVIDENCE_READY")
                self.assertEqual(commercial["external_approval"], "NOT_GRANTED")
                self.assertEqual(report["private_runtime"]["commissioning"]["status"], "HOLD")
                self.assertEqual(commercial["scope"]["company_id"], "ai_revenue")
                self.assertEqual(commercial["scope"]["recipient_scope"], "ai_revenue")
                self.assertIn("internal_owner_review_only", json.dumps(commercial))
                self.assertIs(commercial["scope"]["external_approval_granted"], False)
                self.assertEqual(
                    commercial["scope"], report["private_artifact"]["contents"]["commercial_review_scope"],
                )
                self.assertIs(report["receipt"]["release_authorized"], False)
                self.assertIs(report["customer_contact_authorized"], False)
                self.assertIs(report["spending_authorized"], False)
                self.assertNotIn("commercial", json.dumps(report["occ"]))
                self.assertNotIn(commercial["scope"]["work_scope"], json.dumps(report["occ"]))

    def test_company_recipient_tool_scope_or_approval_widening_blocks_before_worker(self):
        scope = fixed_review_scope("coding")
        with patch("revenue_workflow_demo.FixtureMediation") as worker:
            for changes in (
                {"company_id": "trading_technology"}, {"recipient_scope": "shared_research"},
                {"review_audience": "external_reviewer"}, {"work_scope": "arbitrary_shell"},
                {"service": "app_build"}, {"upfront_cost_cap_cad": 2},
                {"upfront_cost_cap_cad": False}, {"external_approval_granted": True},
                {"external_approval_granted": 0}, {"data_classification": "PRIVATE"},
            ):
                with self.subTest(changes=changes), self.assertRaisesRegex(
                    VerificationBlocked, "commercial_review_scope_mismatch",
                ):
                    run_demo(mode="anchored", service="coding", commercial_scope=replace(scope, **changes))
            worker.assert_not_called()

    def test_commercial_scope_substitution_after_worker_is_ineligible_for_qa_and_anchor(self):
        profile = PROFILES["coding"]
        opportunity = replace(_FIXTURE, kind="coding", reference=profile.reference, country=profile.country)
        task = next(task for task in prepare_queue(plan_delivery(opportunity)) if task.task == profile.task)
        for field, value in (
            ("recipient_scope", "other-tenant"), ("external_approval_granted", 0),
            ("upfront_cost_cap_cad", False),
        ):
            mediation = FixtureMediation(FixtureDelegation(fixture_ticket("coding", task)), task)
            mediation.run_worker()
            altered = run_demo(mode="anchored", service="coding")["private_artifact"]["contents"]
            altered["commercial_review_scope"][field] = value
            with self.subTest(field=field), patch("revenue_runtime_mediation.review_evidence") as qa:
                with self.assertRaisesRegex(VerificationBlocked, "artifact_scope_mismatch"):
                    mediation.review_artifact(canonical(altered))
                qa.assert_not_called()
            with self.assertRaisesRegex(VerificationBlocked, "stage_precondition"):
                mediation.anchor(anchor_available=True)

    def test_static_security_review_dispatches_no_subprocess_and_has_no_target(self):
        with patch("revenue_fixture_dispatch.subprocess.run") as runner:
            report = run_demo(mode="anchored", service="authorized_bug_bounty")
            runner.assert_not_called()
        contents = report["private_artifact"]["contents"]
        output = contents["deliverable"]
        self.assertEqual(output["disposition"], "INTERNAL_STATIC_TERMS_REVIEW_ONLY")
        self.assertEqual(output["terms"]["target_count"], 0)
        self.assertIs(output["terms"]["testing_permission"], False)
        self.assertIs(output["terms"]["submission_permission"], False)
        dispatchable = [task for task in contents["assignments"] if task["fixture_dispatchable"]]
        self.assertEqual([task["task"] for task in dispatchable], ["verify_program_scope"])
        self.assertEqual(dispatchable[0]["role_id"], "ar_compliance_researcher")
        self.assertEqual(report["private_audit"][2]["role"], "ar_qa_reviewer")
        self.assertIs(report["receipt"]["release_authorized"], False)
        self.assertIs(report["external_actions_performed"], False)

    def test_other_security_tasks_cannot_replace_static_scope_worker(self):
        profile = PROFILES["authorized_bug_bounty"]
        opportunity = replace(_FIXTURE, kind="authorized_bug_bounty", reference=profile.reference)
        queue = prepare_queue(plan_delivery(opportunity))
        scope_task = queue[0]
        ticket = fixture_ticket("authorized_bug_bounty", scope_task)
        with patch("revenue_fixture_dispatch._WORKERS") as workers:
            for task in queue[1:]:
                with self.subTest(task=task.task), self.assertRaises(VerificationBlocked):
                    dispatch_fixture(ticket, task)
            with self.assertRaisesRegex(VerificationBlocked, "scope_mismatch"):
                dispatch_fixture(replace(ticket, tool_allowlist=("network",)), scope_task)
            workers.__getitem__.assert_not_called()

    def test_missing_scope_paid_dependency_and_missing_anchor_leave_commissioning_held(self):
        for scenario in ("missing_scope", "paid_dependency", "missing_anchor"):
            with self.subTest(scenario=scenario):
                report = run_demo(mode="anchored", service="authorized_bug_bounty", scenario=scenario)
                self.assertEqual(report["private_commercial_review"]["status"], "HOLD")
                self.assertEqual(report["private_commercial_review"]["external_approval"], "NOT_GRANTED")
                self.assertIsNone(report["receipt"])
                self.assertIs(report["external_actions_performed"], False)
                self.assertIs(report["occ"]["execution_authorized"], False)

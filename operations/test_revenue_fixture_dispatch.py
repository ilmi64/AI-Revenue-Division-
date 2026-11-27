"""Exercise the allowlisted Aevora fixture dispatch and evidence boundaries."""
from dataclasses import replace
import json
from types import MappingProxyType
import unittest
from unittest.mock import patch

from evidence_verifier import VerificationBlocked
from revenue_agent_queue import prepare_queue
from revenue_delivery_plan import plan_delivery
from revenue_fixture_dispatch import PROFILES, dispatch_fixture, fixture_ticket
from revenue_workflow_demo import _FIXTURE, run_demo


class RevenueFixtureDispatchTests(unittest.TestCase):
    def setup_dispatch(self, service="coding"):
        profile = PROFILES[service]
        item = replace(_FIXTURE, kind=service, reference=profile.reference, country=profile.country)
        assignment = next(task for task in prepare_queue(plan_delivery(item)) if task.task == profile.task)
        return fixture_ticket(service, assignment), assignment

    def test_coding_worker_corrects_truncation_and_invokes_independent_qa(self):
        report = run_demo(mode="anchored", service="coding")
        output = report["private_artifact"]["contents"]["deliverable"]
        self.assertEqual(report["fixture_country"], "US")
        self.assertEqual(output["legacy_truncated_tax_cents"], 224)
        self.assertEqual(output["half_up_tax_cents"], 225)
        self.assertEqual(output["total_cents"], 4724)
        self.assertIn("-tax_cents = subtotal_cents * rate_bps // 10000", output["proposed_diff"])
        self.assertIn("+tax_cents = (subtotal_cents * rate_bps + 5000) // 10000", output["proposed_diff"])
        self.assertEqual(report["private_task_review"]["status"], "EVIDENCE_REVIEWED")
        self.assertIs(report["private_task_review"]["completion_verified"], False)
        self.assertIs(report["receipt"]["release_authorized"], False)

    def test_ai_workflow_routes_missing_and_outbound_to_holds_without_model(self):
        report = run_demo(mode="anchored", service="ai_setup")
        output = report["private_artifact"]["contents"]["deliverable"]
        self.assertEqual(report["fixture_country"], "GB")
        self.assertIs(output["model_invoked"], False)
        self.assertEqual([item["disposition"] for item in output["decisions"]], [
            "QUEUE_FOR_INDEPENDENT_QA", "HOLD_MISSING_EVIDENCE", "HOLD_EXTERNAL_ACTION",
        ])
        self.assertIs(report["receipt"]["release_authorized"], False)
        self.assertIs(report["agent_execution_authorized"], False)

    def test_dispatch_rejects_missing_malformed_and_scope_widening_before_worker(self):
        ticket, task = self.setup_dispatch()
        with patch("revenue_fixture_dispatch._WORKERS") as workers:
            for altered in (
                None, {}, replace(ticket, service="research"), replace(ticket, task_id="unknown-task"),
                replace(ticket, company_id="trading_technology"), replace(ticket, recipient_scope="shared_research"),
                replace(ticket, role_id="ar_qa_reviewer"), replace(ticket, data_classification="PRIVATE"),
                replace(ticket, source_fixture="../different.csv"), replace(ticket, maximum_cost_cad=1),
                replace(ticket, maximum_cost_cad=False), replace(ticket, tool_allowlist=("run_shell",)),
            ):
                with self.subTest(altered=altered), self.assertRaises(VerificationBlocked):
                    dispatch_fixture(altered, task)
            workers.__getitem__.assert_not_called()

    def test_assignment_replacement_or_execution_permission_denied(self):
        ticket, task = self.setup_dispatch()
        for altered in (
            None, replace(task, state="APPROVED"), replace(task, role="quality"),
            replace(task, execution_authorized=True), replace(task, external_delivery_authorized=True),
            replace(task, spending_authorized=True), replace(task, task_id="synthetic_invoice_rounding:01", sequence=1),
        ):
            with self.subTest(altered=altered), self.assertRaises(VerificationBlocked):
                dispatch_fixture(ticket, altered)

    def test_worker_exception_and_invalid_evidence_never_reach_anchor(self):
        def missing():
            raise OSError("fixture helper unavailable")

        for worker, reason in (
            (missing, "offline_worker_evidence_unavailable"),
            (lambda: ([], {}, "a" * 64), "malformed_offline_worker_output"),
            (lambda: ({}, {}, "invalid"), "malformed_offline_worker_output"),
            (lambda: ({"total_cents": 4723}, {}, "a" * 64), "offline_worker_known_answer_failed"),
        ):
            with self.subTest(reason=reason), patch(
                "revenue_fixture_dispatch._WORKERS", MappingProxyType({"coding": worker}),
            ), patch("revenue_runtime_mediation._verify_anchored_fixture") as anchor:
                report = run_demo(mode="anchored", service="coding")
                anchor.assert_not_called()
                self.assertIsNone(report["receipt"])
                self.assertEqual(report["private_audit"][-1]["reason"], reason)
                self.assertEqual(report["occ"]["counts"]["blocked"], 1)
                self.assertIs(report["release_authorized"], False)

    def test_nonapp_services_preserve_intake_and_anchor_gates_and_occ_redaction(self):
        for service in ("coding", "ai_setup"):
            for scenario in ("missing_scope", "paid_dependency", "missing_anchor"):
                with self.subTest(service=service, scenario=scenario):
                    report = run_demo(mode="anchored", service=service, scenario=scenario)
                    self.assertIsNone(report["receipt"])
                    self.assertIs(report["spending_authorized"], False)
                    self.assertIs(report["external_actions_performed"], False)
                    self.assertIs(report["customer_contact_authorized"], False)
                    self.assertIs(report["occ"]["execution_authorized"], False)
                    for private in ("fixture", "task_id", "checkpoint", "proposal", "review-routing"):
                        self.assertNotIn(private, json.dumps(report["occ"]).lower())

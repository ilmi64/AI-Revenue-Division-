"""Exercise Aevora's synthetic, anchored internal revenue workflow."""
from dataclasses import replace
import hashlib
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from anchored_evidence_verifier import AnchoredEvidenceVerifier
from revenue_workflow_demo import run_demo
from revenue_task_evidence import review_evidence


class RevenueWorkflowDemoTests(unittest.TestCase):
    def assert_release_denied(self, report):
        for flag in (
            "release_authorized", "external_actions_performed", "agent_execution_authorized",
            "customer_contact_authorized", "spending_authorized",
        ):
            self.assertIs(report[flag], False)
        self.assertIs(report["occ"]["execution_authorized"], False)

    def test_tangible_preflight_result_bound_to_anchored_review(self):
        report = run_demo(mode="anchored")
        self.assertEqual(report, run_demo(mode="anchored"))
        self.assertEqual(report["intake"]["status"], "REVIEW_READY")
        artifact = report["private_artifact"]["contents"]
        self.assertEqual(artifact["delivery_plan"]["classification"], "INTERNAL_PLAN_ONLY")
        self.assertEqual([item["role"] for item in artifact["assignments"]],
                         ["product", "product", "engineering", "quality"])
        self.assertEqual(artifact["assignments"][-1]["charter_division"], "Risk & Recovery")
        self.assertTrue(all(
            item["state"] == "AWAITING_INTERNAL_REVIEW" and not item["execution_authorized"]
            for item in artifact["assignments"]
        ))
        self.assertTrue(artifact["proposal"]["markdown"].startswith("SYNTHETIC INTERNAL DRAFT"))
        self.assertFalse(artifact["proposal"]["submission_authorized"])
        self.assertEqual([item["field"] for item in artifact["deliverable"]["findings"]], ["sku", "quantity"])
        artifact_bytes = json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        self.assertEqual(report["private_artifact"]["sha256"], hashlib.sha256(artifact_bytes).hexdigest())
        self.assertEqual(report["private_test_log"]["observed_exit_code"], 1)
        task_review = report["private_task_review"]
        self.assertEqual(task_review["task_id"], artifact["assignments"][2]["task_id"])
        self.assertEqual(task_review["status"], "EVIDENCE_REVIEWED")
        self.assertIs(task_review["completion_verified"], False)
        self.assertEqual(report["receipt"]["status"], "verified_for_owner_review")
        self.assertEqual(report["receipt"]["audit_sequence"], 1)
        self.assertIs(report["receipt"]["release_authorized"], False)
        self.assert_release_denied(report)

    def test_intake_hold_or_reject_never_runs_delivery_helper(self):
        for scenario, status in (("missing_scope", "HOLD"), ("paid_dependency", "REJECT")):
            with self.subTest(scenario=scenario), patch("revenue_runtime_mediation.dispatch_fixture") as run:
                report = run_demo(mode="anchored", scenario=scenario)
                run.assert_not_called()
                self.assertEqual(report["intake"]["status"], status)
                self.assertIsNone(report["private_artifact"])
                self.assertIsNone(report["receipt"])
                self.assert_release_denied(report)

    def test_missing_anchor_never_falls_back(self):
        report = run_demo(mode="anchored", scenario="missing_anchor")
        self.assertIsNotNone(report["private_artifact"])
        self.assertIsNone(report["receipt"])
        self.assertEqual(report["private_audit"][-1]["reason"], "anchor_or_audit_unavailable")
        self.assertEqual(report["occ"]["counts"]["blocked"], 1)
        self.assert_release_denied(report)

    def test_artifact_substitution_blocks_evidence_review(self):
        verify = AnchoredEvidenceVerifier.verify

        def substitute(verifier, manifest, *, deliverable, **evidence):
            return verify(verifier, manifest, deliverable=deliverable + b" altered", **evidence)

        with patch.object(AnchoredEvidenceVerifier, "verify", autospec=True, side_effect=substitute):
            report = run_demo(mode="anchored")
        self.assertIsNone(report["receipt"])
        self.assertEqual(report["private_audit"][-1]["reason"], "deliverable_digest_mismatch")
        self.assert_release_denied(report)

    def test_wrong_task_and_self_review_prevent_anchored_verification(self):
        for change, reason in (
            ({"task_id": "different-task"}, "task_identity_mismatch"),
            ({"reviewer_role": "engineering"}, "independent_review_unverified"),
        ):
            with self.subTest(change=change):
                def wrong_evidence(item, evidence):
                    return review_evidence(item, replace(evidence, **change))

                with patch("revenue_runtime_mediation.review_evidence", side_effect=wrong_evidence):
                    with patch("revenue_runtime_mediation._verify_anchored_fixture") as anchor:
                        report = run_demo(mode="anchored")
                        anchor.assert_not_called()
                self.assertIn(reason, report["private_task_review"]["reasons"])
                self.assertIsNone(report["receipt"])
                self.assertEqual(report["occ"]["counts"]["blocked"], 1)
                self.assert_release_denied(report)

    def test_cli_requires_anchored_mode_and_has_separate_occ_view(self):
        denied = subprocess.run(
            [sys.executable, "-m", "revenue_workflow_demo"], capture_output=True, timeout=10, check=False,
        )
        self.assertEqual(denied.returncode, 2)
        self.assertEqual(denied.stdout, b"")
        with self.assertRaisesRegex(ValueError, "explicit anchored"):
            run_demo(mode="unanchored")
        separate = subprocess.run(
            [sys.executable, "-m", "revenue_workflow_demo", "--mode", "anchored", "--view", "occ"],
            capture_output=True, timeout=10, check=True,
        )
        self.assertEqual(json.loads(separate.stdout), run_demo(mode="anchored")["occ"])
        for private in (b"fixture-engineering-builder", b"manifest_sha256", b"proposal", b"CAD"):
            self.assertNotIn(private, separate.stdout)

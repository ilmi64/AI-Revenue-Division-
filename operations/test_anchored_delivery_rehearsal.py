"""Exercise the public synthetic workflow and its anchored fault paths."""
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from anchored_delivery_rehearsal import SCENARIOS
from evidence_verifier import VerificationBlocked
from synthetic_delivery_rehearsal import run_rehearsal


class AnchoredDeliveryRehearsalTests(unittest.TestCase):
    def assert_blocked(self, scenario, reason):
        report = run_rehearsal(mode="anchored", scenario=scenario)
        self.assertIsNone(report["receipt"])
        self.assertEqual(report["occ"]["counts"]["blocked"], 1)
        self.assertFalse(report["release_authorized"])
        self.assertFalse(report["external_actions_performed"])
        self.assertEqual(report["private_audit"][-1]["status"], "denied")
        self.assertIn(
            {"stage": "verification", "status": "blocked", "reason": reason},
            report["private_audit"],
        )

    def test_verified_receipt_is_anchored_and_never_releases(self):
        report = run_rehearsal(mode="anchored")
        receipt = report["receipt"]
        self.assertEqual(receipt["status"], "verified_for_owner_review")
        self.assertEqual(receipt["audit_sequence"], 1)
        readback = next(row for row in report["private_audit"]
                        if row["stage"] == "anchored_receipt_readback")
        for field in ("audit_sequence", "audit_sha256", "manifest_sha256"):
            self.assertEqual(receipt[field], readback[field])
        self.assertIs(receipt["release_authorized"], False)
        self.assertIs(report["release_authorized"], False)
        self.assertIs(report["external_actions_performed"], False)
        self.assertEqual(report, run_rehearsal(mode="anchored"))

    def test_authority_failure_cannot_fall_back_to_legacy_replay_store(self):
        with (
            patch("synthetic_delivery_rehearsal._verify_fixture",
                  side_effect=AssertionError("legacy rehearsal path reached")) as legacy,
            patch("synthetic_delivery_rehearsal.SQLiteReviewReplayStore",
                  side_effect=AssertionError("unanchored replay store reached")) as replay_store,
        ):
            self.assert_blocked("missing_anchor", "anchor_or_audit_unavailable")
            with patch("anchored_delivery_rehearsal.AnchoredEvidenceVerifier.verify",
                       side_effect=VerificationBlocked("injected_anchor_outage")):
                self.assert_blocked("baseline", "injected_anchor_outage")
            legacy.assert_not_called()
            replay_store.assert_not_called()

    def test_audit_integrity_and_checkpoint_continuity(self):
        cases = {
            "missing_audit": "anchor_or_audit_unavailable",
            "corrupted_audit": "audit_chain_invalid",
            "interrupted_commit": "audit_anchor_divergence",
            "coordinated_rollback": "audit_receipt_not_anchored",
        }
        for scenario, reason in cases.items():
            with self.subTest(scenario=scenario):
                self.assert_blocked(scenario, reason)

    def test_current_trust_and_exact_company_recipient_and_policy_required(self):
        cases = {
            "stale_trust": "stale_trust_or_policy",
            "wrong_company": "invalid_or_mismatched_manifest_scope",
            "wrong_recipient": "invalid_or_mismatched_manifest_scope",
            "stale_policy": "stale_trust_or_policy",
        }
        for scenario, reason in cases.items():
            with self.subTest(scenario=scenario):
                self.assert_blocked(scenario, reason)

    def test_nonce_replay_is_blocked_across_verifier_reopen(self):
        self.assert_blocked("nonce_replay", "replay_conflict")

    def test_occ_exposes_counters_without_trust_or_audit_data(self):
        report = run_rehearsal(mode="anchored")
        occ = report["occ"]
        self.assertEqual(occ["mode"], "read_only_aggregate")
        self.assertEqual(occ["counts"]["checklist_complete_unverified"], 1)
        self.assertFalse(occ["execution_authorized"])
        rendered = json.dumps(occ)
        for private_value in (report["receipt"]["manifest_sha256"],
                              report["receipt"]["audit_sha256"], "fixture-qa",
                              "fixture-owner", "fictional-recipient", "verified_for_owner_review"):
            self.assertNotIn(private_value, rendered)

    def test_public_cli_requires_anchored_mode(self):
        command = [sys.executable, "-m", "synthetic_delivery_rehearsal"]
        for options in ([], ["--mode", "unanchored"]):
            with self.subTest(options=options):
                outcome = subprocess.run(
                    command + options, capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(outcome.returncode, 2)
                self.assertEqual(outcome.stdout, "")
        outcome = subprocess.run(command + ["--mode", "anchored"], check=True,
                                 capture_output=True, text=True, timeout=15)
        reports = json.loads(outcome.stdout)
        self.assertEqual([item["scenario"] for item in reports], list(SCENARIOS))
        self.assertTrue(all(item["verification_mode"] == "anchored" for item in reports))
        self.assertTrue(all(item["release_authorized"] is False for item in reports))
        self.assertEqual(sum(item["receipt"] is not None for item in reports), 1)


if __name__ == "__main__":
    unittest.main()

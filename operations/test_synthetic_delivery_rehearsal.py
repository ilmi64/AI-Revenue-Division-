"""Synthetic end-to-end approval, denial and redaction regression tests."""
import json
import unittest

from synthetic_delivery_rehearsal import run_unanchored_fixture_rehearsal as run_rehearsal


class SyntheticDeliveryRehearsalTests(unittest.TestCase):
    def assert_delivery_denied(self, report):
        self.assertIs(report["release_authorized"], False)
        self.assertIs(report["external_actions_performed"], False)
        self.assertEqual(report["private_audit"][-1], {
            "stage": "external_delivery", "status": "denied", "release_authorized": False,
        })
        self.assertIs(report["occ"]["execution_authorized"], False)
        self.assertIs(report["occ"]["external_actions_performed"], False)

    def test_verifies_fixture_and_explicitly_denies_delivery(self):
        report = run_rehearsal()
        self.assertEqual(report, run_rehearsal())
        self.assertEqual(report["receipt"]["status"], "verified_for_owner_review")
        self.assertIs(report["receipt"]["release_authorized"], False)
        events = {entry["stage"]: entry for entry in report["private_audit"]}
        self.assertEqual(events["intake"]["status"], "review_ready")
        self.assertEqual(events["checklist"]["status"], "checklist_complete_unverified")
        self.assertEqual(events["nonce_claim"]["manifest_sha256"], report["receipt"]["manifest_sha256"])
        self.assertEqual(report["occ"]["counts"]["checklist_complete_unverified"], 1)
        self.assert_delivery_denied(report)

    def test_negative_paths_emit_blocked_audits_and_no_receipt(self):
        for case, reason in (
            ("missing_registry", "trust_registry_unavailable"),
            ("revoked_reviewer", "untrusted_attestation_key"),
            ("wrong_recipient", "invalid_or_mismatched_manifest_scope"),
            ("wrong_company", "invalid_or_mismatched_manifest_scope"),
            ("stale_policy", "invalid_or_mismatched_manifest_scope"),
            ("replay", "replay_conflict"),
            ("snapshot_rollback", "replay_snapshot_checkpoint_mismatch"),
            ("unavailable_store", "replay_store_unavailable"),
            ("aborted_transaction", "replay_conflict_or_store_integrity_error"),
        ):
            with self.subTest(case=case):
                report = run_rehearsal(case)
                self.assertIsNone(report["receipt"])
                self.assertIn(
                    {"stage": "verification", "status": "blocked", "reason": reason},
                    report["private_audit"],
                )
                self.assertEqual(report["occ"]["counts"]["blocked"], 1)
                self.assert_delivery_denied(report)

    def test_rollback_failures_leave_explicit_audit_evidence(self):
        transaction = run_rehearsal("aborted_transaction")
        self.assertIn({"stage": "transaction_rollback", "nonce_claims": 0}, transaction["private_audit"])
        snapshot = run_rehearsal("snapshot_rollback")
        self.assertIn({"stage": "snapshot_checkpoint", "status": "mismatch"}, snapshot["private_audit"])
        self.assertIn("nonce_claim", [event["stage"] for event in snapshot["private_audit"]])

    def test_occ_projection_contains_only_counters_and_static_metadata(self):
        report = run_rehearsal()
        public = report["occ"]
        self.assertEqual(set(public), {
            "organization", "source_company", "recipient", "mode", "total", "counts",
            "execution_authorized", "external_actions_performed",
        })
        aggregate = json.dumps(public)
        for private in (
            "fictional-opp-1", "fictional-recipient", "manifest_sha256", "sha256",
            "fixture-owner", "fixture-producer", "verified_for_owner_review",
        ):
            self.assertNotIn(private, aggregate)

    def test_scenario_name_is_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown synthetic scenario"):
            run_rehearsal("unrecognized")

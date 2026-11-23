"""Offline stdlib regression tests for strict OCC reporting boundary."""
import copy
import unittest

from occ_commissioning_projection import ProjectionRejected, project


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"company_id": "aevora_ai", "commit_sha": "3" * 40, "gate": "BLOCKED",
             "test_provenance": "OFFLINE_REPORTED", "blockers": ["custody", "owner"], "evidence_digest": None},
            {"company_id": "trading_technology", "commit_sha": None, "gate": "UNKNOWN",
             "test_provenance": "UNVERIFIED", "blockers": ["recovery"], "evidence_digest": None},
        ]

    def test_valid_is_non_authoritative(self):
        result = project(self.rows)
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(len(result["companies"]), 2)

    def test_order_independent(self):
        self.assertEqual(project(self.rows), project(list(reversed(self.rows))))

    def test_private_fields_rejected(self):
        for name in ("private_manifest", "signer_id", "wallet", "customer", "signed_review", "authority"):
            with self.subTest(name=name):
                rows = copy.deepcopy(self.rows)
                rows[0][name] = "secret"
                with self.assertRaises(ProjectionRejected):
                    project(rows)

    def test_no_approved_green_or_execution_status(self):
        for gate in ("APPROVED", "READY", "GREEN", "RELEASED", "COMMISSIONED", True, None):
            with self.subTest(gate=gate):
                rows = copy.deepcopy(self.rows)
                rows[0]["gate"] = gate
                with self.assertRaises(ProjectionRejected):
                    project(rows)

    def test_missing_and_duplicate_companies_rejected(self):
        for rows in ([], [self.rows[0]], [self.rows[0], self.rows[0]], self.rows + [self.rows[1]]):
            with self.assertRaises(ProjectionRejected):
                project(rows)

    def test_unknown_fields_and_invalid_hashes_rejected(self):
        for field, value in (("commit_sha", "short"), ("commit_sha", "Z" * 40),
                             ("evidence_digest", "x" * 64), ("blockers", ["custody", "custody"]),
                             ("test_provenance", "PASSED")):
            with self.subTest(field=field):
                rows = copy.deepcopy(self.rows)
                rows[0][field] = value
                with self.assertRaises(ProjectionRejected):
                    project(rows)

    def test_missing_commit_cannot_claim_test_reproduction(self):
        rows = copy.deepcopy(self.rows)
        rows[1]["test_provenance"] = "INDEPENDENTLY_REPRODUCED"
        with self.assertRaises(ProjectionRejected):
            project(rows)

    def test_reconciliation_requires_recovery_blocker(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["gate"] = "RECONCILIATION_REQUIRED"
        with self.assertRaises(ProjectionRejected):
            project(rows)
        rows[0]["blockers"].append("recovery")
        self.assertEqual(project(rows)["companies"][0]["gate"], "RECONCILIATION_REQUIRED")

    def test_input_not_mutated(self):
        before = copy.deepcopy(self.rows)
        project(self.rows)
        self.assertEqual(self.rows, before)


if __name__ == "__main__":
    unittest.main()

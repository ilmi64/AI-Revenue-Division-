"""Adversarial fail-closed tests for OCC's two-company reporting boundary."""
import copy
import unittest

from occ_commissioning_projection import ProjectionRejected, project


def fixture():
    return [
        {"company_id": "aevora_ai", "commit_sha": "a" * 40, "gate": "BLOCKED",
         "test_provenance": "OFFLINE_REPORTED", "blockers": ["owner"], "evidence_digest": None},
        {"company_id": "trading_technology", "commit_sha": "b" * 40, "gate": "BLOCKED",
         "test_provenance": "UNVERIFIED", "blockers": ["recovery"], "evidence_digest": None},
    ]


class AdversarialProjectionTests(unittest.TestCase):
    def test_rejects_top_level_non_list_types(self):
        for value in (None, {}, "a", (), True, 2):
            with self.subTest(value=value), self.assertRaises(ProjectionRejected):
                project(value)

    def test_rejects_row_type_confusion(self):
        for value in (None, [], "a", True, 1):
            rows = fixture()
            rows[0] = value
            with self.subTest(value=value), self.assertRaises(ProjectionRejected):
                project(rows)

    def test_rejects_nested_blocker_data(self):
        for value in (None, {}, ["owner"], ["owner", {"secret": "private"}], "owner", True):
            rows = fixture()
            rows[0]["blockers"] = value
            with self.subTest(value=value), self.assertRaises(ProjectionRejected):
                project(rows)

    def test_rejects_case_and_unicode_company_spoofing(self):
        for company in ("AEVORA_AI", "aevora_ai ", "aevora_ai\u200b", "trading_technology"):
            rows = fixture()
            rows[0]["company_id"] = company
            with self.subTest(company=company), self.assertRaises(ProjectionRejected):
                project(rows)

    def test_rejects_authorization_field_injection(self):
        for field in ("release_authorized", "execution_authorized", "approval", "private_manifest"):
            rows = fixture()
            rows[0][field] = True
            with self.subTest(field=field), self.assertRaises(ProjectionRejected):
                project(rows)

    def test_rejects_uppercase_and_oversized_digest(self):
        for digest in ("F" * 64, "f" * 65, "f" * 63, "f" * 64 + "\n"):
            rows = fixture()
            rows[0]["evidence_digest"] = digest
            with self.subTest(digest=digest), self.assertRaises(ProjectionRejected):
                project(rows)

    def test_projection_is_deterministic_and_non_mutating(self):
        rows = fixture()
        before = copy.deepcopy(rows)
        one = project(rows)
        two = project(list(reversed(rows)))
        self.assertEqual(one, two)
        self.assertEqual(rows, before)
        self.assertFalse(one["release_authorized"])
        self.assertFalse(one["execution_authorized"])


if __name__ == "__main__":
    unittest.main()

"""OCC cannot elevate a company-supplied verification claim."""
import unittest

from occ_commissioning_projection import ProjectionRejected, project


def rows():
    return [
        {"company_id": "aevora_ai", "commit_sha": "a" * 40, "gate": "BLOCKED",
         "test_provenance": "OFFLINE_REPORTED", "blockers": ["ci"], "evidence_digest": None},
        {"company_id": "trading_technology", "commit_sha": "b" * 40, "gate": "UNKNOWN",
         "test_provenance": "UNVERIFIED", "blockers": ["recovery"], "evidence_digest": None},
    ]


class ProvenanceBoundaryTests(unittest.TestCase):
    def test_rejects_self_asserted_independent_reproduction(self):
        data = rows()
        data[0]["test_provenance"] = "INDEPENDENTLY_REPRODUCED"
        with self.assertRaises(ProjectionRejected):
            project(data)

    def test_rejects_self_asserted_ci_success(self):
        data = rows()
        data[0]["test_provenance"] = "CI_PASSED"
        with self.assertRaises(ProjectionRejected):
            project(data)

    def test_accepts_reported_without_promoting(self):
        report = project(rows())
        self.assertEqual(report["companies"][0]["test_provenance"], "OFFLINE_REPORTED")
        self.assertFalse(report["release_authorized"])


if __name__ == "__main__":
    unittest.main()

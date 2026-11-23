"""Offline isolation and evidence-freshness representation tests.

OCC is a reporting boundary, not a trusted clock or evidence verifier.
"""
import copy
import unittest

from occ_commissioning_projection import ProjectionRejected, project


def rows():
    return [
        {"company_id": "aevora_ai", "commit_sha": "a" * 40, "gate": "BLOCKED",
         "test_provenance": "OFFLINE_REPORTED", "blockers": ["custody"], "evidence_digest": None},
        {"company_id": "trading_technology", "commit_sha": "b" * 40, "gate": "UNKNOWN",
         "test_provenance": "UNVERIFIED", "blockers": ["trusted_time"], "evidence_digest": None},
    ]


class IsolationTests(unittest.TestCase):
    def test_company_isolation(self):
        original = project(rows())
        altered = rows()
        altered[0]["blockers"] = ["owner", "risk"]
        after = project(altered)
        trading_before = next(x for x in original["companies"] if x["company_id"] == "trading_technology")
        trading_after = next(x for x in after["companies"] if x["company_id"] == "trading_technology")
        self.assertEqual(trading_before, trading_after)
        self.assertNotEqual(original["companies"], after["companies"])

    def test_unknown_is_never_authorized(self):
        report = project(rows())
        self.assertFalse(report["release_authorized"])
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["companies"][1]["gate"], "UNKNOWN")

    def test_unverified_evidence_digest_does_not_authorize(self):
        data = rows()
        data[0]["evidence_digest"] = "f" * 64
        report = project(data)
        self.assertFalse(report["release_authorized"])
        self.assertEqual(report["companies"][0]["test_provenance"], "OFFLINE_REPORTED")

    def test_missing_commit_cannot_be_called_reproduced(self):
        data = rows()
        data[0]["commit_sha"] = None
        data[0]["test_provenance"] = "INDEPENDENTLY_REPRODUCED"
        with self.assertRaises(ProjectionRejected):
            project(data)

    def test_company_cannot_supply_extra_evidence_fields(self):
        for field in ("timestamp", "fresh", "expires_at", "customer_id", "source_keys"):
            data = rows()
            data[0][field] = "claimed"
            with self.subTest(field=field), self.assertRaises(ProjectionRejected):
                project(data)

    def test_reconciliation_cannot_omit_recovery(self):
        data = rows()
        data[1]["gate"] = "RECONCILIATION_REQUIRED"
        with self.assertRaises(ProjectionRejected):
            project(data)
        data[1]["blockers"].append("recovery")
        self.assertEqual(project(data)["companies"][1]["gate"], "RECONCILIATION_REQUIRED")

    def test_report_does_not_alias_mutable_input(self):
        data = rows()
        report = project(data)
        saved = copy.deepcopy(report)
        data[0]["blockers"].append("owner")
        self.assertEqual(report, saved)


if __name__ == "__main__":
    unittest.main()

"""Offline structural tests for canonical OCC risk and evidence records."""
import copy
import json
import unittest

from validate_registers import PATHS, validate_all


class OCCRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {
            key: json.loads(path.read_text(encoding="utf-8"))
            for key, path in PATHS.items()
        }

    def changed(self, key):
        result = copy.deepcopy(self.data)
        return result

    def validate(self, data):
        return validate_all(
            data["incidents"], data["risks"], data["decisions"],
            data["queue"], data["registry"], data["evidence"]
        )

    def test_current_canonical_registers_pass(self):
        self.assertEqual(self.validate(self.data), [])

    def test_duplicate_risk_id_fails(self):
        data = self.changed("risks")
        data["risks"]["records"].append(copy.deepcopy(data["risks"]["records"][0]))
        self.assertTrue(any("Risk IDs must be unique" in e for e in self.validate(data)))

    def test_unknown_risk_task_reference_fails(self):
        data = self.changed("risks")
        data["risks"]["records"][0]["related_task_ids"] = ["MISSING"]
        self.assertTrue(any("invalid task reference" in e for e in self.validate(data)))

    def test_unknown_evidence_division_fails(self):
        data = self.changed("evidence")
        data["evidence"]["records"] = [{
            "evidence_id": "EVD-1", "recorded_at_utc": "2026-11-16T00:00:00Z",
            "source_division": "unknown", "evidence_type": "report",
            "description": "test", "source_reference": "test:ref",
            "captured_at_utc": "2026-11-16T00:00:00Z",
            "integrity_status": "not_checked", "review_status": "unreviewed",
            "related_incident_ids": [], "access_classification": "internal",
            "retention_review_at_utc": None
        }]
        self.assertTrue(any("unknown source division" in e for e in self.validate(data)))

    def test_secret_fields_are_rejected(self):
        data = self.changed("evidence")
        data["evidence"]["api_secret"] = "never-store-this"
        self.assertTrue(any("prohibited secret field" in e for e in self.validate(data)))

    def test_invalid_incident_lifecycle_still_fails(self):
        data = self.changed("incidents")
        data["incidents"]["records"] = [{"id": "INC-1", "severity": "critical"}]
        self.assertTrue(self.validate(data))


if __name__ == "__main__":
    unittest.main()

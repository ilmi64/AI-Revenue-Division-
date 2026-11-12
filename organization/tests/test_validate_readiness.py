import copy
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_readiness import validate


class ReadinessValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.registry = json.loads((root / "division-registry.json").read_text(encoding="utf-8"))
        cls.readiness = json.loads((root / "readiness-register.json").read_text(encoding="utf-8"))

    def test_current_register_is_valid_but_reports_unassessed_divisions(self):
        errors, warnings = validate(self.registry, self.readiness)
        self.assertEqual(errors, [])
        self.assertTrue(any("No readiness assessment yet" in item for item in warnings))

    def test_unknown_assessment_division_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["division_assessments"][0]["division_id"] = "not-a-division"
        errors, _ = validate(self.registry, readiness)
        self.assertTrue(any("unknown division" in item for item in errors))

    def test_standby_without_check_evidence_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        item = readiness["division_assessments"][0]
        item["claimed_status"] = "standby"
        item["verified_status"] = "standby"
        item["open_gaps"] = []
        errors, _ = validate(self.registry, readiness)
        self.assertTrue(any("check_results are missing" in item for item in errors))

    def test_failed_check_cannot_support_operational_status(self):
        readiness = copy.deepcopy(self.readiness)
        item = readiness["division_assessments"][0]
        item["claimed_status"] = "operational"
        item["verified_status"] = "operational"
        item["open_gaps"] = []
        item["check_results"] = {
            check["id"]: {"status": "passed", "evidence": "test evidence"}
            for check in readiness["checks"]
            if "operational" in check["required_for"]
        }
        item["check_results"]["tests"]["status"] = "failed"
        errors, _ = validate(self.registry, readiness)
        self.assertTrue(any("tests lacks passed status" in item for item in errors))


if __name__ == "__main__":
    unittest.main()

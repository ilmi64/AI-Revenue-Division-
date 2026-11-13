import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_operating_framework import build_report


class OperatingFrameworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.registry = json.loads((root / "division-registry.json").read_text(encoding="utf-8"))
        cls.framework = json.loads((root / "operating-framework.json").read_text(encoding="utf-8"))

    def test_framework_covers_all_nine_divisions(self):
        report = build_report(self.registry, self.framework)
        self.assertTrue(report["validated"], report["errors"])
        self.assertEqual(report["division_count"], 9)

    def test_every_division_has_measurable_acceptance_criteria(self):
        report = build_report(self.registry, self.framework)
        self.assertTrue(all(x["acceptance_criteria_count"] > 0 for x in report["divisions"]))

    def test_owner_assignment_and_approval_boundaries_are_explicit(self):
        for division in self.framework["divisions"]:
            self.assertTrue(division["owner_assignment"])
            self.assertTrue(division["approval_boundary"])

    def test_unknown_handoff_target_is_rejected(self):
        framework = json.loads(json.dumps(self.framework))
        framework["divisions"][0]["handoffs"].append(
            {"to": "nonexistent", "artifact": "x", "trigger": "y"}
        )
        report = build_report(self.registry, framework)
        self.assertFalse(report["validated"])
        self.assertTrue(any("unknown division" in error for error in report["errors"]))

    def test_missing_acceptance_criteria_is_rejected(self):
        framework = json.loads(json.dumps(self.framework))
        framework["divisions"][0]["acceptance_criteria"] = []
        report = build_report(self.registry, framework)
        self.assertFalse(report["validated"])


if __name__ == "__main__":
    unittest.main()

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_dependency_report import build_report


class DependencyReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.registry = json.loads((root / "division-registry.json").read_text(encoding="utf-8"))
        cls.readiness = json.loads((root / "readiness-register.json").read_text(encoding="utf-8"))
        cls.dependencies = json.loads((root / "dependency-map.json").read_text(encoding="utf-8"))

    def test_map_covers_every_registered_division(self):
        report = build_report(self.registry, self.readiness, self.dependencies)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["division_count"], len(self.registry["divisions"]))

    def test_unready_required_provider_blocks_dependent(self):
        report = build_report(self.registry, self.readiness, self.dependencies)
        ai_revenue = next(x for x in report["divisions"] if x["division_id"] == "ai-revenue")
        self.assertEqual(ai_revenue["dependency_status"], "blocked")
        self.assertTrue(any("technology is building" in x for x in ai_revenue["required_blockers"]))

    def test_supporting_dependency_does_not_create_required_blocker(self):
        report = build_report(self.registry, self.readiness, self.dependencies)
        technology = next(x for x in report["divisions"] if x["division_id"] == "technology")
        self.assertFalse(any("risk is building" in x for x in technology["required_blockers"]))
        self.assertTrue(any("risk is building" in x for x in technology["supporting_gaps"]))

    def test_unknown_provider_is_rejected(self):
        dependencies = json.loads(json.dumps(self.dependencies))
        dependencies["divisions"][0]["depends_on"] = [
            {"division_id": "ghost", "type": "required", "capability": "invalid"}
        ]
        report = build_report(self.registry, self.readiness, dependencies)
        self.assertTrue(any("unknown dependency provider" in x for x in report["errors"]))


if __name__ == "__main__":
    unittest.main()

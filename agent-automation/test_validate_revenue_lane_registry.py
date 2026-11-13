import json
import unittest
from pathlib import Path
from validate_revenue_lane_registry import validate_registry, render_markdown

class RevenueLaneRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(Path("agent-automation/revenue-lane-registry.json").read_text(encoding="utf-8"))

    def test_registry_covers_all_supported_lanes_and_marks_research_gap(self):
        report, errors = validate_registry(self.registry)
        self.assertEqual(errors, [])
        self.assertTrue(report["registry_valid"])
        self.assertEqual(report["lane_count"], 9)
        self.assertEqual(report["research_gap_count"], 1)

    def test_sources_remain_unconnected_and_zero_budget(self):
        report, errors = validate_registry(self.registry)
        self.assertEqual(errors, [])
        self.assertFalse(report["external_accounts_connected"])
        self.assertEqual(report["default_budget_cad"], 0)
        self.assertTrue(all(x.get("human_review_required") for x in self.registry["sources"]))

    def test_rejects_missing_owner_approval_gate(self):
        bad = json.loads(json.dumps(self.registry))
        bad["policy"]["approval_required_for_external_actions"] = False
        _, errors = validate_registry(bad)
        self.assertTrue(any("approval" in e.lower() for e in errors))

    def test_rejects_http_source(self):
        bad = json.loads(json.dumps(self.registry))
        bad["sources"][0]["official_url"] = "http://example.com"
        _, errors = validate_registry(bad)
        self.assertTrue(any("HTTPS" in e for e in errors))

    def test_rejects_unmapped_lane_source(self):
        bad = json.loads(json.dumps(self.registry))
        bad["lanes"][0]["source_ids"] = ["unknown"]
        _, errors = validate_registry(bad)
        self.assertTrue(any("unknown source ids" in e for e in errors))

    def test_markdown_discloses_research_gap_and_no_authority(self):
        report, errors = validate_registry(self.registry)
        self.assertEqual(errors, [])
        rendered = render_markdown(report)
        self.assertIn("Research gaps", rendered)
        self.assertIn("No external action is authorized", rendered)
        self.assertIn("not presumed paid", rendered)

if __name__ == "__main__":
    unittest.main()

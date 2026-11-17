import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "market-data"))
from validate_source_registry import validate_registry

class MarketDataRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "research/market-data/source-registry.json").open(encoding="utf-8") as f:
            cls.registry = json.load(f)

    def test_current_registry_is_research_only_and_valid(self):
        report = validate_registry(self.registry)
        self.assertEqual(report["status"], "validated", report["errors"])
        self.assertEqual(report["live_approved_count"], 0)
        self.assertGreaterEqual(report["instrument_count"], 5)

    def test_duplicate_instrument_is_rejected(self):
        data = json.loads(json.dumps(self.registry))
        data["instruments"].append(data["instruments"][0])
        report = validate_registry(data)
        self.assertEqual(report["status"], "invalid")
        self.assertTrue(any("unique non-empty id" in e for e in report["errors"]))

    def test_unreviewed_source_cannot_be_marked_approved(self):
        data = json.loads(json.dumps(self.registry))
        data["instruments"][0]["candidate_sources"][0]["status"] = "approved"
        report = validate_registry(data)
        self.assertEqual(report["status"], "invalid")

    def test_missing_terms_review_fails_closed(self):
        data = json.loads(json.dumps(self.registry))
        del data["instruments"][0]["candidate_sources"][0]["terms_review"]
        report = validate_registry(data)
        self.assertEqual(report["status"], "invalid")

    def test_nonzero_default_spend_is_rejected(self):
        data = json.loads(json.dumps(self.registry))
        data["policy"]["default_spend_cad"] = 1
        report = validate_registry(data)
        self.assertEqual(report["status"], "invalid")

if __name__ == "__main__":
    unittest.main()

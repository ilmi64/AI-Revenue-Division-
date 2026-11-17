"""Offline structural regression checks for Sprint 3 market desk contracts.

These tests inspect contract structure only. They do not execute a JSON Schema
validator, verify source data, or establish market/live readiness.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


def load(name):
    with (ROOT / name).open(encoding="utf-8") as handle:
        return json.load(handle)


class MarketDeskContractTests(unittest.TestCase):
    def test_capital_flow_handoff_is_research_only_and_crypto_scoped(self):
        schema = load("capital-flow-desk-handoff.schema.json")
        self.assertEqual(schema["properties"]["source_system"]["const"], "occ_capital_flow_intelligence")
        self.assertEqual(schema["properties"]["destination_desk"]["const"], "crypto")
        self.assertEqual(schema["properties"]["mode"]["const"], "research_only")
        event = schema["properties"]["event_records"]["items"]
        self.assertFalse(event["additionalProperties"])
        self.assertNotIn("trade_instruction", event["properties"])
        self.assertNotIn("order", event["properties"])
        self.assertEqual(
            set(event["properties"]["review_status"]["enum"]),
            {"watch", "research", "unverified", "corroborated"},
        )

    def test_handoff_preserves_separate_confidence_dimensions(self):
        event = load("capital-flow-desk-handoff.schema.json")["properties"]["event_records"]["items"]
        required = set(event["required"])
        self.assertTrue({
            "source_reliability", "attribution_confidence",
            "event_confidence", "materiality", "source_ids", "evidence_refs"
        }.issubset(required))

    def test_gold_observation_requires_explicit_quality_fields(self):
        schema = load("market-observation.schema.json")
        gold_condition = next(
            item for item in schema["allOf"]
            if "gold_price_basis" in item.get("then", {}).get("required", [])
        )
        required = set(gold_condition["then"]["required"])
        self.assertTrue({
            "gold_price_basis", "gold_session", "quote_age_seconds",
            "stale_threshold_seconds", "is_stale",
            "financing_status", "settlement_type"
        }.issubset(required))

    def test_gold_basis_does_not_conflate_spot_futures_and_cfd(self):
        schema = load("market-observation.schema.json")
        basis = schema["properties"]["gold_price_basis"]["enum"]
        self.assertIn("indicative_bullion_spot", basis)
        self.assertIn("broker_executable_xauusd", basis)
        self.assertIn("comex_futures", basis)
        self.assertIn("gold_cfd", basis)

    def test_all_contracts_are_closed_objects(self):
        for name in (
            "market-observation.schema.json",
            "specialist-assessment.schema.json",
            "capital-flow-desk-handoff.schema.json",
        ):
            with self.subTest(name=name):
                self.assertFalse(load(name)["additionalProperties"])


if __name__ == "__main__":
    unittest.main()

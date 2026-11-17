"""Deterministic unit tests for the offline OCC evidence-to-desk gate."""
import unittest
from datetime import datetime, timezone

from evidence_to_desk_gate import (
    GENESIS, entry_hash, run_pipeline, validate_market_observation, verify_ledger
)


NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


def make_ledger(status="corroborated"):
    entry = {
        "sequence": 1, "previous_hash": GENESIS,
        "reviewed_at": "2026-11-17T11:00:00Z",
        "event_id": "evt-1", "action": "corroborate",
        "reviewer_id": "reviewer-a", "reason": "test evidence reviewed",
        "review_status": status, "evidence_refs": ["https://example.invalid/evidence"],
        "supersedes_entry_hash": None,
        "authority": "research_review_only_no_trade_or_execution_authority"
    }
    entry["entry_hash"] = entry_hash(entry)
    return [entry]


def make_event():
    return {
        "event_id": "evt-1", "event_type": "large_wallet_transfer",
        "observed_at_epoch": 1794912900, "ingested_at_epoch": 1794913200,
        "source_ids": ["source-a"], "evidence_refs": ["https://example.invalid/evidence"],
        "source_reliability": 4, "attribution_confidence": 4,
        "event_confidence": 4, "materiality": 3,
        "review_status": "corroborated", "direction": "unknown",
        "conflicts": [], "quality_flags": []
    }


def make_registry():
    return {"status": "research_only", "sources": [{
        "source_id": "source-a", "access_status": "verified",
        "cost_status": "free_verified", "terms_review_status": "reviewed_permitted",
        "operational_status": "approved_manual", "access_mode": "public_web"
    }]}


def make_gold():
    return {
        "instrument_id": "XAUUSD", "instrument_type": "xauusd_spot",
        "venue_or_broker": "Example Broker", "source_id": "gold-source",
        "source_timestamp_utc": "2026-11-17T11:59:58Z",
        "received_timestamp_utc": "2026-11-17T11:59:59Z",
        "data_class": "live", "licence_status": "approved",
        "bid": 4000.0, "ask": 4000.5, "currency": "USD",
        "unit_or_contract_multiplier": 1, "session_state": "open",
        "portfolio_version": 1, "quote_unit": "USD per troy ounce",
        "gold_price_basis": "broker_executable_xauusd",
        "gold_session": "London/New York overlap; UTC calendar",
        "quote_age_seconds": 2, "stale_threshold_seconds": 10,
        "is_stale": False, "financing_status": "known_financing_terms",
        "settlement_type": "derivative"
    }


class EvidenceGateTests(unittest.TestCase):
    def test_valid_hash_chain(self):
        self.assertEqual(verify_ledger(make_ledger())[0], True)

    def test_tampered_hash_chain_blocks_entire_pipeline(self):
        ledger = make_ledger()
        ledger[0]["reason"] = "tampered"
        report = run_pipeline([make_event()], ledger, make_registry(), [make_gold()],
                              NOW, 120, 5)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["capital_flow"], [])

    def test_capital_event_passes_only_with_verified_source_and_review(self):
        report = run_pipeline([make_event()], make_ledger(), make_registry(), [],
                              NOW, 120, 5)
        self.assertTrue(report["capital_flow"][0]["eligible"])

    def test_unreviewed_event_fails(self):
        report = run_pipeline([make_event()], [], make_registry(), [], NOW, 120, 5)
        self.assertFalse(report["capital_flow"][0]["eligible"])

    def test_unknown_or_paid_source_fails(self):
        registry = make_registry()
        registry["sources"][0]["cost_status"] = "unknown"
        report = run_pipeline([make_event()], make_ledger(), registry, [], NOW, 120, 5)
        self.assertFalse(report["capital_flow"][0]["eligible"])

    def test_expired_review_fails(self):
        report = run_pipeline([make_event()], make_ledger("expired"), make_registry(), [],
                              NOW, 120, 5)
        self.assertFalse(report["capital_flow"][0]["eligible"])

    def test_valid_gold_observation_passes_research_gate(self):
        result = validate_market_observation(make_gold(), NOW, 120, 5)
        self.assertTrue(result["eligible"])

    def test_stale_gold_observation_fails(self):
        obs = make_gold()
        obs["quote_age_seconds"] = 11
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertFalse(result["eligible"])

    def test_indicative_bullion_is_not_silently_broker_executable(self):
        obs = make_gold()
        obs["gold_price_basis"] = "indicative_bullion_spot"
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertTrue(result["eligible"])
        self.assertTrue(any("not broker-executable" in x for x in result["warnings"]))

    def test_crossed_market_quote_fails(self):
        obs = make_gold()
        obs["bid"], obs["ask"] = 4001, 4000
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertFalse(result["eligible"])

    def test_duplicate_event_ids_fail(self):
        event = make_event()
        report = run_pipeline([event, dict(event)], make_ledger(), make_registry(), [],
                              NOW, 120, 5)
        self.assertTrue(all(not x["eligible"] for x in report["capital_flow"]))

    def test_missing_market_source_registry_fails_closed(self):
        from evidence_to_desk_gate import run_pipeline
        report = run_pipeline([], [], {"status": "research_only", "sources": []},
                              [make_gold()], NOW, 120, 5)
        self.assertFalse(report["market_observations"][0]["eligible"])

    def test_unapproved_market_source_fails(self):
        from evidence_to_desk_gate import run_pipeline
        registry = {"instruments": [{
            "id": "XAUUSD", "candidate_sources": [{
                "name": "Example Broker", "status": "candidate_reference_only",
                "terms_review": "pending", "canada_review": "pending"
            }]
        }]}
        report = run_pipeline([], [], {"status": "research_only", "sources": []},
                              [make_gold()], NOW, 120, 5, registry)
        self.assertFalse(report["market_observations"][0]["eligible"])

    def test_unknown_market_licence_fails(self):
        obs = make_gold()
        obs["licence_status"] = "unknown"
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertFalse(result["eligible"])

    def test_empty_run_does_not_vacuously_pass(self):
        report = run_pipeline([], [], {"status": "research_only", "sources": []},
                              [], NOW, 120, 5)
        self.assertEqual(report["status"], "BLOCKED")

    def test_future_quote_timestamp_fails(self):
        obs = make_gold()
        obs["source_timestamp_utc"] = "2026-11-17T12:01:00Z"
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertFalse(result["eligible"])


if __name__ == "__main__":
    unittest.main()

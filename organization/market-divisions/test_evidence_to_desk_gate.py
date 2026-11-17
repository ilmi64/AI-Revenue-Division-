"""Deterministic unit tests for the offline OCC evidence-to-desk gate."""
import unittest
import json
from pathlib import Path
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

    def test_challenged_capital_event_fails_handoff(self):
        ledger = make_ledger()
        ledger[0]["action"] = "challenge"
        ledger[0]["entry_hash"] = entry_hash(ledger[0])
        report = run_pipeline([make_event()], ledger, make_registry(), [], NOW, 120, 5)
        self.assertFalse(report["capital_flow"][0]["eligible"])

    def test_expired_revalidation_deadline_fails(self):
        event = make_event()
        event["revalidate_by_epoch"] = NOW.timestamp() - 1
        report = run_pipeline([event], make_ledger(), make_registry(), [], NOW, 120, 5)
        self.assertFalse(report["capital_flow"][0]["eligible"])

    def test_gold_quote_age_must_match_source_timestamp(self):
        obs = make_gold()
        obs["quote_age_seconds"] = 30
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertFalse(result["eligible"])

    def test_gold_basis_requires_two_aligned_provenance_legs(self):
        obs = make_gold()
        obs["spot_futures_basis"] = 12.5
        obs["evidence_refs"] = ["spot-ref", "futures-ref"]
        obs["spot_futures_leg_source_ids"] = ["spot-provider", "futures-provider"]
        obs["spot_futures_leg_timestamps_utc"] = [
            "2026-11-17T11:59:58Z", "2026-11-17T11:59:59Z"
        ]
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertTrue(result["eligible"])
        obs["spot_futures_leg_timestamps_utc"][1] = "2026-11-17T11:59:40Z"
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertFalse(result["eligible"])

    def test_four_desk_synthetic_fixture_pack_passes_research_gate_only(self):
        root = Path(__file__).parent
        fixture_path = root / "fixtures" / "specialist-market-observations.synthetic.jsonl"
        registry_path = root / "synthetic-market-source-registry.json"
        observations = [json.loads(line) for line in fixture_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        report = run_pipeline([], [], {"status": "research_only", "sources": []},
                              observations, NOW, 120, 5, registry)
        self.assertEqual(report["status"], "PASS_RESEARCH_GATES")
        self.assertEqual(len(report["market_observations"]), 4)
        self.assertTrue(all(row["eligible"] for row in report["market_observations"]))
        self.assertEqual(report["authority"], "research_only_no_execution_authority")
        self.assertTrue(all(row["data_class"] == "synthetic" for row in observations))

    def test_crypto_identity_must_be_explicit_and_verified(self):
        from evidence_to_desk_gate import validate_market_observation
        obs = {
            "instrument_id": "SOL-USD", "instrument_type": "crypto_spot",
            "venue_or_broker": "SYNTHETIC_TEST_VENUE", "source_id": "synthetic-crypto-fixture",
            "source_timestamp_utc": "2026-11-17T11:59:58Z",
            "received_timestamp_utc": "2026-11-17T12:00:00Z", "data_class": "synthetic",
            "licence_status": "not_applicable", "bid": 99.9, "ask": 100.1,
            "currency": "USD", "unit_or_contract_multiplier": 1,
            "session_state": "open", "portfolio_version": 1,
            "base_asset": "SOL", "quote_asset": "USD", "market_pair": "SOL/USD",
            "token_identity_status": "unverified"
        }
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertFalse(result["eligible"])

    def test_fx_requires_explicit_quote_per_base_orientation(self):
        from evidence_to_desk_gate import validate_market_observation
        obs = {
            "instrument_id": "EURUSD", "instrument_type": "fx_spot",
            "venue_or_broker": "SYNTHETIC_TEST_VENUE", "source_id": "synthetic-forex-fixture",
            "source_timestamp_utc": "2026-11-17T11:59:58Z",
            "received_timestamp_utc": "2026-11-17T12:00:00Z", "data_class": "synthetic",
            "licence_status": "not_applicable", "bid": 1.08, "ask": 1.09,
            "currency": "USD", "unit_or_contract_multiplier": 1,
            "session_state": "open", "portfolio_version": 1,
            "base_currency": "EUR", "quote_currency": "USD",
            "quote_convention": "base_per_quote"
        }
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertFalse(result["eligible"])

    def test_synthetic_fixture_registry_cannot_approve_unlisted_instrument(self):
        root = Path(__file__).parent
        registry = json.loads((root / "synthetic-market-source-registry.json").read_text(encoding="utf-8"))
        obs = dict(make_gold())
        obs["instrument_id"] = "UNLISTED-XAU"
        from evidence_to_desk_gate import validate_market_source
        self.assertTrue(validate_market_source(obs, registry))

    def test_future_quote_timestamp_fails(self):
        obs = make_gold()
        obs["source_timestamp_utc"] = "2026-11-17T12:01:00Z"
        result = validate_market_observation(obs, NOW, 120, 5)
        self.assertFalse(result["eligible"])


if __name__ == "__main__":
    unittest.main()

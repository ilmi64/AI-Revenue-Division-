"""Regression tests for the offline Capital Flow -> Crypto handoff adapter."""
import unittest
from datetime import datetime, timezone

from specialist_research.capital_flow_handoff import (
    HandoffError, _entry_hash, build_handoff, verify_review_ledger,
)

NOW = "2026-11-17T12:00:00Z"
OBS = {
    "instrument_type": "crypto_spot", "base_asset": "SOL",
    "chain_id": "solana", "contract_address": "So11111111111111111111111111111111111111112",
    "token_identity_status": "verified",
}


def event(**overrides):
    value = {
        "event_id": "evt-sol-1", "event_type": "large_wallet_transfer",
        "observed_at_epoch": 1794915000, "revalidate_by_epoch": 1795000000,
        "asset_id": "SOL", "chain": "solana",
        "contract_address": OBS["contract_address"], "transaction_hash": "a" * 64,
        "direction": "inflow", "source_ids": ["source-a"],
        "evidence_refs": ["https://evidence.invalid/tx/1"],
        "source_reliability": 4, "attribution_confidence": 3,
        "event_confidence": 4, "materiality": 3, "corroboration_count": 2,
        "limitations": [], "conflicts": [], "quality_flags": [],
    }
    value.update(overrides)
    return value


def review(action="review", status="corroborated", event_id="evt-sol-1"):
    value = {
        "sequence": 1, "previous_hash": "0" * 64,
        "reviewed_at": NOW, "event_id": event_id, "action": action,
        "reviewer_id": "reviewer-1", "reason": "Reviewed source evidence",
        "review_status": status, "evidence_refs": ["https://evidence.invalid/review/1"],
        "supersedes_entry_hash": None,
        "authority": "research_review_only_no_trade_or_execution_authority",
    }
    value["entry_hash"] = _entry_hash(value)
    return value


REGISTRY = {"sources": [{
    "source_id": "source-a", "access_mode": "public",
    "access_status": "verified", "cost_status": "free",
    "terms_review_status": "approved", "operational_status": "active",
}]}


class CapitalFlowHandoffTests(unittest.TestCase):
    def build(self, events=None, reviews=None, registry=None, observation=None):
        return build_handoff(events if events is not None else [event()],
                             reviews if reviews is not None else [review()],
                             registry if registry is not None else REGISTRY,
                             observation if observation is not None else OBS, NOW)

    def test_exact_identity_and_reviewed_event_attach(self):
        result = self.build()
        self.assertEqual(len(result["event_records"]), 1)
        record = result["event_records"][0]
        self.assertEqual(record["asset_id"], "SOL")
        self.assertEqual(record["chain"], "solana")
        self.assertEqual(record["contract_address"], OBS["contract_address"])
        self.assertEqual(result["mode"], "research_only")

    def test_no_explicit_review_blocks_event(self):
        result = self.build(reviews=[])
        self.assertEqual(result["event_records"], [])

    def test_broken_hash_chain_fails_closed(self):
        bad = [review()]
        bad[0]["reason"] = "tampered"
        with self.assertRaises(HandoffError):
            self.build(reviews=bad)

    def test_challenge_blocks_latest_event(self):
        result = self.build(reviews=[review("challenge", None)])
        self.assertEqual(result["event_records"], [])

    def test_reject_and_expire_block(self):
        for action, status in (("reject", "rejected"), ("expire", "expired")):
            with self.subTest(action=action):
                self.assertEqual(self.build(reviews=[review(action, status)])["event_records"], [])

    def test_stale_event_rejected(self):
        self.assertEqual(self.build(events=[event(observed_at_epoch=1700000000)])["event_records"], [])

    def test_future_event_rejected(self):
        self.assertEqual(self.build(events=[event(observed_at_epoch=1900000000)])["event_records"], [])

    def test_expired_revalidation_rejected(self):
        self.assertEqual(self.build(events=[event(revalidate_by_epoch=1700000000)])["event_records"], [])

    def test_unverified_source_rejected(self):
        registry = {"sources": [{**REGISTRY["sources"][0], "access_status": "unverified"}]}
        self.assertEqual(self.build(registry=registry)["event_records"], [])

    def test_unknown_or_unreviewed_source_terms_rejected(self):
        registry = {"sources": [{**REGISTRY["sources"][0], "terms_review_status": "not_reviewed"}]}
        self.assertEqual(self.build(registry=registry)["event_records"], [])

    def test_wrong_chain_does_not_match(self):
        self.assertEqual(self.build(events=[event(chain="ethereum")])["event_records"], [])

    def test_wrong_contract_does_not_match(self):
        self.assertEqual(self.build(events=[event(contract_address="0x" + "1" * 40)])["event_records"], [])

    def test_ticker_match_without_verified_market_identity_rejected(self):
        obs = {**OBS, "token_identity_status": "unverified"}
        with self.assertRaises(HandoffError):
            self.build(observation=obs)

    def test_low_attribution_confidence_rejected(self):
        self.assertEqual(self.build(events=[event(attribution_confidence=1)])["event_records"], [])

    def test_missing_evidence_rejected(self):
        self.assertEqual(self.build(events=[event(evidence_refs=[])])["event_records"], [])

    def test_orphan_review_rejected(self):
        with self.assertRaises(HandoffError):
            self.build(reviews=[review(event_id="missing-event")])

    def test_duplicate_event_ids_rejected(self):
        with self.assertRaises(HandoffError):
            self.build(events=[event(), event()])

    def test_review_ledger_report_is_integrity_only(self):
        report = verify_review_ledger([review()])
        self.assertTrue(report["valid"])
        self.assertEqual(report["authority"], None) if "authority" in report else None

    def test_never_emits_trade_authority(self):
        result = self.build()
        self.assertNotIn("trade_authority", result)
        self.assertNotIn("execution_permission", result)
        self.assertEqual(result["mode"], "research_only")


if __name__ == "__main__":
    unittest.main()

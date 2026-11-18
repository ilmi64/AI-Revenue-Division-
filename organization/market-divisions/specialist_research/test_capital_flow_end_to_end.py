"""Synthetic end-to-end Capital Flow review -> Crypto handoff tests.

All inputs are synthetic and deterministic. No network, wallet, exchange,
provider API, trading or persistent user data is involved.
"""
import tempfile
import unittest
from pathlib import Path

from specialist_research.capital_flow_handoff import build_handoff, HandoffError
from specialist_research.capital_flow_review_ledger import (
    AUTHORITY, append_review, read_reviews,
)

NOW = "2026-11-17T12:00:00Z"
CONTRACT = "So11111111111111111111111111111111111111112"

def sample_event():
    return {
        "event_id": "synthetic-sol-inflow-001",
        "event_type": "large_wallet_transfer",
        "observed_at_epoch": 1794915000,
        "revalidate_by_epoch": 1795000000,
        "asset_id": "SOL",
        "chain": "solana",
        "contract_address": CONTRACT,
        "transaction_hash": "a" * 64,
        "direction": "inflow",
        "source_ids": ["synthetic-public-source"],
        "evidence_refs": ["https://synthetic.invalid/tx/001"],
        "source_reliability": 4,
        "attribution_confidence": 3,
        "event_confidence": 4,
        "materiality": 3,
        "corroboration_count": 2,
        "limitations": ["Synthetic fixture; not real-world evidence"],
        "conflicts": [],
        "quality_flags": [],
    }


def source_registry():
    return {"sources": [{
        "source_id": "synthetic-public-source",
        "access_mode": "public",
        "access_status": "verified",
        "cost_status": "free",
        "terms_review_status": "approved",
        "canada_review_status": "approved",
        "operational_status": "active",
    }]}


def observation(contract=CONTRACT):
    return {
        "instrument_type": "crypto_spot",
        "base_asset": "SOL",
        "chain_id": "solana",
        "contract_address": contract,
        "token_identity_status": "verified",
    }


def review(**changes):
    value = {
        "reviewed_at": NOW,
        "event_id": "synthetic-sol-inflow-001",
        "action": "review",
        "reviewer_id": "synthetic-test-reviewer",
        "reason": "Synthetic fixture review of cited evidence",
        "review_status": "corroborated",
        "evidence_refs": ["https://synthetic.invalid/review/001"],
        "supersedes_entry_hash": None,
        "authority": AUTHORITY,
    }
    value.update(changes)
    return value


class CapitalFlowEndToEndTests(unittest.TestCase):
    def test_writer_output_passes_independent_crypto_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "reviews.jsonl"
            append_review(ledger, review())
            result = build_handoff(
                [sample_event()], read_reviews(ledger), source_registry(),
                observation(), NOW,
            )
            self.assertEqual(len(result["event_records"]), 1)
            self.assertEqual(result["event_records"][0]["event_id"],
                             "synthetic-sol-inflow-001")
            self.assertEqual(result["destination_desk"], "crypto")
            self.assertEqual(result["mode"], "research_only")
            self.assertIs(result["trade_authority"], False)
            self.assertIs(result["live_readiness"], False)

    def test_later_challenge_blocks_previously_accepted_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "reviews.jsonl"
            first = append_review(ledger, review())
            append_review(ledger, review(
                reviewed_at="2026-11-17T12:05:00Z",
                action="challenge",
                review_status="unverified",
                reason="Synthetic test challenge; evidence requires re-check",
                supersedes_entry_hash=first["entry_hash"],
            ))
            result = build_handoff(
                [sample_event()], read_reviews(ledger), source_registry(),
                observation(), "2026-11-17T12:06:00Z",
            )
            self.assertEqual(result["event_records"], [])
            self.assertEqual(len(result["rejected_matching_events"]), 1)
            self.assertIn("challenge", result["rejected_matching_events"][0]["reason"])

    def test_rejected_source_never_crosses_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "reviews.jsonl"
            append_review(ledger, review())
            registry = source_registry()
            registry["sources"][0]["canada_review_status"] = "not_reviewed"
            result = build_handoff(
                [sample_event()], read_reviews(ledger), registry, observation(), NOW,
            )
            self.assertEqual(result["event_records"], [])
            self.assertIn("source eligibility", result["rejected_matching_events"][0]["reason"])

    def test_exact_contract_identity_is_mandatory(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "reviews.jsonl"
            append_review(ledger, review())
            result = build_handoff(
                [sample_event()], read_reviews(ledger), source_registry(),
                observation("0x" + "1" * 40), NOW,
            )
            self.assertEqual(result["event_records"], [])
            self.assertEqual(result["rejected_matching_events"], [])

    def test_tampered_review_ledger_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "reviews.jsonl"
            append_review(ledger, review())
            rows = read_reviews(ledger)
            rows[0]["reason"] = "tampered after append"
            with self.assertRaises(HandoffError):
                build_handoff([sample_event()], rows, source_registry(),
                              observation(), NOW)

    def test_missing_review_never_attaches_event(self):
        result = build_handoff([sample_event()], [], source_registry(),
                               observation(), NOW)
        self.assertEqual(result["event_records"], [])
        self.assertIn("no explicit review-ledger decision",
                      result["rejected_matching_events"][0]["reason"])


if __name__ == "__main__":
    unittest.main()

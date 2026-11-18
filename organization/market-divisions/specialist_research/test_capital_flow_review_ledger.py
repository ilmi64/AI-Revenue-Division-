"""Tests for the canonical append-only Capital Flow review journal."""
import json
import tempfile
import unittest
from pathlib import Path

from specialist_research.capital_flow_review_ledger import (
    AUTHORITY, ReviewLedgerError, append_review, read_reviews, verify_reviews,
)
from specialist_research.capital_flow_handoff import verify_review_ledger


def sample(**changes):
    value = {
        "reviewed_at": "2026-11-17T12:00:00Z",
        "event_id": "event-1",
        "action": "review",
        "reviewer_id": "reviewer-local-1",
        "reason": "Checked the cited primary evidence",
        "review_status": "research",
        "evidence_refs": ["https://evidence.invalid/item/1"],
        "supersedes_entry_hash": None,
        "authority": AUTHORITY,
    }
    value.update(changes)
    return value


class CapitalFlowReviewLedgerTests(unittest.TestCase):
    def test_append_creates_adapter_compatible_hash_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reviews.jsonl"
            entry = append_review(path, sample())
            rows = read_reviews(path)
            self.assertEqual(entry["sequence"], 1)
            self.assertTrue(verify_reviews(rows)["valid"])
            self.assertTrue(verify_review_ledger(rows)["valid"])

    def test_second_review_must_supersede_latest_event_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reviews.jsonl"
            first = append_review(path, sample())
            second = append_review(path, sample(
                action="corroborate", review_status="corroborated",
                supersedes_entry_hash=first["entry_hash"],
                reviewed_at="2026-11-17T12:05:00Z",
            ))
            self.assertEqual(second["sequence"], 2)
            self.assertTrue(verify_review_ledger(read_reviews(path))["valid"])

    def test_cannot_skip_or_falsify_supersession(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reviews.jsonl"
            append_review(path, sample())
            with self.assertRaises(ReviewLedgerError):
                append_review(path, sample(reviewed_at="2026-11-17T12:06:00Z"))

    def test_reject_requires_rejected_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ReviewLedgerError):
                append_review(Path(tmp) / "reviews.jsonl",
                              sample(action="reject", review_status="research"))

    def test_challenge_cannot_leave_event_corroborated(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ReviewLedgerError):
                append_review(Path(tmp) / "reviews.jsonl",
                              sample(action="challenge", review_status="corroborated"))

    def test_empty_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ReviewLedgerError):
                append_review(Path(tmp) / "reviews.jsonl", sample(evidence_refs=[]))

    def test_future_or_non_utc_shape_is_not_accepted_as_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ReviewLedgerError):
                append_review(Path(tmp) / "reviews.jsonl",
                              sample(reviewed_at="2026-11-17T12:00:00-05:00"))

    def test_tampered_existing_ledger_cannot_be_extended(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reviews.jsonl"
            append_review(path, sample())
            rows = read_reviews(path)
            rows[0]["reason"] = "tampered"
            path.write_text(json.dumps(rows[0]) + "\n", encoding="utf-8")
            with self.assertRaises(ReviewLedgerError):
                append_review(path, sample(
                    reviewed_at="2026-11-17T12:05:00Z",
                    supersedes_entry_hash=rows[0]["entry_hash"],
                ))

    def test_boolean_sequence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reviews.jsonl"
            entry = append_review(path, sample())
            entry["sequence"] = True
            from specialist_research.capital_flow_review_ledger import _entry_hash
            entry["entry_hash"] = _entry_hash(entry)
            self.assertFalse(verify_reviews([entry])["valid"])

    def test_no_trade_authority_or_live_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry = append_review(Path(tmp) / "reviews.jsonl", sample())
            self.assertEqual(entry["authority"], AUTHORITY)
            self.assertNotIn("trade_authority", entry)
            self.assertNotIn("live_readiness", entry)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from capital_flow_review import (
    GENESIS, LedgerError, append_entry, build_entry, load_ledger, verify_ledger
)

class ReviewLedgerTests(unittest.TestCase):
    def make_entry(self, sequence=1, previous=GENESIS, **kwargs):
        reviewed_at = kwargs.pop("reviewed_at", "2026-11-17T12:00:00Z")
        return build_entry(
            sequence=sequence, previous_hash=previous,
            event_id="cfi-event-1", action="review", reviewer_id="reviewer-1",
            reason="Checked primary evidence; identity remains unverified.",
            reviewed_at=reviewed_at, **kwargs
        )

    def test_first_entry_uses_genesis_and_verifies(self):
        entry = self.make_entry()
        report = verify_ledger([entry])
        self.assertEqual(report["status"], "valid")
        self.assertEqual(report["entry_count"], 1)

    def test_second_entry_links_to_first(self):
        first = self.make_entry()
        second = self.make_entry(sequence=2, previous=first["entry_hash"],
                                 action="corroborate", review_status="corroborated")
        self.assertEqual(verify_ledger([first, second])["status"], "valid")

    def test_tampering_is_detected(self):
        entry = self.make_entry()
        changed = dict(entry, reason="changed after the fact")
        self.assertEqual(verify_ledger([changed])["status"], "invalid")

    def test_broken_chain_is_detected(self):
        first = self.make_entry()
        second = self.make_entry(sequence=2, previous="f" * 64)
        self.assertIn("previous_hash", " ".join(verify_ledger([first, second])["errors"]))

    def test_reject_requires_rejected_status(self):
        with self.assertRaises(LedgerError):
            self.make_entry(action="reject")

    def test_reopen_requires_nonterminal_status(self):
        with self.assertRaises(LedgerError):
            self.make_entry(action="reopen", review_status="expired")

    def test_timezone_required(self):
        with self.assertRaises(LedgerError):
            self.make_entry(reviewed_at="2026-11-17T12:00:00")

    def test_append_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reviews.jsonl"
            first = self.make_entry()
            append_entry(path, first)
            loaded = load_ledger(path)
            self.assertEqual(loaded, [first])
            second = self.make_entry(sequence=2, previous=first["entry_hash"],
                                     action="reject", review_status="rejected")
            append_entry(path, second)
            self.assertEqual(len(load_ledger(path)), 2)

    def test_append_refuses_corrupt_existing_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reviews.jsonl"
            path.write_text(json.dumps({"sequence": 1}) + "\n", encoding="utf-8")
            with self.assertRaises(LedgerError):
                load_ledger(path)

if __name__ == "__main__":
    unittest.main()

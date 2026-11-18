import json
import tempfile
import unittest
from pathlib import Path

from specialist_research.snapshot_history import (
    AUTHORITY, HistoryError, append_snapshot, read_history, verify_history,
)

NOW = "2026-11-17T18:00:00Z"


def snapshot(stop=False, status="research", label="a"):
    return {
        "snapshot_type": "unified_occ_research_intelligence",
        "generated_at_utc": NOW,
        "status": "halt" if stop else status,
        "mode": "research_only",
        "active_stops": ([{"source": "crypto", "reason": "test-stop"}] if stop else []),
        "global_stop_active": stop,
        "authority": AUTHORITY,
        "trade_authority": False,
        "live_readiness": False,
        "test_label": label,
    }


class SnapshotHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "history" / "snapshots.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_history_is_valid(self):
        report = verify_history(read_history(self.path))
        self.assertTrue(report["valid"])
        self.assertEqual(report["entry_count"], 0)

    def test_appends_and_verifies_first_snapshot(self):
        record = append_snapshot(self.path, snapshot(), NOW)
        report = verify_history(read_history(self.path))
        self.assertTrue(report["valid"])
        self.assertEqual(record["sequence"], 1)
        self.assertEqual(report["entry_count"], 1)

    def test_sequence_and_previous_hash_link_multiple_snapshots(self):
        append_snapshot(self.path, snapshot(label="first"), NOW)
        second = append_snapshot(self.path, snapshot(label="second"), NOW)
        report = verify_history(read_history(self.path))
        self.assertTrue(report["valid"])
        self.assertEqual(second["sequence"], 2)
        self.assertEqual(second["previous_hash"], report["head_hash"])

    def test_snapshot_digest_detects_snapshot_mutation(self):
        append_snapshot(self.path, snapshot(), NOW)
        rows = read_history(self.path)
        rows[0]["snapshot"]["test_label"] = "tampered"
        report = verify_history(rows)
        self.assertFalse(report["valid"])
        self.assertTrue(any("snapshot digest mismatch" in e for e in report["errors"]))

    def test_record_hash_detects_metadata_mutation(self):
        append_snapshot(self.path, snapshot(), NOW)
        rows = read_history(self.path)
        rows[0]["appended_at_utc"] = "2026-11-17T18:01:00Z"
        report = verify_history(rows)
        self.assertFalse(report["valid"])
        self.assertTrue(any("record_hash mismatch" in e for e in report["errors"]))

    def test_broken_previous_hash_is_detected(self):
        append_snapshot(self.path, snapshot(label="first"), NOW)
        append_snapshot(self.path, snapshot(label="second"), NOW)
        rows = read_history(self.path)
        rows[1]["previous_hash"] = "f" * 64
        report = verify_history(rows)
        self.assertFalse(report["valid"])
        self.assertTrue(any("previous_hash chain mismatch" in e for e in report["errors"]))

    def test_duplicate_identical_snapshot_is_rejected(self):
        row = snapshot()
        append_snapshot(self.path, row, NOW)
        with self.assertRaisesRegex(HistoryError, "duplicate snapshot"):
            append_snapshot(self.path, row, NOW)

    def test_prior_global_stop_cannot_be_cleared(self):
        append_snapshot(self.path, snapshot(stop=True), NOW)
        with self.assertRaisesRegex(HistoryError, "cannot clear"):
            append_snapshot(self.path, snapshot(stop=False), NOW)

    def test_stop_persists_across_subsequent_snapshots(self):
        append_snapshot(self.path, snapshot(stop=True, label="halt-1"), NOW)
        append_snapshot(self.path, snapshot(stop=True, label="halt-2"), NOW)
        report = verify_history(read_history(self.path))
        self.assertTrue(report["valid"])
        self.assertTrue(report["global_stop_active"])

    def test_snapshot_cannot_claim_trade_authority(self):
        bad = snapshot()
        bad["trade_authority"] = True
        with self.assertRaisesRegex(HistoryError, "trade authority"):
            append_snapshot(self.path, bad, NOW)

    def test_append_time_cannot_precede_snapshot_generation(self):
        with self.assertRaisesRegex(HistoryError, "cannot precede"):
            append_snapshot(self.path, snapshot(), "2026-11-17T17:59:59Z")

    def test_invalid_ledger_json_line_is_rejected(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text('{"sequence":1}\nnot-json\n', encoding="utf-8")
        with self.assertRaisesRegex(HistoryError, "invalid JSON"):
            read_history(self.path)

    def test_invalid_existing_chain_blocks_append(self):
        append_snapshot(self.path, snapshot(), NOW)
        rows = read_history(self.path)
        rows[0]["record_hash"] = "0" * 64
        self.path.write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(HistoryError, "existing history is invalid"):
            append_snapshot(self.path, snapshot(label="later"), NOW)


if __name__ == "__main__":
    unittest.main()

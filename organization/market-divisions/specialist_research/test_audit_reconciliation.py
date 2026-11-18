import tempfile
import unittest
from pathlib import Path

from specialist_research.snapshot_history import AUTHORITY, append_snapshot, read_history
from specialist_research.incident_event_ledger import append_event, read_events
from specialist_research.audit_reconciliation import reconcile

NOW = "2026-11-17T20:00:00Z"


def snapshot(stop=False, stop_id="stop-1"):
    stops = ([{"stop_id": stop_id, "source": "crypto", "reason": "synthetic"}]
             if stop else [])
    return {
        "snapshot_type": "unified_occ_research_intelligence",
        "generated_at_utc": NOW,
        "status": "halt" if stop else "research",
        "mode": "research_only",
        "active_stops": stops,
        "global_stop_active": stop,
        "authority": AUTHORITY,
        "trade_authority": False,
        "live_readiness": False,
    }


def event(event_id, kind, stop_id=None):
    details = {"stop_id": stop_id} if stop_id else {}
    refs = ["synthetic:evidence"] if kind == "stop_raised" else []
    return {
        "event_id": event_id, "event_type": kind,
        "occurred_at_utc": NOW, "recorded_at_utc": NOW,
        "actor_id": "synthetic-test", "subject_id": stop_id or "incident-1",
        "summary": "Synthetic audit fixture", "evidence_refs": refs,
        "details": details,
    }


class AuditReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.snap_path = root / "snapshots.jsonl"
        self.event_path = root / "events.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def add_snapshot(self, stop=False, stop_id="stop-1", label=""):
        value = snapshot(stop, stop_id)
        value["fixture_label"] = label
        append_snapshot(self.snap_path, value, NOW)

    def add_stop(self, stop_id="stop-1"):
        append_event(self.event_path, event("event-" + stop_id, "stop_raised", stop_id))

    def audit(self):
        return reconcile(read_history(self.snap_path), read_events(self.event_path))

    def test_matching_clear_histories_consistent(self):
        self.add_snapshot()
        result = self.audit()
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "consistent")

    def test_matching_active_stop_and_event_consistent(self):
        self.add_stop()
        self.add_snapshot(stop=True)
        result = self.audit()
        self.assertTrue(result["valid"])

    def test_snapshot_active_stop_without_event_is_inconsistent(self):
        self.add_snapshot(stop=True)
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("no matching stop_raised event" in x for x in result["errors"]))

    def test_event_stop_missing_from_snapshot_is_inconsistent(self):
        self.add_stop()
        self.add_snapshot(stop=False)
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("stop-state mismatch" in x for x in result["errors"]))

    def test_stop_id_mismatch_is_inconsistent(self):
        self.add_stop("stop-A")
        self.add_snapshot(stop=True, stop_id="stop-B")
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("no matching stop_raised event" in x for x in result["errors"]))

    def test_raised_stop_without_id_warns_but_never_clears_stop(self):
        append_event(self.event_path, event("event-no-id", "stop_raised"))
        self.add_snapshot(stop=True)
        result = self.audit()
        self.assertTrue(result["valid"])
        self.assertTrue(result["event_history"]["global_stop_active"])
        self.assertTrue(result["warnings"])

    def test_corrupt_snapshot_history_blocks_semantic_reconciliation(self):
        self.add_snapshot()
        rows = read_history(self.snap_path)
        rows[0]["snapshot"]["status"] = "tampered"
        self.snap_path.write_text(
            "".join(__import__("json").dumps(x) + "\n" for x in rows), encoding="utf-8")
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("snapshot history integrity failed" in x for x in result["errors"]))

    def test_corrupt_event_ledger_blocks_semantic_reconciliation(self):
        self.add_stop()
        self.add_snapshot(stop=True)
        rows = read_events(self.event_path)
        rows[0]["event"]["summary"] = "tampered"
        self.event_path.write_text(
            "".join(__import__("json").dumps(x) + "\n" for x in rows), encoding="utf-8")
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("event ledger integrity failed" in x for x in result["errors"]))

    def test_empty_snapshot_history_is_not_consistent(self):
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("no snapshot" in x for x in result["errors"]))

    def test_audit_cannot_claim_execution_authority(self):
        self.add_snapshot()
        result = self.audit()
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertEqual(result["authority"], "research_only_no_execution_authority")


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from specialist_research.control_health import build_control_health
from specialist_research.snapshot_history import AUTHORITY, append_snapshot
from specialist_research.incident_event_ledger import append_event

NOW = "2026-11-17T22:00:00Z"


def base_snapshot():
    return {
        "snapshot_type": "unified_occ_research_intelligence",
        "generated_at_utc": NOW, "status": "research", "mode": "research_only",
        "active_stops": [], "global_stop_active": False,
        "authority": AUTHORITY, "trade_authority": False, "live_readiness": False,
        "occ": {"status": "research", "trade_authority": False, "live_readiness": False},
    }


def handover_event():
    return {
        "event_id": "handover-1", "event_type": "handover_recorded",
        "occurred_at_utc": NOW, "recorded_at_utc": NOW,
        "actor_id": "outgoing-shift", "subject_id": "shift-transition-1",
        "summary": "Synthetic day/night handover",
        "evidence_refs": ["fixture:handover-evidence"],
        "details": {
            "handover_id": "handover-1", "outgoing_shift_id": "day",
            "incoming_shift_id": "night", "snapshot_id": "fixture-snapshot",
            "portfolio_version": 1, "outgoing_acknowledged": True,
            "incoming_acknowledged": True, "positions_reconciled": True,
            "dependency_health": "healthy", "active_veto_ids": [],
            "unresolved_critical_items": [],
        },
    }


class ControlHealthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.snapshots = root / "snapshots.jsonl"
        self.events = root / "events.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def seed_snapshot(self):
        append_snapshot(self.snapshots, base_snapshot(), NOW)

    def integrate(self):
        return build_control_health(base_snapshot(), self.snapshots, self.events)

    def test_missing_snapshot_history_fails_closed(self):
        result = self.integrate()
        self.assertEqual(result["control_health"]["status"], "HALT_AUDIT")
        self.assertEqual(result["status"], "halt")
        self.assertEqual(result["control_health"]["snapshot_history_integrity"], "invalid_or_missing")

    def test_valid_ledgers_without_handover_do_not_claim_acceptance(self):
        self.seed_snapshot()
        result = self.integrate()
        self.assertEqual(result["control_health"]["handover_acceptance"], "not_provided")
        self.assertEqual(result["control_health"]["status"], "HALT_AUDIT")

    def test_complete_handover_and_matching_ledgers_pass(self):
        self.seed_snapshot()
        append_event(self.events, handover_event())
        result = self.integrate()
        self.assertEqual(result["control_health"]["status"], "PASS_AUDIT")
        self.assertEqual(result["control_health"]["handover_acceptance"], "accepted")
        self.assertEqual(result["status"], "research")

    def test_corrupt_event_ledger_halts_without_fabricating_stop(self):
        self.seed_snapshot()
        append_event(self.events, handover_event())
        rows = [json.loads(x) for x in self.events.read_text().splitlines()]
        rows[0]["event"]["summary"] = "tampered"
        self.events.write_text("".join(json.dumps(x) + "\n" for x in rows))
        result = self.integrate()
        self.assertEqual(result["control_health"]["status"], "HALT_AUDIT")
        self.assertFalse(result["global_stop_active"])
        self.assertEqual(result["active_stops"], [])

    def test_existing_stop_is_reported_and_never_removed(self):
        snap = base_snapshot()
        snap["status"] = "halt"
        snap["global_stop_active"] = True
        snap["active_stops"] = [{"stop_id": "stop-A", "source": "crypto"}]
        append_snapshot(self.snapshots, snap, NOW)
        stop = {
            "event_id": "stop-A-event", "event_type": "stop_raised",
            "occurred_at_utc": NOW, "recorded_at_utc": NOW,
            "actor_id": "risk", "subject_id": "SOL-USDC",
            "summary": "Synthetic stop", "evidence_refs": ["fixture:stop"],
            "details": {"stop_id": "stop-A"},
        }
        append_event(self.events, stop)
        hand = handover_event()
        hand["details"]["active_veto_ids"] = ["stop-A"]
        append_event(self.events, hand)
        result = self.integrate()
        self.assertIn("stop-A", result["control_health"]["active_stop_ids"])
        self.assertTrue(result["global_stop_active"])
        self.assertEqual(result["active_stops"], snap["active_stops"])

    def test_input_snapshot_is_not_mutated(self):
        self.seed_snapshot()
        source = base_snapshot()
        before = json.dumps(source, sort_keys=True)
        build_control_health(source, self.snapshots, self.events)
        self.assertEqual(json.dumps(source, sort_keys=True), before)

    def test_authority_cannot_be_granted(self):
        source = base_snapshot()
        source["trade_authority"] = True
        with self.assertRaises(ValueError):
            build_control_health(source, self.snapshots, self.events)


if __name__ == "__main__":
    unittest.main()

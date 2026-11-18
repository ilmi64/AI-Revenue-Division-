import tempfile
import unittest
from pathlib import Path

from specialist_research.incident_event_ledger import append_event, read_events
from specialist_research.handover_reconciliation import audit_handovers

NOW = "2026-11-17T21:00:00Z"


def event(event_id, kind="handover_recorded", details=None, subject=None, refs=None):
    return {
        "event_id": event_id, "event_type": kind,
        "occurred_at_utc": NOW, "recorded_at_utc": NOW,
        "actor_id": "synthetic-reviewer", "subject_id": subject or event_id,
        "summary": "Synthetic handover test", "evidence_refs": refs if refs is not None else ["evidence:handover"],
        "details": details or {},
    }


def handover(hid="h-1", outgoing="day-1", incoming="night-1"):
    return {
        "handover_id": hid, "outgoing_shift_id": outgoing,
        "incoming_shift_id": incoming, "snapshot_id": "occ-snapshot-1",
        "portfolio_version": 7, "outgoing_acknowledged": True,
        "incoming_acknowledged": True, "positions_reconciled": True,
        "dependency_health": "healthy", "active_veto_ids": [],
        "unresolved_critical_items": [],
    }


class HandoverReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "events.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def append(self, value):
        append_event(self.path, value)

    def audit(self):
        return audit_handovers(read_events(self.path))

    def test_empty_ledger_cannot_imply_handover_acceptance(self):
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["handover_count"], 0)
        self.assertFalse(result["trade_authority"])

    def test_complete_handover_is_accepted(self):
        self.append(event("evt-h1", details=handover()))
        result = self.audit()
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "accepted")

    def test_missing_acknowledgement_blocks_handover(self):
        data = handover()
        data["incoming_acknowledged"] = False
        self.append(event("evt-h1", details=data))
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("incoming_acknowledged" in x for x in result["errors"]))

    def test_unreconciled_positions_block_handover(self):
        data = handover()
        data["positions_reconciled"] = False
        self.append(event("evt-h1", details=data))
        self.assertFalse(self.audit()["valid"])

    def test_unhealthy_dependencies_block_handover(self):
        data = handover()
        data["dependency_health"] = "degraded"
        self.append(event("evt-h1", details=data))
        self.assertFalse(self.audit()["valid"])

    def test_unresolved_critical_items_block_handover(self):
        data = handover()
        data["unresolved_critical_items"] = ["unreconciled critical exposure"]
        self.append(event("evt-h1", details=data))
        self.assertFalse(self.audit()["valid"])

    def test_active_veto_is_carried_forward_and_reported(self):
        data = handover()
        data["active_veto_ids"] = ["veto-gold-1"]
        self.append(event("evt-h1", details=data))
        result = self.audit()
        self.assertTrue(result["valid"])
        self.assertTrue(any("veto-gold-1" in x for x in result["warnings"]))

    def test_duplicate_handover_id_is_detected(self):
        self.append(event("evt-h1", details=handover("same")))
        self.append(event("evt-h2", details=handover("same", "night-1", "day-2")))
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("duplicate handover_id" in x for x in result["errors"]))

    def test_duplicate_shift_transition_is_detected(self):
        self.append(event("evt-h1", details=handover("h-1")))
        self.append(event("evt-h2", details=handover("h-2")))
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("duplicate handover transition" in x for x in result["errors"]))

    def test_shift_chain_discontinuity_is_reported(self):
        self.append(event("evt-h1", details=handover("h-1", "day-1", "night-1")))
        self.append(event("evt-h2", details=handover("h-2", "day-2", "night-2")))
        result = self.audit()
        self.assertTrue(result["valid"])
        self.assertTrue(any("continuity gap" in x for x in result["warnings"]))

    def test_shift_chain_uses_occurrence_time_when_events_are_backfilled(self):
        later = event("evt-h2", details=handover("h-2", "night-1", "day-2"))
        later["occurred_at_utc"] = "2026-11-18T21:00:00Z"
        later["recorded_at_utc"] = "2026-11-18T21:00:00Z"
        earlier = event("evt-h1", details=handover("h-1", "day-1", "night-1"))
        self.append(later)
        self.append(earlier)
        result = self.audit()
        self.assertTrue(result["valid"], result["errors"])
        self.assertFalse(any("continuity gap" in x for x in result["warnings"]))
        self.assertEqual(result["handover_ids"], ["h-1", "h-2"])

    def test_missing_evidence_blocks_handover(self):
        self.append(event("evt-h1", details=handover(), refs=[]))
        result = self.audit()
        self.assertFalse(result["valid"])

    def test_open_incident_is_visible_at_handover(self):
        self.append(event("evt-open", "incident_opened", {"incident_type": "test"}, "inc-1", []))
        self.append(event("evt-h1", details=handover()))
        result = self.audit()
        self.assertEqual(result["open_incidents"], ["inc-1"])

    def test_stop_remains_latched_after_handover(self):
        self.append(event("evt-stop", "stop_raised", {"stop_id": "gold-stop"}, "gold-stop"))
        data = handover()
        data["active_veto_ids"] = ["gold-stop"]
        self.append(event("evt-h1", details=data))
        result = self.audit()
        self.assertTrue(result["global_stop_active"])

    def test_invalid_event_ledger_blocks_handover_audit(self):
        self.append(event("evt-h1", details=handover()))
        rows = read_events(self.path)
        rows[0]["event"]["summary"] = "tampered"
        import json
        self.path.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertFalse(result["ledger_integrity_valid"])


    def test_handover_cannot_drop_previously_raised_stop_id(self):
        self.append(event("evt-stop", "stop_raised", {"stop_id": "gold-stop"}, "gold-stop"))
        self.append(event("evt-h1", details=handover()))
        result = self.audit()
        self.assertFalse(result["valid"])
        self.assertTrue(any("not carried forward" in x for x in result["errors"]))

    def test_future_stop_does_not_retroactively_block_earlier_handover(self):
        self.append(event("evt-h1", details=handover()))
        future_stop = event(
            "evt-future-stop", "stop_raised",
            {"stop_id": "future-gold-stop"}, "future-gold-stop"
        )
        future_stop["occurred_at_utc"] = "2026-11-18T21:00:00Z"
        future_stop["recorded_at_utc"] = "2026-11-18T21:00:00Z"
        self.append(future_stop)
        result = self.audit()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["status"], "accepted")
        self.assertTrue(result["global_stop_active"])


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from specialist_research.incident_event_ledger import (
    AUTHORITY, EventLedgerError, append_event, read_events, verify_events,
)

NOW = "2026-11-17T19:00:00Z"


def event(event_id, event_type="incident_opened", subject="incident-1",
          refs=None, details=None):
    return {
        "event_id": event_id, "event_type": event_type,
        "occurred_at_utc": NOW, "recorded_at_utc": NOW,
        "actor_id": "operator-reviewer", "subject_id": subject,
        "summary": "Synthetic test event",
        "evidence_refs": refs if refs is not None else [],
        "details": details if details is not None else {},
    }


class IncidentEventLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "occ" / "events.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_ledger_is_valid(self):
        self.assertTrue(verify_events(read_events(self.path))["valid"])

    def test_appends_and_verifies_event(self):
        append_event(self.path, event("evt-1"))
        report = verify_events(read_events(self.path))
        self.assertTrue(report["valid"])
        self.assertEqual(report["entry_count"], 1)

    def test_sequence_and_hash_chain_across_events(self):
        append_event(self.path, event("evt-1"))
        second = append_event(self.path, event("evt-2", subject="incident-2"))
        self.assertEqual(second["sequence"], 2)
        self.assertTrue(verify_events(read_events(self.path))["valid"])

    def test_duplicate_event_id_rejected(self):
        append_event(self.path, event("evt-1"))
        with self.assertRaisesRegex(EventLedgerError, "duplicate event_id"):
            append_event(self.path, event("evt-1", subject="other"))

    def test_stop_raise_latches_global_stop(self):
        append_event(self.path, event("evt-stop", "stop_raised",
                                      refs=["evidence:stop"]))
        report = verify_events(read_events(self.path))
        self.assertTrue(report["global_stop_active"])

    def test_challenge_does_not_clear_stop(self):
        append_event(self.path, event("evt-stop", "stop_raised",
                                      refs=["evidence:stop"]))
        append_event(self.path, event("evt-challenge", "stop_challenged",
                                      refs=["evidence:challenge"]))
        self.assertTrue(verify_events(read_events(self.path))["global_stop_active"])

    def test_corrective_action_does_not_clear_stop(self):
        append_event(self.path, event("evt-stop", "stop_raised",
                                      refs=["evidence:stop"]))
        append_event(self.path, event("evt-fix", "corrective_action_verified",
                                      refs=["evidence:fix"]))
        self.assertTrue(verify_events(read_events(self.path))["global_stop_active"])

    def test_recovery_evidence_does_not_clear_stop(self):
        append_event(self.path, event("evt-stop", "stop_raised",
                                      refs=["evidence:stop"]))
        append_event(self.path, event("evt-recovery", "recovery_evidence_added",
                                      refs=["evidence:recovery"]))
        self.assertTrue(verify_events(read_events(self.path))["global_stop_active"])

    def test_stop_clearance_request_is_evidence_only_and_pending(self):
        append_event(self.path, event("evt-stop", "stop_raised",
                                      refs=["evidence:stop"]))
        append_event(self.path, event(
            "evt-request", "stop_clearance_requested",
            refs=["evidence:clearance-review"], details={"approval_status": "pending"}))
        self.assertTrue(verify_events(read_events(self.path))["global_stop_active"])

    def test_stop_clearance_request_cannot_be_marked_approved(self):
        with self.assertRaisesRegex(EventLedgerError, "pending or rejected"):
            append_event(self.path, event(
                "evt-request", "stop_clearance_requested",
                refs=["evidence:clearance"], details={"approval_status": "approved"}))

    def test_stop_events_require_evidence(self):
        with self.assertRaisesRegex(EventLedgerError, "requires evidence_refs"):
            append_event(self.path, event("evt-stop", "stop_raised"))

    def test_duplicate_evidence_refs_rejected(self):
        with self.assertRaisesRegex(EventLedgerError, "must be unique"):
            append_event(self.path, event("evt-stop", "stop_raised",
                                          refs=["same", "same"]))

    def test_future_recording_timestamp_restriction(self):
        bad = event("evt-1")
        bad["recorded_at_utc"] = "2026-11-17T18:59:59Z"
        with self.assertRaisesRegex(EventLedgerError, "cannot precede"):
            append_event(self.path, bad)

    def test_event_mutation_detected(self):
        append_event(self.path, event("evt-1"))
        rows = read_events(self.path)
        rows[0]["event"]["summary"] = "tampered"
        report = verify_events(rows)
        self.assertFalse(report["valid"])
        self.assertTrue(any("event digest mismatch" in x for x in report["errors"]))

    def test_entry_mutation_detected(self):
        append_event(self.path, event("evt-1"))
        rows = read_events(self.path)
        rows[0]["sequence"] = 8
        report = verify_events(rows)
        self.assertFalse(report["valid"])
        self.assertTrue(any("entry_hash mismatch" in x for x in report["errors"]))

    def test_incident_open_close_projection_is_separate_from_stop_state(self):
        append_event(self.path, event("evt-open", "incident_opened"))
        append_event(self.path, event("evt-stop", "stop_raised",
                                      refs=["evidence:stop"]))
        append_event(self.path, event("evt-close", "incident_closed"))
        report = verify_events(read_events(self.path))
        self.assertEqual(report["open_incidents"], [])
        self.assertTrue(report["global_stop_active"])

    def test_authority_cannot_be_escalated_in_details(self):
        with self.assertRaisesRegex(EventLedgerError, "cannot grant trade authority"):
            append_event(self.path, event("evt-1", details={"trade_authority": True}))

    def test_invalid_existing_chain_blocks_append(self):
        append_event(self.path, event("evt-1"))
        rows = read_events(self.path)
        rows[0]["entry_hash"] = "0" * 64
        self.path.write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(EventLedgerError, "existing event ledger invalid"):
            append_event(self.path, event("evt-2"))


if __name__ == "__main__":
    unittest.main()

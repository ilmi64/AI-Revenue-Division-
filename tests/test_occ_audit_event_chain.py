"""Tests for deterministic OCC hash-linked audit events."""
import copy
import unittest

from occ.audit_event_chain import (
    AuditChainError,
    append_audit_event,
    verify_audit_chain,
)

IDENTITY = {
    "market_class": "METALS", "product_type": "SPOT", "venue": "ExampleVenue",
    "symbol": "XAUUSD", "quote_currency": "USD", "contract_unit": "troy_ounce",
    "settlement_method": "CASH", "custody_model": "UNKNOWN",
    "financing_model": "UNKNOWN",
}


class AuditEventChainTests(unittest.TestCase):
    def test_append_and_verify_multiple_events(self):
        first = append_audit_event(
            [], event_type="FEED_CONFLICT_DETECTED", occurred_at_epoch=100,
            instrument_identity=IDENTITY, details={"spread_bps": 42.5},
        )
        second = append_audit_event(
            first, event_type="QUARANTINE_ENTERED", occurred_at_epoch=101,
            instrument_identity=IDENTITY, details={"reason_code": "SOURCE_CONFLICT"},
        )
        report = verify_audit_chain(second)
        self.assertTrue(report["valid"])
        self.assertEqual(report["event_count"], 2)
        self.assertEqual(second[1]["previous_hash"], second[0]["event_hash"])
        self.assertFalse(report["chain_authenticated"])
        self.assertFalse(report["tamper_resistant"])

    def test_append_does_not_mutate_prior_sequence(self):
        original = append_audit_event(
            [], event_type="FEED_CONFLICT_DETECTED", occurred_at_epoch=100,
            instrument_identity=IDENTITY, details={},
        )
        snapshot = copy.deepcopy(original)
        append_audit_event(
            original, event_type="RECOVERY_REVIEW_REQUIRED", occurred_at_epoch=101,
            instrument_identity=IDENTITY, details={},
        )
        self.assertEqual(original, snapshot)

    def test_modified_details_fail_hash_verification(self):
        events = append_audit_event(
            [], event_type="FEED_CONFLICT_DETECTED", occurred_at_epoch=100,
            instrument_identity=IDENTITY, details={"spread_bps": 42.5},
        )
        events[0]["details"]["spread_bps"] = 1.0
        with self.assertRaises(AuditChainError):
            verify_audit_chain(events)

    def test_reordered_or_removed_event_fails_chain(self):
        events = []
        for kind, stamp in [
            ("FEED_CONFLICT_DETECTED", 100),
            ("QUARANTINE_ENTERED", 101),
        ]:
            events = append_audit_event(
                events, event_type=kind, occurred_at_epoch=stamp,
                instrument_identity=IDENTITY, details={},
            )
        with self.assertRaises(AuditChainError):
            verify_audit_chain(events[1:])

    def test_rejects_untrusted_flags_becoming_true(self):
        events = append_audit_event(
            [], event_type="RELEASE_CLAIM_RECORDED", occurred_at_epoch=100,
            instrument_identity=IDENTITY, details={"decision_claim": "APPROVE_RELEASE"},
        )
        events[0]["execution_eligible"] = True
        with self.assertRaises(AuditChainError):
            verify_audit_chain(events)

    def test_rejects_non_finite_timestamp(self):
        with self.assertRaises(AuditChainError):
            append_audit_event(
                [], event_type="FEED_CONFLICT_DETECTED", occurred_at_epoch=float("nan"),
                instrument_identity=IDENTITY, details={},
            )

    def test_rejects_unsupported_event_type(self):
        with self.assertRaises(AuditChainError):
            append_audit_event(
                [], event_type="CLEAR_QUARANTINE", occurred_at_epoch=100,
                instrument_identity=IDENTITY, details={},
            )


if __name__ == "__main__":
    unittest.main()

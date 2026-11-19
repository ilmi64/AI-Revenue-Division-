"""Tests for the OCC independent-feed agreement diagnostic."""
import unittest

from occ.independent_feed_agreement import (
    FeedAgreementError,
    analyze_independent_feed_agreement,
)


IDENTITY = {
    "market_class": "CRYPTO", "product_type": "SPOT", "venue": "ExampleVenue",
    "symbol": "BTCUSDT", "base_currency": "BTC", "quote_currency": "USDT",
    "contract_unit": "BTC", "settlement_method": "TOKEN_DELIVERY",
    "custody_model": "UNKNOWN", "financing_model": "UNKNOWN",
}
NOW = 1_800_000_000


def registry(source, adapter, group, state="APPROVED_FOR_PAPER"):
    item = {
        "source_id": source, "adapter_id": adapter, "venue": "ExampleVenue",
        "endpoint": "https://example.invalid/feed", "transport": "HTTPS",
        "parser_version": "1", "independence_group": group,
        "instrument_identity": IDENTITY, "review_state": state,
    }
    if state == "APPROVED_FOR_PAPER":
        item.update({"reviewer_id": "reviewer", "review_evidence_ref": "evidence",
                     "reviewed_at_epoch": NOW - 10})
    return item


def quote(source, adapter, event, bid, ask):
    return {
        "source_id": source, "adapter_id": adapter, "provider_id": source,
        "event_id": event, "venue": "ExampleVenue", "sequence": 1,
        "instrument_identity": IDENTITY, "bid": bid, "ask": ask,
        "observed_at_epoch": NOW - 2, "received_at_epoch": NOW - 1,
    }


class FeedAgreementTests(unittest.TestCase):
    def run_analysis(self, observations, registry_entries, **kwargs):
        return analyze_independent_feed_agreement(
            IDENTITY, observations, registry_entries, now_epoch=NOW, **kwargs
        )

    def test_close_quotes_are_only_unverified_diagnostic_agreement(self):
        result = self.run_analysis(
            [quote("s1", "a1", "e1", 100.0, 100.1),
             quote("s2", "a2", "e2", 100.1, 100.2)],
            [registry("s1", "a1", "g1"), registry("s2", "a2", "g2")],
        )
        self.assertEqual(result["status"], "AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED")
        self.assertFalse(result["consensus_authorized"])
        self.assertFalse(result["market_data_trusted"])
        self.assertFalse(result["execution_eligible"])

    def test_wide_spread_is_conflict(self):
        result = self.run_analysis(
            [quote("s1", "a1", "e1", 100.0, 100.1),
             quote("s2", "a2", "e2", 101.0, 101.1)],
            [registry("s1", "a1", "g1"), registry("s2", "a2", "g2")],
        )
        self.assertEqual(result["status"], "CONFLICT_DETECTED")

    def test_same_declared_group_is_not_independent_consensus(self):
        result = self.run_analysis(
            [quote("s1", "a1", "e1", 100.0, 100.1),
             quote("s2", "a2", "e2", 100.0, 100.1)],
            [registry("s1", "a1", "shared"), registry("s2", "a2", "shared")],
        )
        self.assertEqual(result["status"], "DECLARED_GROUPS_NOT_INDEPENDENTLY_VERIFIED")

    def test_unapproved_registry_entry_is_rejected(self):
        result = self.run_analysis(
            [quote("s1", "a1", "e1", 100.0, 100.1),
             quote("s2", "a2", "e2", 100.0, 100.1)],
            [registry("s1", "a1", "g1", "UNREVIEWED"),
             registry("s2", "a2", "g2")],
        )
        self.assertEqual(result["status"], "INPUTS_REJECTED")

    def test_duplicate_source_and_event_are_rejected(self):
        observations = [
            quote("s1", "a1", "same", 100.0, 100.1),
            quote("s1", "a1", "same", 100.0, 100.1),
            quote("s2", "a2", "e2", 100.0, 100.1),
        ]
        result = self.run_analysis(
            observations, [registry("s1", "a1", "g1"), registry("s2", "a2", "g2")]
        )
        self.assertEqual(result["status"], "INPUTS_REJECTED")
        self.assertTrue(any("duplicate event_id" in issue for issue in result["issues"]))

    def test_identity_mismatch_is_rejected(self):
        wrong = quote("s2", "a2", "e2", 100.0, 100.1)
        wrong["instrument_identity"] = {**IDENTITY, "quote_currency": "USD"}
        result = self.run_analysis(
            [quote("s1", "a1", "e1", 100.0, 100.1), wrong],
            [registry("s1", "a1", "g1"), registry("s2", "a2", "g2")],
        )
        self.assertEqual(result["status"], "INPUTS_REJECTED")

    def test_invalid_threshold_rejected(self):
        with self.assertRaises(FeedAgreementError):
            self.run_analysis([], [], max_spread_bps=float("nan"))

    def test_missing_sources_fail_closed(self):
        result = self.run_analysis([], [])
        self.assertEqual(result["status"], "INSUFFICIENT_SOURCES")
        self.assertIsNone(result["diagnostic_midpoint_median"])
        self.assertFalse(result["paper_use_authorized"])


if __name__ == "__main__":
    unittest.main()

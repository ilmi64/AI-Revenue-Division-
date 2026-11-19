"""Tests for OCC market-data quarantine and recovery review transitions."""
import unittest

from occ.market_data_quarantine import (
    QuarantineStateError,
    transition_market_data_quarantine,
)


IDENTITY = {
    "market_class": "METALS", "product_type": "SPOT", "venue": "ExampleVenue",
    "symbol": "XAUUSD", "quote_currency": "USD", "contract_unit": "troy_ounce",
    "settlement_method": "CASH", "custody_model": "UNKNOWN",
    "financing_model": "UNKNOWN",
}


def report(status, sources=("feed-a", "feed-b"), spread=40.0, threshold=25.0):
    return {
        "status": status,
        "expected_instrument_identity": IDENTITY,
        "accepted_observations": [{"source_id": source} for source in sources],
        "diagnostic_spread_bps": spread,
        "max_spread_bps": threshold,
        "independence_verified": False,
        "provider_identity_authenticated": False,
        "registry_authority_authenticated": False,
        "market_data_trusted": False,
        "consensus_authorized": False,
        "paper_use_authorized": False,
        "execution_eligible": False,
    }


class MarketDataQuarantineTests(unittest.TestCase):
    def test_conflict_enters_quarantine(self):
        result = transition_market_data_quarantine(
            report("CONFLICT_DETECTED"), now_epoch=1000
        )
        self.assertEqual(result["state"], "QUARANTINED")
        self.assertTrue(result["quarantine_active"])
        self.assertEqual(result["conflict_count"], 1)
        self.assertFalse(result["release_authorized"])

    def test_repeated_conflict_preserves_original_quarantine_time(self):
        first = transition_market_data_quarantine(
            report("CONFLICT_DETECTED"), now_epoch=1000
        )
        second = transition_market_data_quarantine(
            report("CONFLICT_DETECTED", spread=50), now_epoch=1010,
            prior_state=first,
        )
        self.assertEqual(second["quarantined_at_epoch"], 1000)
        self.assertEqual(second["conflict_count"], 2)

    def test_agreement_only_moves_to_review_required(self):
        prior = transition_market_data_quarantine(
            report("CONFLICT_DETECTED"), now_epoch=1000
        )
        result = transition_market_data_quarantine(
            report("AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED", spread=2),
            now_epoch=1010, prior_state=prior,
        )
        self.assertEqual(result["state"], "RECOVERY_REVIEW_REQUIRED")
        self.assertTrue(result["quarantine_active"])
        self.assertFalse(result["automatic_recovery_performed"])
        self.assertFalse(result["release_authorized"])

    def test_review_claim_does_not_release_quarantine(self):
        prior = transition_market_data_quarantine(
            report("CONFLICT_DETECTED"), now_epoch=1000
        )
        result = transition_market_data_quarantine(
            report("AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED", spread=2),
            now_epoch=1010, prior_state=prior,
            recovery_review_claim={
                "decision": "APPROVE_RELEASE", "reviewer_id": "operator",
                "evidence_ref": "case-123", "reviewed_at_epoch": 1009,
            },
        )
        self.assertEqual(result["state"], "RECOVERY_REVIEW_REQUIRED")
        self.assertFalse(result["recovery_review"]["review_claim_authenticated"])
        self.assertFalse(result["release_authorized"])

    def test_mismatched_prior_identity_rejected(self):
        prior = transition_market_data_quarantine(
            report("CONFLICT_DETECTED"), now_epoch=1000
        )
        changed = dict(IDENTITY, quote_currency="CAD")
        prior["instrument_identity"] = changed
        with self.assertRaises(QuarantineStateError):
            transition_market_data_quarantine(
                report("AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED", spread=2),
                now_epoch=1010, prior_state=prior,
            )

    def test_bad_conflict_threshold_rejected(self):
        with self.assertRaises(QuarantineStateError):
            transition_market_data_quarantine(
                report("CONFLICT_DETECTED", spread=20, threshold=25),
                now_epoch=1000,
            )

    def test_unverified_inputs_keep_source_quarantined(self):
        prior = transition_market_data_quarantine(
            report("CONFLICT_DETECTED"), now_epoch=1000
        )
        result = transition_market_data_quarantine(
            report("INPUTS_REJECTED", sources=()), now_epoch=1010,
            prior_state=prior,
        )
        self.assertEqual(result["state"], "QUARANTINED")
        self.assertTrue(result["quarantine_active"])


if __name__ == "__main__":
    unittest.main()

"""Synthetic tests for offline venue intelligence evidence intake."""
import unittest

from specialist_research.venue_intelligence import (
    assess_evidence_bundle, build_research_intake_report, prepare_profile_draft,
)


def bundle(**overrides):
    required = {
        "crypto_perpetual": {
            "contract_multiplier": 1, "quote_currency": "USD",
            "settlement_currency": "USD", "initial_margin_rate": 0.1,
            "maintenance_tiers": [{"notional_cap": None, "maintenance_rate": 0.05}],
            "mark_price_rule": "mark", "liquidation_fee_rate": 0.01,
            "funding_convention": "signed_cashflow_to_position",
            "funding_interval": "8h", "partial_liquidation_policy": "full_only",
            "liquidation_fee_basis": "notional",
        }
    }["crypto_perpetual"]
    source = {
        "source_id": "official-1", "source_uri": "https://example.invalid/spec",
        "source_class": "official_contract_specification",
        "publisher": "Synthetic Venue", "published_at_utc": "2026-01-01T00:00:00Z",
        "captured_at_utc": "2026-01-02T00:00:00Z", "content_sha256": "a" * 64,
    }
    facts = [{
        "fact_key": key, "value": value, "source_id": "official-1",
        "observed_at_utc": "2026-01-02T00:00:00Z",
    } for key, value in required.items()]
    value = {
        "venue_id": "synthetic", "instrument_id": "BTC-PERP",
        "instrument_type": "crypto_perpetual", "sources": [source], "facts": facts,
    }
    value.update(overrides)
    return value


class VenueIntelligenceTests(unittest.TestCase):
    def test_complete_bundle_remains_unverified(self):
        result = assess_evidence_bundle(bundle(), "2026-01-03T00:00:00Z")
        self.assertEqual(result["status"], "EVIDENCE_COVERAGE_COMPLETE_UNVERIFIED")
        self.assertEqual(result["missing_fact_keys"], [])
        self.assertFalse(result["source_independence_verified"])
        self.assertFalse(result["trade_authority"])

    def test_missing_critical_fact_blocks_coverage(self):
        item = bundle()
        item["facts"] = [f for f in item["facts"] if f["fact_key"] != "initial_margin_rate"]
        result = assess_evidence_bundle(item, "2026-01-03T00:00:00Z")
        self.assertEqual(result["status"], "INCOMPLETE_EVIDENCE_COVERAGE")
        self.assertIn("initial_margin_rate", result["critical_missing_fact_keys"])

    def test_conflicting_values_block(self):
        item = bundle()
        duplicate = dict(item["facts"][0])
        duplicate["value"] = 99
        item["facts"].append(duplicate)
        result = assess_evidence_bundle(item, "2026-01-03T00:00:00Z")
        self.assertEqual(result["status"], "BLOCKED_CONFLICTING_EVIDENCE")

    def test_unknown_source_reference_invalidates_bundle(self):
        item = bundle()
        item["facts"][0]["source_id"] = "unknown"
        result = assess_evidence_bundle(item, "2026-01-03T00:00:00Z")
        self.assertEqual(result["status"], "INVALID_EVIDENCE_BUNDLE")

    def test_future_observation_invalidates_bundle(self):
        item = bundle()
        item["facts"][0]["observed_at_utc"] = "2027-01-01T00:00:00Z"
        result = assess_evidence_bundle(item, "2026-01-03T00:00:00Z")
        self.assertEqual(result["status"], "INVALID_EVIDENCE_BUNDLE")

    def test_bad_source_digest_invalidates_bundle(self):
        item = bundle()
        item["sources"][0]["content_sha256"] = "not-a-hash"
        result = assess_evidence_bundle(item, "2026-01-03T00:00:00Z")
        self.assertEqual(result["status"], "INVALID_EVIDENCE_BUNDLE")

    def test_complete_bundle_creates_unapproved_draft(self):
        result = prepare_profile_draft(bundle(), "2026-01-03T00:00:00Z")
        self.assertEqual(result["status"], "PROFILE_DRAFT_PREPARED_NOT_APPROVED")
        draft = result["profile_draft"]
        self.assertEqual(draft["profile_state"], "under_review")
        self.assertEqual(draft["verification_state"], "unverified")
        self.assertEqual(draft["review_state"], "pending")
        self.assertFalse(result["profile_approval_performed"])

    def test_conflict_prevents_profile_draft(self):
        item = bundle()
        item["facts"].append(dict(item["facts"][0], value="conflict"))
        result = prepare_profile_draft(item, "2026-01-03T00:00:00Z")
        self.assertEqual(result["status"], "BLOCKED_PROFILE_DRAFT")
        self.assertIsNone(result["profile_draft"])

    def test_unsupported_asset_type_is_blocked(self):
        item = bundle(instrument_type="crypto_spot")
        result = assess_evidence_bundle(item, "2026-01-03T00:00:00Z")
        self.assertEqual(result["status"], "INVALID_EVIDENCE_BUNDLE")

    def test_intake_report_keeps_venue_records_separate(self):
        result = build_research_intake_report(
            [bundle(), bundle(instrument_id="ETH-PERP")], "2026-01-03T00:00:00Z"
        )
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["status_counts"]["EVIDENCE_COVERAGE_COMPLETE_UNVERIFIED"], 2)
        self.assertFalse(result["live_readiness"])


if __name__ == "__main__":
    unittest.main()

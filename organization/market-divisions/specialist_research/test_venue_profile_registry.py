"""Synthetic tests for the venue profile registry."""
import unittest

from specialist_research.venue_profile_registry import (
    append_profile_revision, resolve_profile, validate_registry,
)


def record(revision=1, effective_from="2026-01-01T00:00:00Z", **overrides):
    value = {
        "profile_id": "synthetic-btc-perp-r1",
        "revision": revision,
        "venue_id": "synthetic-venue",
        "instrument_id": "BTC-PERP",
        "instrument_type": "crypto_perpetual",
        "effective_from_utc": effective_from,
        "effective_to_utc": None,
        "profile_state": "approved",
        "verification_state": "source_checked",
        "review_state": "accepted",
        "reviewer_id": "reviewer-1",
        "reviewed_at_utc": "2026-01-02T00:00:00Z",
        "venue_spec": {
            "schema_version": "1.0.0", "venue_id": "synthetic-venue",
            "instrument_type": "crypto_perpetual", "quote_currency": "USD",
            "mark_price_rule": "mark", "contract_multiplier": 1.0,
            "initial_margin_rate": 0.2, "liquidation_fee_rate": 0.01,
            "max_impact_bps": 100.0, "impact_coefficient": 10.0,
            "liquidation_buffer_ratio": 1.2, "partial_liquidation_supported": False,
            "maintenance_tiers": [{"notional_cap": None, "maintenance_rate": 0.1}],
        },
        "contract_profile": {
            "schema_version": "1.0.0", "profile_id": "synthetic-btc-perp",
            "venue_id": "synthetic-venue", "instrument_id": "BTC-PERP",
            "instrument_type": "crypto_perpetual", "quote_currency": "USD",
            "settlement_currency": "USD", "settlement_method": "not_applicable",
            "roll_method": "not_applicable", "financing_convention": "funding_rate",
        },
        "provenance": [{
            "source_id": "venue-docs", "source_uri": "https://example.invalid/venue/spec",
            "source_type": "official_documentation",
            "captured_at_utc": "2026-01-01T00:00:00Z",
            "evidence_sha256": "a" * 64,
        }],
    }
    value.update(overrides)
    return value


def registry(*records):
    return {"schema_version": "1.0.0", "profiles": list(records)}


class VenueProfileRegistryTests(unittest.TestCase):
    def test_approved_reviewed_profile_is_research_eligible_only(self):
        result = resolve_profile(
            registry(record()), "synthetic-venue", "BTC-PERP", "2026-02-01T00:00:00Z"
        )
        self.assertEqual(result["status"], "RESEARCH_ELIGIBLE_REVIEWED_PROFILE")
        self.assertTrue(result["research_eligible"])
        self.assertFalse(result["operational_readiness"])
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])

    def test_unverified_profile_is_blocked(self):
        item = record(profile_state="unverified", verification_state="unverified",
                      review_state="not_reviewed")
        result = resolve_profile(
            registry(item), "synthetic-venue", "BTC-PERP", "2026-02-01T00:00:00Z"
        )
        self.assertEqual(result["status"], "BLOCKED_UNREVIEWED_PROFILE")
        self.assertIsNone(result["profile"])

    def test_approved_unverified_profile_fails_validation(self):
        item = record(verification_state="unverified")
        self.assertTrue(any("cannot have unverified" in e for e in validate_registry(registry(item))))

    def test_effective_date_bounds(self):
        item = record(effective_to_utc="2026-01-15T00:00:00Z")
        before = resolve_profile(registry(item), "synthetic-venue", "BTC-PERP", "2025-12-31T00:00:00Z")
        after = resolve_profile(registry(item), "synthetic-venue", "BTC-PERP", "2026-01-15T00:00:00Z")
        self.assertEqual(before["status"], "NO_EFFECTIVE_PROFILE")
        self.assertEqual(after["status"], "NO_EFFECTIVE_PROFILE")

    def test_append_revision_closes_previous_interval(self):
        first = record()
        base = registry(first)
        second = record(
            revision=2, effective_from="2026-02-01T00:00:00Z",
            profile_id="synthetic-btc-perp-r2",
            reviewed_at_utc="2026-02-01T00:00:00Z",
        )
        result = append_profile_revision(base, second)
        self.assertEqual(result["status"], "APPENDED_IN_MEMORY")
        self.assertEqual(result["registry"]["profiles"][0]["effective_to_utc"],
                         "2026-02-01T00:00:00Z")
        selected = resolve_profile(
            result["registry"], "synthetic-venue", "BTC-PERP", "2026-02-02T00:00:00Z"
        )
        self.assertEqual(selected["selected_revision"], 2)
        self.assertFalse(result["persistence_performed"])

    def test_revision_gap_is_rejected(self):
        result = append_profile_revision(registry(record()), record(revision=3,
            effective_from="2026-02-01T00:00:00Z"))
        self.assertEqual(result["status"], "BLOCKED_REVISION_SEQUENCE")

    def test_source_digest_and_duplicate_reference_are_validated(self):
        item = record()
        item["provenance"].append(dict(item["provenance"][0]))
        errors = validate_registry(registry(item))
        self.assertTrue(any("duplicated" in e for e in errors))

    def test_venue_contract_identity_mismatch_is_rejected(self):
        item = record()
        item["contract_profile"]["venue_id"] = "other"
        self.assertTrue(any("must match registry record" in e
                            for e in validate_registry(registry(item))))

    def test_rejected_profile_is_not_resolved_for_research(self):
        item = record(profile_state="rejected", review_state="rejected")
        result = resolve_profile(
            registry(item), "synthetic-venue", "BTC-PERP", "2026-02-01T00:00:00Z"
        )
        self.assertEqual(result["status"], "BLOCKED_PROFILE_STATE")

    def test_unknown_profile_returns_no_effective_record(self):
        result = resolve_profile(
            registry(record()), "another-venue", "BTC-PERP", "2026-02-01T00:00:00Z"
        )
        self.assertEqual(result["status"], "NO_EFFECTIVE_PROFILE")


if __name__ == "__main__":
    unittest.main()

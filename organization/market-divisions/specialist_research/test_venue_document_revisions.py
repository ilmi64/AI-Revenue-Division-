"""Synthetic tests for venue document revision tracking."""
import unittest

from specialist_research.venue_document_revisions import (
    assess_document_freshness, assess_profile_revision_impact, build_revision_review_queue,
    capture_document_revision, compare_document_revisions,
)


def revision(captured, text="margin 10%", facts=None, document_id="oanda-gold"):
    result = capture_document_revision({
        "document_id": document_id,
        "canonical_uri": "https://example.invalid/gold-spec",
        "title": "Gold contract terms",
        "publisher": "Synthetic Publisher",
        "source_class": "official_contract_specification",
        "captured_at_utc": captured,
        "published_at_utc": None,
        "extraction_method": "manual_researcher_entry",
        "document_text": text,
        "extracted_facts": facts if facts is not None else [
            {"fact_key": "initial_margin_rate", "value": 0.10, "unit": "ratio"},
            {"fact_key": "contract_multiplier", "value": 100, "unit": "troy_oz"},
        ],
    })
    if result["status"] != "REVISION_CAPTURED_UNAUTHENTICATED":
        raise AssertionError(result)
    return result["revision"]


class VenueDocumentRevisionTests(unittest.TestCase):
    def test_same_extracted_facts_and_same_content_are_no_change(self):
        old = revision("2026-01-01T00:00:00Z")
        new = revision("2026-01-02T00:00:00Z")
        result = compare_document_revisions(old, new)
        self.assertEqual(result["status"], "NO_CHANGE")
        self.assertFalse(result["human_review_required"])

    def test_margin_change_is_critical_and_requires_review(self):
        old = revision("2026-01-01T00:00:00Z")
        new = revision("2026-01-02T00:00:00Z", text="margin 12%", facts=[
            {"fact_key": "initial_margin_rate", "value": 0.12, "unit": "ratio"},
            {"fact_key": "contract_multiplier", "value": 100, "unit": "troy_oz"},
        ])
        result = compare_document_revisions(old, new)
        self.assertEqual(result["status"], "REVISION_CHANGED_REVIEW_REQUIRED")
        self.assertEqual(result["critical_changed_fact_keys"], ["initial_margin_rate"])
        self.assertFalse(result["profile_update_performed"])

    def test_added_and_removed_fields_are_reported(self):
        old = revision("2026-01-01T00:00:00Z")
        new = revision("2026-01-02T00:00:00Z", text="revised", facts=[
            {"fact_key": "contract_multiplier", "value": 100, "unit": "troy_oz"},
            {"fact_key": "settlement_method", "value": "cash"},
        ])
        result = compare_document_revisions(old, new)
        changes = {item["fact_key"]: item["change_type"] for item in result["changes"]}
        self.assertEqual(changes["initial_margin_rate"], "REMOVED")
        self.assertEqual(changes["settlement_method"], "ADDED")

    def test_conflicting_extractions_are_not_resolved(self):
        old = revision("2026-01-01T00:00:00Z")
        new = revision("2026-01-02T00:00:00Z", text="conflicting extraction", facts=[
            {"fact_key": "initial_margin_rate", "value": 0.10},
            {"fact_key": "initial_margin_rate", "value": 0.15},
        ])
        result = compare_document_revisions(old, new)
        self.assertEqual(
            next(x for x in result["changes"] if x["fact_key"] == "initial_margin_rate")["change_type"],
            "CONFLICTED",
        )

    def test_content_change_without_fact_change_still_requires_review(self):
        old = revision("2026-01-01T00:00:00Z")
        new = revision("2026-01-02T00:00:00Z", text="new wording, same extraction")
        result = compare_document_revisions(old, new)
        self.assertTrue(result["content_changed"])
        self.assertEqual(result["changes"], [])
        self.assertTrue(result["human_review_required"])

    def test_tampered_content_digest_is_rejected(self):
        old = revision("2026-01-01T00:00:00Z")
        new = revision("2026-01-02T00:00:00Z")
        new["content_sha256"] = "0" * 64
        result = compare_document_revisions(old, new)
        self.assertEqual(result["status"], "INVALID_REVISION_COMPARISON")

    def test_non_increasing_capture_time_is_rejected(self):
        old = revision("2026-01-02T00:00:00Z")
        new = revision("2026-01-01T00:00:00Z")
        result = compare_document_revisions(old, new)
        self.assertEqual(result["status"], "INVALID_REVISION_COMPARISON")

    def test_profile_becomes_stale_when_source_revision_changes(self):
        old = revision("2026-01-01T00:00:00Z")
        latest = revision("2026-01-02T00:00:00Z", text="new terms")
        result = assess_profile_revision_impact(
            {"source_revision_ids": [{"document_id": "oanda-gold", "revision_id": old["revision_id"]}]}, [latest]
        )
        self.assertEqual(result["status"], "STALE_REVIEW_REQUIRED")
        self.assertEqual(result["stale_document_ids"], ["oanda-gold"])
        self.assertFalse(result["profile_update_performed"])

    def test_profile_is_current_when_linked_to_latest_revision(self):
        latest = revision("2026-01-02T00:00:00Z")
        result = assess_profile_revision_impact(
            {"source_revision_ids": [{"document_id": "oanda-gold", "revision_id": latest["revision_id"]}]}, [latest]
        )
        self.assertEqual(result["status"], "CURRENT_SOURCE_REVISIONS")

    def test_untracked_or_duplicate_latest_revisions_fail_closed(self):
        latest = revision("2026-01-02T00:00:00Z")
        duplicate = dict(latest)
        result = assess_profile_revision_impact(
            {"source_revision_ids": [{"document_id": "oanda-gold", "revision_id": latest["revision_id"]}]}, [latest, duplicate]
        )
        self.assertEqual(result["status"], "INVALID_PROFILE_REVISION_INPUT")

    def test_new_untracked_document_requires_profile_review(self):
        linked = revision("2026-01-01T00:00:00Z")
        extra = revision(
            "2026-01-02T00:00:00Z", text="new exchange circular",
            document_id="new-margin-circular",
        )
        result = assess_profile_revision_impact(
            {"source_revision_ids": [{
                "document_id": "oanda-gold", "revision_id": linked["revision_id"]
            }]}, [linked, extra]
        )
        self.assertEqual(result["status"], "STALE_REVIEW_REQUIRED")
        self.assertIn("new-margin-circular", result["untracked_latest_document_ids"])

    def test_profile_source_missing_from_latest_capture_is_stale(self):
        old = revision("2026-01-01T00:00:00Z")
        result = assess_profile_revision_impact(
            {"source_revision_ids": [{
                "document_id": "oanda-gold", "revision_id": old["revision_id"]
            }]}, []
        )
        self.assertEqual(result["status"], "STALE_REVIEW_REQUIRED")
        self.assertIn("oanda-gold", result["missing_latest_document_ids"])

    def test_source_locator_only_change_does_not_change_fact_value(self):
        old = revision("2026-01-01T00:00:00Z", facts=[
            {"fact_key": "contract_multiplier", "value": 100, "unit": "troy_oz", "source_locator": "page 2"},
        ])
        new = revision("2026-01-02T00:00:00Z", text="same term, new page layout", facts=[
            {"fact_key": "contract_multiplier", "value": 100, "unit": "troy_oz", "source_locator": "page 4"},
        ])
        result = compare_document_revisions(old, new)
        self.assertEqual(result["changes"], [])
        self.assertTrue(result["content_changed"])
        self.assertTrue(result["human_review_required"])

    def test_review_queue_prioritizes_critical_contract_changes(self):
        old = revision("2026-01-01T00:00:00Z")
        critical = revision("2026-01-02T00:00:00Z", text="margin changed", facts=[
            {"fact_key": "initial_margin_rate", "value": 0.15, "unit": "ratio"},
        ])
        standard = revision("2026-01-02T00:00:00Z", text="description changed", facts=[
            {"fact_key": "marketing_description", "value": "new wording"},
        ])
        queue = build_revision_review_queue([
            compare_document_revisions(old, standard),
            compare_document_revisions(old, critical),
        ])
        self.assertEqual(queue["status"], "REVIEW_REQUIRED")
        self.assertEqual(queue["items"][0]["priority"], "CRITICAL")
        self.assertEqual(queue["critical_item_count"], 1)
        self.assertFalse(queue["profile_update_performed"])

    def test_review_queue_includes_stale_profile_sources(self):
        old = revision("2026-01-01T00:00:00Z")
        latest = revision("2026-01-02T00:00:00Z", text="new terms")
        impact = assess_profile_revision_impact(
            {"source_revision_ids": [{"document_id": "oanda-gold", "revision_id": old["revision_id"]}]},
            [latest],
        )
        queue = build_revision_review_queue([], [impact])
        self.assertEqual(queue["status"], "REVIEW_REQUIRED")
        self.assertEqual(queue["items"][0]["review_type"], "PROFILE_SOURCE_FRESHNESS")
        self.assertEqual(queue["items"][0]["document_id"], "oanda-gold")

    def test_invalid_comparison_blocks_review_queue(self):
        queue = build_revision_review_queue([{"status": "INVALID_REVISION_COMPARISON"}])
        self.assertEqual(queue["status"], "INVALID_REVIEW_QUEUE_INPUT")
        self.assertEqual(queue["items"], [])
        self.assertTrue(queue["human_review_required"])

    def test_empty_review_queue_has_no_approval_authority(self):
        queue = build_revision_review_queue([])
        self.assertEqual(queue["status"], "NO_REVIEW_ITEMS")
        self.assertFalse(queue["human_review_required"])
        self.assertFalse(queue["trade_authority"])
        self.assertFalse(queue["live_readiness"])

    def test_explicit_freshness_policy_flags_stale_capture(self):
        captured = revision("2026-01-01T00:00:00Z")
        result = assess_document_freshness(
            [captured], "2026-01-03T00:00:00Z",
            [{"document_id": "oanda-gold", "max_age_days": 1}],
        )
        self.assertEqual(result["status"], "STALE_EVIDENCE_REVIEW_REQUIRED")
        self.assertEqual(result["stale_document_ids"], ["oanda-gold"])

    def test_missing_ttl_is_not_assumed_fresh_or_stale(self):
        captured = revision("2026-01-01T00:00:00Z")
        result = assess_document_freshness([captured], "2026-01-30T00:00:00Z", [])
        self.assertEqual(result["status"], "NOT_ASSESSED_NO_TTL")
        self.assertEqual(result["unassessed_document_ids"], ["oanda-gold"])
        self.assertFalse(result["human_review_required"])

    def test_future_capture_and_invalid_ttl_fail_closed(self):
        captured = revision("2026-01-02T00:00:00Z")
        future = assess_document_freshness([captured], "2026-01-01T00:00:00Z", [])
        self.assertEqual(future["status"], "INVALID_FRESHNESS_INPUT")
        invalid_ttl = assess_document_freshness(
            [revision("2026-01-01T00:00:00Z")], "2026-01-02T00:00:00Z",
            [{"document_id": "oanda-gold", "max_age_days": True}],
        )
        self.assertEqual(invalid_ttl["status"], "INVALID_FRESHNESS_INPUT")

    def test_stale_capture_enters_review_queue_as_critical(self):
        captured = revision("2026-01-01T00:00:00Z")
        freshness = assess_document_freshness(
            [captured], "2026-01-03T00:00:00Z",
            [{"document_id": "oanda-gold", "max_age_days": 1}],
        )
        queue = build_revision_review_queue([], freshness_reports=[freshness])
        self.assertEqual(queue["status"], "REVIEW_REQUIRED")
        self.assertEqual(queue["items"][0]["review_type"], "DOCUMENT_CAPTURE_FRESHNESS")
        self.assertEqual(queue["items"][0]["priority"], "CRITICAL")

    def test_authority_never_upgraded(self):
        old = revision("2026-01-01T00:00:00Z")
        new = revision("2026-01-02T00:00:00Z", text="new terms")
        result = compare_document_revisions(old, new)
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertFalse(result["profile_approval_performed"])


if __name__ == "__main__":
    unittest.main()

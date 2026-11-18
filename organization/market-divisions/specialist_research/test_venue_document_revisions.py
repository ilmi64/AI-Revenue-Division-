"""Synthetic tests for venue document revision tracking."""
import unittest

from specialist_research.venue_document_revisions import (
    assess_profile_revision_impact, capture_document_revision,
    compare_document_revisions,
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
            {"source_revision_ids": [old["revision_id"]]}, [latest]
        )
        self.assertEqual(result["status"], "STALE_REVIEW_REQUIRED")
        self.assertEqual(result["stale_document_ids"], ["oanda-gold"])
        self.assertFalse(result["profile_update_performed"])

    def test_profile_is_current_when_linked_to_latest_revision(self):
        latest = revision("2026-01-02T00:00:00Z")
        result = assess_profile_revision_impact(
            {"source_revision_ids": [latest["revision_id"]]}, [latest]
        )
        self.assertEqual(result["status"], "CURRENT_SOURCE_REVISIONS")

    def test_untracked_or_duplicate_latest_revisions_fail_closed(self):
        latest = revision("2026-01-02T00:00:00Z")
        duplicate = dict(latest)
        result = assess_profile_revision_impact(
            {"source_revision_ids": [latest["revision_id"]]}, [latest, duplicate]
        )
        self.assertEqual(result["status"], "INVALID_PROFILE_REVISION_INPUT")

    def test_authority_never_upgraded(self):
        old = revision("2026-01-01T00:00:00Z")
        new = revision("2026-01-02T00:00:00Z", text="new terms")
        result = compare_document_revisions(old, new)
        self.assertFalse(result["trade_authority"])
        self.assertFalse(result["live_readiness"])
        self.assertFalse(result["profile_approval_performed"])


if __name__ == "__main__":
    unittest.main()

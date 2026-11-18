"""Tests for the partial official venue-document capture manifest."""
import json
from pathlib import Path
import unittest

from specialist_research.venue_document_capture import (
    build_capture_report, validate_capture_manifest,
)
from specialist_research.venue_document_revisions import validate_revision


MANIFEST_PATH = Path(__file__).with_name("venue_document_capture_manifest.json")


class VenueDocumentCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_validates(self):
        self.assertEqual(validate_capture_manifest(self.manifest), [])

    def test_all_nine_excerpt_digests_match_captured_text(self):
        self.assertEqual(len(self.manifest["captures"]), 9)
        for capture in self.manifest["captures"]:
            self.assertEqual(validate_revision(capture), [])

    def test_all_seven_catalogue_candidates_have_document_links(self):
        coverage = self.manifest["candidate_coverage"]
        self.assertEqual(len(coverage), 7)
        self.assertEqual(
            {item["candidate_id"] for item in coverage},
            {
                "kraken_mtf_crypto_linear_derivatives",
                "coinbase_intx_crypto_perpetuals",
                "oanda_canada_fx_cfd",
                "oanda_canada_index_cfd",
                "oanda_canada_gold_cfd",
                "cme_comex_gold_futures",
                "cme_equity_index_futures",
            },
        )

    def test_report_discloses_partial_capture_and_no_profile_eligibility(self):
        report = build_capture_report(self.manifest)
        self.assertEqual(report["status"], "PARTIAL_EVIDENCE_CAPTURE_VALID")
        self.assertEqual(report["document_count"], 9)
        self.assertEqual(report["candidate_count"], 7)
        self.assertFalse(report["full_document_capture"])
        self.assertTrue(all(not item["profile_eligible"] for item in report["documents"]))
        self.assertFalse(report["trade_authority"])
        self.assertFalse(report["live_readiness"])

    def test_tampered_excerpt_digest_fails_closed(self):
        altered = json.loads(json.dumps(self.manifest))
        altered["captures"][0]["content_sha256"] = "0" * 64
        self.assertTrue(validate_capture_manifest(altered))

    def test_full_document_claim_is_rejected(self):
        altered = json.loads(json.dumps(self.manifest))
        altered["captures"][0]["full_document_capture"] = True
        self.assertTrue(validate_capture_manifest(altered))

    def test_missing_candidate_coverage_is_rejected(self):
        altered = json.loads(json.dumps(self.manifest))
        altered["candidate_coverage"].pop()
        self.assertTrue(validate_capture_manifest(altered))

    def test_candidate_document_link_mismatch_is_rejected(self):
        altered = json.loads(json.dumps(self.manifest))
        altered["candidate_coverage"][0]["candidate_id"] = "cme_comex_gold_futures"
        self.assertTrue(validate_capture_manifest(altered))

    def test_capture_timestamp_precision_must_be_consistent(self):
        altered = json.loads(json.dumps(self.manifest))
        altered["captures"][0]["captured_at_utc"] = "2026-11-17T12:30:00Z"
        self.assertTrue(validate_capture_manifest(altered))

    def test_unknown_capture_scope_is_rejected(self):
        altered = json.loads(json.dumps(self.manifest))
        altered["captures"][0]["capture_scope"] = "full_document"
        self.assertTrue(validate_capture_manifest(altered))


if __name__ == "__main__":
    unittest.main()

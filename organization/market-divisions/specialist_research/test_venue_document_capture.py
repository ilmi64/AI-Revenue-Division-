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

    def test_all_seventeen_excerpt_digests_match_captured_text(self):
        self.assertEqual(len(self.manifest["captures"]), 17)
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
        self.assertEqual(report["document_count"], 17)
        self.assertEqual(report["candidate_count"], 7)
        self.assertFalse(report["full_document_capture"])
        self.assertTrue(all(not item["profile_eligible"] for item in report["documents"]))
        self.assertFalse(report["trade_authority"])
        self.assertFalse(report["live_readiness"])

    def test_gold_cfd_evidence_covers_hours_closeout_and_account_eligibility(self):
        captures = {item["document_id"]: item for item in self.manifest["captures"]}
        expected = {
            "oanda_xauusd_instrument_page",
            "oanda_canada_trading_hours_and_gap_risk",
            "oanda_canada_margin_closeout",
            "oanda_canada_cfd_account_eligibility",
        }
        self.assertTrue(expected.issubset(captures))
        self.assertEqual(captures["oanda_canada_trading_hours_and_gap_risk"]["extracted_facts"][1]["value"], "Sunday-Friday 18:05-16:59")
        self.assertTrue(any(f["fact_key"] == "margin_closeout_policy" for f in captures["oanda_canada_margin_closeout"]["extracted_facts"]))

    def test_account_level_margin_rule_excerpts_capture_threshold_and_scope(self):
        captures = {item["document_id"]: item for item in self.manifest["captures"]}
        rules = captures["oanda_canada_margin_rules_faq"]
        facts = {item["fact_key"]: item["value"] for item in rules["extracted_facts"]}
        self.assertEqual(facts["daily_margin_check_time"], "15:45")
        self.assertEqual(facts["time_based_closeout_days"], 6)
        self.assertEqual(facts["closeout_scope"], "all open positions")
        account = captures["oanda_canada_subaccount_closeout_differences"]
        self.assertTrue(any(item["fact_key"] == "unrelated_pending_orders" for item in account["extracted_facts"]))

    def test_oanda_v20_order_api_evidence_captures_linkage_and_fill_semantics(self):
        captures = {item["document_id"]: item for item in self.manifest["captures"]}
        orders = captures["oanda_v20_order_definition"]
        facts = {item["fact_key"]: item["value"] for item in orders["extracted_facts"]}
        self.assertEqual(facts["dependent_order_link"], "tradeID")
        self.assertIn("REDUCE_FIRST", facts["reduce_first_semantics"])
        self.assertIn("REDUCE_ONLY", facts["reduce_only_semantics"])
        endpoint = captures["oanda_v20_account_pending_orders_endpoint"]
        self.assertTrue(any(item["fact_key"] == "pending_orders_endpoint" for item in endpoint["extracted_facts"]))

    def test_gold_cfd_capture_does_not_claim_physical_ownership(self):
        item = next(x for x in self.manifest["captures"] if x["document_id"] == "oanda_xauusd_instrument_page")
        self.assertIn({"fact_key": "physical_ownership", "value": False, "unit": "ownership_right"}, item["extracted_facts"])

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

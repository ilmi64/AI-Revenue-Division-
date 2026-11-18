"""Synthetic tests for the candidate venue research catalogue."""
import json
from pathlib import Path
import unittest

from specialist_research.venue_catalogue import build_catalogue_report, validate_catalogue


CATALOGUE_PATH = Path(__file__).with_name("venue_research_catalogue.json")


class VenueCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))

    def test_seed_catalogue_validates(self):
        self.assertEqual(validate_catalogue(self.catalogue), [])

    def test_catalogue_covers_all_four_divisions(self):
        report = build_catalogue_report(self.catalogue)
        self.assertEqual(set(report["division_coverage"]), {"crypto", "forex", "indices", "gold"})

    def test_sources_are_candidates_not_captured_documents(self):
        report = build_catalogue_report(self.catalogue)
        self.assertTrue(all(
            candidate["status"] == "DOCUMENTATION_LOCATED_NOT_CAPTURED"
            for candidate in report["candidates"]
        ))
        self.assertEqual(report["source_authentication"], "NOT_PERFORMED")

    def test_no_candidate_is_profile_eligible(self):
        report = build_catalogue_report(self.catalogue)
        self.assertTrue(all(not item["profile_eligible"] for item in report["candidates"]))

    def test_duplicate_candidate_id_rejected(self):
        item = json.loads(json.dumps(self.catalogue))
        item["candidates"].append(item["candidates"][0])
        self.assertTrue(any("duplicated" in error for error in validate_catalogue(item)))

    def test_non_https_source_rejected(self):
        item = json.loads(json.dumps(self.catalogue))
        item["candidates"][0]["sources"][0]["source_uri"] = "http://example.com"
        self.assertTrue(any("HTTPS" in error for error in validate_catalogue(item)))

    def test_falsely_marked_capture_rejected(self):
        item = json.loads(json.dumps(self.catalogue))
        item["candidates"][0]["sources"][0]["full_document_capture"] = True
        self.assertTrue(any("full_document_capture" in error for error in validate_catalogue(item)))

    def test_jurisdiction_must_remain_unverified(self):
        item = json.loads(json.dumps(self.catalogue))
        item["jurisdiction"]["eligibility_status"] = "APPROVED"
        self.assertTrue(any("eligibility" in error for error in validate_catalogue(item)))

    def test_kraken_canadian_derivatives_restriction_is_enforced(self):
        report = build_catalogue_report(self.catalogue)
        item = next(x for x in report["candidates"] if x["candidate_id"] == "kraken_mtf_crypto_linear_derivatives")
        self.assertEqual(item["canadian_shortlist_status"], "EXCLUDE_CANADIAN_DERIVATIVES")
        altered = json.loads(json.dumps(self.catalogue))
        altered["candidates"][0]["jurisdiction_status"] = "UNVERIFIED_FOR_CANADA_ON"
        self.assertTrue(any("Kraken's published Canadian derivatives restriction" in e for e in validate_catalogue(altered)))

    def test_coinbase_intx_is_institutional_only_and_unconfirmed(self):
        report = build_catalogue_report(self.catalogue)
        item = next(x for x in report["candidates"] if x["candidate_id"] == "coinbase_intx_crypto_perpetuals")
        self.assertEqual(item["canadian_shortlist_status"], "INSTITUTIONAL_JURISDICTION_UNCONFIRMED")
        altered = json.loads(json.dumps(self.catalogue))
        altered["candidates"][1]["jurisdiction_status"] = "APPROVED_FOR_CANADA"
        self.assertTrue(any("Coinbase International Exchange's institutional-only" in e for e in validate_catalogue(altered)))

    def test_trade_authority_cannot_be_enabled(self):
        item = json.loads(json.dumps(self.catalogue))
        item["global_controls"]["trade_authority"] = True
        self.assertTrue(any("trade_authority" in error for error in validate_catalogue(item)))


if __name__ == "__main__":
    unittest.main()

import unittest
from external_opportunity_sources import (
    parse_jobicy, parse_remoteok, parse_himalayas, country_hint, classify, collect
)

class ExternalOpportunitySourceTests(unittest.TestCase):
    def test_jobicy_parser_preserves_attribution_and_original_link(self):
        payload={"jobs":[{"id":12,"jobTitle":"Python Automation Engineer","companyName":"Acme",
            "url":"https://jobicy.com/jobs/12","jobGeo":"Canada","jobExcerpt":"Build Python automation.",
            "pubDate":"2026-11-13","jobIndustry":["Software"]}]}
        rows=parse_jobicy(payload)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["source_name"],"Jobicy")
        self.assertEqual(rows[0]["url"],"https://jobicy.com/jobs/12")
        self.assertIn("canada",rows[0]["eligibility_hint"])

    def test_remoteok_skips_legal_notice_and_keeps_original_url(self):
        payload=[{"legal":"API terms"}, {"id":"1","position":"Freelance Python Developer",
            "company":"Acme","url":"https://remoteok.com/remote-jobs/1",
            "location":"Worldwide","description":"Python contract"}]
        rows=parse_remoteok(payload)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["source_name"],"Remote OK")
        self.assertEqual(rows[0]["url"],"https://remoteok.com/remote-jobs/1")

    def test_himalayas_maps_country_restrictions(self):
        payload={"jobs":[{"guid":"https://himalayas.app/jobs/1","title":"AI Evaluator",
            "companyName":"Example","applicationLink":"https://himalayas.app/jobs/1",
            "locationRestrictions":["Canada"],"excerpt":"Evaluate AI model responses"}]}
        rows=parse_himalayas(payload)
        self.assertEqual(rows[0]["lane"],"ai_evaluation")
        self.assertEqual(rows[0]["eligibility_hint"],"canada_or_worldwide_listed_check_full_terms")

    def test_unknown_location_never_becomes_canada_eligible(self):
        self.assertEqual(country_hint("Remote"),"location_text_present_check_full_terms")
        self.assertEqual(country_hint(None),"unknown")

    def test_irrelevant_listing_is_excluded(self):
        self.assertEqual(parse_jobicy({"jobs":[{"jobTitle":"Accountant","companyName":"X",
            "url":"https://jobicy.com/jobs/1","jobGeo":"USA","jobExcerpt":"Accounting"}]}),[])

    def test_classification_is_conservative(self):
        self.assertEqual(classify("LLM evaluator role"),"ai_evaluation")
        self.assertEqual(classify("penetration test analyst"),"security_testing")

    def test_collect_reports_source_errors_without_fabricating_rows(self):
        def bad_fetch(url): raise RuntimeError("offline")
        rows, errors=collect(fetcher=bad_fetch, sleep=lambda _: None)
        self.assertEqual(rows,[])
        self.assertEqual(len(errors),3)

if __name__ == "__main__":
    unittest.main()

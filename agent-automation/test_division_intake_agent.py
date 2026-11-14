import json, tempfile, unittest
from pathlib import Path
from division_intake_agent import ingest, normalize

class DivisionIntakeTests(unittest.TestCase):
    def test_accepts_https_curated_record(self):
        item = normalize({"title":"Python automation contract","url":"https://example.com/job/1",
                          "source_name":"Example","lane":"freelance_services"}, "freelance_services")
        self.assertEqual(item["commercial_status"], "unverified_lead")
        self.assertFalse(item["funding_verified"])
        self.assertTrue(item["human_review_required"])

    def test_rejects_non_https(self):
        with self.assertRaises(ValueError):
            normalize({"title":"x","url":"http://example.com","source_name":"x",
                       "lane":"ai_evaluation"}, "ai_evaluation")

    def test_rejects_lane_mismatch(self):
        with self.assertRaises(ValueError):
            normalize({"title":"x","url":"https://example.com","source_name":"x",
                       "lane":"ai_evaluation"}, "freelance_services")

    def test_combines_and_deduplicates_feeds_and_github(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "freelance_services.json").write_text(json.dumps([{
                "title":"Contract","url":"https://example.com/1","source_name":"Example",
                "lane":"freelance_services"}]))
            github = {"results":[{"title":"Issue","url":"https://github.com/a/b/issues/1","signals":["bounty_keyword"]}]}
            records, errors = ingest(tmp, github)
            self.assertEqual(len(records), 2)
            self.assertFalse(errors)
            self.assertEqual({x["lane"] for x in records}, {"freelance_services","github_bounties"})

    def test_preserves_external_source_metadata(self):
        item = normalize({"title":"Role","url":"https://example.com/role",
                          "source_name":"Jobicy","lane":"remote_employment",
                          "company":"Acme","location_text":"Canada",
                          "eligibility_hint":"canada_or_worldwide_listed_check_full_terms",
                          "source_attribution":"Credit Jobicy"}, "remote_employment")
        self.assertEqual(item["company"], "Acme")
        self.assertIn("Canada", item["location_text"])
        self.assertEqual(item["source_attribution"], "Credit Jobicy")

    def test_remote_employment_lane_is_supported(self):
        item = normalize({"title":"Remote role","url":"https://example.com/role",
                          "source_name":"Job board","lane":"remote_employment"}, "remote_employment")
        self.assertEqual(item["lane"], "remote_employment")

    def test_missing_feed_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            records, errors = ingest(tmp)
            self.assertEqual(records, [])
            self.assertEqual(errors, [])

if __name__ == "__main__":
    unittest.main()

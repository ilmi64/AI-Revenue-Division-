import unittest
from ats_job_board_sources import validate_config, endpoint, parse_board, collect

class ATSJobBoardTests(unittest.TestCase):
    def test_config_rejects_unsafe_slugs_and_unknown_providers(self):
        with self.assertRaises(ValueError):
            validate_config({"boards":[{"provider":"greenhouse","board":"../secret"}]})
        with self.assertRaises(ValueError):
            validate_config({"boards":[{"provider":"unknown","board":"demo"}]})

    def test_endpoints_are_https_and_lever_eu_supported(self):
        self.assertEqual(endpoint({"provider":"greenhouse","board":"acme","region":"global"}),
                         "https://boards-api.greenhouse.io/v1/boards/acme/jobs?content=true")
        self.assertIn("https://api.lever.co/", endpoint({"provider":"lever","board":"acme","region":"global"}))
        self.assertIn("api.eu.lever.co", endpoint({"provider":"lever","board":"acme","region":"eu"}))
        self.assertIn("api.ashbyhq.com", endpoint({"provider":"ashby","board":"acme","region":"global"}))

    def test_greenhouse_parser_retains_employer_and_application_urls(self):
        entry={"provider":"greenhouse","board":"acme","company":"Acme","region":"global"}
        payload={"jobs":[{"id":1,"title":"Python Automation Engineer","location":{"name":"Canada"},
            "absolute_url":"https://jobs.acme.com/1","first_published":"2026-11-01",
            "content":"Build Python automation","departments":[{"name":"Engineering"}]}]}
        rows=parse_board(entry,payload)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["application_url"],"https://jobs.acme.com/1")
        self.assertEqual(rows[0]["eligibility_hint"],"canada_or_worldwide_listed_check_full_terms")
        self.assertFalse(rows[0]["eligibility_verified"])

    def test_lever_and_ashby_payload_shapes(self):
        lever={"provider":"lever","board":"acme","company":"Acme","region":"global"}
        self.assertEqual(len(parse_board(lever,[{"id":"x","text":"Freelance Python Developer",
            "hostedUrl":"https://jobs.lever.co/acme/x","categories":{"location":"Remote"}}])),1)
        ashby={"provider":"ashby","board":"acme","company":"Acme","region":"global"}
        self.assertEqual(len(parse_board(ashby,{"jobs":[{"title":"AI Evaluator","jobUrl":"https://jobs.ashbyhq.com/acme/x",
            "applyUrl":"https://jobs.ashbyhq.com/acme/x/apply","isListed":True}]})),1)
        self.assertEqual(parse_board(ashby,{"jobs":[{"title":"Python Developer","jobUrl":"https://jobs.ashbyhq.com/a/x","isListed":False}]}),[])

    def test_invalid_or_irrelevant_urls_are_ignored(self):
        entry={"provider":"ashby","board":"acme","company":"Acme","region":"global"}
        rows=parse_board(entry,{"jobs":[{"title":"Python Engineer","jobUrl":"http://bad.example/job"},
            {"title":"Accountant","jobUrl":"https://jobs.example/accountant"}]})
        self.assertEqual(rows,[])

    def test_collect_reports_board_failures_without_fake_rows(self):
        cfg={"boards":[{"provider":"greenhouse","board":"acme"}]}
        rows,errors,health=collect(cfg,fetcher=lambda _: (_ for _ in ()).throw(RuntimeError("offline")),sleep=lambda _:None)
        self.assertEqual(rows,[])
        self.assertEqual(len(errors),1)
        self.assertEqual(health[0]["status"],"error")

if __name__ == "__main__":
    unittest.main()

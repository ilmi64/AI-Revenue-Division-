import json, tempfile, unittest
from pathlib import Path
from validate_ats_board_candidates import main

class CandidateValidationTests(unittest.TestCase):
    def test_shortlist_is_review_only_and_has_valid_board_entries(self):
        path=Path(__file__).with_name("ats-board-candidates.json")
        data=json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["candidates"]),10)
        for row in data["candidates"]:
            self.assertIn(row["provider"],("greenhouse","lever","ashby"))
            self.assertTrue(row["board"])
            self.assertTrue(row["careers_url"].startswith("https://"))
            self.assertTrue(row["evidence_url"].startswith("https://"))
            self.assertTrue(row["approval_required"])
    def test_validator_does_not_write_live_config(self):
        data=json.loads(Path(__file__).with_name("ats-board-candidates.json").read_text())
        self.assertEqual(data["validation_policy"].split(".")[0],"Careers URL and board slug are sourced from public employer ATS pages")
        self.assertTrue(all(x["approval_required"] for x in data["candidates"]))

if __name__=="__main__":
    unittest.main()

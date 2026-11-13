import unittest
from research_radar import render_markdown

class ResearchRadarTests(unittest.TestCase):
    def test_render_includes_sources_and_human_review(self):
        results = [{
            "project": "Activepieces", "repository": "activepieces/activepieces",
            "status": "ok", "tag": "v1.2.3", "name": "Release | Notes",
            "published_at": "2026-11-01T12:00:00Z",
            "url": "https://github.com/activepieces/activepieces/releases/tag/v1.2.3",
            "summary": "Example release notes",
        }]
        report = render_markdown(results, "2026-11-13T00:00:00+00:00")
        self.assertIn("AI & Automation Research Radar", report)
        self.assertIn("Release \\| Notes", report)
        self.assertIn("Example release notes", report)
        self.assertIn("Required human review", report)
        self.assertIn("does not call an LLM", report)

    def test_handles_no_release(self):
        results = [{"project": "Dify", "repository": "langgenius/dify", "status": "no_stable_release"}]
        report = render_markdown(results, "2026-11-13T00:00:00+00:00")
        self.assertIn("No stable release found", report)

if __name__ == "__main__":
    unittest.main()

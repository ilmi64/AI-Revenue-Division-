import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from revenue_evidence_custody import LocalEvidenceCustody
from revenue_review_separation import assess_review


class ReviewerSeparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.custody = LocalEvidenceCustody(Path(self.tmp.name) / "evidence.sqlite")
        self.author = self.custody.append("demo_001:01", "agent_1", "engineering", b"work")
        self.reviewer = self.custody.append("demo_001:01", "reviewer_2", "quality", b"review")

    def tearDown(self):
        self.tmp.cleanup()

    def test_distinct_review_only_structurally_separated(self):
        result = assess_review(self.author, self.reviewer)
        self.assertEqual(result.status, "STRUCTURALLY_SEPARATED")
        self.assertFalse(result.identity_authenticated)
        self.assertFalse(result.completion_verified)
        self.assertFalse(result.delivery_authorized)

    def test_same_identity_fails(self):
        result = assess_review(self.author, replace(self.reviewer, actor_id="agent_1"))
        self.assertIn("self_review", result.blockers)

    def test_same_role_fails(self):
        result = assess_review(self.author, replace(self.reviewer, actor_role="engineering"))
        self.assertIn("reviewer_role_invalid", result.blockers)

    def test_wrong_task_fails(self):
        result = assess_review(self.author, replace(self.reviewer, task_id="other_001:01"))
        self.assertIn("task_mismatch", result.blockers)

    def test_reversed_sequence_fails(self):
        result = assess_review(self.author, replace(self.reviewer, sequence=1))
        self.assertIn("review_order_invalid", result.blockers)

    def test_broken_chain_fails(self):
        result = assess_review(self.author, replace(self.reviewer, previous_digest="0"*64))
        self.assertIn("broken_adjacent_chain", result.blockers)

    def test_reused_artifact_fails(self):
        result = assess_review(self.author, replace(self.reviewer, artifact_digest=self.author.artifact_digest))
        self.assertIn("review_artifact_not_distinct", result.blockers)


if __name__ == "__main__":
    unittest.main()

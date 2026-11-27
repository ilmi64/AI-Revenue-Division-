import hashlib
import unittest
from dataclasses import replace

from revenue_agent_queue import prepare_queue
from revenue_delivery_plan import plan_delivery
from revenue_intake_sandbox import Opportunity
from revenue_task_evidence import TaskEvidence, review_evidence


def task():
    item = Opportunity("demo_001", "coding", "CA", 300, 0, True, True, True, True)
    return prepare_queue(plan_delivery(item))[0]


def evidence(item):
    artifact = b"offline demonstration artifact"
    return TaskEvidence(item.task_id, hashlib.sha256(artifact).hexdigest(),
                        artifact, item.role, "quality", True)


class TaskEvidenceTests(unittest.TestCase):
    def test_valid_evidence_is_review_only(self):
        item = task()
        result = review_evidence(item, evidence(item))
        self.assertEqual(result.status, "EVIDENCE_REVIEWED")
        self.assertFalse(result.completion_verified)
        self.assertFalse(result.external_delivery_authorized)
        self.assertFalse(result.execution_authorized)

    def test_tampered_artifact_is_held(self):
        item = task()
        result = review_evidence(item, replace(evidence(item), artifact_bytes=b"tampered"))
        self.assertIn("artifact_digest_invalid", result.reasons)

    def test_self_review_is_held(self):
        item = task()
        result = review_evidence(item, replace(evidence(item), reviewer_role=item.role))
        self.assertIn("independent_review_unverified", result.reasons)

    def test_unattested_review_is_held(self):
        item = task()
        result = review_evidence(item, replace(evidence(item), reviewer_attested=False))
        self.assertEqual(result.status, "HOLD")

    def test_wrong_task_identity_is_held(self):
        item = task()
        result = review_evidence(item, replace(evidence(item), task_id="other:01"))
        self.assertEqual(result.status, "HOLD")

    def test_queue_permission_escalation_is_held(self):
        item = replace(task(), execution_authorized=True)
        result = review_evidence(item, evidence(item))
        self.assertIn("queue_permissions_invalid", result.reasons)

    def test_empty_artifact_is_held(self):
        item = task()
        result = review_evidence(item, replace(evidence(item), artifact_bytes=b""))
        self.assertEqual(result.status, "HOLD")


if __name__ == "__main__":
    unittest.main()

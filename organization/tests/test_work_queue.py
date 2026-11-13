import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_work_queue import build_report


class WorkQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.registry = json.loads((root / "division-registry.json").read_text(encoding="utf-8"))
        cls.queue = json.loads((root / "work-queue.json").read_text(encoding="utf-8"))

    def copy_queue(self):
        return json.loads(json.dumps(self.queue))

    def test_queue_covers_all_nine_divisions_and_is_unassigned(self):
        report = build_report(self.registry, self.copy_queue())
        self.assertTrue(report["validated"], report["errors"])
        self.assertEqual(len(report["divisions"]), 9)
        self.assertEqual(report["task_count"], 18)
        self.assertEqual(report["completed_count"], 0)
        self.assertEqual(report["in_progress_count"], 0)
        self.assertEqual(report["unassigned_count"], 18)

    def test_incomplete_dependencies_are_reported_as_blocked(self):
        report = build_report(self.registry, self.copy_queue())
        task = next(row for row in report["tasks"] if row["task_id"] == "AIR-001")
        self.assertEqual(task["computed_status"], "blocked")
        self.assertIn("RES-001", task["unresolved_dependencies"])

    def test_unknown_dependency_is_rejected(self):
        queue = self.copy_queue()
        queue["tasks"][0]["depends_on"] = ["DOES-NOT-EXIST"]
        report = build_report(self.registry, queue)
        self.assertFalse(report["validated"])
        self.assertTrue(any("unknown dependency" in error for error in report["errors"]))

    def test_dependency_cycle_is_rejected(self):
        queue = self.copy_queue()
        queue["tasks"][0]["depends_on"] = ["EXEC-002"]
        queue["tasks"][1]["depends_on"] = ["EXEC-001"]
        report = build_report(self.registry, queue)
        self.assertFalse(report["validated"])
        self.assertTrue(any("cycle" in error.lower() for error in report["errors"]))

    def test_completed_task_requires_evidence_and_timestamp(self):
        queue = self.copy_queue()
        task = queue["tasks"][0]
        task["status"] = "completed"
        task["execution_state"] = "done"
        report = build_report(self.registry, queue)
        self.assertFalse(report["validated"])
        self.assertTrue(any("completed tasks require" in error for error in report["errors"]))

    def test_ready_task_requires_owner_assignment(self):
        queue = self.copy_queue()
        queue["tasks"][0]["status"] = "ready"
        report = build_report(self.registry, queue)
        self.assertFalse(report["validated"])
        self.assertTrue(any("ready tasks require an assigned owner" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()

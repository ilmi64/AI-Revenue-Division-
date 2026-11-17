import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_task_dispatch import build_dispatch_report
from validate_work_queue import build_report as build_queue_report


class TaskDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "division-registry.json").read_text(encoding="utf-8"))
        cls.queue = json.loads((ROOT / "work-queue.json").read_text(encoding="utf-8"))
        cls.roles = json.loads((ROOT / "ai-workforce" / "agent-roles.json").read_text(encoding="utf-8"))
        cls.queue_report = build_queue_report(cls.registry, cls.queue)

    def test_all_queue_tasks_get_prepared_packets_but_none_are_dispatched(self):
        report = build_dispatch_report(self.registry, self.queue, self.roles, self.queue_report)
        self.assertEqual(report["status"], "validated", report["errors"])
        self.assertEqual(report["task_count"], 20)
        self.assertEqual(report["dispatch_count"], 0)
        self.assertEqual(report["execution_authority"], "none")
        self.assertEqual(report["unassigned_count"], 20)
        self.assertTrue(all(not task["can_execute"] for task in report["tasks"]))
        self.assertTrue(all(task["named_owner"] is None for task in report["tasks"]))

    def test_unresolved_dependencies_block_packets(self):
        report = build_dispatch_report(self.registry, self.queue, self.roles, self.queue_report)
        air = next(task for task in report["tasks"] if task["task_id"] == "AIR-001")
        self.assertEqual(air["dispatch_status"], "blocked_by_unresolved_dependencies")
        self.assertIn("RES-001", air["unresolved_dependencies"])

    def test_role_template_is_not_treated_as_named_owner(self):
        report = build_dispatch_report(self.registry, self.queue, self.roles, self.queue_report)
        packet = next(task for task in report["tasks"] if task["task_id"] == "RISK-001")
        self.assertEqual(packet["role_template_id"], "risk-compliance-reviewer")
        self.assertEqual(packet["owner_status"], "unassigned_pending_owner_confirmation")
        self.assertIsNone(packet["named_owner"])

    def test_recorded_owner_still_requires_acknowledgement(self):
        queue = json.loads(json.dumps(self.queue))
        queue["tasks"][0]["owner_assignment"] = "Executive Management lead"
        report = build_dispatch_report(self.registry, queue, self.roles,
                                       build_queue_report(self.registry, queue))
        packet = next(task for task in report["tasks"] if task["task_id"] == "EXEC-001")
        self.assertEqual(packet["dispatch_status"], "prepared_waiting_for_owner_acknowledgement")
        self.assertEqual(packet["named_owner"], "Executive Management lead")
        self.assertEqual(report["dispatch_count"], 0)

    def test_invalid_queue_validation_prevents_validated_dispatch_report(self):
        queue = json.loads(json.dumps(self.queue))
        queue["tasks"][0]["depends_on"] = ["UNKNOWN-TASK"]
        queue_report = build_queue_report(self.registry, queue)
        report = build_dispatch_report(self.registry, queue, self.roles, queue_report)
        self.assertEqual(report["status"], "invalid")
        self.assertEqual(report["dispatch_count"], 0)

    def test_missing_division_role_mapping_fails_closed(self):
        roles = json.loads(json.dumps(self.roles))
        roles["division_role_map"].pop("animora")
        report = build_dispatch_report(self.registry, self.queue, roles, self.queue_report)
        self.assertEqual(report["status"], "invalid")
        self.assertTrue(any("division_role_map" in error for error in report["errors"]))

    def test_unknown_role_is_rejected(self):
        roles = json.loads(json.dumps(self.roles))
        roles["division_role_map"]["crypto"] = "unbounded-super-agent"
        report = build_dispatch_report(self.registry, self.queue, roles, self.queue_report)
        self.assertEqual(report["status"], "invalid")
        self.assertTrue(any("unknown role" in error for error in report["errors"]))

    def test_malformed_queue_fails_closed(self):
        report = build_dispatch_report(self.registry, {"tasks": None}, self.roles)
        self.assertEqual(report["status"], "invalid")
        self.assertEqual(report["dispatch_count"], 0)


if __name__ == "__main__":
    unittest.main()

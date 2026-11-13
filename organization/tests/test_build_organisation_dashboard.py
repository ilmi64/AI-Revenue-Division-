import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_organisation_dashboard import build_dashboard


class OrganisationDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.registry = json.loads((root / "division-registry.json").read_text(encoding="utf-8"))
        cls.readiness = json.loads((root / "readiness-register.json").read_text(encoding="utf-8"))
        cls.dependencies = json.loads((root / "dependency-map.json").read_text(encoding="utf-8"))
        cls.operating = json.loads((root / "operating-framework.json").read_text(encoding="utf-8"))
        cls.work_queue = json.loads((root / "work-queue.json").read_text(encoding="utf-8"))

    def build(self, work_queue=None, execution_log=None):
        return build_dashboard(
            self.registry, self.readiness, self.dependencies, self.operating, [], [],
            work_queue if work_queue is not None else self.work_queue, execution_log
        )

    def test_dashboard_covers_all_divisions_and_never_promotes_readiness(self):
        report = self.build()
        self.assertEqual(report["organisation"]["division_count"], 9)
        self.assertEqual(report["organisation"]["verified_standby_or_operational"], 0)
        self.assertTrue(all(x["verified_status"] not in {"standby", "operational"} for x in report["division_scorecard"]))

    def test_crypto_blockers_are_visible(self):
        report = self.build()
        crypto = next(x for x in report["division_scorecard"] if x["id"] == "crypto")
        self.assertTrue(crypto["required_blockers"])
        self.assertEqual(crypto["verified_status"], "testing")

    def test_finance_and_animora_are_not_assumed_ready(self):
        report = self.build()
        finance = next(x for x in report["division_scorecard"] if x["id"] == "finance")
        animora = next(x for x in report["division_scorecard"] if x["id"] == "animora")
        self.assertEqual(finance["verified_status"], "unassessed")
        self.assertEqual(animora["verified_status"], "deferred")


    def test_dashboard_uses_supplied_execution_log(self):
        queue = json.loads(json.dumps(self.work_queue))
        task = next(item for item in queue["tasks"] if item["id"] == "TECH-001")
        task["owner_assignment"] = "owner-confirmed"
        events = [
            {
                "event_id": "EV-START",
                "task_id": "TECH-001",
                "event_type": "started",
                "timestamp": "2026-11-12T12:00:00-05:00",
                "actor": "test-owner",
                "summary": "Started controlled test task",
                "evidence": []
            },
            {
                "event_id": "EV-DONE",
                "task_id": "TECH-001",
                "event_type": "completed",
                "timestamp": "2026-11-12T13:00:00-05:00",
                "actor": "test-owner",
                "summary": "Completed controlled test task",
                "evidence": ["tests/test_evidence.txt"]
            }
        ]

        report = self.build(queue, {"events": events})

        self.assertTrue(report["division_execution_evidence"]["validated"])
        self.assertEqual(report["division_execution_evidence"]["event_count"], 2)
        self.assertEqual(
            report["division_execution_evidence"]["task_state_from_events"]["TECH-001"],
            "completed"
        )

    def test_revenue_snapshot_and_operating_framework_are_embedded(self):
        report = self.build()
        self.assertEqual(report["ai_revenue"]["finance_cad"]["net_cash_received_verified_by_ledger_status"], "0.00")
        self.assertTrue(report["division_operating_framework"]["validated"])
        self.assertEqual(report["division_operating_framework"]["division_count"], 9)
        self.assertIn("risk_register", report)
        self.assertIn("outstanding_decisions", report)
        self.assertTrue(report["division_work_queue"]["validated"])
        self.assertEqual(report["division_work_queue"]["task_count"], 18)
        self.assertEqual(report["division_work_queue"]["completed_count"], 0)
        self.assertTrue(report["division_execution_evidence"]["validated"])
        self.assertEqual(report["division_execution_evidence"]["event_count"], 0)


if __name__ == "__main__":
    unittest.main()

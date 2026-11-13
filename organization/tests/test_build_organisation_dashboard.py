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

    def build(self):
        return build_dashboard(self.registry, self.readiness, self.dependencies, self.operating, [], [], self.work_queue)

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

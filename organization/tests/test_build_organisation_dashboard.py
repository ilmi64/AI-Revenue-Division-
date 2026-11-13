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

    def build(self, work_queue=None, execution_log=None, risk_register=None, decision_register=None, incident_register=None, recovery_plan=None):
        return build_dashboard(
            self.registry, self.readiness, self.dependencies, self.operating, [], [],
            work_queue if work_queue is not None else self.work_queue, execution_log,
            risk_register, decision_register, incident_register,
            recovery_plan if recovery_plan is not None else json.loads((Path(__file__).resolve().parents[1] / "recovery-plan.json").read_text(encoding="utf-8"))
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


    def test_risk_decision_and_work_queue_links_are_reported(self):
        risk_register = {"records": [{
            "id": "RISK-TEST-001",
            "division_id": "technology",
            "severity": "medium",
            "status": "open",
            "description": "Regression fixture risk",
            "mitigation": "Run the linked validation task",
            "owner_assignment": "unassigned_pending_owner_confirmation",
            "related_task_ids": ["TECH-001"],
            "related_decision_ids": ["DEC-TEST-001"],
            "evidence": []
        }]}
        decision_register = {"records": [{
            "id": "DEC-TEST-001",
            "scope": "Test-only decision fixture",
            "status": "pending",
            "impact": "No external impact",
            "reversibility": "Fully reversible; test fixture only",
            "requested_action": "Review the test fixture",
            "related_risk_ids": ["RISK-TEST-001"],
            "related_task_ids": ["TECH-001"],
            "owner_outcome_evidence": []
        }]}

        report = self.build(risk_register=risk_register, decision_register=decision_register)

        self.assertEqual(report["risk_register"]["summary"]["risk_count"], 1)
        self.assertEqual(report["decision_register"]["summary"]["decision_count"], 1)
        self.assertEqual(report["risk_register"]["summary"]["linked_task_count"], 1)
        self.assertEqual(report["outstanding_decisions"][-1]["id"], "DEC-TEST-001")
        self.assertEqual(report["data_quality"]["governance_link_errors"], [])

    def test_governance_links_reject_unknown_work_queue_tasks(self):
        risk_register = {"records": [{
            "id": "RISK-TEST-002",
            "division_id": "technology",
            "severity": "low",
            "status": "open",
            "description": "Dangling reference fixture",
            "mitigation": "Correct the task reference",
            "owner_assignment": "unassigned_pending_owner_confirmation",
            "related_task_ids": ["MISSING-999"],
            "related_decision_ids": [],
            "evidence": []
        }]}

        report = self.build(risk_register=risk_register, decision_register={"records": []})

        self.assertTrue(any("unknown task MISSING-999" in error for error in report["data_quality"]["governance_link_errors"]))


    def test_governance_validator_reports_malformed_records_without_crashing(self):
        report = self.build(
            risk_register={"records": [{"id": ["not-a-string"], "related_task_ids": "TECH-001"}]},
            decision_register={"records": [None]}
        )
        errors = report["data_quality"]["governance_link_errors"]
        self.assertTrue(any("non-empty string id" in error for error in errors))
        self.assertTrue(any("must be an object" in error for error in errors))

    def test_approved_decision_requires_owner_outcome_evidence(self):
        decision_register = {"records": [{
            "id": "DEC-TEST-APPROVED",
            "scope": "Test-only scope",
            "status": "approved",
            "impact": "No external impact",
            "reversibility": "Reversible test fixture",
            "requested_action": "Approve test fixture",
            "related_risk_ids": [],
            "related_task_ids": [],
            "owner_outcome_evidence": []
        }]}
        report = self.build(decision_register=decision_register)
        self.assertTrue(any("requires explicit owner outcome evidence" in error for error in report["data_quality"]["governance_link_errors"]))
        self.assertFalse(any(row.get("id") == "DEC-TEST-APPROVED" for row in report["outstanding_decisions"]))


    def test_critical_risk_creates_stop_only_cross_division_escalation(self):
        queue = json.loads(json.dumps(self.work_queue))
        task = next(item for item in queue["tasks"] if item["id"] == "TECH-001")
        task["owner_assignment"] = "owner-confirmed"
        risk_register = {"records": [{
            "id": "RISK-CRITICAL-001",
            "division_id": "technology",
            "severity": "critical",
            "status": "mitigating",
            "description": "Test-only critical risk",
            "mitigation": "Pause affected activity and obtain independent review",
            "owner_assignment": "unassigned_pending_owner_confirmation",
            "related_task_ids": ["TECH-001"],
            "related_decision_ids": ["DEC-PENDING-001"],
            "evidence": ["test-fixture:evidence"]
        }]}
        decision_register = {"records": [{
            "id": "DEC-PENDING-001",
            "scope": "Test fixture only",
            "status": "pending",
            "impact": "No external impact",
            "reversibility": "Reversible test fixture",
            "requested_action": "Review the test fixture",
            "related_risk_ids": ["RISK-CRITICAL-001"],
            "related_task_ids": ["TECH-001"],
            "owner_outcome_evidence": []
        }]}
        events = {"events": [{
            "event_id": "EV-ESCALATION-START",
            "task_id": "TECH-001",
            "event_type": "started",
            "timestamp": "2026-11-12T14:00:00-05:00",
            "actor": "test-owner",
            "summary": "Started test fixture task",
            "evidence": []
        }]}

        report = self.build(queue, events, risk_register, decision_register)
        escalation = report["risk_escalations"]["records"][0]

        self.assertEqual(report["risk_escalations"]["immediate_review_count"], 1)
        self.assertEqual(escalation["route"], ["risk", "executive", "technology"])
        self.assertEqual(escalation["broadcast_scope"], "all_divisions")
        self.assertEqual(len(escalation["broadcast_divisions"]), 9)
        self.assertEqual(escalation["linked_tasks"][0]["derived_execution_state"], "in_progress")
        self.assertEqual(escalation["pending_owner_decision_ids"], ["DEC-PENDING-001"])
        self.assertEqual(escalation["description"], "Test-only critical risk")
        self.assertEqual(escalation["risk_evidence"], ["test-fixture:evidence"])
        self.assertIn("STOP-ONLY ADVISORY", escalation["recommended_action"])
        self.assertEqual(escalation["dispatch_status"], "derived_dashboard_route_only_not_dispatched")
        self.assertEqual(report["data_quality"]["governance_link_errors"], [])

    def test_risk_escalation_does_not_invent_notifications_for_empty_register(self):
        report = self.build()
        self.assertEqual(report["risk_escalations"]["count"], 0)
        self.assertEqual(report["risk_escalations"]["immediate_review_count"], 0)


    def test_malformed_register_roots_are_reported_without_crashing(self):
        report = self.build(risk_register="not-an-object", decision_register=[])
        self.assertTrue(report["data_quality"]["governance_link_errors"])
        self.assertEqual(report["risk_escalations"]["count"], 0)


    def test_dashboard_reports_empty_incident_register_without_inventing_events(self):
        report = self.build()
        self.assertEqual(report["incident_response"]["incident_count"], 0)
        self.assertEqual(report["incident_response"]["corrective_action_count"], 0)
        self.assertEqual(report["incident_response"]["critical_or_high_count"], 0)
        self.assertEqual(report["data_quality"]["incident_register_errors"], [])


    def test_critical_incident_creates_stop_only_route_without_dispatch(self):
        risk = {"records": [{
            "id": "RISK-INC-1", "division_id": "technology", "severity": "critical",
            "status": "open", "description": "Linked test risk", "mitigation": "Review",
            "owner_assignment": "unassigned_pending_owner_confirmation",
            "related_task_ids": [], "related_decision_ids": [], "evidence": ["test:risk"]
        }]}
        incident = {"records": [{
            "id": "INC-CRIT-1", "summary": "Test-only incident", "severity": "critical",
            "status": "recovering", "affected_division_id": "technology",
            "containment_recommendation": "Pause affected workflow pending review",
            "owner_assignment": "unassigned_pending_owner_confirmation",
            "detection_evidence": ["test:incident"],
            "related_risk_ids": ["RISK-INC-1"], "related_task_ids": [],
            "related_decision_ids": [], "corrective_actions": []
        }]}
        report = self.build(risk_register=risk, decision_register={"records": []}, incident_register=incident)
        escalation = report["incident_response"]["escalations"][0]
        self.assertEqual(escalation["route"], ["risk", "executive", "technology"])
        self.assertIn("STOP-ONLY ADVISORY", escalation["recommended_action"])
        self.assertEqual(escalation["dispatch_status"], "dashboard_route_only_not_dispatched")
        self.assertEqual(report["data_quality"]["incident_register_errors"], [])


    def test_dashboard_surfaces_recovery_plan_without_claiming_production_readiness(self):
        plan = json.loads((Path(__file__).resolve().parents[1] / "recovery-plan.json").read_text(encoding="utf-8"))
        report = self.build()
        recovery = report["technical_recovery"]
        self.assertEqual(recovery["procedure_count"], 4)
        self.assertFalse(recovery["production_recovery_verified"])
        self.assertIn("security_posture", report)
        self.assertEqual(report["security_posture"]["workflow_permissions"]["expected"], {"contents": "read"})
        self.assertIn("temporary_fixture_only", recovery["drill_scope"])
        self.assertEqual(recovery["plan_status"], "design_only_pending_owner_and_environment_confirmation")

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
        self.assertTrue(report["cross_division_integration"]["validated"])
        self.assertEqual(report["cross_division_integration"]["dependency_edge_count"], 28)
        self.assertEqual(report["cross_division_integration"]["connected_edge_count"], 28)


if __name__ == "__main__":
    unittest.main()

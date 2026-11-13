#!/usr/bin/env python3
"""Build a read-only consolidated Organisation Control Centre report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from build_dependency_report import build_report
from build_executive_snapshot import build_snapshot, read_csv
from validate_readiness import validate
from validate_operating_framework import build_report as build_operating_framework_report
from validate_work_queue import build_report as build_work_queue_report
from validate_execution_log import build_report as build_execution_log_report
from validate_division_integrations import build_report as build_division_integration_report
from validate_incident_register import validate as validate_incident_register


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_governance_links(work_queue, risk_register, decision_register, registry):
    """Validate governance references defensively; malformed input becomes errors, not crashes."""
    errors = []
    tasks = {
        item.get("id") for item in (work_queue or {}).get("tasks", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    divisions = {item.get("id") for item in registry.get("divisions", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
    risks = risk_register or {"records": []}
    decisions = decision_register or {"records": []}
    risk_rows = risks.get("records", []) if isinstance(risks, dict) else None
    decision_rows = decisions.get("records", []) if isinstance(decisions, dict) else None
    if not isinstance(risk_rows, list) or not isinstance(decision_rows, list):
        return ["Risk and decision records must be arrays in object registers."], {
            "risk_count": 0, "decision_count": 0, "linked_task_count": 0
        }

    def index_records(rows, label):
        indexed = {}
        for position, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{label} record at index {position} must be an object.")
                continue
            record_id = row.get("id")
            if not isinstance(record_id, str) or not record_id.strip():
                errors.append(f"{label} record at index {position} requires a non-empty string id.")
                continue
            if record_id in indexed:
                errors.append(f"{label} record ids must be unique: {record_id}.")
            indexed[record_id] = row
        return indexed

    risk_index = index_records(risk_rows, "Risk")
    decision_index = index_records(decision_rows, "Decision")
    linked_tasks = set()

    def references(row, field, known, label, record_id):
        values = row.get(field, [])
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            errors.append(f"{label} {record_id} field {field} must be an array of non-empty strings.")
            return []
        target_label = {
            "related_task_ids": "task",
            "related_decision_ids": "decision",
            "related_risk_ids": "risk"
        }.get(field, field)
        for value in values:
            if value not in known:
                errors.append(f"{label} {record_id} references unknown {target_label} {value}.")
        return values

    for record_id, row in risk_index.items():
        for field in ("severity", "status", "description", "division_id", "mitigation", "owner_assignment"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"Risk {record_id} requires non-empty {field}.")
        if row.get("severity") not in {"critical", "high", "medium", "low", "unassessed"}:
            errors.append(f"Risk {record_id} has invalid severity.")
        if row.get("status") not in {"open", "mitigating", "accepted_pending_owner_approval", "closed", "unassessed"}:
            errors.append(f"Risk {record_id} has invalid status.")
        if row.get("division_id") not in divisions:
            errors.append(f"Risk {record_id} references unknown division {row.get('division_id')!r}.")
        linked_tasks.update(references(row, "related_task_ids", tasks, "Risk", record_id))
        references(row, "related_decision_ids", decision_index, "Risk", record_id)

    for record_id, row in decision_index.items():
        for field in ("scope", "status", "impact", "reversibility", "requested_action"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"Decision {record_id} requires non-empty {field}.")
        linked_tasks.update(references(row, "related_task_ids", tasks, "Decision", record_id))
        references(row, "related_risk_ids", risk_index, "Decision", record_id)
        if row.get("status") == "approved" and not row.get("owner_outcome_evidence"):
            errors.append(f"Approved decision {record_id} requires explicit owner outcome evidence.")

    return errors, {
        "risk_count": len(risk_rows),
        "decision_count": len(decision_rows),
        "linked_task_count": len(linked_tasks)
    }


def build_risk_escalation_report(risk_register, decision_register, work_queue, execution_report, operating_framework, registry):
    """Derive internal escalation routes; never dispatch notifications or authorise actions."""
    risks = risk_register.get("records", []) if isinstance(risk_register, dict) else []
    decisions = decision_register.get("records", []) if isinstance(decision_register, dict) else []
    tasks = {
        item.get("id"): item for item in (work_queue or {}).get("tasks", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    decision_index = {
        item.get("id"): item for item in decisions
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    task_states = execution_report.get("task_state_from_events", {})
    all_divisions = sorted(item.get("id") for item in registry.get("divisions", []) if isinstance(item, dict) and isinstance(item.get("id"), str))
    risk_division = next(
        (item for item in operating_framework.get("divisions", []) if item.get("id") == "risk"), {}
    )
    broadcast_handoff = next(
        (item for item in risk_division.get("handoffs", [])
         if isinstance(item, dict) and item.get("to") == "all"), None
    )
    escalations = []
    for risk in risks if isinstance(risks, list) else []:
        if not isinstance(risk, dict) or risk.get("status") in {"closed", "unassessed"}:
            continue
        severity = risk.get("severity")
        if severity not in {"critical", "high", "medium", "low"}:
            continue
        task_ids = risk.get("related_task_ids", [])
        decision_ids = risk.get("related_decision_ids", [])
        linked_tasks = []
        for task_id in task_ids if isinstance(task_ids, list) else []:
            if not isinstance(task_id, str):
                continue
            task = tasks.get(task_id)
            if task:
                linked_tasks.append({
                    "task_id": task_id,
                    "division_id": task.get("division_id"),
                    "derived_execution_state": task_states.get(task_id, "no_validated_execution_event")
                })
        pending_decisions = [
            decision_id for decision_id in decision_ids if isinstance(decision_id, str)
            and decision_id in decision_index and decision_index[decision_id].get("status") == "pending"
        ] if isinstance(decision_ids, list) else []
        urgent = severity in {"critical", "high"}
        affected = risk.get("division_id")
        escalations.append({
            "risk_id": risk.get("id"),
            "severity": severity,
            "risk_status": risk.get("status"),
            "description": risk.get("description", ""),
            "mitigation": risk.get("mitigation", ""),
            "owner_assignment": risk.get("owner_assignment", "unassigned_pending_owner_confirmation"),
            "risk_evidence": risk.get("evidence", []) if isinstance(risk.get("evidence", []), list) else [],
            "affected_division": affected,
            "escalation_tier": "immediate_independent_review" if urgent else "standard_risk_review",
            "route": ["risk", "executive"] + ([affected] if isinstance(affected, str) and affected not in {"risk", "executive"} else []),
            "broadcast_scope": "all_divisions",
            "broadcast_divisions": all_divisions,
            "recommended_action": (
                "STOP-ONLY ADVISORY: recommend pausing the affected activity pending independent Risk review and Executive coordination. This is a recommendation, not an executed stop or permission to act."
                if urgent else
                "Route for documented Risk review and proportionate mitigation; no execution authority is created."
            ),
            "linked_tasks": linked_tasks,
            "pending_owner_decision_ids": pending_decisions,
            "owner_decision_path": (
                "Existing linked owner decision is pending."
                if pending_decisions else
                "Create a scoped owner decision request only if the proposed response crosses a reserved approval boundary."
            ),
            "handoff_artifact": broadcast_handoff.get("artifact") if isinstance(broadcast_handoff, dict) else None,
            "handoff_trigger": broadcast_handoff.get("trigger") if isinstance(broadcast_handoff, dict) else None,
            "dispatch_status": "derived_dashboard_route_only_not_dispatched",
            "authority": "Risk may independently challenge and recommend stop; only the owner can approve reserved actions. Deterministic controls remain authoritative."
        })
    escalations.sort(key=lambda row: (row["escalation_tier"] != "immediate_independent_review", row["risk_id"] or ""))
    return {
        "policy": "Escalations are derived from evidence-backed risk records. Dashboard routing does not send notifications, change task states, execute stops, close risks, or approve actions.",
        "count": len(escalations),
        "immediate_review_count": sum(row["escalation_tier"] == "immediate_independent_review" for row in escalations),
        "records": escalations
    }

def build_dashboard(registry, readiness, dependency_map, operating_framework, opportunities, ledger, work_queue=None, execution_log=None, risk_register=None, decision_register=None, incident_register=None):
    errors, warnings = validate(registry, readiness)
    dependency_report = build_report(registry, readiness, dependency_map)
    revenue = build_snapshot(opportunities, ledger)
    operating = build_operating_framework_report(registry, operating_framework)
    work_queue_report = build_work_queue_report(registry, work_queue or {"tasks": []})
    execution_report = build_execution_log_report(registry, work_queue or {"tasks": []}, execution_log or {"events": []})
    integration_report = build_division_integration_report(registry, dependency_map, operating_framework)
    governance_errors, governance_summary = validate_governance_links(work_queue, risk_register, decision_register, registry)
    risk_records = risk_register.get("records", []) if isinstance(risk_register, dict) and isinstance(risk_register.get("records", []), list) else []
    decision_records = decision_register.get("records", []) if isinstance(decision_register, dict) and isinstance(decision_register.get("records", []), list) else []
    risk_escalations = build_risk_escalation_report(risk_register, decision_register, work_queue, execution_report, operating_framework, registry)
    incident_source = incident_register
    incident_errors = validate_incident_register(
        incident_source, risk_register or {"records": []},
        decision_register or {"records": []}, work_queue or {"tasks": []}, registry
    )
    incident_records = incident_source.get("records", []) if isinstance(incident_source, dict) and isinstance(incident_source.get("records", []), list) else []
    incident_actions = [
        action for incident in incident_records if isinstance(incident, dict)
        for action in incident.get("corrective_actions", [])
        if isinstance(incident.get("corrective_actions", []), list) and isinstance(action, dict)
    ]
    incident_response = {
        "policy": "Incident and corrective-action states are owner-maintained evidence records. The dashboard does not contain, recover, roll back, notify, assign owners, or close incidents. Critical/high records follow the existing Risk stop-only advisory route.",
        "incident_count": len(incident_records),
        "critical_or_high_count": sum(
            1 for row in incident_records if isinstance(row, dict)
            and row.get("severity") in {"critical", "high"}
            and row.get("status") not in {"closed", "unassessed"}
        ),
        "corrective_action_count": len(incident_actions),
        "corrective_actions_completed": sum(1 for row in incident_actions if row.get("status") == "completed"),
        "escalations": [
            {
                "incident_id": row.get("id"),
                "severity": row.get("severity"),
                "route": ["risk", "executive"] + ([row.get("affected_division_id")] if row.get("affected_division_id") not in {"risk", "executive"} else []),
                "recommended_action": "STOP-ONLY ADVISORY: recommend pausing affected activity pending independent Risk review and Executive coordination; no stop is executed.",
                "dispatch_status": "dashboard_route_only_not_dispatched"
            }
            for row in incident_records if isinstance(row, dict)
            and row.get("severity") in {"critical", "high"}
            and row.get("status") not in {"closed", "unassessed"}
        ],
        "records": incident_records
    }

    assessments = {a["division_id"]: a for a in readiness.get("division_assessments", [])}
    divisions = []
    for division in registry.get("divisions", []):
        assessment = assessments.get(division["id"], {})
        dependency = next(
            (row for row in dependency_report.get("divisions", [])
             if row["division_id"] == division["id"]),
            {}
        )
        divisions.append({
            "id": division["id"],
            "name": division["name"],
            "registry_status": division.get("status", "unassessed"),
            "verified_status": assessment.get("verified_status", "unassessed"),
            "dependency_status": dependency.get("dependency_status", "unmapped"),
            "required_blockers": dependency.get("required_blockers", []),
            "supporting_gaps": dependency.get("supporting_gaps", []),
            "open_gaps": assessment.get("open_gaps", []),
            "evidence_count": len(assessment.get("evidence", []))
        })

    risks = []
    decisions = []
    for division in divisions:
        for gap in division["open_gaps"]:
            risks.append({
                "division_id": division["id"],
                "category": "readiness_gap",
                "description": gap
            })
            decisions.append({
                "division_id": division["id"],
                "item": gap,
                "requires_owner_decision": any(
                    term in gap.lower()
                    for term in ("approval", "owner", "reconcile", "review", "fund", "funding")
                )
            })
        for blocker in division["required_blockers"]:
            risks.append({
                "division_id": division["id"],
                "category": "dependency_blocker",
                "description": blocker
            })

    organisation = registry.get("organisation", {})
    reserved_approvals = organisation.get("owner_approval_required_for", [])
    return {
        "schema_version": 1,
        "report_type": "read_only_organisation_control_centre",
        "policy": "This report consolidates source records. It does not change readiness, approve actions, connect accounts, or verify bank balances.",
        "organisation": {
            "name": organisation.get("name", "Organisation"),
            "strategic_priority": organisation.get("strategic_priority", ""),
            "operating_budget_default": organisation.get("operating_budget_default", "Not specified"),
            "division_count": len(divisions),
            "verified_standby_or_operational": sum(
                1 for d in divisions if d["verified_status"] in {"standby", "operational"}
            ),
            "divisions_with_required_dependency_blockers": sum(
                1 for d in divisions if d["required_blockers"]
            )
        },
        "division_scorecard": divisions,
        "cross_division_dependencies": dependency_report,
        "division_operating_framework": operating,
        "division_work_queue": work_queue_report,
        "division_execution_evidence": execution_report,
        "cross_division_integration": integration_report,
        "ai_revenue": revenue,
        "risk_escalations": risk_escalations,
        "incident_response": incident_response,
        "risk_register": {
            "records": risk_records,
            "readiness_and_dependency_warnings": risks,
            "summary": governance_summary
        },
        "decision_register": {
            "records": decision_records,
            "readiness_gap_prompts": decisions,
            "summary": governance_summary
        },
        "outstanding_decisions": decisions + [row for row in decision_records if isinstance(row, dict) and row.get("status") == "pending"],
        "reserved_owner_approvals": reserved_approvals,
        "data_quality": {
            "readiness_validation_errors": errors,
            "readiness_validation_warnings": warnings,
            "dependency_map_errors": dependency_report.get("errors", []),
            "operating_framework_errors": operating.get("errors", []),
            "work_queue_errors": work_queue_report.get("errors", []),
            "execution_log_errors": execution_report.get("errors", []),
            "cross_division_integration_errors": integration_report.get("errors", []),
            "governance_link_errors": governance_errors,
            "incident_register_errors": incident_errors,
            "revenue_warnings": revenue["data_quality"]["warnings"],
            "note": "Absence of a record is not proof that work or funds do not exist outside these source files."
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("organization/division-registry.json"))
    parser.add_argument("--readiness", type=Path, default=Path("organization/readiness-register.json"))
    parser.add_argument("--dependencies", type=Path, default=Path("organization/dependency-map.json"))
    parser.add_argument("--operating-framework", type=Path, default=Path("organization/operating-framework.json"))
    parser.add_argument("--work-queue", type=Path, default=Path("organization/work-queue.json"))
    parser.add_argument("--execution-log", type=Path, default=Path("organization/execution-log.json"))
    parser.add_argument("--risk-register", type=Path, default=Path("organization/risk-register.json"))
    parser.add_argument("--decision-register", type=Path, default=Path("organization/decision-register.json"))
    parser.add_argument("--incident-register", type=Path, default=Path("organization/incident-register.json"))
    parser.add_argument("--opportunities", type=Path, default=Path("intelligence/opportunity-tracker.csv"))
    parser.add_argument("--ledger", type=Path, default=Path("finance/revenue-ledger.csv"))
    args = parser.parse_args()
    report = build_dashboard(
        load_json(args.registry), load_json(args.readiness), load_json(args.dependencies),
        load_json(args.operating_framework), read_csv(args.opportunities), read_csv(args.ledger),
        load_json(args.work_queue), load_json(args.execution_log),
        load_json(args.risk_register), load_json(args.decision_register), load_json(args.incident_register)
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["data_quality"]["readiness_validation_errors"] or report["data_quality"]["dependency_map_errors"] or report["data_quality"]["operating_framework_errors"] or report["data_quality"]["work_queue_errors"] or report["data_quality"]["execution_log_errors"] or report["data_quality"]["cross_division_integration_errors"] or report["data_quality"]["governance_link_errors"] or report["data_quality"]["incident_register_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

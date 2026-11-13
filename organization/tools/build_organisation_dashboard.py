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


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_governance_links(work_queue, risk_register, decision_register):
    """Validate risk/decision references without changing source records."""
    errors = []
    tasks = {item.get("id") for item in (work_queue or {}).get("tasks", []) if isinstance(item, dict)}
    risks = risk_register or {"records": []}
    decisions = decision_register or {"records": []}
    risk_rows = risks.get("records", [])
    decision_rows = decisions.get("records", [])
    if not isinstance(risk_rows, list) or not isinstance(decision_rows, list):
        return ["Risk and decision records must be arrays."], {"risk_count": 0, "decision_count": 0, "linked_task_count": 0}
    risk_ids = [row.get("id") for row in risk_rows if isinstance(row, dict)]
    decision_ids = [row.get("id") for row in decision_rows if isinstance(row, dict)]
    if len(risk_ids) != len(risk_rows) or any(not isinstance(value, str) or not value.strip() for value in risk_ids):
        errors.append("Every risk record must be an object with a non-empty string id.")
    if len(decision_ids) != len(decision_rows) or any(not isinstance(value, str) or not value.strip() for value in decision_ids):
        errors.append("Every decision record must be an object with a non-empty string id.")
    if len(set(risk_ids)) != len(risk_ids):
        errors.append("Risk record ids must be unique.")
    if len(set(decision_ids)) != len(decision_ids):
        errors.append("Decision record ids must be unique.")
    risk_id_set, decision_id_set = set(risk_ids), set(decision_ids)
    linked_tasks = set()
    for row in risk_rows:
        if not isinstance(row, dict):
            continue
        for field in ("severity", "status", "description", "division_id", "mitigation", "owner_assignment"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"Risk {row.get('id', '<unknown>')} requires non-empty {field}.")
        for task_id in row.get("related_task_ids", []):
            linked_tasks.add(task_id)
            if task_id not in tasks:
                errors.append(f"Risk {row.get('id')} references unknown task {task_id}.")
        for decision_id in row.get("related_decision_ids", []):
            if decision_id not in decision_id_set:
                errors.append(f"Risk {row.get('id')} references unknown decision {decision_id}.")
    for row in decision_rows:
        if not isinstance(row, dict):
            continue
        for field in ("scope", "status", "impact", "reversibility", "requested_action"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"Decision {row.get('id', '<unknown>')} requires non-empty {field}.")
        for task_id in row.get("related_task_ids", []):
            linked_tasks.add(task_id)
            if task_id not in tasks:
                errors.append(f"Decision {row.get('id')} references unknown task {task_id}.")
        for risk_id in row.get("related_risk_ids", []):
            if risk_id not in risk_id_set:
                errors.append(f"Decision {row.get('id')} references unknown risk {risk_id}.")
        if row.get("status") == "approved" and not row.get("owner_outcome_evidence"):
            errors.append(f"Approved decision {row.get('id')} requires explicit owner outcome evidence.")
    return errors, {"risk_count": len(risk_rows), "decision_count": len(decision_rows), "linked_task_count": len(linked_tasks)}


def build_dashboard(registry, readiness, dependency_map, operating_framework, opportunities, ledger, work_queue=None, execution_log=None, risk_register=None, decision_register=None):
    errors, warnings = validate(registry, readiness)
    dependency_report = build_report(registry, readiness, dependency_map)
    revenue = build_snapshot(opportunities, ledger)
    operating = build_operating_framework_report(registry, operating_framework)
    work_queue_report = build_work_queue_report(registry, work_queue or {"tasks": []})
    execution_report = build_execution_log_report(registry, work_queue or {"tasks": []}, execution_log or {"events": []})
    integration_report = build_division_integration_report(registry, dependency_map, operating_framework)\n    governance_errors, governance_summary = validate_governance_links(work_queue, risk_register, decision_register)

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
        "risk_register": risks,
        "outstanding_decisions": decisions,
        "reserved_owner_approvals": reserved_approvals,
        "data_quality": {
            "readiness_validation_errors": errors,
            "readiness_validation_warnings": warnings,
            "dependency_map_errors": dependency_report.get("errors", []),
            "operating_framework_errors": operating.get("errors", []),
            "work_queue_errors": work_queue_report.get("errors", []),
            "execution_log_errors": execution_report.get("errors", []),
            "cross_division_integration_errors": integration_report.get("errors", []),\n            "governance_link_errors": governance_errors,
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
    parser.add_argument("--execution-log", type=Path, default=Path("organization/execution-log.json"))\n    parser.add_argument("--risk-register", type=Path, default=Path("organization/risk-register.json"))\n    parser.add_argument("--decision-register", type=Path, default=Path("organization/decision-register.json"))
    parser.add_argument("--opportunities", type=Path, default=Path("intelligence/opportunity-tracker.csv"))
    parser.add_argument("--ledger", type=Path, default=Path("finance/revenue-ledger.csv"))
    args = parser.parse_args()
    report = build_dashboard(
        load_json(args.registry), load_json(args.readiness), load_json(args.dependencies),
        load_json(args.operating_framework), read_csv(args.opportunities), read_csv(args.ledger),
        load_json(args.work_queue), load_json(args.execution_log)
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["data_quality"]["readiness_validation_errors"] or report["data_quality"]["dependency_map_errors"] or report["data_quality"]["operating_framework_errors"] or report["data_quality"]["work_queue_errors"] or report["data_quality"]["execution_log_errors"] or report["data_quality"]["cross_division_integration_errors"] or report["data_quality"]["governance_link_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

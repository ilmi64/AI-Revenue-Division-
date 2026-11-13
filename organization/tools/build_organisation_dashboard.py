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


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_dashboard(registry, readiness, dependency_map, operating_framework, opportunities, ledger):
    errors, warnings = validate(registry, readiness)
    dependency_report = build_report(registry, readiness, dependency_map)
    revenue = build_snapshot(opportunities, ledger)
    operating = build_operating_framework_report(registry, operating_framework)

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
        "ai_revenue": revenue,
        "risk_register": risks,
        "outstanding_decisions": decisions,
        "reserved_owner_approvals": reserved_approvals,
        "data_quality": {
            "readiness_validation_errors": errors,
            "readiness_validation_warnings": warnings,
            "dependency_map_errors": dependency_report.get("errors", []),
            "operating_framework_errors": operating.get("errors", []),
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
    parser.add_argument("--opportunities", type=Path, default=Path("intelligence/opportunity-tracker.csv"))
    parser.add_argument("--ledger", type=Path, default=Path("finance/revenue-ledger.csv"))
    args = parser.parse_args()
    report = build_dashboard(
        load_json(args.registry), load_json(args.readiness), load_json(args.dependencies),
        load_json(args.operating_framework), read_csv(args.opportunities), read_csv(args.ledger)
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["data_quality"]["readiness_validation_errors"] or report["data_quality"]["dependency_map_errors"] or report["data_quality"]["operating_framework_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

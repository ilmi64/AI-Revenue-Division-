#!/usr/bin/env python3
"""Generate a read-only cross-division dependency and readiness report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


READY = {"standby", "operational"}


def load(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_report(registry, readiness, dependency_map):
    errors = []
    registry_divisions = {d["id"]: d for d in registry.get("divisions", [])}
    assessments = {a["division_id"]: a for a in readiness.get("division_assessments", [])}
    dependency_entries = dependency_map.get("divisions", [])
    mapped_ids = [d.get("division_id") for d in dependency_entries]
    if len(mapped_ids) != len(set(mapped_ids)):
        errors.append("Duplicate division dependency entries")
    if set(mapped_ids) != set(registry_divisions):
        errors.append("Dependency map division IDs do not match division registry IDs")
    for entry in dependency_entries:
        division_id = entry.get("division_id")
        if division_id not in registry_divisions:
            errors.append(f"Unknown division in dependency map: {division_id}")
            continue
        for dependency in entry.get("depends_on", []):
            provider = dependency.get("division_id")
            if provider not in registry_divisions:
                errors.append(f"{division_id}: unknown dependency provider {provider}")
            if provider == division_id:
                errors.append(f"{division_id}: self-dependency is not allowed")
            if dependency.get("type") not in {"required", "supporting"}:
                errors.append(f"{division_id}: dependency {provider} has invalid type")
    if errors:
        return {"schema_version": 1, "errors": errors, "divisions": []}

    rows = []
    for entry in dependency_entries:
        division_id = entry["division_id"]
        assessment = assessments.get(division_id, {})
        current_status = assessment.get("verified_status", registry_divisions[division_id].get("status", "unassessed"))
        dependency_results = []
        blockers = []
        supporting_gaps = []
        for dependency in entry.get("depends_on", []):
            provider = dependency["division_id"]
            provider_assessment = assessments.get(provider, {})
            provider_status = provider_assessment.get(
                "verified_status", registry_divisions[provider].get("status", "unassessed")
            )
            satisfied = provider_status in READY
            result = {
                "provider_division": provider,
                "type": dependency["type"],
                "capability": dependency["capability"],
                "provider_verified_status": provider_status,
                "satisfied": satisfied
            }
            dependency_results.append(result)
            if not satisfied:
                message = f"{provider} is {provider_status}; needs standby/operational evidence"
                if dependency["type"] == "required":
                    blockers.append(message)
                else:
                    supporting_gaps.append(message)
        rows.append({
            "division_id": division_id,
            "division_name": registry_divisions[division_id].get("name", division_id),
            "verified_status": current_status,
            "dependency_status": "blocked" if blockers else ("clear" if not supporting_gaps else "supporting_gaps"),
            "required_blockers": blockers,
            "supporting_gaps": supporting_gaps,
            "dependencies": dependency_results,
            "notes": entry.get("notes", "")
        })
    return {
        "schema_version": 1,
        "policy": "A dependency is satisfied only when its provider has verified standby or operational status. This report does not promote readiness or authorise activity.",
        "division_count": len(rows),
        "blocked_divisions": sum(1 for row in rows if row["dependency_status"] == "blocked"),
        "divisions": rows,
        "errors": []
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("organization/division-registry.json"))
    parser.add_argument("--readiness", type=Path, default=Path("organization/readiness-register.json"))
    parser.add_argument("--dependencies", type=Path, default=Path("organization/dependency-map.json"))
    args = parser.parse_args()
    report = build_report(load(args.registry), load(args.readiness), load(args.dependencies))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

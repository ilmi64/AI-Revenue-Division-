#!/usr/bin/env python3
"""Validate and render the organisation's division operating framework."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {
    "id", "purpose", "responsibilities", "deliverables", "cadence",
    "handoffs", "acceptance_criteria", "owner_assignment", "approval_boundary"
}


def build_report(registry, framework):
    errors = []
    registry_ids = {item.get("id") for item in registry.get("divisions", [])}
    divisions = framework.get("divisions")
    if not isinstance(divisions, list):
        return {"schema_version": 1, "errors": ["framework.divisions must be a list"], "divisions": []}

    ids = [item.get("id") for item in divisions if isinstance(item, dict)]
    if len(ids) != len(divisions):
        errors.append("Every framework division must be an object with an id")
    if len(ids) != len(set(ids)):
        errors.append("Framework division IDs must be unique")
    if set(ids) != registry_ids:
        errors.append("Framework division IDs must exactly match the division registry")

    known = set(ids)
    for item in divisions:
        if not isinstance(item, dict):
            continue
        division_id = item.get("id", "<missing>")
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            errors.append(f"{division_id}: missing required fields: {', '.join(sorted(missing))}")
            continue
        for field in ("responsibilities", "deliverables", "acceptance_criteria"):
            if not isinstance(item[field], list) or not item[field]:
                errors.append(f"{division_id}: {field} must be a non-empty list")
        if not isinstance(item["cadence"], dict) or not item["cadence"]:
            errors.append(f"{division_id}: cadence must be a non-empty object")
        if not isinstance(item["handoffs"], list):
            errors.append(f"{division_id}: handoffs must be a list")
        else:
            for handoff in item["handoffs"]:
                target = handoff.get("to")
                if target != "all" and target not in known:
                    errors.append(f"{division_id}: handoff references unknown division {target!r}")
                if not handoff.get("artifact") or not handoff.get("trigger"):
                    errors.append(f"{division_id}: each handoff needs an artifact and trigger")
        if not item.get("owner_assignment"):
            errors.append(f"{division_id}: owner_assignment must be explicit, including pending confirmation")
        if not item.get("approval_boundary"):
            errors.append(f"{division_id}: approval_boundary must be explicit")

    rows = []
    registry_by_id = {item["id"]: item for item in registry.get("divisions", [])}
    for item in divisions:
        if not isinstance(item, dict):
            continue
        registry_item = registry_by_id.get(item.get("id"), {})
        rows.append({
            "division_id": item.get("id"),
            "division_name": registry_item.get("name", item.get("id")),
            "registry_status": registry_item.get("status", "unassessed"),
            "responsibility_count": len(item.get("responsibilities", [])),
            "deliverable_count": len(item.get("deliverables", [])),
            "reporting_cadences": list(item.get("cadence", {}).keys()),
            "handoff_count": len(item.get("handoffs", [])),
            "acceptance_criteria_count": len(item.get("acceptance_criteria", [])),
            "owner_assignment": item.get("owner_assignment"),
            "approval_boundary": item.get("approval_boundary")
        })

    return {
        "schema_version": 1,
        "framework_status": framework.get("framework_status", "unspecified"),
        "policy": framework.get("policy", ""),
        "division_count": len(rows),
        "validated": not errors,
        "divisions": rows,
        "errors": errors
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("organization/division-registry.json"))
    parser.add_argument("--framework", type=Path, default=Path("organization/operating-framework.json"))
    args = parser.parse_args()
    try:
        with args.registry.open("r", encoding="utf-8") as handle:
            registry = json.load(handle)
        with args.framework.open("r", encoding="utf-8") as handle:
            framework = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = build_report(registry, framework)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

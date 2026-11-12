#!/usr/bin/env python3
"""Validate the Organisation Control Centre's division and readiness records.

Standard-library only. This is a local data-integrity gate, not proof that a
division is operational. Elevated readiness requires explicit per-check evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DIVISION_STATUSES = {"planned", "building", "testing", "standby", "operational", "deferred"}
READINESS_STATUSES = DIVISION_STATUSES


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc


def validate(registry, readiness):
    errors, warnings = [], []
    divisions = registry.get("divisions")
    assessments = readiness.get("division_assessments")
    checks = readiness.get("checks")
    if not isinstance(divisions, list):
        return ["registry.divisions must be a list"], warnings
    if not isinstance(assessments, list):
        return ["readiness.division_assessments must be a list"], warnings
    if not isinstance(checks, list):
        return ["readiness.checks must be a list"], warnings

    ids = [d.get("id") for d in divisions if isinstance(d, dict)]
    if len(ids) != len(divisions):
        errors.append("Every division entry must be an object with an id")
    if len(ids) != len(set(ids)):
        errors.append("Division ids must be unique")
    known = set(ids)
    check_ids = [c.get("id") for c in checks if isinstance(c, dict)]
    if len(check_ids) != len(checks) or len(check_ids) != len(set(check_ids)):
        errors.append("Readiness check ids must be present and unique")

    assessment_ids = []
    for item in assessments:
        if not isinstance(item, dict):
            errors.append("Every division assessment must be an object")
            continue
        division_id = item.get("division_id")
        assessment_ids.append(division_id)
        if division_id not in known:
            errors.append(f"Assessment references unknown division: {division_id}")
        status = item.get("verified_status")
        if status not in READINESS_STATUSES:
            errors.append(f"{division_id}: invalid verified_status {status!r}")
        if item.get("claimed_status") not in READINESS_STATUSES:
            errors.append(f"{division_id}: invalid claimed_status")
        if not isinstance(item.get("evidence"), list) or not isinstance(item.get("open_gaps"), list):
            errors.append(f"{division_id}: evidence and open_gaps must be lists")
        if status in {"standby", "operational"}:
            results = item.get("check_results")
            if not isinstance(results, dict):
                errors.append(f"{division_id}: {status} blocked; explicit check_results are missing")
                continue
            required = {
                c["id"] for c in checks
                if status in c.get("required_for", [])
            }
            missing = required - set(results)
            if missing:
                errors.append(f"{division_id}: {status} blocked; missing check results: {', '.join(sorted(missing))}")
            for check_id in required & set(results):
                result = results[check_id]
                if not isinstance(result, dict) or result.get("status") != "passed" or not result.get("evidence"):
                    errors.append(f"{division_id}: {status} blocked; {check_id} lacks passed status or evidence")
            if item.get("open_gaps"):
                errors.append(f"{division_id}: {status} blocked while open_gaps remain")

    if len(assessment_ids) != len(set(assessment_ids)):
        errors.append("There must be at most one assessment per division")
    missing_assessments = known - set(assessment_ids)
    if missing_assessments:
        warnings.append("No readiness assessment yet for: " + ", ".join(sorted(missing_assessments)))

    for division in divisions:
        if not isinstance(division, dict):
            continue
        status = division.get("status")
        if status not in DIVISION_STATUSES:
            errors.append(f"{division.get('id')}: invalid registry status {status!r}")
        for dependency in division.get("supports", []):
            if dependency not in known and dependency != "all":
                errors.append(f"{division.get('id')}: unknown supports reference {dependency!r}")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("organization/division-registry.json"))
    parser.add_argument("--readiness", type=Path, default=Path("organization/readiness-register.json"))
    args = parser.parse_args()
    try:
        registry = load_json(args.registry)
        readiness = load_json(args.readiness)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors, warnings = validate(registry, readiness)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS: registry and readiness records are structurally valid ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

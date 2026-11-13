#!/usr/bin/env python3
"""Validate the proposed organisation-wide division work queue."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALID_STATUS = {"proposed", "ready", "blocked", "in_progress", "completed", "cancelled"}
VALID_EXECUTION = {"not_started", "in_progress", "done", "paused"}
REQUIRED = {
    "id", "division_id", "title", "objective", "priority", "depends_on",
    "required_evidence", "acceptance_criteria", "approval_gate",
    "owner_assignment", "status", "execution_state", "completion_evidence",
    "completed_at"
}


def build_report(registry, queue):
    errors = []
    registry_ids = {item.get("id") for item in registry.get("divisions", [])}
    tasks = queue.get("tasks")
    if not isinstance(tasks, list):
        return {"schema_version": 1, "validated": False,
                "errors": ["work_queue.tasks must be a list"], "tasks": []}

    ids = []
    for task in tasks:
        if isinstance(task, dict):
            ids.append(task.get("id"))
        else:
            errors.append("Every task must be an object")
    if len(ids) != len(set(ids)):
        errors.append("Task IDs must be unique")
    if any(not task_id for task_id in ids):
        errors.append("Every task must have a non-empty id")

    by_id = {task.get("id"): task for task in tasks if isinstance(task, dict) and task.get("id")}
    graph = {}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = task.get("id", "<missing>")
        missing = REQUIRED - set(task)
        if missing:
            errors.append(f"{task_id}: missing fields: {', '.join(sorted(missing))}")
            continue
        if task.get("division_id") not in registry_ids:
            errors.append(f"{task_id}: unknown division {task.get('division_id')!r}")
        if task.get("status") not in VALID_STATUS:
            errors.append(f"{task_id}: invalid status {task.get('status')!r}")
        if task.get("execution_state") not in VALID_EXECUTION:
            errors.append(f"{task_id}: invalid execution_state {task.get('execution_state')!r}")
        if task.get("priority") not in {"critical", "high", "medium", "low"}:
            errors.append(f"{task_id}: invalid priority")
        for field in ("depends_on", "required_evidence", "acceptance_criteria", "completion_evidence"):
            if not isinstance(task.get(field), list):
                errors.append(f"{task_id}: {field} must be a list")
        if not task.get("title") or not task.get("objective") or not task.get("approval_gate"):
            errors.append(f"{task_id}: title, objective and approval_gate must be explicit")
        if not task.get("owner_assignment"):
            errors.append(f"{task_id}: owner_assignment must be explicit")
        graph[task_id] = task.get("depends_on", []) if isinstance(task.get("depends_on"), list) else []
        if task.get("status") == "completed":
            if task.get("execution_state") != "done" or not task.get("completion_evidence") or not task.get("completed_at"):
                errors.append(f"{task_id}: completed tasks require done state, evidence and completed_at")
        if task.get("status") == "in_progress":
            if task.get("execution_state") != "in_progress" or task.get("owner_assignment") == "unassigned_pending_owner_confirmation":
                errors.append(f"{task_id}: in-progress tasks require an assigned owner and in_progress execution_state")
        if task.get("status") == "ready" and task.get("owner_assignment") == "unassigned_pending_owner_confirmation":
            errors.append(f"{task_id}: ready tasks require an assigned owner")

    for task_id, dependencies in graph.items():
        for dependency_id in dependencies:
            if dependency_id not in by_id:
                errors.append(f"{task_id}: references unknown dependency {dependency_id!r}")
            if dependency_id == task_id:
                errors.append(f"{task_id}: task cannot depend on itself")

    visiting, visited = set(), set()
    def visit(task_id):
        if task_id in visiting:
            errors.append(f"Dependency cycle detected at {task_id}")
            return
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency_id in graph.get(task_id, []):
            if dependency_id in graph:
                visit(dependency_id)
        visiting.remove(task_id)
        visited.add(task_id)
    for task_id in graph:
        visit(task_id)

    rows = []
    completed_ids = {task_id for task_id, task in by_id.items()
                     if task.get("status") == "completed" and task.get("execution_state") == "done"
                     and task.get("completion_evidence") and task.get("completed_at")}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = task.get("id")
        dependencies = task.get("depends_on", [])
        unresolved = [dep for dep in dependencies if dep not in completed_ids]
        computed_status = task.get("status", "invalid")
        if computed_status not in {"completed", "cancelled"} and unresolved:
            computed_status = "blocked"
        rows.append({
            "task_id": task_id,
            "division_id": task.get("division_id"),
            "title": task.get("title"),
            "priority": task.get("priority"),
            "recorded_status": task.get("status"),
            "computed_status": computed_status,
            "execution_state": task.get("execution_state"),
            "owner_assignment": task.get("owner_assignment"),
            "unresolved_dependencies": unresolved,
            "approval_gate": task.get("approval_gate")
        })

    division_rows = []
    for division in registry.get("divisions", []):
        division_id = division.get("id")
        selected = [row for row in rows if row["division_id"] == division_id]
        division_rows.append({
            "division_id": division_id,
            "task_count": len(selected),
            "proposed_count": sum(row["recorded_status"] == "proposed" for row in selected),
            "blocked_count": sum(row["computed_status"] == "blocked" for row in selected),
            "in_progress_count": sum(row["recorded_status"] == "in_progress" for row in selected),
            "completed_count": sum(row["recorded_status"] == "completed" for row in selected),
            "unassigned_count": sum(row["owner_assignment"] == "unassigned_pending_owner_confirmation" for row in selected)
        })

    return {
        "schema_version": 1,
        "queue_status": queue.get("queue_status", "unspecified"),
        "policy": queue.get("policy", ""),
        "validated": not errors,
        "task_count": len(rows),
        "completed_count": sum(row["recorded_status"] == "completed" for row in rows),
        "in_progress_count": sum(row["recorded_status"] == "in_progress" for row in rows),
        "blocked_count": sum(row["computed_status"] == "blocked" for row in rows),
        "unassigned_count": sum(row["owner_assignment"] == "unassigned_pending_owner_confirmation" for row in rows),
        "divisions": division_rows,
        "tasks": rows,
        "errors": errors
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("organization/division-registry.json"))
    parser.add_argument("--queue", type=Path, default=Path("organization/work-queue.json"))
    args = parser.parse_args()
    try:
        with args.registry.open("r", encoding="utf-8") as handle:
            registry = json.load(handle)
        with args.queue.open("r", encoding="utf-8") as handle:
            queue = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = build_report(registry, queue)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

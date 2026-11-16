"""Prepare bounded task packets without assigning owners or dispatching work."""
from __future__ import annotations


def build_dispatch_report(registry, queue, role_registry, queue_report=None):
    """Create read-only work packets; this function never assigns or executes tasks."""
    errors = []
    divisions = {
        item.get("id"): item for item in registry.get("divisions", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    roles = {
        item.get("id"): item for item in role_registry.get("roles", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    role_map = role_registry.get("division_role_map", {})
    if not isinstance(role_map, dict) or set(role_map) != set(divisions):
        errors.append("division_role_map must cover every registered division exactly")
        role_map = role_map if isinstance(role_map, dict) else {}
    for division_id, role_id in role_map.items():
        if division_id not in divisions:
            errors.append(f"role map references unknown division {division_id}")
        if role_id not in roles:
            errors.append(f"division {division_id} references unknown role {role_id}")

    tasks = queue.get("tasks", []) if isinstance(queue, dict) else None
    if not isinstance(tasks, list):
        return {
            "schema_version": 1, "status": "invalid", "task_count": 0,
            "prepared_count": 0, "blocked_count": 0, "unassigned_count": 0,
            "dispatch_count": 0, "execution_authority": "none",
            "tasks": [], "errors": errors + ["work queue tasks must be a list"]
        }

    queue_rows = {
        row.get("task_id"): row for row in (queue_report or {}).get("tasks", [])
        if isinstance(row, dict) and isinstance(row.get("task_id"), str)
    }
    packets = []
    seen = set()
    for task in tasks:
        if not isinstance(task, dict):
            errors.append("Every dispatch source task must be an object")
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            errors.append("Every dispatch source task requires a stable ID")
            continue
        if task_id in seen:
            errors.append(f"Duplicate dispatch task ID: {task_id}")
            continue
        seen.add(task_id)
        division_id = task.get("division_id")
        if division_id not in divisions:
            errors.append(f"{task_id}: unknown division {division_id!r}")
        role_id = role_map.get(division_id)
        if role_id not in roles:
            errors.append(f"{task_id}: no valid bounded role template for division")
        queue_state = queue_rows.get(task_id, {})
        unresolved = queue_state.get("unresolved_dependencies", [])
        if not isinstance(unresolved, list):
            unresolved = []
            errors.append(f"{task_id}: unresolved dependency data is invalid")
        if task.get("status") == "cancelled":
            dispatch_status = "cancelled_not_dispatched"
        elif unresolved:
            dispatch_status = "blocked_by_unresolved_dependencies"
        else:
            dispatch_status = "prepared_waiting_for_owner_confirmation"
        packets.append({
            "task_id": task_id,
            "division_id": division_id,
            "division_name": divisions.get(division_id, {}).get("name"),
            "title": task.get("title"),
            "objective": task.get("objective"),
            "role_template_id": role_id,
            "role_template_authority": roles.get(role_id, {}).get("authority"),
            "owner_status": "unassigned_pending_owner_confirmation",
            "named_owner": None,
            "dispatch_status": dispatch_status,
            "recorded_task_status": task.get("status"),
            "unresolved_dependencies": unresolved,
            "inputs_required": task.get("required_evidence", []),
            "output_contract": task.get("acceptance_criteria", []),
            "approval_gate": task.get("approval_gate"),
            "approval_state": "not_requested",
            "risk_class": "unassessed",
            "evidence": [],
            "handoff_acknowledgements": {
                "sending_division": "not_acknowledged",
                "receiving_division": "not_acknowledged"
            },
            "dispatch_state": "not_dispatched",
            "execution_authority": "none",
            "can_execute": False
        })

    prepared = sum(p["dispatch_status"] == "prepared_waiting_for_owner_confirmation" for p in packets)
    blocked = sum(p["dispatch_status"] == "blocked_by_unresolved_dependencies" for p in packets)
    unassigned = sum(p["owner_status"] == "unassigned_pending_owner_confirmation" for p in packets)
    return {
        "schema_version": 1,
        "status": "validated" if not errors else "invalid",
        "policy": "Read-only packet preparation only. No task is assigned, dispatched, executed, approved, or completed by this report. Named ownership, receiving acknowledgement, evidence review and any required owner approval remain separate gates.",
        "task_count": len(packets),
        "prepared_count": prepared,
        "blocked_count": blocked,
        "unassigned_count": unassigned,
        "dispatch_count": 0,
        "execution_authority": "none",
        "tasks": packets,
        "errors": errors
    }

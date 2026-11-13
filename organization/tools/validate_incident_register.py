#!/usr/bin/env python3
"""Validate evidence-backed incident and corrective-action records."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

INCIDENT_STATUSES = {"reported", "triaged", "contained", "recovering", "monitoring", "closed", "unassessed"}
ACTION_STATUSES = {"proposed", "assigned", "in_progress", "blocked", "completed", "deferred_pending_owner_approval"}
SEVERITIES = {"critical", "high", "medium", "low", "unassessed"}

def owner_confirmed(value):
    return isinstance(value, str) and (value == "owner-confirmed" or value.startswith("owner-confirmed:") or value.startswith("owner_confirmed:"))

def validate(register, risk_register, decision_register, work_queue, registry):
    errors = []
    if not isinstance(register, dict):
        return ["Incident register root must be an object."]
    rows = register.get("records")
    if not isinstance(rows, list):
        return ["Incident register records must be an array."]
    if not isinstance(risk_register, dict):
        errors.append("Risk register root must be an object.")
        risk_register = {"records": []}
    if not isinstance(decision_register, dict):
        errors.append("Decision register root must be an object.")
        decision_register = {"records": []}
    if not isinstance(work_queue, dict):
        errors.append("Work queue root must be an object.")
        work_queue = {"tasks": []}
    if not isinstance(registry, dict):
        errors.append("Division registry root must be an object.")
        registry = {"divisions": []}
    risk_rows = risk_register.get("records", [])
    decision_rows = decision_register.get("records", [])
    task_rows = work_queue.get("tasks", [])
    division_rows = registry.get("divisions", [])
    if not isinstance(risk_rows, list):
        errors.append("Risk register records must be an array.")
        risk_rows = []
    if not isinstance(decision_rows, list):
        errors.append("Decision register records must be an array.")
        decision_rows = []
    if not isinstance(task_rows, list):
        errors.append("Work queue tasks must be an array.")
        task_rows = []
    if not isinstance(division_rows, list):
        errors.append("Division registry divisions must be an array.")
        division_rows = []
    risks = {x.get("id") for x in risk_rows if isinstance(x, dict) and isinstance(x.get("id"), str)}
    decisions = {x.get("id"): x for x in decision_rows if isinstance(x, dict) and isinstance(x.get("id"), str)}
    tasks = {x.get("id") for x in task_rows if isinstance(x, dict) and isinstance(x.get("id"), str)}
    divisions = {x.get("id") for x in division_rows if isinstance(x, dict) and isinstance(x.get("id"), str)}
    seen = set()
    for i, incident in enumerate(rows):
        if not isinstance(incident, dict):
            errors.append(f"Incident at index {i} must be an object.")
            continue
        iid = incident.get("id")
        if not isinstance(iid, str) or not iid.strip():
            errors.append(f"Incident at index {i} requires a non-empty string id.")
            continue
        if iid in seen:
            errors.append(f"Incident ids must be unique: {iid}.")
        seen.add(iid)
        for field in ("summary", "containment_recommendation", "owner_assignment"):
            if not isinstance(incident.get(field), str) or not incident[field].strip():
                errors.append(f"Incident {iid} requires non-empty {field}.")
        if incident.get("severity") not in SEVERITIES:
            errors.append(f"Incident {iid} has invalid severity.")
        status = incident.get("status")
        if status not in INCIDENT_STATUSES:
            errors.append(f"Incident {iid} has invalid status.")
        division = incident.get("affected_division_id")
        if division not in divisions:
            errors.append(f"Incident {iid} references unknown affected division {division!r}.")
        evidence = incident.get("detection_evidence")
        if not isinstance(evidence, list) or not evidence or any(not isinstance(x, str) or not x.strip() for x in evidence):
            errors.append(f"Incident {iid} requires non-empty detection_evidence references.")
        for field, known, label in (("related_risk_ids", risks, "risk"), ("related_task_ids", tasks, "task"), ("related_decision_ids", set(decisions), "decision")):
            values = incident.get(field, [])
            if not isinstance(values, list) or any(not isinstance(x, str) or not x.strip() for x in values):
                errors.append(f"Incident {iid} field {field} must be an array of non-empty strings.")
                continue
            for value in values:
                if value not in known:
                    errors.append(f"Incident {iid} references unknown {label} {value}.")
        actions = incident.get("corrective_actions", [])
        if not isinstance(actions, list):
            errors.append(f"Incident {iid} corrective_actions must be an array.")
            actions = []
        action_ids = set()
        for j, action in enumerate(actions):
            if not isinstance(action, dict):
                errors.append(f"Incident {iid} corrective action at index {j} must be an object.")
                continue
            aid = action.get("id")
            if not isinstance(aid, str) or not aid.strip():
                errors.append(f"Incident {iid} corrective action at index {j} requires a non-empty id.")
                continue
            if aid in action_ids:
                errors.append(f"Incident {iid} corrective action ids must be unique: {aid}.")
            action_ids.add(aid)
            for field in ("description", "owner_assignment", "status"):
                if not isinstance(action.get(field), str) or not action[field].strip():
                    errors.append(f"Corrective action {aid} requires non-empty {field}.")
            astatus = action.get("status")
            if astatus not in ACTION_STATUSES:
                errors.append(f"Corrective action {aid} has invalid status.")
            assigned = owner_confirmed(action.get("owner_assignment"))
            if astatus in {"assigned", "in_progress", "completed"} and not assigned:
                errors.append(f"Corrective action {aid} status {astatus} requires confirmed owner assignment.")
            a_evidence = action.get("completion_evidence", [])
            if not isinstance(a_evidence, list) or any(not isinstance(x, str) or not x.strip() for x in a_evidence):
                errors.append(f"Corrective action {aid} completion_evidence must be an array of non-empty strings.")
                a_evidence = []
            if astatus == "completed" and not a_evidence:
                errors.append(f"Completed corrective action {aid} requires completion evidence.")
            decision_id = action.get("owner_decision_id")
            if decision_id is not None and decision_id not in decisions:
                errors.append(f"Corrective action {aid} references unknown decision {decision_id}.")
            if astatus == "deferred_pending_owner_approval":
                decision = decisions.get(decision_id)
                if not decision or decision.get("status") != "pending":
                    errors.append(f"Deferred corrective action {aid} requires a linked pending owner decision.")
        if status == "closed":
            review = incident.get("post_incident_review_evidence")
            if not isinstance(review, list) or not review or any(not isinstance(x, str) or not x.strip() for x in review):
                errors.append(f"Closed incident {iid} requires post_incident_review_evidence.")
            if any(not isinstance(a, dict) or a.get("status") != "completed" for a in actions):
                errors.append(f"Closed incident {iid} requires every corrective action to be completed; deferrals do not count as closure.")
            approved = any(
                decisions.get(did, {}).get("status") == "approved" and decisions.get(did, {}).get("owner_outcome_evidence")
                for did in incident.get("related_decision_ids", []) if isinstance(did, str)
            )
            if not approved:
                errors.append(f"Closed incident {iid} requires a linked approved owner decision with outcome evidence.")
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incidents", type=Path, default=Path("organization/incident-register.json"))
    parser.add_argument("--risks", type=Path, default=Path("organization/risk-register.json"))
    parser.add_argument("--decisions", type=Path, default=Path("organization/decision-register.json"))
    parser.add_argument("--work-queue", type=Path, default=Path("organization/work-queue.json"))
    parser.add_argument("--registry", type=Path, default=Path("organization/division-registry.json"))
    args = parser.parse_args()
    loaded = [json.loads(p.read_text(encoding="utf-8")) for p in (args.incidents, args.risks, args.decisions, args.work_queue, args.registry)]
    errors = validate(*loaded)
    if errors:
        print("\n".join(errors))
        return 1
    print("Incident register valid.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

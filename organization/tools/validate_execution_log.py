#!/usr/bin/env python3
"""Validate append-only division execution events against the proposed work queue."""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime
from pathlib import Path

EVENT_TYPES = {"started", "progress", "blocked", "paused", "resumed", "completed"}
REQUIRED = {"event_id", "task_id", "event_type", "timestamp", "actor", "summary", "evidence"}

def parse_time(value):
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp must be a non-empty ISO-8601 string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed

def build_report(registry, queue, log):
    errors, rows = [], []
    if not isinstance(registry, dict) or not isinstance(queue, dict) or not isinstance(log, dict):
        return {"schema_version": 1, "validated": False,
                "errors": ["registry, queue and log must each be JSON objects"], "events": []}
    task_records = queue.get("tasks", [])
    division_records = registry.get("divisions", [])
    if not isinstance(task_records, list):
        return {"schema_version": 1, "validated": False, "errors": ["tasks must be a list"], "events": []}
    if not isinstance(division_records, list):
        return {"schema_version": 1, "validated": False, "errors": ["divisions must be a list"], "events": []}
    tasks = {t.get("id"): t for t in task_records
             if isinstance(t, dict) and isinstance(t.get("id"), str) and t.get("id")}
    divisions = {d.get("id") for d in division_records
                 if isinstance(d, dict) and isinstance(d.get("id"), str) and d.get("id")}
    events = log.get("events")
    if not isinstance(events, list):
        return {"schema_version": 1, "validated": False, "errors": ["events must be a list"], "events": []}
    seen, prior, state = set(), {}, {}
    for index, event in enumerate(events):
        prefix = f"event[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        missing = REQUIRED - set(event)
        if missing:
            errors.append(f"{prefix}: missing fields: {', '.join(sorted(missing))}")
            continue
        event_valid = True
        eid, tid, kind = event["event_id"], event["task_id"], event["event_type"]
        if not isinstance(eid, str) or not eid:
            errors.append(f"{prefix}: event_id must be a non-empty string")
            event_valid = False
            label = prefix
        else:
            label = eid
            if eid in seen:
                errors.append(f"{prefix}: event_id must be unique and non-empty")
                event_valid = False
            else:
                seen.add(eid)
        if not isinstance(tid, str) or not tid:
            errors.append(f"{label}: task_id must be a non-empty string")
            continue
        task = tasks.get(tid)
        if task is None:
            errors.append(f"{label}: unknown task {tid!r}")
            continue
        if task.get("division_id") not in divisions:
            errors.append(f"{label}: task has unknown division")
            event_valid = False
        if not isinstance(kind, str) or kind not in EVENT_TYPES:
            errors.append(f"{label}: invalid event_type {kind!r}")
            event_valid = False
        try:
            stamp = parse_time(event["timestamp"])
            if tid in prior and stamp < prior[tid]:
                errors.append(f"{label}: event timestamp precedes the prior event for {tid}")
                event_valid = False
            prior[tid] = stamp
        except (ValueError, TypeError) as exc:
            errors.append(f"{label}: {exc}")
            event_valid = False
        if not isinstance(event["actor"], str) or not event["actor"].strip():
            errors.append(f"{label}: actor is required")
            event_valid = False
        if not isinstance(event["summary"], str) or not event["summary"].strip():
            errors.append(f"{label}: summary is required")
            event_valid = False
        evidence = event["evidence"]
        if not isinstance(evidence, list) or any(not isinstance(x, str) or not x.strip() for x in evidence):
            errors.append(f"{label}: evidence must be a list of non-empty references")
            evidence = []
            event_valid = False
        if kind in {"started", "resumed", "completed"} if isinstance(kind, str) else False:
            if task.get("owner_assignment") == "unassigned_pending_owner_confirmation":
                errors.append(f"{label}: {kind} requires an assigned task owner")
                event_valid = False
        previous = state.get(tid, "not_started")
        allowed = {
            "started": {"not_started", "paused"},
            "progress": {"in_progress"},
            "blocked": {"in_progress", "not_started"},
            "paused": {"in_progress"},
            "resumed": {"paused", "blocked"},
            "completed": {"in_progress"},
        }
        if isinstance(kind, str) and kind in allowed:
            if previous not in allowed[kind]:
                errors.append(f"{label}: {kind} is not allowed after state {previous}")
                event_valid = False
            if kind == "completed" and not evidence:
                errors.append(f"{label}: completed event requires evidence references")
                event_valid = False
            if kind == "resumed" and previous == "blocked" and not evidence:
                errors.append(f"{label}: resuming a blocked task requires evidence that the blocker was resolved")
                event_valid = False
            if event_valid:
                if kind in {"started", "resumed"}:
                    state[tid] = "in_progress"
                elif kind == "blocked":
                    state[tid] = "blocked"
                elif kind == "paused":
                    state[tid] = "paused"
                elif kind == "completed":
                    state[tid] = "completed"
        rows.append({"event_id": eid if isinstance(eid, str) else label, "task_id": tid,
                     "division_id": task.get("division_id"), "event_type": kind if isinstance(kind, str) else "invalid",
                     "timestamp": event["timestamp"], "summary": event["summary"],
                     "evidence_count": len(evidence)})
    by_division = []
    for did in sorted(divisions):
        selected = [r for r in rows if r["division_id"] == did]
        by_division.append({"division_id": did, "event_count": len(selected),
                            "started_events": sum(x["event_type"] == "started" for x in selected),
                            "progress_events": sum(x["event_type"] == "progress" for x in selected),
                            "blocked_events": sum(x["event_type"] == "blocked" for x in selected),
                            "completed_events": sum(x["event_type"] == "completed" for x in selected)})
    return {"schema_version": 1, "validated": not errors, "event_count": len(rows),
            "task_state_from_events": state, "divisions": by_division, "events": rows, "errors": errors}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("organization/division-registry.json"))
    parser.add_argument("--queue", type=Path, default=Path("organization/work-queue.json"))
    parser.add_argument("--log", type=Path, default=Path("organization/execution-log.json"))
    args = parser.parse_args()
    try:
        registry, queue, log = [json.loads(p.read_text(encoding="utf-8")) for p in (args.registry, args.queue, args.log)]
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = build_report(registry, queue, log)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["validated"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

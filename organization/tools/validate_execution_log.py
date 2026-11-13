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
    tasks = {t.get("id"): t for t in queue.get("tasks", []) if isinstance(t, dict)}
    divisions = {d.get("id") for d in registry.get("divisions", [])}
    events = log.get("events")
    if not isinstance(events, list):
        return {"schema_version": 1, "validated": False, "errors": ["events must be a list"], "events": []}
    seen, prior, state = set(), {}, {}
    for index, event in enumerate(events):
        prefix = f"event[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix}: must be an object"); continue
        missing = REQUIRED - set(event)
        if missing:
            errors.append(f"{prefix}: missing fields: {', '.join(sorted(missing))}"); continue
        eid, tid, kind = event["event_id"], event["task_id"], event["event_type"]
        if not isinstance(eid, str) or not eid or eid in seen:
            errors.append(f"{prefix}: event_id must be unique and non-empty")
        seen.add(eid)
        task = tasks.get(tid)
        if task is None:
            errors.append(f"{eid}: unknown task {tid!r}"); continue
        if task.get("division_id") not in divisions:
            errors.append(f"{eid}: task has unknown division")
        if kind not in EVENT_TYPES:
            errors.append(f"{eid}: invalid event_type {kind!r}")
        try:
            stamp = parse_time(event["timestamp"])
            if tid in prior and stamp < prior[tid]:
                errors.append(f"{eid}: event timestamp precedes the prior event for {tid}")
            prior[tid] = stamp
        except (ValueError, TypeError) as exc:
            errors.append(f"{eid}: {exc}")
        if not isinstance(event["actor"], str) or not event["actor"].strip():
            errors.append(f"{eid}: actor is required")
        if not isinstance(event["summary"], str) or not event["summary"].strip():
            errors.append(f"{eid}: summary is required")
        evidence = event["evidence"]
        if not isinstance(evidence, list) or any(not isinstance(x, str) or not x.strip() for x in evidence):
            errors.append(f"{eid}: evidence must be a list of non-empty references")
            evidence = []
        if kind in {"started", "resumed", "completed"} and task.get("owner_assignment") == "unassigned_pending_owner_confirmation":
            errors.append(f"{eid}: {kind} requires an assigned task owner")
        previous = state.get(tid, "not_started")
        allowed = {
            "started": {"not_started", "paused"},
            "progress": {"in_progress"},
            "blocked": {"in_progress", "not_started"},
            "paused": {"in_progress"},
            "resumed": {"paused"},
            "completed": {"in_progress"},
        }
        if kind in allowed and previous not in allowed[kind]:
            errors.append(f"{eid}: {kind} is not allowed after state {previous}")
        if kind == "completed" and not evidence:
            errors.append(f"{eid}: completed event requires evidence references")
        if kind in {"started", "resumed"}: state[tid] = "in_progress"
        elif kind == "blocked": state[tid] = "blocked"
        elif kind == "paused": state[tid] = "paused"
        elif kind == "completed": state[tid] = "completed"
        rows.append({"event_id": eid, "task_id": tid, "division_id": task.get("division_id"),
                     "event_type": kind, "timestamp": event["timestamp"], "summary": event["summary"],
                     "evidence_count": len(evidence)})
    by_division = []
    for did in sorted(x for x in divisions if x):
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
        print(f"ERROR: {exc}", file=sys.stderr); return 2
    report = build_report(registry, queue, log)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["validated"] else 1
if __name__ == "__main__":
    raise SystemExit(main())

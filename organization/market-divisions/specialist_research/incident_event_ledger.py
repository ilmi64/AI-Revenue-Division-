"""Append-only OCC incident, veto, handover and corrective-action event ledger.

Offline JSONL, single-writer. Stop state is monotonic: this ledger records
stop-clearance requests as evidence only; it has no stop-clearance operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GENESIS = "0" * 64
AUTHORITY = "research_only_no_execution_authority"
EVENT_TYPES = {
    "incident_opened",
    "stop_raised",
    "stop_challenged",
    "corrective_action_proposed",
    "corrective_action_verified",
    "recovery_evidence_added",
    "handover_recorded",
    "stop_clearance_requested",
    "incident_closed",
}
REQUIRES_EVIDENCE = {
    "stop_raised", "stop_challenged", "corrective_action_verified",
    "recovery_evidence_added", "handover_recorded", "stop_clearance_requested",
}


class EventLedgerError(ValueError):
    pass


def canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise EventLedgerError("event is not canonical JSON data") from exc


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise EventLedgerError(f"{field} must be ISO-8601 UTC ending Z")
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise EventLedgerError(f"{field} is invalid") from exc
    if result.utcoffset() != timezone.utc.utcoffset(result):
        raise EventLedgerError(f"{field} must be UTC")
    return result


def validate_event(event: dict[str, Any]) -> None:
    if not isinstance(event, dict):
        raise EventLedgerError("event must be an object")
    required = ("event_id", "event_type", "occurred_at_utc", "recorded_at_utc",
                "actor_id", "subject_id", "summary", "evidence_refs", "details")
    missing = [key for key in required if key not in event]
    if missing:
        raise EventLedgerError("event missing fields: " + ", ".join(missing))
    if not isinstance(event["event_id"], str) or not event["event_id"].strip():
        raise EventLedgerError("event_id must be non-empty")
    if event["event_type"] not in EVENT_TYPES:
        raise EventLedgerError("unsupported event_type")
    if not isinstance(event["actor_id"], str) or not event["actor_id"].strip():
        raise EventLedgerError("actor_id must be non-empty")
    if not isinstance(event["subject_id"], str) or not event["subject_id"].strip():
        raise EventLedgerError("subject_id must be non-empty")
    if not isinstance(event["summary"], str) or not event["summary"].strip():
        raise EventLedgerError("summary must be non-empty")
    occurred = utc(event["occurred_at_utc"], "occurred_at_utc")
    recorded = utc(event["recorded_at_utc"], "recorded_at_utc")
    if recorded < occurred:
        raise EventLedgerError("recorded_at_utc cannot precede occurred_at_utc")
    refs = event["evidence_refs"]
    if not isinstance(refs, list) or any(not isinstance(x, str) or not x.strip() for x in refs):
        raise EventLedgerError("evidence_refs must be an array of non-empty strings")
    if len(refs) != len(set(refs)):
        raise EventLedgerError("evidence_refs must be unique")
    if event["event_type"] in REQUIRES_EVIDENCE and not refs:
        raise EventLedgerError("this event_type requires evidence_refs")
    if not isinstance(event["details"], dict):
        raise EventLedgerError("details must be an object")
    if "trade_authority" in event["details"] and event["details"]["trade_authority"] is not False:
        raise EventLedgerError("event cannot grant trade authority")
    if "live_readiness" in event["details"] and event["details"]["live_readiness"] is not False:
        raise EventLedgerError("event cannot grant live readiness")
    if event["event_type"] == "stop_clearance_requested":
        if event["details"].get("approval_status") not in {"pending", "rejected"}:
            raise EventLedgerError("stop-clearance request must remain pending or rejected")


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise EventLedgerError(f"blank line at {line_number}")
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EventLedgerError(f"invalid JSON at line {line_number}") from exc
            if not isinstance(item, dict):
                raise EventLedgerError(f"event object required at line {line_number}")
            events.append(item)
    return events


def _entry_hash(entry: dict[str, Any]) -> str:
    return digest({key: value for key, value in entry.items() if key != "entry_hash"})


def verify_events(entries: list[dict[str, Any]]) -> dict[str, Any]:
    previous = GENESIS
    errors: list[str] = []
    ids: set[str] = set()
    stop_active = False
    incident_open: dict[str, bool] = {}
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            errors.append(f"row {index}: entry must be object")
            continue
        sequence = entry.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence != index:
            errors.append(f"row {index}: invalid sequence")
        if entry.get("ledger_version") != "1.0.0":
            errors.append(f"row {index}: unsupported ledger_version")
        if entry.get("previous_hash") != previous:
            errors.append(f"row {index}: previous_hash mismatch")
        if entry.get("authority") != AUTHORITY:
            errors.append(f"row {index}: authority marker invalid")
        event = entry.get("event")
        try:
            validate_event(event)
        except EventLedgerError as exc:
            errors.append(f"row {index}: {exc}")
        else:
            if entry.get("event_sha256") != digest(event):
                errors.append(f"row {index}: event digest mismatch")
            event_id = event["event_id"]
            if event_id in ids:
                errors.append(f"row {index}: duplicate event_id")
            ids.add(event_id)
            if event["event_type"] == "stop_raised":
                stop_active = True
            if event["event_type"] == "incident_opened":
                incident_open[event["subject_id"]] = True
            elif event["event_type"] == "incident_closed":
                incident_open[event["subject_id"]] = False
            # stop_challenged, corrective actions, recovery evidence and a
            # clearance request never clear the latched stop.
        if entry.get("entry_hash") != _entry_hash(entry):
            errors.append(f"row {index}: entry_hash mismatch")
        if isinstance(entry.get("entry_hash"), str):
            previous = entry["entry_hash"]
    return {
        "valid": not errors, "errors": errors, "entry_count": len(entries),
        "head_hash": previous, "global_stop_active": stop_active,
        "open_incidents": sorted(key for key, value in incident_open.items() if value),
    }


def append_event(path: Path, event: dict[str, Any]) -> dict[str, Any]:
    validate_event(event)
    entries = read_events(path)
    report = verify_events(entries)
    if not report["valid"]:
        raise EventLedgerError("existing event ledger invalid: " + "; ".join(report["errors"]))
    if any(row["event"]["event_id"] == event["event_id"] for row in entries):
        raise EventLedgerError("duplicate event_id")
    entry = {
        "ledger_version": "1.0.0",
        "sequence": len(entries) + 1,
        "previous_hash": report["head_hash"],
        "event_sha256": digest(event),
        "event": event,
        "authority": AUTHORITY,
    }
    entry["entry_hash"] = _entry_hash(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical(entry) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or append OCC incident/control events")
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--ledger", required=True, type=Path)
    append = sub.add_parser("append")
    append.add_argument("--ledger", required=True, type=Path)
    append.add_argument("--event", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "verify":
            report = verify_events(read_events(args.ledger))
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0 if report["valid"] else 1
        event = json.loads(args.event.read_text(encoding="utf-8"))
        entry = append_event(args.ledger, event)
        print(json.dumps({"appended": True, "sequence": entry["sequence"],
                          "entry_hash": entry["entry_hash"], "trade_authority": False}, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, EventLedgerError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

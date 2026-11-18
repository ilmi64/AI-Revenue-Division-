"""Offline reconciliation of OCC snapshot history and control-event history."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .snapshot_history import HistoryError, read_history, verify_history
    from .incident_event_ledger import EventLedgerError, read_events, verify_events
except ImportError:  # direct script execution from this directory
    from snapshot_history import HistoryError, read_history, verify_history
    from incident_event_ledger import EventLedgerError, read_events, verify_events


def _stop_ids(snapshot: dict[str, Any]) -> tuple[set[str], list[str]]:
    ids: set[str] = set()
    warnings: list[str] = []
    for index, stop in enumerate(snapshot.get("active_stops", [])):
        if not isinstance(stop, dict):
            warnings.append(f"snapshot active_stops[{index}] is not an object")
            continue
        stop_id = stop.get("stop_id")
        if isinstance(stop_id, str) and stop_id.strip():
            if stop_id in ids:
                warnings.append(f"duplicate snapshot stop_id: {stop_id}")
            ids.add(stop_id)
        else:
            warnings.append(f"snapshot active_stops[{index}] has no stop_id; exact event correlation unavailable")
    return ids, warnings


def reconcile(snapshot_records: list[dict[str, Any]],
              event_records: list[dict[str, Any]]) -> dict[str, Any]:
    snapshot_report = verify_history(snapshot_records)
    event_report = verify_events(event_records)
    errors: list[str] = []
    warnings: list[str] = []

    if not snapshot_report["valid"]:
        errors.append("snapshot history integrity failed")
    if not event_report["valid"]:
        errors.append("incident event ledger integrity failed")
    if not snapshot_records:
        errors.append("no snapshot history is available; current OCC state cannot be reconciled")

    latest_snapshot = snapshot_records[-1].get("snapshot") if snapshot_records else None
    if snapshot_records and not isinstance(latest_snapshot, dict):
        errors.append("latest snapshot payload is missing or invalid")
        latest_snapshot = None

    if latest_snapshot is not None and snapshot_report["valid"] and event_report["valid"]:
        snapshot_stop = latest_snapshot["global_stop_active"]
        event_stop = event_report["global_stop_active"]
        if snapshot_stop != event_stop:
            errors.append(
                f"stop-state mismatch: latest snapshot={snapshot_stop}, event ledger={event_stop}"
            )

        snapshot_ids, stop_warnings = _stop_ids(latest_snapshot)
        warnings.extend(stop_warnings)
        raised_ids: set[str] = set()
        for row in event_records:
            event = row["event"]
            if event["event_type"] == "stop_raised":
                stop_id = event["details"].get("stop_id")
                if isinstance(stop_id, str) and stop_id.strip():
                    raised_ids.add(stop_id)
                else:
                    warnings.append(
                        f"stop_raised event {event['event_id']} has no details.stop_id"
                    )

        if snapshot_stop:
            if not snapshot_ids:
                warnings.append("active global stop has no correlatable stop_id")
            for stop_id in sorted(snapshot_ids - raised_ids):
                errors.append(f"snapshot active stop has no matching stop_raised event: {stop_id}")
        for stop_id in sorted(raised_ids - snapshot_ids):
            # Event ledger is monotonic, so a stop raised at any point must
            # remain represented by the latest active snapshot in this model.
            errors.append(f"event-ledger stop is absent from latest snapshot: {stop_id}")

        if not snapshot_stop and raised_ids:
            errors.append("event ledger contains a stop_raised event but latest snapshot reports no active stop")

    elif snapshot_records and (not snapshot_report["valid"] or not event_report["valid"]):
        warnings.append("cross-ledger semantic checks skipped because at least one ledger failed integrity verification")

    return {
        "valid": not errors,
        "status": "consistent" if not errors else "inconsistent",
        "snapshot_history": {
            "valid": snapshot_report["valid"],
            "entry_count": snapshot_report["entry_count"],
            "global_stop_active": snapshot_report["global_stop_active"],
            "head_hash": snapshot_report["head_hash"],
        },
        "event_history": {
            "valid": event_report["valid"],
            "entry_count": event_report["entry_count"],
            "global_stop_active": event_report["global_stop_active"],
            "open_incidents": event_report["open_incidents"],
            "head_hash": event_report["head_hash"],
        },
        "latest_snapshot_id": snapshot_records[-1].get("snapshot_id") if snapshot_records else None,
        "errors": errors,
        "warnings": warnings,
        "authority": "research_only_no_execution_authority",
        "trade_authority": False,
        "live_readiness": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile OCC snapshot and event histories")
    parser.add_argument("--snapshot-history", required=True, type=Path)
    parser.add_argument("--event-ledger", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = reconcile(read_history(args.snapshot_history), read_events(args.event_ledger))
        rendered = json.dumps(result, indent=2, sort_keys=True)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0 if result["valid"] else 1
    except (OSError, HistoryError, EventLedgerError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

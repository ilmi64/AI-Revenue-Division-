"""Offline day/night handover continuity and acknowledgement audit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .incident_event_ledger import EventLedgerError, read_events, verify_events
except ImportError:
    from incident_event_ledger import EventLedgerError, read_events, verify_events

REQUIRED_HANDOVER_FIELDS = (
    "handover_id", "outgoing_shift_id", "incoming_shift_id", "snapshot_id",
    "portfolio_version", "outgoing_acknowledged", "incoming_acknowledged",
    "positions_reconciled", "dependency_health", "active_veto_ids",
    "unresolved_critical_items",
)


def _handover_details(event: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    details = event.get("details")
    if not isinstance(details, dict):
        return None, [f"handover event {event.get('event_id')} details must be an object"]
    errors = []
    for key in REQUIRED_HANDOVER_FIELDS:
        if key not in details:
            errors.append(f"handover event {event.get('event_id')} missing details.{key}")
    return details, errors


def audit_handovers(event_records: list[dict[str, Any]]) -> dict[str, Any]:
    ledger = verify_events(event_records)
    errors: list[str] = []
    warnings: list[str] = []
    if not ledger["valid"]:
        errors.append("incident event ledger integrity failed; handover semantics cannot be trusted")

    handovers = []
    raised_stop_ids: set[str] = set()
    unkeyed_stop_events = False
    if ledger["valid"]:
        for row in event_records:
            event = row["event"]
            if event["event_type"] == "stop_raised":
                stop_id = event["details"].get("stop_id")
                if isinstance(stop_id, str) and stop_id.strip():
                    raised_stop_ids.add(stop_id)
                else:
                    unkeyed_stop_events = True
        for row in event_records:
            event = row["event"]
            if event["event_type"] != "handover_recorded":
                continue
            details, missing = _handover_details(event)
            errors.extend(missing)
            if details is None:
                continue
            handovers.append((event, details))

    seen_handover_ids: set[str] = set()
    seen_transitions: set[tuple[str, str]] = set()
    for event, details in handovers:
        event_id = event["event_id"]
        outgoing = details.get("outgoing_shift_id")
        incoming = details.get("incoming_shift_id")
        if not isinstance(outgoing, str) or not outgoing.strip():
            errors.append(f"handover {event_id}: outgoing_shift_id invalid")
        if not isinstance(incoming, str) or not incoming.strip():
            errors.append(f"handover {event_id}: incoming_shift_id invalid")
        if isinstance(outgoing, str) and isinstance(incoming, str):
            if outgoing == incoming:
                errors.append(f"handover {event_id}: outgoing and incoming shifts must differ")
            transition = (outgoing, incoming)
            if transition in seen_transitions:
                errors.append(f"duplicate handover transition: {outgoing} -> {incoming}")
            seen_transitions.add(transition)

        handover_id = details.get("handover_id")
        if not isinstance(handover_id, str) or not handover_id.strip():
            warnings.append(f"handover event {event_id} has no explicit handover_id")
        elif handover_id in seen_handover_ids:
            errors.append(f"duplicate handover_id: {handover_id}")
        else:
            seen_handover_ids.add(handover_id)

        for key in ("outgoing_acknowledged", "incoming_acknowledged", "positions_reconciled"):
            if details.get(key) is not True:
                errors.append(f"handover {event_id}: {key} is not explicitly true")
        if details.get("dependency_health") != "healthy":
            errors.append(f"handover {event_id}: dependency health is not explicitly healthy")

        vetoes = details.get("active_veto_ids")
        if not isinstance(vetoes, list) or any(not isinstance(x, str) or not x.strip() for x in vetoes):
            errors.append(f"handover {event_id}: active_veto_ids must be an array of non-empty IDs")
        elif vetoes:
            warnings.append(f"handover {event_id}: active vetoes carried forward: {', '.join(sorted(set(vetoes)))}")
        if isinstance(vetoes, list):
            missing_vetoes = raised_stop_ids - set(vetoes)
            if missing_vetoes and not unkeyed_stop_events:
                errors.append(
                    f"handover {event_id}: active stop IDs not carried forward: {', '.join(sorted(missing_vetoes))}"
                )
            elif missing_vetoes:
                warnings.append(
                    f"handover {event_id}: stop-ID carry-forward cannot be fully checked because a stop event lacks an ID"
                )

        critical = details.get("unresolved_critical_items")
        if not isinstance(critical, list) or any(not isinstance(x, str) or not x.strip() for x in critical):
            errors.append(f"handover {event_id}: unresolved_critical_items must be an array of non-empty descriptions")
        elif critical:
            errors.append(f"handover {event_id}: unresolved critical items prevent acceptance")
        if not isinstance(details.get("snapshot_id"), str) or not details["snapshot_id"].strip():
            errors.append(f"handover {event_id}: snapshot_id missing")
        version = details.get("portfolio_version")
        if not isinstance(version, (str, int)) or isinstance(version, bool):
            errors.append(f"handover {event_id}: portfolio_version missing or invalid")

        if not event.get("evidence_refs"):
            errors.append(f"handover {event_id}: evidence references missing")

    if ledger["valid"] and not handovers:
        errors.append("no explicit handover events are recorded; acceptance cannot be inferred")

    # Handover events must describe one continuous chain. A discontinuity is
    # a warning because this offline ledger cannot know whether a shift was
    # intentionally skipped or whether an expected shift record is missing.
    for previous, current in zip(handovers, handovers[1:]):
        prev_event, prev_details = previous
        event, details = current
        prev_incoming = prev_details.get("incoming_shift_id")
        outgoing = details.get("outgoing_shift_id")
        if isinstance(prev_incoming, str) and isinstance(outgoing, str) and prev_incoming != outgoing:
            warnings.append(
                f"handover continuity gap between {prev_event['event_id']} "
                f"(incoming {prev_incoming}) and {event['event_id']} (outgoing {outgoing})"
            )

    return {
        "valid": not errors,
        "status": "accepted" if not errors else "blocked",
        "ledger_integrity_valid": ledger["valid"],
        "handover_count": len(handovers),
        "handover_ids": [d.get("handover_id") for _, d in handovers],
        "errors": errors,
        "warnings": warnings,
        "open_incidents": ledger.get("open_incidents", []),
        "global_stop_active": ledger.get("global_stop_active", False),
        "authority": "research_only_no_execution_authority",
        "trade_authority": False,
        "live_readiness": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OCC day/night handover records")
    parser.add_argument("--event-ledger", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = audit_handovers(read_events(args.event_ledger))
        rendered = json.dumps(result, indent=2, sort_keys=True)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0 if result["valid"] else 1
    except (OSError, EventLedgerError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

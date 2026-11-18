"""Read-only integration of OCC history and handover audits into a snapshot.

The adapter reads local journals, never writes to them, and adds a separate
control-health gate. Audit failures promote the snapshot's research status to
HALT without inventing or clearing a specialist/global-stop event.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

try:
    from .audit_reconciliation import reconcile
    from .handover_reconciliation import audit_handovers
    from .incident_event_ledger import EventLedgerError, read_events
    from .snapshot_history import HistoryError, read_history
except ImportError:
    from audit_reconciliation import reconcile
    from handover_reconciliation import audit_handovers
    from incident_event_ledger import EventLedgerError, read_events
    from snapshot_history import HistoryError, read_history

AUTHORITY = "research_only_no_execution_authority"


def build_control_health(snapshot: dict[str, Any],
                         snapshot_history_path: Path,
                         event_ledger_path: Path) -> dict[str, Any]:
    """Return a copied snapshot enriched with read-only OCC audit results."""
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    if snapshot.get("snapshot_type") != "unified_occ_research_intelligence":
        raise ValueError("unsupported snapshot_type")
    if snapshot.get("trade_authority") is not False or snapshot.get("live_readiness") is not False:
        raise ValueError("control-health integration accepts research-only snapshots")

    enriched = copy.deepcopy(snapshot)
    try:
        snapshot_records = read_history(Path(snapshot_history_path))
        event_records = read_events(Path(event_ledger_path))
        cross_ledger = reconcile(snapshot_records, event_records)
        handover = audit_handovers(event_records)
        read_errors: list[str] = []
    except (OSError, HistoryError, EventLedgerError, ValueError) as exc:
        snapshot_records, event_records = [], []
        cross_ledger = {
            "valid": False, "errors": [f"audit input unavailable or invalid: {exc}"],
            "warnings": [], "snapshot_history": {"valid": False},
            "event_history": {"valid": False, "open_incidents": []},
            "latest_snapshot_id": None,
        }
        handover = {
            "valid": False, "status": "blocked", "handover_count": 0,
            "errors": ["handover audit could not be completed"],
            "warnings": [], "open_incidents": [], "global_stop_active": False,
        }
        read_errors = [str(exc)]

    cross_errors = list(cross_ledger.get("errors", []))
    handover_errors = list(handover.get("errors", []))
    known_snapshot_ids = {
        row.get("snapshot_id") for row in snapshot_records
        if isinstance(row, dict) and isinstance(row.get("snapshot_id"), str)
    }
    for row in event_records:
        event = row.get("event", {}) if isinstance(row, dict) else {}
        if isinstance(event, dict) and event.get("event_type") == "handover_recorded":
            details = event.get("details", {})
            referenced_id = details.get("snapshot_id") if isinstance(details, dict) else None
            if isinstance(referenced_id, str) and referenced_id not in known_snapshot_ids:
                handover_errors.append(
                    f"handover {event.get('event_id')}: snapshot_id does not reference a verified snapshot-history entry"
                )
    warnings = list(cross_ledger.get("warnings", [])) + list(handover.get("warnings", []))
    integrity_ok = bool(cross_ledger.get("snapshot_history", {}).get("valid")) and bool(
        cross_ledger.get("event_history", {}).get("valid"))
    handover_count = handover.get("handover_count", 0)
    handover_status = "not_provided" if handover_count == 0 else (
        "accepted" if handover.get("valid") else "blocked")
    if not integrity_ok or not cross_ledger.get("valid") or not handover.get("valid"):
        status = "HALT_AUDIT"
    elif warnings:
        status = "WARN_AUDIT"
    else:
        status = "PASS_AUDIT"

    stop_ids: set[str] = set()
    for record in snapshot_records:
        snap = record.get("snapshot", {}) if isinstance(record, dict) else {}
        stops = snap.get("active_stops", []) if isinstance(snap, dict) else []
        for stop in stops:
            if isinstance(stop, dict) and isinstance(stop.get("stop_id"), str):
                stop_ids.add(stop["stop_id"])
    for row in event_records:
        event = row.get("event", {}) if isinstance(row, dict) else {}
        if not isinstance(event, dict):
            continue
        details = event.get("details", {})
        if event.get("event_type") == "stop_raised" and isinstance(details, dict):
            stop_id = details.get("stop_id")
            if isinstance(stop_id, str) and stop_id.strip():
                stop_ids.add(stop_id)
        if event.get("event_type") == "handover_recorded" and isinstance(details, dict):
            vetoes = details.get("active_veto_ids", [])
            if isinstance(vetoes, list):
                stop_ids.update(x for x in vetoes if isinstance(x, str) and x.strip())

    unresolved: list[str] = []
    for row in event_records:
        event = row.get("event", {}) if isinstance(row, dict) else {}
        if isinstance(event, dict) and event.get("event_type") == "handover_recorded":
            details = event.get("details", {})
            items = details.get("unresolved_critical_items", []) if isinstance(details, dict) else []
            if isinstance(items, list):
                unresolved.extend(x for x in items if isinstance(x, str))
    continuity_gaps = [x for x in warnings if "continuity gap" in x.lower()]

    enriched["control_health"] = {
        "schema_version": "1.0.0",
        "status": status,
        "snapshot_history_integrity": "valid" if cross_ledger.get("snapshot_history", {}).get("valid") else "invalid_or_missing",
        "event_ledger_integrity": "valid" if cross_ledger.get("event_history", {}).get("valid") else "invalid_or_missing",
        "cross_ledger_consistency": "consistent" if cross_ledger.get("valid") else "inconsistent",
        "handover_acceptance": handover_status,
        "handover_count": handover_count,
        "latest_verified_snapshot_id": cross_ledger.get("latest_snapshot_id"),
        "active_stop_ids": sorted(stop_ids),
        "open_incidents": cross_ledger.get("event_history", {}).get("open_incidents", handover.get("open_incidents", [])),
        "unresolved_critical_items": unresolved,
        "continuity_gaps": continuity_gaps,
        "errors": cross_errors + handover_errors + read_errors,
        "warnings": warnings,
        "authority": AUTHORITY,
        "trade_authority": False,
        "live_readiness": False,
        "limitations": [
            "Audits are offline and read-only; source journals are not modified",
            "A hash chain is an integrity aid, not a signature or tamper-proof storage",
            "No live position, dependency, signer, clock or shift-scheduler verification is performed",
            "HALT_AUDIT is a control-health hold and does not fabricate a stop_raised event",
            "This adapter does not clear, downgrade or replace any specialist or OCC stop",
        ],
    }
    if status == "HALT_AUDIT":
        enriched["status"] = "halt"
        occ = enriched.get("occ")
        if isinstance(occ, dict):
            occ["status"] = "halt"
    return enriched

"""Offline OCC visibility over explicitly assigned company fixture inputs."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from occ_readonly import SnapshotError, VALID_GATE, assess_snapshot, read_fixture


COMMON_SUBSYSTEMS = (
    "main_hub", "ai_workforce", "research_intelligence", "security_controls", "recovery",
)
COMPANY_SUBSYSTEMS = {
    "ai_revenue": ("commercial_operations",),
    "trading_technology": ("polybot", "paper_trading", "risk_controls"),
}
AEVORA_COUNTS = (
    "blocked", "checklist_complete_unverified", "hold", "rejected", "review_ready",
)
_MISSING = object()
_INVALID = object()


def _snapshot_view(snapshot, company_id, now):
    if snapshot is _MISSING:
        return {"input_status": "MISSING", "display_status": "UNKNOWN"}
    try:
        assessed = assess_snapshot(snapshot, company_id, now=now)
    except (SnapshotError, OverflowError):
        # Validation errors can contain raw identifiers or field names.
        return {"input_status": "REJECTED", "display_status": "UNKNOWN"}

    incident = assessed["incident_summary"]
    if incident["quarantined"]:
        return {
            "input_status": "QUARANTINED",
            "display_status": "UNKNOWN",
            "trust": assessed["trust"],
        }
    if assessed["stale"]:
        return {
            "input_status": "STALE",
            "display_status": "STALE",
            "trust": assessed["trust"],
        }

    allowed = COMMON_SUBSYSTEMS + COMPANY_SUBSYSTEMS[company_id]
    if set(snapshot["subsystems"]).difference(allowed):
        return {"input_status": "REJECTED", "display_status": "UNKNOWN"}
    gates = snapshot["gates"]
    return {
        "input_status": "UNVERIFIED",
        "display_status": assessed["display_status"],
        "trust": assessed["trust"],
        "reported_subsystem_statuses": {
            name: snapshot["subsystems"].get(name, "UNKNOWN")
            for name in allowed
        },
        "reported_gate_counts": {
            status: sum(gate["status"] == status for gate in gates)
            for status in sorted(VALID_GATE)
        },
        "reported_critical_gates_not_passed": len(assessed["critical_gates_not_passed"]),
        "reported_blocker_count": assessed["blocker_count"],
        "reported_incident_count": incident["open_count"],
        "reported_evidence_count": len(assessed["evidence_refs"]),
    }


def _aevora_operations_view(report):
    if report is _MISSING:
        return {"input_status": "MISSING"}
    expected = {
        "organization": "Daivora Group",
        "source_company": "Aevora AI",
        "recipient": "Main Hub/OCC",
        "mode": "read_only_aggregate",
    }
    if (
        not isinstance(report, dict)
        or set(report) != set(expected) | {
            "total", "counts", "execution_authorized", "external_actions_performed",
        }
        or any(report[name] != value for name, value in expected.items())
        or report["execution_authorized"] is not False
        or report["external_actions_performed"] is not False
    ):
        return {"input_status": "REJECTED"}
    counts = report["counts"]
    total = report["total"]
    if (
        not isinstance(counts, dict)
        or set(counts) != set(AEVORA_COUNTS)
        or any(type(count) is not int or count < 0 for count in counts.values())
        or type(total) is not int
        or total != sum(counts.values())
    ):
        return {"input_status": "REJECTED"}
    return {
        "input_status": "UNVERIFIED_UNTIMED",
        "reported_counts": {name: counts[name] for name in AEVORA_COUNTS},
        "reported_total": total,
    }


def build_company_visibility(
    *,
    ai_revenue_snapshot=_MISSING,
    trading_snapshot=_MISSING,
    aevora_operations=_MISSING,
    now=None,
):
    """Summarize separate company inputs. Omitted inputs remain unknown."""
    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime")
    return {
        "mode": "offline_read_only",
        "operational_claim": False,
        "companies": {
            "ai_revenue": {
                "snapshot": _snapshot_view(ai_revenue_snapshot, "ai_revenue", now),
                "operations": _aevora_operations_view(aevora_operations),
            },
            "trading_technology": {
                "snapshot": _snapshot_view(trading_snapshot, "trading_technology", now),
            },
        },
    }


def _read_optional(path):
    if path is None:
        return _MISSING
    try:
        return read_fixture(path)
    except (ValueError, OverflowError):
        return _INVALID


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ai-revenue-snapshot", type=Path)
    parser.add_argument("--trading-snapshot", type=Path)
    parser.add_argument("--aevora-operations", type=Path)
    parser.add_argument("--format", choices=("json", "mobile-html"), default="json")
    args = parser.parse_args()
    report = build_company_visibility(
        ai_revenue_snapshot=_read_optional(args.ai_revenue_snapshot),
        trading_snapshot=_read_optional(args.trading_snapshot),
        aevora_operations=_read_optional(args.aevora_operations),
    )
    if args.format == "mobile-html":
        from occ_mobile_visibility import render_mobile_visibility

        print(render_mobile_visibility(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

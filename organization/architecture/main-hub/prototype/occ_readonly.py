"""Offline, read-only Main Hub/OCC prototype. Synthetic fixtures only; no network or writes."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED = {
    "ai_revenue": "ai-revenue.snapshot.example.json",
    "trading_technology": "trading-technology.snapshot.example.json",
}
VALID_OVERALL = {"HEALTHY", "DEGRADED", "BLOCKED", "UNKNOWN", "STALE"}
VALID_GATE = {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "WAIVED"}


class SnapshotError(ValueError):
    pass


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise SnapshotError("published_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise SnapshotError("published_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def assess_snapshot(snapshot: dict[str, Any], expected_company: str,
                    now: datetime | None = None, max_age_hours: int = 24) -> dict[str, Any]:
    """Validate a narrow allowlist and return a conservative display record."""
    if not isinstance(snapshot, dict):
        raise SnapshotError("snapshot must be an object")
    required = {
        "snapshot_id", "company_id", "schema_version", "source_revision",
        "published_at", "overall_status", "subsystems", "gates", "blockers",
        "incident_summary", "evidence",
    }
    if set(snapshot) != required:
        missing = sorted(required - set(snapshot))
        extra = sorted(set(snapshot) - required)
        raise SnapshotError(f"snapshot field mismatch; missing={missing}; extra={extra}")
    if snapshot["company_id"] != expected_company:
        raise SnapshotError("company identity mismatch")
    if snapshot["schema_version"] != "0.1":
        raise SnapshotError("unsupported schema version")
    if snapshot["overall_status"] not in VALID_OVERALL:
        raise SnapshotError("invalid overall status")
    if not isinstance(snapshot["subsystems"], dict) or not snapshot["subsystems"]:
        raise SnapshotError("subsystems must be a non-empty object")
    if not isinstance(snapshot["gates"], list) or not isinstance(snapshot["blockers"], list):
        raise SnapshotError("gates and blockers must be arrays")
    for gate in snapshot["gates"]:
        if not isinstance(gate, dict) or gate.get("status") not in VALID_GATE:
            raise SnapshotError("invalid gate record")
        if not isinstance(gate.get("critical"), bool):
            raise SnapshotError("gate critical flag must be boolean")

    published = _parse_time(snapshot["published_at"])
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age_hours = (current - published).total_seconds() / 3600
    is_stale = age_hours > max_age_hours or age_hours < -5 / 60
    synthetic = str(snapshot["source_revision"]).startswith("0000000-synthetic")
    critical_not_pass = [
        gate["gate_id"] for gate in snapshot["gates"]
        if gate["critical"] and gate["status"] != "PASS"
    ]

    # No authentication adapter exists in v0.1. Therefore no input is trusted
    # and the effective status cannot be promoted to HEALTHY.
    if synthetic:
        display_status = "UNKNOWN"
        trust = "SYNTHETIC_UNTRUSTED"
    elif is_stale:
        display_status = "STALE"
        trust = "UNAUTHENTICATED"
    else:
        display_status = "UNKNOWN"
        trust = "UNAUTHENTICATED"

    return {
        "company_id": expected_company,
        "snapshot_id": snapshot["snapshot_id"],
        "reported_status": snapshot["overall_status"],
        "display_status": display_status,
        "trust": trust,
        "age_hours": round(age_hours, 2),
        "stale": is_stale,
        "critical_gates_not_passed": critical_not_pass,
        "blocker_count": len(snapshot["blockers"]),
        "incident_summary": snapshot["incident_summary"],
        "evidence_refs": [
            item.get("reference") for item in snapshot["evidence"]
            if isinstance(item, dict) and isinstance(item.get("reference"), str)
        ],
    }


def build_report(fixtures_dir: Path, now: datetime | None = None) -> dict[str, Any]:
    companies = []
    for company_id, filename in EXPECTED.items():
        path = fixtures_dir / filename
        with path.open("r", encoding="utf-8") as handle:
            snapshot = json.load(handle)
        companies.append(assess_snapshot(snapshot, company_id, now=now))
    return {
        "product": "Main Hub / OCC read-only prototype",
        "version": "0.1",
        "mode": "offline_read_only",
        "operational_claim": False,
        "company_count": len(companies),
        "companies": companies,
        "notice": "Synthetic or unauthenticated data is never represented as healthy or operational.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).resolve().parents[1] / "fixtures")
    parser.add_argument("--output", type=Path, help="Optional report path; omitted means stdout only.")
    args = parser.parse_args()
    report = build_report(args.fixtures)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

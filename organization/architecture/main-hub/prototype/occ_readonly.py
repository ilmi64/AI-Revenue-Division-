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
VALID_SUBSYSTEM = VALID_OVERALL | {"NOT_IMPLEMENTED"}
VALID_GATE = {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "WAIVED"}
VALID_SEVERITY = {"low", "medium", "high", "critical"}
VALID_INCIDENT_SEVERITY = VALID_SEVERITY | {"none"}


class SnapshotError(ValueError):
    """Raised when a company snapshot is malformed or outside the allowlist."""


def _keys(record: Any, required: set[str], optional: set[str], label: str) -> None:
    if not isinstance(record, dict):
        raise SnapshotError(f"{label} must be an object")
    missing = required - set(record)
    extra = set(record) - required - optional
    if missing or extra:
        raise SnapshotError(
            f"{label} field mismatch; missing={sorted(missing)}; extra={sorted(extra)}"
        )


def _nonempty_string(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotError(f"{label} must be a non-empty string")


def _unique_ids(records: list[dict[str, Any]], field: str, label: str) -> set[str]:
    seen: set[str] = set()
    for record in records:
        value = record[field]
        if value in seen:
            raise SnapshotError(f"duplicate {label}: {value}")
        seen.add(value)
    return seen


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise SnapshotError("published_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SnapshotError("published_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise SnapshotError("published_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def assess_snapshot(snapshot: dict[str, Any], expected_company: str,
                    now: datetime | None = None, max_age_hours: int = 24) -> dict[str, Any]:
    """Validate a strict snapshot shape and return a conservative display record."""
    required = {
        "snapshot_id", "company_id", "schema_version", "source_revision",
        "published_at", "overall_status", "subsystems", "gates", "blockers",
        "incident_summary", "evidence",
    }
    _keys(snapshot, required, set(), "snapshot")
    if expected_company not in EXPECTED or snapshot["company_id"] != expected_company:
        raise SnapshotError("company identity mismatch")
    if snapshot["schema_version"] != "0.1":
        raise SnapshotError("unsupported schema version")
    _nonempty_string(snapshot["snapshot_id"], "snapshot_id")
    _nonempty_string(snapshot["source_revision"], "source_revision")
    if len(snapshot["source_revision"]) < 7:
        raise SnapshotError("source_revision must contain at least 7 characters")
    if not isinstance(snapshot["overall_status"], str) or snapshot["overall_status"] not in VALID_OVERALL:
        raise SnapshotError("invalid overall status")

    subsystems = snapshot["subsystems"]
    if not isinstance(subsystems, dict) or not subsystems:
        raise SnapshotError("subsystems must be a non-empty object")
    for name, status in subsystems.items():
        _nonempty_string(name, "subsystem name")
        if not isinstance(status, str) or status not in VALID_SUBSYSTEM:
            raise SnapshotError(f"invalid subsystem status for {name}")

    if not isinstance(snapshot["gates"], list) or not isinstance(snapshot["blockers"], list):
        raise SnapshotError("gates and blockers must be arrays")
    if not isinstance(snapshot["evidence"], list):
        raise SnapshotError("evidence must be an array")
    _unique_ids(snapshot["gates"], "gate_id", "gate_id")
    _unique_ids(snapshot["blockers"], "blocker_id", "blocker_id")
    for gate in snapshot["gates"]:
        _keys(gate, {"gate_id", "status", "critical", "evidence_refs"}, {"notes"}, "gate")
        _nonempty_string(gate["gate_id"], "gate_id")
        if not isinstance(gate["status"], str) or gate["status"] not in VALID_GATE or not isinstance(gate["critical"], bool):
            raise SnapshotError("invalid gate status or critical flag")
        if not isinstance(gate["evidence_refs"], list) or not all(
            isinstance(ref, str) and ref.strip() for ref in gate["evidence_refs"]
        ):
            raise SnapshotError("gate evidence_refs must be an array of non-empty strings")
        if len(gate["evidence_refs"]) != len(set(gate["evidence_refs"])):
            raise SnapshotError(f"duplicate evidence reference in gate {gate['gate_id']}")
        if "notes" in gate and not isinstance(gate["notes"], str):
            raise SnapshotError("gate notes must be a string")

    for blocker in snapshot["blockers"]:
        _keys(blocker, {"blocker_id", "severity", "summary"}, set(), "blocker")
        _nonempty_string(blocker["blocker_id"], "blocker_id")
        _nonempty_string(blocker["summary"], "blocker summary")
        if not isinstance(blocker["severity"], str) or blocker["severity"] not in VALID_SEVERITY:
            raise SnapshotError("invalid blocker severity")

    incident = snapshot["incident_summary"]
    _keys(incident, {"open_count", "highest_severity", "quarantined"}, set(), "incident_summary")
    if not isinstance(incident["open_count"], int) or isinstance(incident["open_count"], bool) or incident["open_count"] < 0:
        raise SnapshotError("incident open_count must be a non-negative integer")
    if not isinstance(incident["highest_severity"], str) or incident["highest_severity"] not in VALID_INCIDENT_SEVERITY:
        raise SnapshotError("invalid incident severity")
    if not isinstance(incident["quarantined"], bool):
        raise SnapshotError("incident quarantined must be boolean")

    _unique_ids(snapshot["evidence"], "evidence_id", "evidence_id")
    evidence_ids = {item["evidence_id"] for item in snapshot["evidence"]}
    evidence_refs = []
    for evidence in snapshot["evidence"]:
        _keys(evidence, {"evidence_id", "reference", "evidence_type"}, {"verified_at"}, "evidence")
        _nonempty_string(evidence["evidence_id"], "evidence_id")
        _nonempty_string(evidence["reference"], "evidence reference")
        if not isinstance(evidence["evidence_type"], str) or evidence["evidence_type"] not in {
            "commit", "test_run", "report", "approval_record",
            "deployment_record", "external_source", "other"
        }:
            raise SnapshotError("invalid evidence type")
        if evidence.get("verified_at") is not None:
            _parse_time(evidence["verified_at"])
        evidence_refs.append(evidence["reference"])

    for gate in snapshot["gates"]:
        unresolved = set(gate["evidence_refs"]) - evidence_ids
        if unresolved:
            raise SnapshotError(
                f"gate {gate['gate_id']} references unknown evidence_id(s): {sorted(unresolved)}"
            )

    published = _parse_time(snapshot["published_at"])
    if now is not None and not isinstance(now, datetime):
        raise SnapshotError("now must be a timezone-aware datetime")
    if now is not None and (now.tzinfo is None or now.utcoffset() is None):
        raise SnapshotError("now must include a timezone")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if isinstance(max_age_hours, bool) or not isinstance(max_age_hours, int) or max_age_hours < 0:
        raise SnapshotError("max_age_hours must be a non-negative integer")
    age_hours = (current - published).total_seconds() / 3600
    is_stale = age_hours > max_age_hours or age_hours < -5 / 60
    synthetic = snapshot["source_revision"].startswith("0000000-synthetic")
    critical_not_pass = [
        gate["gate_id"] for gate in snapshot["gates"]
        if gate["critical"] and gate["status"] != "PASS"
    ]

    # No publisher authentication exists yet. Never promote any input to HEALTHY.
    if is_stale:
        display_status = "STALE"
    else:
        display_status = "UNKNOWN"
    trust = "SYNTHETIC_UNTRUSTED" if synthetic else "UNAUTHENTICATED"

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
        "incident_summary": incident,
        "evidence_refs": evidence_refs,
    }


def build_report(fixtures_dir: Path, now: datetime | None = None) -> dict[str, Any]:
    companies = []
    for company_id, filename in EXPECTED.items():
        path = fixtures_dir / filename
        try:
            with path.open("r", encoding="utf-8") as handle:
                snapshot = json.load(handle)
        except OSError as exc:
            raise SnapshotError(f"cannot read fixture {filename}: {exc.strerror or exc}") from exc
        except json.JSONDecodeError as exc:
            raise SnapshotError(
                f"fixture {filename} contains invalid JSON at line {exc.lineno}, column {exc.colno}"
            ) from exc
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
    try:
        report = build_report(args.fixtures)
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (SnapshotError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

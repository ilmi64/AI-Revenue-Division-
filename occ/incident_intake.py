"""Pure, read-only OCC incident snapshot validation and reporting.

This module does not poll divisions, persist incidents, acknowledge or resolve
records, send notifications, or invoke trading/execution capabilities.
"""
from __future__ import annotations

from collections import Counter
import math
from typing import Any, Iterable, Mapping


SEVERITIES = {"INFO", "WARNING", "CRITICAL"}
STATUSES = {"OPEN", "ACKNOWLEDGED", "RESOLVED"}
_SEVERITY_ORDER = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}


class IncidentIntakeError(ValueError):
    """An incoming division incident snapshot is invalid."""


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, TypeError, ValueError):
        return False


def validate_incident(record: Mapping[str, Any], *, now_epoch: float) -> dict[str, Any]:
    """Validate and copy one normalized incident snapshot."""
    if not isinstance(record, Mapping):
        raise IncidentIntakeError("incident must be a mapping")
    required = (
        "source_system", "source_incident_id", "division",
        "severity", "status", "reason_code", "summary",
    )
    for key in required:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise IncidentIntakeError(f"{key} must be a non-empty string")
    severity = record["severity"].upper()
    status = record["status"].upper()
    if severity not in SEVERITIES:
        raise IncidentIntakeError("severity must be INFO, WARNING, or CRITICAL")
    if status not in STATUSES:
        raise IncidentIntakeError("status must be OPEN, ACKNOWLEDGED, or RESOLVED")
    if not _finite_number(now_epoch) or now_epoch < 0:
        raise IncidentIntakeError("now_epoch must be a finite non-negative epoch")

    result = dict(record)
    for key in ("observed_at_epoch", "updated_at_epoch"):
        value = record.get(key)
        if not _finite_number(value) or value < 0:
            raise IncidentIntakeError(f"{key} must be a finite non-negative epoch")
        if value > now_epoch:
            raise IncidentIntakeError(f"{key} cannot be in the future")
        result[key] = float(value)
    if result["updated_at_epoch"] < result["observed_at_epoch"]:
        raise IncidentIntakeError("updated_at_epoch cannot predate observed_at_epoch")
    instrument = record.get("instrument")
    if instrument is not None and (not isinstance(instrument, str) or not instrument.strip()):
        raise IncidentIntakeError("instrument must be omitted or a non-empty string")
    result["severity"] = severity
    result["status"] = status
    result["age_seconds"] = max(0.0, float(now_epoch) - result["observed_at_epoch"])
    return result


def build_incident_report(
    records: Iterable[Mapping[str, Any]], *, now_epoch: float,
    stale_after_seconds: float = 300.0,
) -> dict[str, Any]:
    """Build a deterministic read-only summary from supplied snapshots."""
    if not _finite_number(stale_after_seconds) or stale_after_seconds <= 0:
        raise IncidentIntakeError("stale_after_seconds must be finite and positive")
    if not _finite_number(now_epoch) or now_epoch < 0:
        raise IncidentIntakeError("now_epoch must be a finite non-negative epoch")
    try:
        validated = [validate_incident(item, now_epoch=now_epoch) for item in records]
    except TypeError as exc:
        raise IncidentIntakeError("records must be an iterable of incident mappings") from exc
    seen: set[tuple[str, str]] = set()
    for item in validated:
        key = (item["source_system"], item["source_incident_id"])
        if key in seen:
            raise IncidentIntakeError("duplicate source incident identity in snapshot")
        seen.add(key)

    active = [item for item in validated if item["status"] != "RESOLVED"]
    stale = [item for item in active if item["age_seconds"] >= stale_after_seconds]
    ordered = sorted(
        validated,
        key=lambda item: (
            _SEVERITY_ORDER[item["severity"]],
            0 if item["status"] == "OPEN" else 1 if item["status"] == "ACKNOWLEDGED" else 2,
            item["observed_at_epoch"],
            item["source_system"],
            item["source_incident_id"],
        ),
    )
    return {
        "generated_at_epoch": float(now_epoch),
        "read_only": True,
        "source_record_count": len(validated),
        "active_count": len(active),
        "resolved_count": len(validated) - len(active),
        "stale_active_count": len(stale),
        "severity_counts": dict(Counter(item["severity"] for item in active)),
        "status_counts": dict(Counter(item["status"] for item in validated)),
        "incidents": ordered,
    }

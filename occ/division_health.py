"""Pure, read-only division health snapshot validation and reporting.

Health is deliberately separate from readiness: this module never certifies a
division as operational, production-ready, or approved for live activity.
It does not poll components, persist state, send notifications, or execute work.
"""
from __future__ import annotations

from collections import Counter
import math
from typing import Any, Iterable, Mapping


HEALTH_STATES = {"HEALTHY", "DEGRADED", "FAILED", "UNKNOWN"}
EVIDENCE_LEVELS = {"UNVERIFIED", "ADAPTER_VALIDATED", "SOURCE_VERIFIED"}
_HEALTH_ORDER = {"HEALTHY": 0, "UNKNOWN": 1, "DEGRADED": 2, "FAILED": 3}


class DivisionHealthError(ValueError):
    """A supplied division health snapshot is invalid."""


def _finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, TypeError, ValueError):
        return False


def validate_health_snapshot(
    record: Mapping[str, Any],
    *,
    now_epoch: float,
    stale_after_seconds: float = 300.0,
) -> dict[str, Any]:
    """Validate and copy one caller-supplied health observation.

    Evidence level and source identity remain caller-supplied assertions; this
    validator does not authenticate the source, transport, or evidence.
    """
    if not isinstance(record, Mapping):
        raise DivisionHealthError("health snapshot must be a mapping")
    for key in ("division", "component", "source_system", "health_status"):
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DivisionHealthError(f"{key} must be a non-empty string")

    health_status = record["health_status"].upper()
    if health_status not in HEALTH_STATES:
        raise DivisionHealthError(
            "health_status must be HEALTHY, DEGRADED, FAILED, or UNKNOWN"
        )
    evidence_level = record.get("evidence_level", "UNVERIFIED")
    if not isinstance(evidence_level, str) or evidence_level.upper() not in EVIDENCE_LEVELS:
        raise DivisionHealthError(
            "evidence_level must be UNVERIFIED, ADAPTER_VALIDATED, or SOURCE_VERIFIED"
        )
    if not _finite_number(now_epoch) or now_epoch < 0:
        raise DivisionHealthError("now_epoch must be a finite non-negative epoch")
    if not _finite_number(stale_after_seconds) or stale_after_seconds <= 0:
        raise DivisionHealthError("stale_after_seconds must be finite and positive")

    observed = record.get("observed_at_epoch")
    if not _finite_number(observed) or observed < 0:
        raise DivisionHealthError("observed_at_epoch must be a finite non-negative epoch")
    if observed > now_epoch:
        raise DivisionHealthError("observed_at_epoch cannot be in the future")

    summary = record.get("summary", "")
    if not isinstance(summary, str):
        raise DivisionHealthError("summary must be a string")
    source_reference = record.get("source_reference")
    if source_reference is not None and (
        not isinstance(source_reference, str) or not source_reference.strip()
    ):
        raise DivisionHealthError("source_reference must be omitted or non-empty")

    age = max(0.0, float(now_epoch) - float(observed))
    stale = age >= float(stale_after_seconds)
    result = dict(record)
    result["health_status"] = health_status
    result["evidence_level"] = evidence_level.upper()
    result["observed_at_epoch"] = float(observed)
    result["age_seconds"] = age
    result["stale"] = stale
    # Stale evidence cannot support a healthy effective state.
    result["effective_health_status"] = (
        "UNKNOWN" if stale else health_status
    )
    result["readiness_assessed"] = False
    return result


def build_division_health_report(
    records: Iterable[Mapping[str, Any]],
    *,
    now_epoch: float,
    expected_divisions: Iterable[str] | None = None,
    stale_after_seconds: float = 300.0,
) -> dict[str, Any]:
    """Build a deterministic aggregate health report from supplied snapshots.

    Missing expected divisions count as UNKNOWN. Duplicate
    (division, component, source_system) observations are rejected.
    No status in this report grants operational or live-trading readiness.
    """
    if not _finite_number(now_epoch) or now_epoch < 0:
        raise DivisionHealthError("now_epoch must be a finite non-negative epoch")
    if not _finite_number(stale_after_seconds) or stale_after_seconds <= 0:
        raise DivisionHealthError("stale_after_seconds must be finite and positive")

    try:
        validated = [
            validate_health_snapshot(
                item,
                now_epoch=now_epoch,
                stale_after_seconds=stale_after_seconds,
            )
            for item in records
        ]
    except TypeError as exc:
        raise DivisionHealthError("records must be an iterable of health mappings") from exc

    seen: set[tuple[str, str, str]] = set()
    for item in validated:
        identity = (item["division"], item["component"], item["source_system"])
        if identity in seen:
            raise DivisionHealthError("duplicate division/component/source identity")
        seen.add(identity)

    expected: list[str] = []
    if isinstance(expected_divisions, str):
        raise DivisionHealthError("expected_divisions must be an iterable of names, not a string")
    if expected_divisions is not None:
        try:
            for division in expected_divisions:
                if not isinstance(division, str) or not division.strip():
                    raise DivisionHealthError("expected division names must be non-empty strings")
                if division in expected:
                    raise DivisionHealthError("expected_divisions contains duplicates")
                expected.append(division)
        except TypeError as exc:
            raise DivisionHealthError("expected_divisions must be iterable") from exc

    observed_divisions = {item["division"] for item in validated}
    missing = sorted(set(expected) - observed_divisions)
    effective_states = [item["effective_health_status"] for item in validated]
    if missing:
        effective_states.extend("UNKNOWN" for _ in missing)
    overall = (
        max(effective_states, key=lambda state: _HEALTH_ORDER[state])
        if effective_states else "UNKNOWN"
    )

    ordered = sorted(
        validated,
        key=lambda item: (
            item["division"], item["component"], item["source_system"],
            item["observed_at_epoch"],
        ),
    )
    health_counts = Counter(item["effective_health_status"] for item in ordered)
    if missing:
        health_counts["UNKNOWN"] += len(missing)

    return {
        "generated_at_epoch": float(now_epoch),
        "read_only": True,
        "health_status": overall,
        "readiness_assessed": False,
        "operational_ready": False,
        "source_snapshot_count": len(ordered),
        "division_count": len(observed_divisions),
        "expected_division_count": len(expected),
        "missing_expected_divisions": missing,
        "stale_snapshot_count": sum(1 for item in ordered if item["stale"]),
        "health_counts": dict(health_counts),
        "snapshots": ordered,
        "limitations": [
            "Health is not operational readiness or live-trading approval.",
            "Evidence levels and source identities are caller-supplied and unauthenticated.",
            "Missing expected divisions and stale observations are treated as UNKNOWN.",
        ],
    }

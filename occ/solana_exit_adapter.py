"""Read-only adapter for Solana paper-exit CoordinationStore snapshots.

The adapter depends only on the two documented query methods, not on the
Solana repository's Python package. It never writes to the source store.
"""
from __future__ import annotations

from typing import Any, Protocol

from .incident_intake import build_incident_report


class SolanaExitIncidentSource(Protocol):
    def unresolved_exit_market_data_incidents(self) -> list[dict[str, Any]]: ...
    def unresolved_position_exits(self) -> list[dict[str, Any]]: ...


class SolanaExitAdapterError(ValueError):
    """A source snapshot cannot be mapped without inventing identity/evidence."""


def _required_text(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SolanaExitAdapterError(f"source {key} is missing or invalid")
    return value.strip()


def _required_epoch(record: dict[str, Any], key: str) -> float:
    value = record.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SolanaExitAdapterError(f"source {key} is missing or invalid")
    try:
        return float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise SolanaExitAdapterError(f"source {key} is outside the supported numeric range") from exc


def collect_solana_exit_incidents(
    source: SolanaExitIncidentSource,
    *,
    now_epoch: float,
    stale_after_seconds: float = 300.0,
) -> dict[str, Any]:
    """Read source snapshots, map them to OCC records, and build a report.

    Both source queries are read-only. Source statuses are not changed.
    Severity is CRITICAL by adapter policy: an unresolved exit-mark incident
    or unresolved exit operation means exit safety/reconciliation is uncertain.
    Source workflow statuses are retained as metadata, while OCC status stays
    OPEN because these query APIs do not expose authenticated OCC acknowledgement.
    """
    market_query = getattr(source, "unresolved_exit_market_data_incidents", None)
    exit_query = getattr(source, "unresolved_position_exits", None)
    if not callable(market_query) or not callable(exit_query):
        raise SolanaExitAdapterError("source lacks required read-only query methods")

    market_rows = market_query()
    exit_rows = exit_query()
    if not isinstance(market_rows, list) or not isinstance(exit_rows, list):
        raise SolanaExitAdapterError("source queries must return lists of snapshots")

    normalized: list[dict[str, Any]] = []
    for item in market_rows:
        if not isinstance(item, dict):
            raise SolanaExitAdapterError("market-data source row must be a mapping")
        incident_id = _required_text(item, "incident_id")
        symbol = _required_text(item, "symbol")
        reason = _required_text(item, "reason_code")
        observed = _required_epoch(item, "first_seen_epoch")
        updated = _required_epoch(item, "last_seen_epoch")
        if item.get("status") != "UNRESOLVED":
            raise SolanaExitAdapterError("market-data query returned a non-unresolved row")
        normalized.append({
            "source_system": "solana-paper-exit-market-data",
            "source_incident_id": f"market-data:{incident_id}",
            "division": "Crypto",
            "severity": "CRITICAL",
            "status": "OPEN",
            "reason_code": reason,
            "summary": f"Unresolved paper-exit market-data incident: {reason}",
            "observed_at_epoch": observed,
            "updated_at_epoch": updated,
            "instrument": symbol,
            "source_status": item["status"],
            "source_occurrences": item.get("occurrences", 1),
        })

    for item in exit_rows:
        if not isinstance(item, dict):
            raise SolanaExitAdapterError("position-exit source row must be a mapping")
        operation_id = _required_text(item, "operation_id")
        symbol = _required_text(item, "symbol")
        source_status = _required_text(item, "status")
        if source_status not in {"PENDING", "REVIEW_REQUIRED"}:
            raise SolanaExitAdapterError("position-exit query returned an unsupported status")
        created = _required_epoch(item, "created_at_epoch")
        reason = (
            "EXIT_OPERATION_PENDING_RECONCILIATION"
            if source_status == "PENDING"
            else "EXIT_OPERATION_REVIEW_REQUIRED"
        )
        normalized.append({
            "source_system": "solana-paper-exit-position",
            "source_incident_id": f"position-exit:{operation_id}",
            "division": "Crypto",
            "severity": "CRITICAL",
            "status": "OPEN",
            "reason_code": reason,
            "summary": f"Paper position exit remains unresolved ({source_status})",
            "observed_at_epoch": created,
            "updated_at_epoch": created,
            "instrument": symbol,
            "source_status": source_status,
        })

    return build_incident_report(
        normalized,
        now_epoch=now_epoch,
        stale_after_seconds=stale_after_seconds,
    )

"""Local append-only OCC snapshot history with stop-persistence checks.

This is a single-writer, offline audit aid. SHA-256 detects accidental or
unauthorized edits relative to the recorded chain; it is not a signature,
identity proof, access-control system, or tamper-proof storage.
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


class HistoryError(ValueError):
    """Raised when a snapshot or history ledger fails validation."""


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise HistoryError("record is not canonical JSON data") from exc


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise HistoryError(f"{field} must be an ISO-8601 UTC timestamp ending Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise HistoryError(f"{field} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise HistoryError(f"{field} must be UTC")
    return parsed


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict):
        raise HistoryError("snapshot must be a JSON object")
    required = ("snapshot_type", "generated_at_utc", "status", "mode",
                "active_stops", "global_stop_active", "authority",
                "trade_authority", "live_readiness")
    missing = [key for key in required if key not in snapshot]
    if missing:
        raise HistoryError("snapshot missing required fields: " + ", ".join(missing))
    if snapshot["snapshot_type"] != "unified_occ_research_intelligence":
        raise HistoryError("unsupported snapshot_type")
    if snapshot["status"] not in {"research", "unverified", "halt"}:
        raise HistoryError("unsupported snapshot status")
    if snapshot["mode"] != "research_only":
        raise HistoryError("snapshot mode must be research_only")
    parse_utc(snapshot["generated_at_utc"], "generated_at_utc")
    if snapshot["authority"] != AUTHORITY:
        raise HistoryError("snapshot authority marker invalid")
    if snapshot["trade_authority"] is not False or snapshot["live_readiness"] is not False:
        raise HistoryError("snapshot cannot assert trade authority or live readiness")
    if not isinstance(snapshot["global_stop_active"], bool):
        raise HistoryError("global_stop_active must be boolean")
    if not isinstance(snapshot["active_stops"], list):
        raise HistoryError("active_stops must be an array")
    if snapshot["global_stop_active"] and not snapshot["active_stops"]:
        raise HistoryError("active global stop requires at least one stop record")
    if not snapshot["global_stop_active"] and snapshot["active_stops"]:
        raise HistoryError("inactive global stop cannot contain active stop records")


def _record_hash(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "record_hash"}
    return sha256_json(payload)


def verify_history(records: list[dict[str, Any]]) -> dict[str, Any]:
    previous = GENESIS
    errors: list[str] = []
    seen_snapshot_ids: set[str] = set()
    previous_stop = False

    for expected_sequence, record in enumerate(records, 1):
        if not isinstance(record, dict):
            errors.append(f"row {expected_sequence}: record must be an object")
            continue
        if record.get("sequence") != expected_sequence:
            errors.append(f"row {expected_sequence}: invalid sequence")
        if record.get("previous_hash") != previous:
            errors.append(f"row {expected_sequence}: previous_hash chain mismatch")
        if record.get("authority") != AUTHORITY:
            errors.append(f"row {expected_sequence}: authority marker invalid")
        snapshot = record.get("snapshot")
        try:
            validate_snapshot(snapshot)
        except HistoryError as exc:
            errors.append(f"row {expected_sequence}: {exc}")
        else:
            digest = sha256_json(snapshot)
            if record.get("snapshot_sha256") != digest:
                errors.append(f"row {expected_sequence}: snapshot digest mismatch")
            if previous_stop and snapshot["global_stop_active"] is not True:
                errors.append(f"row {expected_sequence}: prior global stop was cleared")
            previous_stop = snapshot["global_stop_active"]

        snapshot_id = record.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            errors.append(f"row {expected_sequence}: snapshot_id missing")
        elif snapshot_id in seen_snapshot_ids:
            errors.append(f"row {expected_sequence}: duplicate snapshot_id")
        else:
            seen_snapshot_ids.add(snapshot_id)

        try:
            parse_utc(record.get("appended_at_utc"), "appended_at_utc")
        except HistoryError as exc:
            errors.append(f"row {expected_sequence}: {exc}")
        expected_hash = _record_hash(record)
        if record.get("record_hash") != expected_hash:
            errors.append(f"row {expected_sequence}: record_hash mismatch")
        if isinstance(record.get("record_hash"), str):
            previous = record["record_hash"]

    return {
        "valid": not errors,
        "errors": errors,
        "entry_count": len(records),
        "head_hash": previous,
        "global_stop_active": previous_stop,
    }


def read_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise HistoryError(f"{path}: blank line at {line_number}")
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise HistoryError(f"{path}: invalid JSON at line {line_number}") from exc
            if not isinstance(item, dict):
                raise HistoryError(f"{path}: object required at line {line_number}")
            records.append(item)
    return records


def append_snapshot(path: Path, snapshot: dict[str, Any], appended_at_utc: str) -> dict[str, Any]:
    validate_snapshot(snapshot)
    appended_at = parse_utc(appended_at_utc, "appended_at_utc")
    generated_at = parse_utc(snapshot["generated_at_utc"], "generated_at_utc")
    if appended_at < generated_at:
        raise HistoryError("append timestamp cannot precede snapshot generation")

    records = read_history(path)
    report = verify_history(records)
    if not report["valid"]:
        raise HistoryError("existing history is invalid: " + "; ".join(report["errors"]))
    if report["global_stop_active"] and snapshot["global_stop_active"] is not True:
        raise HistoryError("cannot clear a previously recorded global stop in this journal")
    snapshot_id = "occ_" + sha256_json(snapshot)[:24]
    if any(row.get("snapshot_id") == snapshot_id for row in records):
        raise HistoryError("duplicate snapshot; identical snapshot already recorded")

    record = {
        "ledger_version": "1.0.0",
        "sequence": len(records) + 1,
        "previous_hash": report["head_hash"],
        "appended_at_utc": appended_at_utc,
        "snapshot_id": snapshot_id,
        "snapshot_sha256": sha256_json(snapshot),
        "snapshot": snapshot,
        "authority": AUTHORITY,
    }
    record["record_hash"] = _record_hash(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(record) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or append local OCC snapshot history")
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--history", required=True, type=Path)
    append = sub.add_parser("append")
    append.add_argument("--history", required=True, type=Path)
    append.add_argument("--snapshot", required=True, type=Path)
    append.add_argument("--appended-at-utc", required=True)
    args = parser.parse_args()
    try:
        if args.command == "verify":
            report = verify_history(read_history(args.history))
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0 if report["valid"] else 1
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        record = append_snapshot(args.history, snapshot, args.appended_at_utc)
        print(json.dumps({"appended": True, "sequence": record["sequence"],
                          "snapshot_id": record["snapshot_id"],
                          "record_hash": record["record_hash"],
                          "trade_authority": False}, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, HistoryError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Append-only, offline review ledger for capital-flow event decisions.

The ledger is a hash-chained JSONL file. It records reviewer actions without
mutating normalized event records or their source evidence. Single-writer use
is required; this module does not provide distributed locking or signatures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ACTIONS = {"review", "corroborate", "challenge", "correct", "reject", "expire", "reopen"}
STATUSES = {"watch", "research", "unverified", "corroborated", "rejected", "expired"}
GENESIS = "0" * 64


class LedgerError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LedgerError(f"{field}: non-empty string required")
    return value.strip()


def _timestamp(value: str | None = None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LedgerError("reviewed_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise LedgerError("reviewed_at must include timezone")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _hash_entry(entry: dict[str, Any]) -> str:
    payload = {key: value for key, value in entry.items() if key != "entry_hash"}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def verify_ledger(entries: Iterable[dict[str, Any]]) -> dict[str, Any]:
    expected_sequence = 1
    previous = GENESIS
    count = 0
    errors: list[str] = []
    for index, entry in enumerate(entries, 1):
        count += 1
        if not isinstance(entry, dict):
            errors.append(f"line {index}: entry must be an object")
            continue
        if entry.get("sequence") != expected_sequence:
            errors.append(f"line {index}: expected sequence {expected_sequence}")
        if entry.get("previous_hash") != previous:
            errors.append(f"line {index}: previous_hash does not match prior entry")
        actual_hash = _hash_entry(entry)
        if entry.get("entry_hash") != actual_hash:
            errors.append(f"line {index}: entry_hash mismatch")
        previous = entry.get("entry_hash") if isinstance(entry.get("entry_hash"), str) else previous
        expected_sequence += 1
    return {
        "status": "valid" if not errors else "invalid",
        "entry_count": count,
        "head_hash": previous if count else GENESIS,
        "errors": errors,
        "authority": "audit_integrity_check_only_not_a_digital_signature"
    }


def load_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LedgerError(f"line {line_number}: invalid JSON: {exc}") from exc
            if not isinstance(entry, dict):
                raise LedgerError(f"line {line_number}: expected JSON object")
            entries.append(entry)
    report = verify_ledger(entries)
    if report["status"] != "valid":
        raise LedgerError("ledger integrity check failed: " + "; ".join(report["errors"]))
    return entries


def build_entry(*, sequence: int, previous_hash: str, event_id: str,
                action: str, reviewer_id: str, reason: str,
                review_status: str | None = None, evidence_refs: list[str] | None = None,
                reviewed_at: str | None = None, supersedes_entry_hash: str | None = None) -> dict[str, Any]:
    event_id = _nonempty(event_id, "event_id")
    reviewer_id = _nonempty(reviewer_id, "reviewer_id")
    reason = _nonempty(reason, "reason")
    action = _nonempty(action, "action").lower()
    if action not in ACTIONS:
        raise LedgerError(f"action: must be one of {sorted(ACTIONS)}")
    if review_status is not None and review_status not in STATUSES:
        raise LedgerError(f"review_status: must be one of {sorted(STATUSES)}")
    if action in {"reject", "expire"} and review_status not in {"rejected", "expired"}:
        raise LedgerError(f"{action}: matching review_status is required")
    if action == "reopen" and review_status not in {"watch", "research", "unverified"}:
        raise LedgerError("reopen: review_status must be watch, research or unverified")
    if not isinstance(sequence, int) or sequence < 1:
        raise LedgerError("sequence must be a positive integer")
    if len(previous_hash) != 64 or any(c not in "0123456789abcdef" for c in previous_hash):
        raise LedgerError("previous_hash must be 64 lowercase hexadecimal characters")
    refs = evidence_refs or []
    if not isinstance(refs, list) or any(not isinstance(x, str) or not x.strip() for x in refs):
        raise LedgerError("evidence_refs must be an array of non-empty strings")
    entry = {
        "sequence": sequence,
        "previous_hash": previous_hash,
        "reviewed_at": _timestamp(reviewed_at),
        "event_id": event_id,
        "action": action,
        "reviewer_id": reviewer_id,
        "reason": reason,
        "review_status": review_status,
        "evidence_refs": sorted(set(x.strip() for x in refs)),
        "supersedes_entry_hash": supersedes_entry_hash,
        "authority": "research_review_only_no_trade_or_execution_authority"
    }
    entry["entry_hash"] = _hash_entry(entry)
    return entry


def append_entry(path: Path, entry: dict[str, Any]) -> None:
    # Verify existing ledger and entry linkage before appending.
    existing = load_ledger(path)
    expected_sequence = len(existing) + 1
    expected_previous = existing[-1]["entry_hash"] if existing else GENESIS
    if entry.get("sequence") != expected_sequence or entry.get("previous_hash") != expected_previous:
        raise LedgerError("new entry does not extend the verified ledger head")
    if entry.get("entry_hash") != _hash_entry(entry):
        raise LedgerError("new entry hash is invalid")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(entry) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline append-only capital-flow review ledger")
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("ledger", type=Path)
    append = sub.add_parser("append")
    append.add_argument("ledger", type=Path)
    append.add_argument("--event-id", required=True)
    append.add_argument("--action", required=True, choices=sorted(ACTIONS))
    append.add_argument("--reviewer-id", required=True)
    append.add_argument("--reason", required=True)
    append.add_argument("--status", choices=sorted(STATUSES))
    append.add_argument("--evidence-ref", action="append", default=[])
    append.add_argument("--reviewed-at")
    append.add_argument("--supersedes-entry-hash")
    args = parser.parse_args()

    try:
        if args.command == "verify":
            report = verify_ledger(load_ledger(args.ledger))
            print(json.dumps(report, indent=2))
            return 0 if report["status"] == "valid" else 1
        entries = load_ledger(args.ledger)
        entry = build_entry(
            sequence=len(entries) + 1,
            previous_hash=entries[-1]["entry_hash"] if entries else GENESIS,
            event_id=args.event_id, action=args.action, reviewer_id=args.reviewer_id,
            reason=args.reason, review_status=args.status, evidence_refs=args.evidence_ref,
            reviewed_at=args.reviewed_at, supersedes_entry_hash=args.supersedes_entry_hash
        )
        append_entry(args.ledger, entry)
        print(json.dumps({"status": "appended", "sequence": entry["sequence"],
                          "entry_hash": entry["entry_hash"]}, indent=2))
        return 0
    except (LedgerError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

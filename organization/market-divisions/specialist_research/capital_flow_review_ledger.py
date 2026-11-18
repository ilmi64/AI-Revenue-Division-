"""Append-only, fail-closed Capital Flow review ledger (offline, research-only).

The wire format is intentionally compatible with capital_flow_handoff.verify_review_ledger.
This is a single-writer local journal; hash chaining is an integrity aid, not a signature.
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
AUTHORITY = "research_review_only_no_trade_or_execution_authority"
ACTIONS = {"review", "corroborate", "challenge", "correct", "reject", "expire", "reopen"}
STATUSES = {"watch", "research", "unverified", "corroborated", "rejected", "expired"}
HANDOFF_STATUSES = {"watch", "research", "unverified", "corroborated"}


class ReviewLedgerError(ValueError):
    """Raised when a review cannot safely be appended or verified."""


def canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ReviewLedgerError("review record is not canonical JSON data") from exc


def _utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ReviewLedgerError("reviewed_at must be ISO-8601 UTC ending Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ReviewLedgerError("reviewed_at is invalid") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ReviewLedgerError("reviewed_at must be UTC")
    return parsed


def _entry_hash(entry: dict[str, Any]) -> str:
    payload = {key: value for key, value in entry.items() if key != "entry_hash"}
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def validate_review(review: dict[str, Any]) -> None:
    if not isinstance(review, dict):
        raise ReviewLedgerError("review must be an object")
    for field in ("event_id", "reviewer_id", "reason"):
        value = review.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ReviewLedgerError(field + " must be a non-empty string")
    action = review.get("action")
    status = review.get("review_status")
    if not isinstance(action, str) or action not in ACTIONS:
        raise ReviewLedgerError("unsupported review action")
    if status is not None and (not isinstance(status, str) or status not in STATUSES):
        raise ReviewLedgerError("unsupported review_status")
    if action == "reject" and status != "rejected":
        raise ReviewLedgerError("reject action requires rejected status")
    if action == "expire" and status != "expired":
        raise ReviewLedgerError("expire action requires expired status")
    if action == "reopen" and status not in {"watch", "research", "unverified"}:
        raise ReviewLedgerError("reopen requires watch, research or unverified status")
    if action in {"review", "corroborate", "correct"} and status not in HANDOFF_STATUSES:
        raise ReviewLedgerError(action + " requires a research review status")
    if action == "challenge" and status not in {None, "unverified", "rejected"}:
        raise ReviewLedgerError("challenge status must be null, unverified or rejected")
    if action == "reject" and status != "rejected":
        raise ReviewLedgerError("reject action/status mismatch")
    _utc(review.get("reviewed_at"))
    refs = review.get("evidence_refs")
    if not isinstance(refs, list) or not refs or any(
            not isinstance(ref, str) or not ref.strip() for ref in refs):
        raise ReviewLedgerError("evidence_refs must contain non-empty strings")
    if len(refs) != len(set(refs)):
        raise ReviewLedgerError("evidence_refs must be unique")
    if review.get("authority") != AUTHORITY:
        raise ReviewLedgerError("research-only authority marker required")
    supersedes = review.get("supersedes_entry_hash")
    if supersedes is not None and (
            not isinstance(supersedes, str) or len(supersedes) != 64
            or any(ch not in "0123456789abcdef" for ch in supersedes)):
        raise ReviewLedgerError("supersedes_entry_hash must be null or lowercase SHA-256")


def read_reviews(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ReviewLedgerError(f"blank line at {line_number}")
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ReviewLedgerError(f"invalid JSON at line {line_number}") from exc
            if not isinstance(value, dict):
                raise ReviewLedgerError(f"review entry object required at line {line_number}")
            rows.append(value)
    return rows


def _validate_lifecycle(entries: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    latest: dict[str, dict[str, Any]] = {}
    blocked: dict[str, str] = {}
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            continue
        event_id = entry.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            continue
        prior = latest.get(event_id)
        action = entry.get("action")
        if prior is None and action != "review":
            errors.append(f"row {index}: first event decision must be review")
        if prior is not None:
            prior_refs = set(prior.get("evidence_refs", [])) if isinstance(prior.get("evidence_refs"), list) else set()
            new_refs = set(entry.get("evidence_refs", [])) - prior_refs if isinstance(entry.get("evidence_refs"), list) else set()
            if event_id in blocked:
                if action not in {"correct", "reopen"}:
                    errors.append(f"row {index}: blocked event requires correct or reopen")
                if not new_refs:
                    errors.append(f"row {index}: resolving a blocked event requires new evidence references")
                if blocked[event_id] in {"reject", "expire"} and action == "reopen":
                    errors.append(f"row {index}: rejected or expired event cannot be reopened")
            elif action == "reopen":
                errors.append(f"row {index}: reopen is only valid after a blocking challenge")
            if action == "correct" and not new_refs:
                errors.append(f"row {index}: correction requires new evidence references")
        if action in {"challenge", "reject", "expire"}:
            blocked[event_id] = action
        elif action in {"correct", "reopen"} and event_id in blocked:
            blocked.pop(event_id, None)
        latest[event_id] = entry
    return errors


def verify_reviews(entries: list[dict[str, Any]]) -> dict[str, Any]:
    previous = GENESIS
    errors: list[str] = []
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            errors.append(f"row {index}: entry must be an object")
            continue
        seq = entry.get("sequence")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq != index:
            errors.append(f"row {index}: invalid sequence")
        if entry.get("previous_hash") != previous:
            errors.append(f"row {index}: previous_hash mismatch")
        review = {key: value for key, value in entry.items()
                  if key not in {"sequence", "previous_hash", "entry_hash"}}
        try:
            validate_review(review)
        except ReviewLedgerError as exc:
            errors.append(f"row {index}: {exc}")
        if entry.get("entry_hash") != _entry_hash(entry):
            errors.append(f"row {index}: entry_hash mismatch")
        if isinstance(entry.get("entry_hash"), str):
            previous = entry["entry_hash"]
    errors.extend(_validate_lifecycle(entries))
    return {"valid": not errors, "errors": errors, "entry_count": len(entries),
            "head_hash": previous, "authority": "integrity_check_only_not_a_digital_signature"}


def append_review(path: Path, review: dict[str, Any]) -> dict[str, Any]:
    """Append one validated review; refuses to extend an invalid existing journal."""
    validate_review(review)
    entries = read_reviews(path)
    report = verify_reviews(entries)
    if not report["valid"]:
        raise ReviewLedgerError("existing review ledger invalid: " + "; ".join(report["errors"]))
    prior = [row for row in entries if row.get("event_id") == review["event_id"]]
    expected = prior[-1]["entry_hash"] if prior else None
    candidate = entries + [{"sequence": len(entries) + 1,
                            "previous_hash": report["head_hash"], **review,
                            "entry_hash": "0" * 64}]
    lifecycle_errors = _validate_lifecycle(candidate)
    if lifecycle_errors:
        raise ReviewLedgerError("; ".join(lifecycle_errors))
    if review.get("supersedes_entry_hash") != expected:
        raise ReviewLedgerError("supersedes_entry_hash must reference the latest prior review for this event")
    entry = {
        "sequence": len(entries) + 1,
        "previous_hash": report["head_hash"],
        **review,
    }
    entry["entry_hash"] = _entry_hash(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical(entry) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Append or verify the OCC Capital Flow review ledger")
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--ledger", required=True, type=Path)
    append = sub.add_parser("append")
    append.add_argument("--ledger", required=True, type=Path)
    append.add_argument("--review", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "verify":
            report = verify_reviews(read_reviews(args.ledger))
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0 if report["valid"] else 1
        review = json.loads(args.review.read_text(encoding="utf-8"))
        entry = append_review(args.ledger, review)
        print(json.dumps({"appended": True, "sequence": entry["sequence"],
                          "entry_hash": entry["entry_hash"],
                          "trade_authority": False, "live_readiness": False}, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ReviewLedgerError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Offline, deterministic normalisation for capital-flow research events.

This module uses only the Python standard library. It does not fetch data,
infer wallet ownership, calculate trading signals, or authorize execution.
Input and output are JSON Lines (one JSON object per line).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

EVENT_TYPES = {
    "fundraise_announced", "grant_announced", "investment_disclosed",
    "token_launch_announced", "token_distribution", "vesting_unlock_scheduled",
    "vesting_unlock_observed", "treasury_transfer", "treasury_deployment",
    "treasury_withdrawal", "large_wallet_transfer", "exchange_inflow",
    "exchange_outflow", "bridge_inflow", "bridge_outflow",
    "wallet_accumulation_candidate", "wallet_distribution_candidate",
    "liquidity_added", "liquidity_removed", "market_maker_transfer",
    "stablecoin_supply_change", "stablecoin_netflow",
    "developer_activity_change", "grant_activity_change",
    "ecosystem_integration", "governance_treasury_proposal",
    "buyback_announced", "buyback_executed",
}
REVIEW_STATUSES = {"watch", "research", "unverified", "corroborated", "rejected", "expired"}
DIRECTIONS = {"inflow", "outflow", "internal", "unknown"}
HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class EventError(ValueError):
    """Raised when an event is malformed or violates the local contract."""


def _epoch(value: Any, field: str, *, nullable: bool = False) -> float | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool):
        raise EventError(f"{field}: boolean is not a timestamp")
    if isinstance(value, (int, float)):
        if value < 0:
            raise EventError(f"{field}: timestamp must be non-negative")
        return float(value)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            if nullable:
                return None
            raise EventError(f"{field}: empty timestamp")
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EventError(f"{field}: expected epoch seconds or ISO-8601") from exc
        if parsed.tzinfo is None:
            raise EventError(f"{field}: timezone required; naive timestamps are rejected")
        return parsed.astimezone(timezone.utc).timestamp()
    raise EventError(f"{field}: unsupported timestamp type")


def _clean_list(value: Any, field: str, *, required: bool = False) -> list[str]:
    if value is None:
        values: list[Any] = []
    elif isinstance(value, list):
        values = value
    else:
        raise EventError(f"{field}: expected an array")
    result = sorted({str(item).strip() for item in values if str(item).strip()})
    if required and not result:
        raise EventError(f"{field}: at least one value is required")
    return result


def normalize_event(raw: dict[str, Any], *, now_epoch: float | None = None,
                    stale_after_seconds: float = 7 * 86400) -> dict[str, Any]:
    """Normalize one record; unknown attribution and valuations remain null."""
    if not isinstance(raw, dict):
        raise EventError("event: expected an object")
    event_type = str(raw.get("event_type", "")).strip().lower()
    if event_type not in EVENT_TYPES:
        raise EventError("event_type: unsupported or missing value")

    observed = _epoch(raw.get("observed_at_epoch", raw.get("observed_at")), "observed_at_epoch")
    ingested = _epoch(raw.get("ingested_at_epoch", raw.get("ingested_at", now_epoch)), "ingested_at_epoch")
    occurred = _epoch(raw.get("occurred_at_epoch", raw.get("occurred_at")), "occurred_at_epoch", nullable=True)
    assert observed is not None and ingested is not None

    sources = _clean_list(raw.get("source_ids"), "source_ids", required=True)
    evidence = _clean_list(raw.get("evidence_refs"), "evidence_refs", required=True)
    chain = raw.get("chain")
    chain = str(chain).strip().lower() if chain is not None and str(chain).strip() else None
    asset = raw.get("asset_id")
    asset = str(asset).strip().upper() if asset is not None and str(asset).strip() else None
    tx = raw.get("transaction_hash")
    tx = str(tx).strip().lower() if tx is not None and str(tx).strip() else None
    if tx is not None and not HASH_RE.fullmatch(tx):
        raise EventError("transaction_hash: expected 32-byte hex hash")

    direction = str(raw.get("direction", "unknown")).strip().lower()
    if direction not in DIRECTIONS:
        raise EventError("direction: unsupported value")
    status = str(raw.get("review_status", "unverified")).strip().lower()
    if status not in REVIEW_STATUSES:
        raise EventError("review_status: unsupported value")

    event_id = str(raw.get("event_id", "")).strip()
    if not event_id:
        identity = "|".join([chain or "?", tx or "no-tx", event_type, *evidence])
        event_id = "cfi_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]

    output = {
        "event_id": event_id,
        "event_type": event_type,
        "chain": chain,
        "asset_id": asset,
        "contract_address": _optional_text(raw.get("contract_address")),
        "transaction_hash": tx,
        "block_height": _optional_nonnegative_int(raw.get("block_height"), "block_height"),
        "subject_entity_id": _optional_text(raw.get("subject_entity_id")),
        "counterparty_entity_id": _optional_text(raw.get("counterparty_entity_id")),
        "occurred_at_epoch": occurred,
        "observed_at_epoch": observed,
        "ingested_at_epoch": ingested,
        "source_timezone_or_precision": _optional_text(raw.get("source_timezone_or_precision")),
        "value_native": _optional_nonnegative_number(raw.get("value_native"), "value_native"),
        "native_unit": _optional_text(raw.get("native_unit")),
        "value_usd_estimate": _optional_nonnegative_number(raw.get("value_usd_estimate"), "value_usd_estimate"),
        "value_cad_estimate": _optional_nonnegative_number(raw.get("value_cad_estimate"), "value_cad_estimate"),
        "valuation_at_epoch": _epoch(raw.get("valuation_at_epoch"), "valuation_at_epoch", nullable=True),
        "valuation_source_id": _optional_text(raw.get("valuation_source_id")),
        "direction": direction,
        "direction_reference": _optional_text(raw.get("direction_reference")),
        "source_ids": sources,
        "evidence_refs": evidence,
        "raw_evidence_sha256": _optional_hash(raw.get("raw_evidence_sha256")),
        "corroboration_count": _nonnegative_int(raw.get("corroboration_count", 0), "corroboration_count"),
        "source_reliability": _score(raw.get("source_reliability", 0), "source_reliability"),
        "attribution_confidence": _score(raw.get("attribution_confidence", 0), "attribution_confidence"),
        "event_confidence": _score(raw.get("event_confidence", 0), "event_confidence"),
        "materiality": _score(raw.get("materiality", 0), "materiality"),
        "limitations": _clean_list(raw.get("limitations"), "limitations"),
        "conflicts": _clean_list(raw.get("conflicts"), "conflicts"),
        "review_status": status,
        "revalidate_by_epoch": _epoch(raw.get("revalidate_by_epoch"), "revalidate_by_epoch", nullable=True),
    }

    # Derived flags are warnings only. They never infer intent or beneficial ownership.
    flags = _clean_list(raw.get("quality_flags"), "quality_flags")
    if output["subject_entity_id"] and output["subject_entity_id"] == output["counterparty_entity_id"]:
        flags.append("possible_self_transfer")
    classification = str(raw.get("transfer_classification", "")).strip().lower()
    if classification in {"exchange_hot_wallet_reshuffle", "bridge_hop", "wrapped_token_mint_burn",
                          "internal_treasury_move", "self_transfer"}:
        flags.append(classification)
    if now_epoch is not None and now_epoch - observed > stale_after_seconds:
        flags.append("stale_observation")
    if occurred is None:
        flags.append("occurred_at_unknown")
    if output["subject_entity_id"] is None or output["attribution_confidence"] < 3:
        flags.append("attribution_unverified")
    output["quality_flags"] = sorted(set(flags))
    return output


def _optional_text(value: Any) -> str | None:
    if value is None or not str(value).strip():
        return None
    return str(value).strip()


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EventError(f"{field}: expected a non-negative integer")
    return value


def _optional_nonnegative_int(value: Any, field: str) -> int | None:
    return None if value is None else _nonnegative_int(value, field)


def _score(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
        raise EventError(f"{field}: expected integer from 0 to 5")
    return value


def _optional_nonnegative_number(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise EventError(f"{field}: expected a non-negative number or null")
    return float(value)


def _optional_hash(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip().lower()
    if not HASH_RE.fullmatch(value):
        raise EventError("raw_evidence_sha256: expected 64 hexadecimal characters")
    return value


def deduplicate(events: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Merge exact chain+transaction+type duplicates; retain conflicting evidence."""
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    output: list[dict[str, Any]] = []
    duplicates = 0
    for event in events:
        tx = event.get("transaction_hash")
        chain = event.get("chain")
        if not tx or not chain:
            output.append(event)
            continue
        key = (chain, tx, event["event_type"])
        if key not in by_key:
            by_key[key] = event
            output.append(event)
            continue
        duplicates += 1
        existing = by_key[key]
        existing["source_ids"] = sorted(set(existing["source_ids"]) | set(event["source_ids"]))
        existing["evidence_refs"] = sorted(set(existing["evidence_refs"]) | set(event["evidence_refs"]))
        existing["quality_flags"] = sorted(set(existing["quality_flags"]) | set(event["quality_flags"]))
        for field in ("value_native", "value_usd_estimate", "value_cad_estimate", "direction",
                      "subject_entity_id", "counterparty_entity_id"):
            if existing.get(field) != event.get(field):
                note = f"duplicate_conflict:{field}"
                existing["conflicts"] = sorted(set(existing["conflicts"]) | {note})
                existing["quality_flags"] = sorted(set(existing["quality_flags"]) | {"duplicate_conflict"})
        existing["corroboration_count"] = max(existing["corroboration_count"], event["corroboration_count"])
    return output, duplicates


def process_jsonl(lines: Iterable[str], *, now_epoch: float | None = None) -> tuple[list[dict[str, Any]], list[str], int]:
    normalized: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            normalized.append(normalize_event(raw, now_epoch=now_epoch))
        except (json.JSONDecodeError, EventError) as exc:
            errors.append(f"line {line_number}: {exc}")
    unique, duplicate_count = deduplicate(normalized)
    return unique, errors, duplicate_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline capital-flow JSONL normalizer")
    parser.add_argument("input", type=Path, help="Input JSONL file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output JSONL file")
    parser.add_argument("--now-epoch", type=float, default=None, help="Optional fixed reference time for stale checks")
    args = parser.parse_args()
    with args.input.open("r", encoding="utf-8") as handle:
        events, errors, duplicates = process_jsonl(handle, now_epoch=args.now_epoch)
    with args.output.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"accepted={len(events)} duplicates_merged={duplicates} rejected={len(errors)}")
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Verified offline Capital Flow -> Crypto research-only handoff adapter.

The adapter re-resolves canonical events and their append-only review ledger,
checks source eligibility and exact chain/asset/contract identity, then emits
schema-shaped research context. It never creates a market observation or trade signal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GENESIS = "0" * 64
ALLOWED_HANDOFF_STATES = {"watch", "research", "unverified", "corroborated"}
BLOCKING_ACTIONS = {"challenge", "reject", "expire"}
MIN_CONFIDENCE = 2


class HandoffError(ValueError):
    """Raised when source evidence cannot safely cross the desk boundary."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _entry_hash(entry: dict[str, Any]) -> str:
    payload = {key: value for key, value in entry.items() if key != "entry_hash"}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def verify_review_ledger(entries: list[dict[str, Any]]) -> dict[str, Any]:
    previous = GENESIS
    errors: list[str] = []
    for sequence, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            errors.append(f"ledger row {sequence} is not an object")
            continue
        if entry.get("sequence") != sequence:
            errors.append(f"ledger row {sequence} has invalid sequence")
        if entry.get("previous_hash") != previous:
            errors.append(f"ledger row {sequence} breaks previous_hash chain")
        if entry.get("entry_hash") != _entry_hash(entry):
            errors.append(f"ledger row {sequence} has invalid entry_hash")
        if not isinstance(entry.get("event_id"), str) or not entry["event_id"].strip():
            errors.append(f"ledger row {sequence} missing event_id")
        action = entry.get("action")
        status = entry.get("review_status")
        if action not in {"review", "corroborate", "challenge", "correct", "reject", "expire", "reopen"}:
            errors.append(f"ledger row {sequence} has invalid action")
        if status is not None and status not in {
            "watch", "research", "unverified", "corroborated", "rejected", "expired"
        }:
            errors.append(f"ledger row {sequence} has invalid review_status")
        if action == "reject" and status != "rejected":
            errors.append(f"ledger row {sequence} reject action/status mismatch")
        if action == "expire" and status != "expired":
            errors.append(f"ledger row {sequence} expire action/status mismatch")
        if action == "reopen" and status not in {"watch", "research", "unverified"}:
            errors.append(f"ledger row {sequence} reopen status invalid")
        if entry.get("authority") != "research_review_only_no_trade_or_execution_authority":
            errors.append(f"ledger row {sequence} authority marker missing")
        if not isinstance(entry.get("reviewer_id"), str) or not entry["reviewer_id"].strip():
            errors.append(f"ledger row {sequence} reviewer_id missing")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            errors.append(f"ledger row {sequence} reason missing")
        refs = entry.get("evidence_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            errors.append(f"ledger row {sequence} evidence_refs malformed")
        try:
            _parse_utc(entry.get("reviewed_at"), "reviewed_at")
        except HandoffError as exc:
            errors.append(f"ledger row {sequence}: {exc}")
        previous = entry.get("entry_hash") if isinstance(entry.get("entry_hash"), str) else previous
    return {"valid": not errors, "errors": errors, "entry_count": len(entries), "head_hash": previous}


def _parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise HandoffError(f"{field} must be an ISO-8601 UTC timestamp ending Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise HandoffError(f"{field} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise HandoffError(f"{field} must be UTC")
    return parsed


def _epoch(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HandoffError(f"{field} must be numeric epoch seconds")
    return float(value)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise HandoffError(f"{path}: line {line_number}: invalid JSON") from exc
            if not isinstance(item, dict):
                raise HandoffError(f"{path}: line {line_number}: object required")
            records.append(item)
    return records


def _source_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(registry, dict) or not isinstance(registry.get("sources"), list):
        raise HandoffError("source registry must contain a sources array")
    result: dict[str, dict[str, Any]] = {}
    for source in registry["sources"]:
        if not isinstance(source, dict) or not isinstance(source.get("source_id"), str):
            raise HandoffError("source registry contains malformed source")
        source_id = source["source_id"]
        if source_id in result:
            raise HandoffError(f"duplicate source_id: {source_id}")
        result[source_id] = source
    return result


def _source_is_eligible(source: dict[str, Any]) -> bool:
    # Deliberately narrow: "unverified", "not_accessible", unknown cost and
    # unreviewed terms in the current candidate registry all fail closed.
    return (
        source.get("access_status") in {"verified", "approved"}
        and source.get("access_mode") not in {"not_accessible", "unknown", None}
        and source.get("cost_status") in {"free", "zero_cost"}
        and source.get("terms_review_status") in {"approved", "reviewed"}
        and source.get("operational_status") in {"approved", "active", "research_only"}
    )


def _latest_reviews(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for entry in entries:
        latest[entry["event_id"]] = entry
    return latest


def _validate_event(event: dict[str, Any], now: datetime, max_age_seconds: int) -> tuple[str, list[str]]:
    event_id = event.get("event_id")
    if not isinstance(event_id, str) or not event_id.strip():
        raise HandoffError("canonical event_id missing")
    if not isinstance(event.get("event_type"), str) or not event["event_type"].strip():
        raise HandoffError(f"{event_id}: event_type missing")
    if event.get("direction", "unknown") not in {"inflow", "outflow", "internal", "unknown"}:
        raise HandoffError(f"{event_id}: direction invalid")
    event_time = datetime.fromtimestamp(_epoch(event.get("observed_at_epoch"), "observed_at_epoch"), timezone.utc)
    if event_time > now:
        raise HandoffError(f"{event_id}: event timestamp is in the future")
    if (now - event_time).total_seconds() > max_age_seconds:
        raise HandoffError(f"{event_id}: event is stale")
    revalidate = event.get("revalidate_by_epoch")
    if revalidate is None:
        raise HandoffError(f"{event_id}: revalidate_by_epoch is required")
    deadline = datetime.fromtimestamp(_epoch(revalidate, "revalidate_by_epoch"), timezone.utc)
    if deadline <= now:
        raise HandoffError(f"{event_id}: revalidation deadline expired")
    sources = event.get("source_ids")
    evidence = event.get("evidence_refs")
    if not isinstance(sources, list) or not sources or len(set(sources)) != len(sources):
        raise HandoffError(f"{event_id}: unique source_ids required")
    if not isinstance(evidence, list) or not evidence or len(set(evidence)) != len(evidence):
        raise HandoffError(f"{event_id}: unique evidence_refs required")
    if event.get("conflicts"):
        raise HandoffError(f"{event_id}: unresolved evidence conflicts")
    flags = event.get("quality_flags", [])
    if not isinstance(flags, list):
        raise HandoffError(f"{event_id}: quality_flags must be an array")
    blocking = {"stale_observation", "duplicate_conflict", "possible_self_transfer",
                "exchange_hot_wallet_reshuffle", "bridge_hop", "wrapped_token_mint_burn",
                "internal_treasury_move", "self_transfer"}
    found = sorted(blocking.intersection(flags))
    if found:
        raise HandoffError(f"{event_id}: blocking quality flags: {','.join(found)}")
    for field in ("source_reliability", "attribution_confidence", "event_confidence", "materiality"):
        value = event.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            raise HandoffError(f"{event_id}: {field} must be an integer from 0 to 5")
        if field != "materiality" and value < MIN_CONFIDENCE:
            raise HandoffError(f"{event_id}: {field} below minimum research threshold")
    return event_time.strftime("%Y-%m-%dT%H:%M:%SZ"), sources


def build_handoff(events: list[dict[str, Any]], reviews: list[dict[str, Any]],
                  source_registry: dict[str, Any], observation: dict[str, Any],
                  now_utc: str, max_age_seconds: int = 7 * 86400) -> dict[str, Any]:
    """Resolve and validate matching capital-flow events for one exact Crypto market."""
    now = _parse_utc(now_utc, "now_utc")
    if max_age_seconds <= 0:
        raise HandoffError("max_age_seconds must be positive")
    if observation.get("instrument_type") not in {"crypto_spot", "crypto_perpetual"}:
        raise HandoffError("capital-flow context can only attach to a Crypto instrument")
    base = observation.get("base_asset")
    chain_id = observation.get("chain_id")
    contract = observation.get("contract_address")
    if not all(isinstance(x, str) and x.strip() for x in (base, chain_id, contract)):
        raise HandoffError("Crypto base_asset, chain_id and contract_address are all required")
    if observation.get("token_identity_status") != "verified":
        raise HandoffError("Crypto token identity is not verified")

    ledger_report = verify_review_ledger(reviews)
    if not ledger_report["valid"]:
        raise HandoffError("review ledger integrity failure: " + "; ".join(ledger_report["errors"]))
    by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        event_id = event.get("event_id") if isinstance(event, dict) else None
        if not isinstance(event_id, str) or not event_id.strip():
            raise HandoffError("canonical event has no event_id")
        if event_id in by_id:
            raise HandoffError(f"duplicate canonical event_id: {event_id}")
        by_id[event_id] = event
    for review in reviews:
        if review["event_id"] not in by_id:
            raise HandoffError(f"orphan review references unknown event: {review['event_id']}")

    sources = _source_map(source_registry)
    latest = _latest_reviews(reviews)
    records = []
    rejected = []
    for event_id, event in by_id.items():
        # Never attach by ticker alone. All three identity dimensions must match.
        if event.get("asset_id") != base:
            continue
        if str(event.get("chain") or "").lower() != chain_id.lower():
            continue
        if event.get("contract_address") != contract:
            continue
        try:
            observed_at, source_ids = _validate_event(event, now, max_age_seconds)
            decision = latest.get(event_id)
            if decision is None:
                raise HandoffError(f"{event_id}: no explicit review-ledger decision")
            reviewed_at = _parse_utc(decision.get("reviewed_at"), "reviewed_at")
            if reviewed_at > now:
                raise HandoffError(f"{event_id}: review timestamp is in the future")
            if (now - reviewed_at).total_seconds() > 90 * 86400:
                raise HandoffError(f"{event_id}: latest review is stale")
            action = decision.get("action")
            status = decision.get("review_status")
            if action in BLOCKING_ACTIONS:
                raise HandoffError(f"{event_id}: latest review action {action} blocks handoff")
            if status not in ALLOWED_HANDOFF_STATES:
                raise HandoffError(f"{event_id}: latest review status is not handoff-eligible")
            if decision.get("authority") != "research_review_only_no_trade_or_execution_authority":
                raise HandoffError(f"{event_id}: review authority marker missing")
            missing = [source_id for source_id in source_ids
                       if source_id not in sources or not _source_is_eligible(sources[source_id])]
            if missing:
                raise HandoffError(f"{event_id}: source eligibility not established: {','.join(missing)}")
            refs = sorted(set(event["evidence_refs"]) | set(decision.get("evidence_refs", [])))
            if not refs:
                raise HandoffError(f"{event_id}: evidence references missing")
            records.append({
                "event_id": event_id,
                "event_type": event.get("event_type"),
                "review_status": status,
                "observed_at_utc": observed_at,
                "asset_id": event.get("asset_id"),
                "chain": event.get("chain"),
                "contract_address": event.get("contract_address"),
                "transaction_hash": event.get("transaction_hash"),
                "direction": event.get("direction", "unknown"),
                "source_ids": source_ids,
                "evidence_refs": refs,
                "source_reliability": event["source_reliability"],
                "attribution_confidence": event["attribution_confidence"],
                "event_confidence": event["event_confidence"],
                "materiality": event["materiality"],
                "corroboration_count": event.get("corroboration_count", 0),
                "limitations": sorted(set(event.get("limitations", [])) | {"Research context only; not an execution signal"}),
                "conflicts": [],
                "quality_flags": sorted(set(event.get("quality_flags", []))),
                "revalidate_by_utc": datetime.fromtimestamp(
                    _epoch(event["revalidate_by_epoch"], "revalidate_by_epoch"), timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
        except (HandoffError, TypeError) as exc:
            rejected.append({"event_id": event_id, "reason": str(exc)})

    records.sort(key=lambda item: item["event_id"])
    return {
        "schema_version": "1.0.0",
        "handoff_id": "cfi_crypto_" + hashlib.sha256(
            (base + "|" + chain_id + "|" + contract + "|" + now_utc + "|" +
             "|".join(item["event_id"] for item in records)).encode("utf-8")
        ).hexdigest()[:24],
        "created_at_utc": now_utc,
        "source_system": "occ_capital_flow_intelligence",
        "destination_desk": "crypto",
        "mode": "research_only",
        "instrument_identity": {"base_asset": base, "chain_id": chain_id, "contract_address": contract},
        "event_records": records,
        "rejected_matching_events": rejected,
        "review_ledger": {"valid": True, "entry_count": ledger_report["entry_count"],
                          "head_hash": ledger_report["head_hash"],
                          "authority": "integrity_check_only_not_a_digital_signature"},
        "limitations": [
            "Capital-flow evidence is context, not a directional trading signal",
            "No position sizing, leverage, order, execution or trade authority",
            "Exact base asset, chain and contract identity required; ticker-only matching is prohibited",
            "Source access, cost and terms must be explicitly verified; unverified providers fail closed",
        ],
        "consumer_rules": [
            "Crypto desk independently assesses event relevance and market liquidity",
            "Preserve source and evidence references and keep confidence dimensions separate",
            "Never use this handoff as a market observation or substitute for the OCC market evidence gate",
        ],
        "trade_authority": False,
        "live_readiness": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a verified research-only Capital Flow -> Crypto handoff")
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--reviews", required=True, type=Path)
    parser.add_argument("--source-registry", required=True, type=Path)
    parser.add_argument("--crypto-observation", required=True, type=Path)
    parser.add_argument("--now-utc", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        events = _read_jsonl(args.events)
        reviews = _read_jsonl(args.reviews)
        registry = json.loads(args.source_registry.read_text(encoding="utf-8"))
        observation = json.loads(args.crypto_observation.read_text(encoding="utf-8"))
        result = build_handoff(events, reviews, registry, observation, args.now_utc)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "built", "accepted_events": len(result["event_records"]),
                          "rejected_matching_events": len(result["rejected_matching_events"]),
                          "trade_authority": False, "output": str(args.output)}, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, HandoffError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

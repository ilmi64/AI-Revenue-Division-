"""Offline OCC evidence-to-desk gate.

Standard-library only. Reads supplied JSON/JSONL snapshots; performs no network
calls, account access, scheduling, publishing, orders or execution. A PASS means
only that the supplied record passed configured research-evidence gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GENESIS = "0" * 64
EVENT_REVIEW_STATES = {"watch", "research", "unverified", "corroborated"}
EVENT_FINAL_STATES = {"rejected", "expired"}
GOLD_TYPES = {"xauusd_spot", "gold_future", "gold_cfd"}
ALLOWED_RESEARCH_DATA = {"live", "delayed", "indicative", "historical", "synthetic"}


class GateError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise GateError(f"{field}: UTC timestamp ending Z required")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise GateError(f"{field}: invalid ISO-8601 timestamp") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise GateError(f"{field}: UTC timestamp required")
    return parsed


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise GateError(f"{path}:{number}: invalid JSON") from exc
            if not isinstance(value, dict):
                raise GateError(f"{path}:{number}: object required")
            rows.append(value)
    return rows


def entry_hash(entry: dict[str, Any]) -> str:
    payload = {key: value for key, value in entry.items() if key != "entry_hash"}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def verify_ledger(entries: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors, previous = [], GENESIS
    for sequence, entry in enumerate(entries, 1):
        if entry.get("sequence") != sequence:
            errors.append(f"ledger sequence mismatch at row {sequence}")
        if entry.get("previous_hash") != previous:
            errors.append(f"ledger previous_hash mismatch at row {sequence}")
        actual = entry_hash(entry)
        if entry.get("entry_hash") != actual:
            errors.append(f"ledger entry_hash mismatch at row {sequence}")
        if entry.get("authority") != "research_review_only_no_trade_or_execution_authority":
            errors.append(f"ledger authority marker missing at row {sequence}")
        previous = entry.get("entry_hash") if isinstance(entry.get("entry_hash"), str) else previous
    return not errors, errors


def latest_reviews(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest = {}
    for entry in entries:
        event_id = entry.get("event_id")
        if isinstance(event_id, str):
            latest[event_id] = entry
    return latest


def validate_source_registry(registry: dict[str, Any], source_ids: set[str]) -> list[str]:
    errors = []
    if registry.get("status") != "research_only":
        errors.append("source registry status is not research_only")
    records = registry.get("sources")
    if not isinstance(records, list):
        return errors + ["source registry sources array missing"]
    by_id = {row.get("source_id"): row for row in records if isinstance(row, dict)}
    for source_id in sorted(source_ids):
        row = by_id.get(source_id)
        if row is None:
            errors.append(f"source {source_id}: absent from source registry")
            continue
        if row.get("access_status") not in {"verified"}:
            errors.append(f"source {source_id}: access not verified")
        if row.get("cost_status") not in {"free_verified", "not_applicable"}:
            errors.append(f"source {source_id}: cost not cleared as free/not-applicable")
        if row.get("terms_review_status") != "reviewed_permitted":
            errors.append(f"source {source_id}: terms not reviewed as permitted")
        if row.get("operational_status") not in {"approved_manual", "approved_adapter"}:
            errors.append(f"source {source_id}: operational status not approved")
        if row.get("access_mode") == "not_accessible":
            errors.append(f"source {source_id}: source is not accessible")
    return errors


def validate_capital_event(event: dict[str, Any], reviews: dict[str, dict[str, Any]],
                           now: datetime, registry: dict[str, Any]) -> dict[str, Any]:
    errors, warnings = [], []
    event_id = event.get("event_id")
    if not isinstance(event_id, str) or not event_id.strip():
        errors.append("event_id missing")
    for field in ("source_ids", "evidence_refs"):
        value = event.get(field)
        if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value):
            errors.append(f"{field} missing or invalid")
    for field in ("source_reliability", "attribution_confidence", "event_confidence", "materiality"):
        value = event.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            errors.append(f"{field} must be integer 0..5")
    try:
        observed = datetime.fromtimestamp(float(event["observed_at_epoch"]), timezone.utc)
        ingested = datetime.fromtimestamp(float(event["ingested_at_epoch"]), timezone.utc)
        if observed > now:
            errors.append("event observation is in the future")
        if ingested > now:
            errors.append("event ingestion is in the future")
        if (now - observed).total_seconds() > 7 * 86400:
            warnings.append("event observation older than default 7-day research window")
    except (KeyError, TypeError, ValueError, OverflowError):
        errors.append("observed_at_epoch/ingested_at_epoch invalid")
    source_ids = set(event.get("source_ids", [])) if isinstance(event.get("source_ids"), list) else set()
    errors.extend(validate_source_registry(registry, source_ids))
    if event_id in reviews:
        review = reviews[event_id]
        status = review.get("review_status")
        if status not in EVENT_REVIEW_STATES:
            errors.append(f"latest review status {status!r} is not handoff-eligible")
        if review.get("action") in {"reject", "expire"}:
            errors.append("latest review action rejects or expires the event")
        if not isinstance(review.get("reviewer_id"), str) or not review.get("reviewer_id"):
            errors.append("latest review lacks reviewer identity")
        try:
            reviewed = parse_utc(review.get("reviewed_at"), "reviewed_at")
            if (now - reviewed).total_seconds() > 30 * 86400:
                errors.append("review is older than 30 days")
            if reviewed > now:
                errors.append("review timestamp is in the future")
        except GateError as exc:
            errors.append(str(exc))
    else:
        errors.append("no review-ledger entry for event")
    if event.get("conflicts"):
        warnings.append("event has unresolved conflicts")
    if event.get("quality_flags"):
        warnings.append("event has quality flags: " + ",".join(sorted(set(event["quality_flags"]))))
    if event.get("attribution_confidence", 0) < 3:
        warnings.append("attribution confidence below 3/5")
    if event.get("review_status") in EVENT_FINAL_STATES:
        errors.append("canonical event status is rejected or expired")
    return {"record_id": event_id, "eligible": not errors, "errors": errors, "warnings": warnings,
            "mode": "research_only", "trade_authority": False}


def validate_market_observation(obs: dict[str, Any], now: datetime,
                                max_age_seconds: float, max_clock_skew_seconds: float) -> dict[str, Any]:
    errors, warnings = [], []
    instrument_type = obs.get("instrument_type")
    for field in ("instrument_id", "venue_or_broker", "source_id", "portfolio_version"):
        if field not in obs:
            errors.append(f"{field} missing")
    try:
        source_time = parse_utc(obs.get("source_timestamp_utc"), "source_timestamp_utc")
        received_time = parse_utc(obs.get("received_timestamp_utc"), "received_timestamp_utc")
        age = (now - source_time).total_seconds()
        skew = abs((received_time - source_time).total_seconds())
        if age < -max_clock_skew_seconds:
            errors.append("source timestamp is in the future beyond clock-skew tolerance")
        if age > max_age_seconds:
            errors.append("market observation exceeds configured maximum age")
        if skew > max_clock_skew_seconds:
            errors.append("source/receive timestamp skew exceeds configured tolerance")
    except GateError as exc:
        age = None
        errors.append(str(exc))
    bid, ask = obs.get("bid"), obs.get("ask")
    for field, value in (("bid", bid), ("ask", ask)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            errors.append(f"{field} must be finite and positive")
    if isinstance(bid, (int, float)) and isinstance(ask, (int, float)) and bid > ask:
        errors.append("crossed quote: bid exceeds ask")
    if obs.get("licence_status") not in {"approved", "not_applicable"}:
        warnings.append("licence not cleared; research evidence cannot be promoted")
    if obs.get("data_class") != "live":
        warnings.append(f"data class {obs.get('data_class')!r} is not live; research-only")
    if obs.get("session_state") != "open":
        warnings.append("session is not explicitly open")
    if instrument_type in GOLD_TYPES:
        required = ("gold_price_basis", "gold_session", "quote_unit", "quote_age_seconds",
                    "stale_threshold_seconds", "is_stale", "financing_status", "settlement_type")
        for field in required:
            if field not in obs or obs.get(field) is None:
                errors.append(f"Gold field {field} missing")
        if obs.get("gold_price_basis") == "indicative_bullion_spot" and instrument_type == "xauusd_spot":
            warnings.append("indicative bullion reference is not broker-executable XAUUSD")
        try:
            quote_age = float(obs["quote_age_seconds"])
            stale_limit = float(obs["stale_threshold_seconds"])
            if not math.isfinite(quote_age) or not math.isfinite(stale_limit) or stale_limit <= 0:
                errors.append("Gold quote age/threshold invalid")
            elif quote_age > stale_limit or obs.get("is_stale") is True:
                errors.append("Gold quote is stale")
            elif obs.get("is_stale") is not False:
                errors.append("Gold stale flag must be explicit false")
        except (KeyError, TypeError, ValueError):
            errors.append("Gold quote age/threshold invalid")
        if obs.get("financing_status") in {"unknown", "not_reviewed"}:
            warnings.append("Gold financing not assessed; no product suitability conclusion")
        if obs.get("settlement_type") == "unknown":
            warnings.append("Gold settlement structure unknown")
        if instrument_type == "gold_future" and (not obs.get("contract_code") or not obs.get("expiry_utc")):
            errors.append("Gold futures require contract code and expiry")
    if instrument_type == "fx_spot" and (not obs.get("base_currency") or not obs.get("quote_currency")):
        errors.append("FX base/quote currency mapping missing")
    if instrument_type in {"index_future", "gold_future"} and not obs.get("contract_code"):
        errors.append("futures contract code missing")
    return {"record_id": obs.get("instrument_id"), "eligible": not errors,
            "errors": errors, "warnings": warnings, "age_seconds": age,
            "mode": "research_only", "trade_authority": False}


def run_pipeline(events: list[dict[str, Any]], ledger: list[dict[str, Any]],
                 registry: dict[str, Any], observations: list[dict[str, Any]],
                 now: datetime, max_market_age: float, max_clock_skew: float) -> dict[str, Any]:
    ledger_ok, ledger_errors = verify_ledger(ledger)
    if not ledger_ok:
        return {"status": "BLOCKED", "reason": "review ledger integrity failure",
                "ledger_errors": ledger_errors, "capital_flow": [], "market_observations": [],
                "authority": "research_only_no_execution_authority"}
    reviews = latest_reviews(ledger)
    event_ids = [event.get("event_id") for event in events]
    duplicate_ids = {item for item in event_ids if event_ids.count(item) > 1}
    cf_results = []
    for event in events:
        result = validate_capital_event(event, reviews, now, registry)
        if result["record_id"] in duplicate_ids:
            result["eligible"] = False
            result["errors"].append("duplicate event_id in batch")
        cf_results.append(result)
    market_results = [validate_market_observation(obs, now, max_market_age, max_clock_skew)
                      for obs in observations]
    all_pass = all(x["eligible"] for x in cf_results + market_results)
    return {"status": "PASS_RESEARCH_GATES" if all_pass else "PARTIAL_OR_BLOCKED",
            "generated_at_utc": now.isoformat().replace("+00:00", "Z"),
            "ledger": {"status": "valid", "entries": len(ledger), "head_hash": ledger[-1]["entry_hash"] if ledger else GENESIS},
            "capital_flow": cf_results, "market_observations": market_results,
            "authority": "research_only_no_execution_authority",
            "important": "Passing these gates is not live readiness, product approval, a trading signal, or execution permission."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline OCC evidence-to-desk research gate")
    parser.add_argument("--events", type=Path, help="Normalized capital-flow JSONL")
    parser.add_argument("--ledger", type=Path, help="Capital-flow review ledger JSONL")
    parser.add_argument("--source-registry", type=Path, help="Capital-flow source registry JSON")
    parser.add_argument("--observations", type=Path, help="Market observations JSONL")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--now-utc", required=True, help="Fixed UTC ISO-8601 reference time ending Z")
    parser.add_argument("--max-market-age-seconds", type=float, default=120)
    parser.add_argument("--max-clock-skew-seconds", type=float, default=5)
    args = parser.parse_args()
    try:
        now = parse_utc(args.now_utc, "--now-utc")
        events = read_jsonl(args.events) if args.events else []
        ledger = read_jsonl(args.ledger) if args.ledger else []
        registry = read_json(args.source_registry) if args.source_registry else {"status": "research_only", "sources": []}
        observations = read_jsonl(args.observations) if args.observations else []
        report = run_pipeline(events, ledger, registry, observations, now,
                              args.max_market_age_seconds, args.max_clock_skew_seconds)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "capital_flow_records": len(events),
                          "market_observations": len(observations), "output": str(args.output),
                          "authority": report["authority"]}, indent=2))
        return 0 if report["status"] == "PASS_RESEARCH_GATES" else 1
    except (OSError, json.JSONDecodeError, GateError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

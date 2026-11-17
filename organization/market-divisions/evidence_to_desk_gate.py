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
        revalidate_by = event.get("revalidate_by_epoch")
        if revalidate_by is not None:
            if isinstance(revalidate_by, bool) or not isinstance(revalidate_by, (int, float)):
                errors.append("revalidate_by_epoch invalid")
            elif now.timestamp() > revalidate_by:
                errors.append("event revalidation deadline has passed")
    except (KeyError, TypeError, ValueError, OverflowError):
        errors.append("observed_at_epoch/ingested_at_epoch invalid")
    source_values = event.get("source_ids", [])
    source_ids = {value for value in source_values if isinstance(value, str)} if isinstance(source_values, list) else set()
    errors.extend(validate_source_registry(registry, source_ids))
    if event_id in reviews:
        review = reviews[event_id]
        status = review.get("review_status")
        if status not in EVENT_REVIEW_STATES:
            errors.append(f"latest review status {status!r} is not handoff-eligible")
        if review.get("action") in {"reject", "expire"}:
            errors.append("latest review action rejects or expires the event")
        if review.get("action") == "challenge":
            errors.append("latest review action challenges the event; resolve before handoff")
        if not isinstance(review.get("reason"), str) or not review.get("reason").strip():
            errors.append("latest review lacks a non-empty rationale")
        review_refs = review.get("evidence_refs", [])
        if not isinstance(review_refs, list):
            errors.append("latest review evidence_refs is not an array")
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
    allowed_types = {"crypto_spot", "crypto_perpetual", "fx_spot", "index_cash",
                     "index_future", "index_cfd", "xauusd_spot", "gold_future", "gold_cfd"}
    if instrument_type not in allowed_types:
        errors.append("instrument_type missing or unsupported")
    for field in ("instrument_id", "venue_or_broker", "source_id", "portfolio_version",
                  "currency", "unit_or_contract_multiplier", "data_class", "licence_status",
                  "session_state"):
        if field not in obs:
            errors.append(f"{field} missing")
    if obs.get("data_class") not in ALLOWED_RESEARCH_DATA:
        errors.append("data_class missing or unsupported")
    if isinstance(obs.get("portfolio_version"), bool) or not isinstance(obs.get("portfolio_version"), int) or obs.get("portfolio_version", -1) < 0:
        errors.append("portfolio_version must be a non-negative integer")
    multiplier = obs.get("unit_or_contract_multiplier")
    if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)) or not math.isfinite(multiplier) or multiplier <= 0:
        errors.append("unit_or_contract_multiplier must be finite and positive")
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
        errors.append("licence status is not approved")
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
        allowed_basis = {
            "xauusd_spot": {"broker_executable_xauusd", "indicative_bullion_spot", "synthetic_test"},
            "gold_future": {"comex_futures", "synthetic_test"},
            "gold_cfd": {"gold_cfd", "synthetic_test"}
        }
        if instrument_type in GOLD_TYPES and obs.get("gold_price_basis") not in allowed_basis[instrument_type]:
            errors.append("Gold price basis does not match the declared instrument type")
        if not isinstance(obs.get("gold_session"), str) or not obs.get("gold_session").strip():
            errors.append("Gold session/calendar provenance must be a non-empty string")
        if obs.get("gold_price_basis") == "indicative_bullion_spot" and instrument_type == "xauusd_spot":
            warnings.append("indicative bullion reference is not broker-executable XAUUSD")
        if obs.get("spot_futures_basis") is not None:
            refs = obs.get("evidence_refs")
            leg_sources = obs.get("spot_futures_leg_source_ids")
            leg_times = obs.get("spot_futures_leg_timestamps_utc")
            if not isinstance(refs, list) or len(set(refs)) < 2:
                errors.append("spot/futures basis requires two distinct evidence references")
            if not isinstance(leg_sources, list) or len(set(leg_sources)) != 2:
                errors.append("spot/futures basis requires two distinct leg source IDs")
            if not isinstance(leg_times, list) or len(leg_times) != 2:
                errors.append("spot/futures basis requires two leg timestamps")
            else:
                try:
                    first = parse_utc(leg_times[0], "spot_futures_leg_timestamps_utc[0]")
                    second = parse_utc(leg_times[1], "spot_futures_leg_timestamps_utc[1]")
                    if abs((first - second).total_seconds()) > max_clock_skew_seconds:
                        errors.append("spot/futures basis legs are not time-aligned")
                except GateError as exc:
                    errors.append(str(exc))
        try:
            quote_age = float(obs["quote_age_seconds"])
            stale_limit = float(obs["stale_threshold_seconds"])
            if not math.isfinite(quote_age) or not math.isfinite(stale_limit) or stale_limit <= 0:
                errors.append("Gold quote age/threshold invalid")
            elif quote_age > stale_limit or obs.get("is_stale") is True:
                errors.append("Gold quote is stale")
            elif age is not None and abs(quote_age - max(age, 0.0)) > max_clock_skew_seconds:
                errors.append("Gold quote_age_seconds conflicts with source timestamp age")
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
    if instrument_type in {"crypto_spot", "crypto_perpetual"}:
        for field in ("base_asset", "quote_asset", "market_pair"):
            if not isinstance(obs.get(field), str) or not obs.get(field).strip():
                errors.append(f"Crypto {field} missing")
        if obs.get("base_asset") == obs.get("quote_asset"):
            errors.append("Crypto base and quote assets must differ")
        if obs.get("token_identity_status") == "unverified":
            errors.append("Crypto token identity is unverified")
        if obs.get("token_identity_status") not in {"verified", "unverified", "not_applicable"}:
            errors.append("Crypto token_identity_status missing or invalid")
        chain_id, contract = obs.get("chain_id"), obs.get("contract_address")
        if (chain_id is None) != (contract is None):
            errors.append("Crypto chain_id and contract_address must both be supplied or both be null")
    if instrument_type == "crypto_perpetual":
        if not isinstance(obs.get("settlement_asset"), str) or not obs.get("settlement_asset"):
            errors.append("Crypto perpetual settlement asset missing")
        rate, interval = obs.get("funding_rate"), obs.get("funding_interval_hours")
        if rate is not None and (isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate)):
            errors.append("Crypto perpetual funding_rate invalid")
        if interval is not None and (isinstance(interval, bool) or not isinstance(interval, (int, float)) or not math.isfinite(interval) or interval <= 0):
            errors.append("Crypto perpetual funding interval invalid")
    if instrument_type == "fx_spot":
        if not obs.get("base_currency") or not obs.get("quote_currency"):
            errors.append("FX base/quote currency mapping missing")
        if obs.get("quote_convention") != "quote_per_base":
            errors.append("FX quote convention must be explicit as quote currency per base unit")
        if obs.get("base_currency") == obs.get("quote_currency"):
            errors.append("FX base and quote currencies must differ")
    if instrument_type == "index_cash":
        if not obs.get("index_code") or not obs.get("index_calculation_currency"):
            errors.append("cash index identity/currency missing")
    if instrument_type in {"index_future", "gold_future"}:
        if not obs.get("contract_code"):
            errors.append("futures contract code missing")
        if not obs.get("expiry_utc"):
            errors.append("futures expiry missing")
    if instrument_type in {"index_cfd", "gold_cfd"}:
        if not obs.get("broker_symbol") or not obs.get("contract_unit"):
            errors.append("broker CFD symbol/contract unit missing")
    return {"record_id": obs.get("instrument_id"), "eligible": not errors,
            "errors": errors, "warnings": warnings, "age_seconds": age,
            "mode": "research_only", "trade_authority": False}


def validate_market_source(obs: dict[str, Any], registry: dict[str, Any] | None) -> list[str]:
    if registry is None:
        return ["market source registry not supplied"]
    if not isinstance(registry, dict):
        return ["market source registry must be a JSON object"]
    errors = []
    instruments = registry.get("instruments")
    if not isinstance(instruments, list):
        return ["market source registry instruments array missing"]
    instrument = next((row for row in instruments
                       if isinstance(row, dict) and row.get("id") == obs.get("instrument_id")), None)
    if instrument is None:
        return [f"instrument {obs.get('instrument_id')!r} absent from market source registry"]
    candidates = instrument.get("candidate_sources", [])
    matched = next((row for row in candidates if isinstance(row, dict)
                    and row.get("name") == obs.get("source_id")), None)
    if matched is None:
        return [f"source {obs.get('source_id')!r} is not a named candidate for instrument"]
    if matched.get("status") not in {"approved_read_only", "approved_manual"}:
        errors.append(f"market source status {matched.get('status')!r} is not approved")
    if matched.get("terms_review") != "approved":
        errors.append("market source terms are not approved")
    if matched.get("canada_review") != "approved":
        errors.append("market source Canada eligibility is not approved")
    return errors


def run_pipeline(events: list[dict[str, Any]], ledger: list[dict[str, Any]],
                 registry: dict[str, Any], observations: list[dict[str, Any]],
                 now: datetime, max_market_age: float, max_clock_skew: float,
                 market_registry: dict[str, Any] | None = None) -> dict[str, Any]:
    if not math.isfinite(max_market_age) or max_market_age <= 0:
        raise GateError("max_market_age_seconds must be finite and positive")
    if not math.isfinite(max_clock_skew) or max_clock_skew < 0:
        raise GateError("max_clock_skew_seconds must be finite and non-negative")
    if not isinstance(registry, dict):
        raise GateError("capital-flow source registry must be a JSON object")
    if market_registry is not None and not isinstance(market_registry, dict):
        raise GateError("market source registry must be a JSON object")
    if not events and not observations:
        return {"status": "BLOCKED", "reason": "no evidence records supplied",
                "ledger_errors": [], "capital_flow": [], "market_observations": [],
                "authority": "research_only_no_execution_authority"}
    ledger_ok, ledger_errors = verify_ledger(ledger)
    if not ledger_ok:
        return {"status": "BLOCKED", "reason": "review ledger integrity failure",
                "ledger_errors": ledger_errors, "capital_flow": [], "market_observations": [],
                "authority": "research_only_no_execution_authority"}
    reviews = latest_reviews(ledger)
    event_ids = [event.get("event_id") for event in events if isinstance(event.get("event_id"), str)]
    duplicate_ids = {item for item in event_ids if event_ids.count(item) > 1}
    cf_results = []
    for event in events:
        result = validate_capital_event(event, reviews, now, registry)
        if result["record_id"] in duplicate_ids:
            result["eligible"] = False
            result["errors"].append("duplicate event_id in batch")
        cf_results.append(result)
    market_results = []
    for obs in observations:
        result = validate_market_observation(obs, now, max_market_age, max_clock_skew)
        result["errors"].extend(validate_market_source(obs, market_registry))
        result["eligible"] = not result["errors"]
        market_results.append(result)
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
    parser.add_argument("--market-source-registry", type=Path, help="Market-data source registry JSON")
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
        market_registry = read_json(args.market_source_registry) if args.market_source_registry else None
        report = run_pipeline(events, ledger, registry, observations, now,
                              args.max_market_age_seconds, args.max_clock_skew_seconds, market_registry)
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

"""Offline multi-desk replay; runs the OCC evidence gate from raw local inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .engines import ASSESSORS, coordinate
    from .capital_flow_handoff import build_handoff, _read_jsonl
except ImportError:  # direct script execution
    from engines import ASSESSORS, coordinate
    from capital_flow_handoff import build_handoff, _read_jsonl

# Run from organization/market-divisions so this resolves the canonical gate.
import evidence_to_desk_gate as _evidence_gate
parse_utc = _evidence_gate.parse_utc
run_pipeline = _evidence_gate.run_pipeline


DESK_TYPES = {
    "crypto": {"crypto_spot", "crypto_perpetual"},
    "forex": {"fx_spot"},
    "indices": {"index_cash", "index_future", "index_cfd"},
    "gold": {"xauusd_spot", "gold_future", "gold_cfd"},
}


def replay(observations: list[dict[str, Any]], now_utc: str,
           market_source_registry: dict[str, Any],
           capital_flow_events: list[dict[str, Any]] | None = None,
           capital_flow_reviews: list[dict[str, Any]] | None = None,
           capital_flow_source_registry: dict[str, Any] | None = None,
           max_market_age_seconds: float = 120,
           max_clock_skew_seconds: float = 5) -> dict[str, Any]:
    """Run the OCC evidence gate internally from raw observations and source registry.

    There is deliberately no gate-report parameter. A caller cannot promote an
    arbitrary JSON report by setting status/authority strings; the gate is rerun
    over the supplied source snapshots immediately before desk assessment.
    """
    if not isinstance(observations, list) or not observations:
        raise ValueError("non-empty raw observations list required")
    if not isinstance(market_source_registry, dict):
        raise ValueError("market source registry JSON object required")
    now = parse_utc(now_utc, "now_utc")
    gate_report = run_pipeline(
        events=[],
        ledger=[],
        registry={"status": "research_only", "sources": []},
        observations=observations,
        now=now,
        max_market_age=max_market_age_seconds,
        max_clock_skew=max_clock_skew_seconds,
        market_registry=market_source_registry,
    )
    errors: list[str] = []
    if gate_report.get("authority") != "research_only_no_execution_authority":
        errors.append("internally generated evidence gate authority marker invalid")
    if gate_report.get("status") != "PASS_RESEARCH_GATES":
        errors.append("internally generated OCC evidence gate did not pass")
    gate_rows = gate_report.get("market_observations")
    if not isinstance(gate_rows, list):
        errors.append("internally generated gate market_observations array missing")
        gate_rows = []
    gate_by_id: dict[str, list[dict[str, Any]]] = {}
    for row in gate_rows:
        if isinstance(row, dict) and isinstance(row.get("record_id"), str):
            gate_by_id.setdefault(row["record_id"], []).append(row)

    packets = []
    seen: set[str] = set()
    for obs in observations:
        instrument_id = obs.get("instrument_id") if isinstance(obs, dict) else None
        if not isinstance(instrument_id, str) or not instrument_id:
            packets.append({
                "desk_id": "unknown", "instrument_id": instrument_id,
                "status": "halt", "mode": "research_only", "trade_authority": False,
                "data_quality": {"errors": ["instrument_id missing"], "warnings": []},
                "risk_flags": ["EVIDENCE_GATE_BLOCK"],
            })
            continue
        if instrument_id in seen:
            errors.append(f"duplicate instrument_id in replay batch: {instrument_id}")
        seen.add(instrument_id)
        matches = gate_by_id.get(instrument_id, [])
        desk = next((name for name, kinds in DESK_TYPES.items()
                     if isinstance(obs, dict) and obs.get("instrument_type") in kinds), "unknown")
        if len(matches) != 1 or matches[0].get("eligible") is not True:
            packets.append({
                "desk_id": desk, "instrument_id": instrument_id,
                "instrument_type": obs.get("instrument_type") if isinstance(obs, dict) else None,
                "as_of_utc": now_utc, "mode": "research_only",
                "status": "halt", "trade_authority": False,
                "data_quality": {
                    "errors": ["raw observation failed internally rerun OCC evidence gate"],
                    "warnings": matches[0].get("warnings", []) if len(matches) == 1 else [],
                },
                "risk_flags": ["EVIDENCE_GATE_BLOCK"],
            })
            continue
        if desk == "unknown":
            errors.append(f"unsupported instrument type for {instrument_id}")
            continue
        packet = ASSESSORS[desk](obs, now_utc)
        gate_warnings = matches[0].get("warnings", [])
        packet["data_quality"]["warnings"] = sorted(set(
            packet["data_quality"]["warnings"] + [f"OCC_GATE: {w}" for w in gate_warnings]
        ))
        if packet["status"] == "research" and packet["data_quality"]["warnings"]:
            packet["status"] = "unverified"
        packet["evidence_gate"] = {
            "eligible": True,
            "warnings": gate_warnings,
            "method": "rerun_from_raw_observation_and_source_registry",
            "max_market_age_seconds": max_market_age_seconds,
            "max_clock_skew_seconds": max_clock_skew_seconds,
        }
        if desk == "crypto" and capital_flow_events is not None:
            try:
                handoff = build_handoff(
                    capital_flow_events, capital_flow_reviews or [],
                    capital_flow_source_registry or {}, obs, now_utc,
                )
                packet["capital_flow_handoff"] = handoff
                if handoff["rejected_matching_events"]:
                    packet["data_quality"]["warnings"].append(
                        "one or more matching Capital Flow events were rejected by the handoff gate"
                    )
                    if packet["status"] == "research":
                        packet["status"] = "unverified"
            except (ValueError, TypeError) as exc:
                packet["capital_flow_handoff"] = {
                    "status": "blocked", "reason": str(exc),
                    "destination_desk": "crypto",
                    "event_records": [], "rejected_matching_events": [],
                    "mode": "research_only",
                    "trade_authority": False, "live_readiness": False,
                }
                packet["data_quality"]["warnings"].append("Capital Flow handoff validation failed")
                packet["risk_flags"].append("CAPITAL_FLOW_HANDOFF_REJECTED")
                if packet["status"] == "research":
                    packet["status"] = "unverified"
        packets.append(packet)

    instrument_desks: dict[str, set[str]] = {}
    for packet in packets:
        iid, desk = packet.get("instrument_id"), packet.get("desk_id")
        if isinstance(iid, str) and isinstance(desk, str):
            instrument_desks.setdefault(iid, set()).add(desk)
    collisions = sorted(iid for iid, desks in instrument_desks.items() if len(desks) > 1)
    if collisions:
        errors.append("instrument identity assigned to multiple desks: " + ",".join(collisions))

    occ = coordinate(packets, now_utc)
    if errors:
        occ["status"] = "halt"
        occ["errors"].extend(errors)
    crypto_handoffs = [p.get("capital_flow_handoff") for p in packets
                       if isinstance(p, dict) and isinstance(p.get("capital_flow_handoff"), dict)]
    accepted = sum(len(h.get("event_records", [])) for h in crypto_handoffs
                   if isinstance(h.get("event_records"), list))
    flow_status = ("consumed_research_context" if accepted else
                   "provided_no_eligible_match" if capital_flow_events is not None else "not_consumed")
    gate_code_path = Path(_evidence_gate.__file__).resolve()
    gate_code_sha256 = hashlib.sha256(gate_code_path.read_bytes()).hexdigest()

    def canonical_sha256(value: Any) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    observations_sha256 = canonical_sha256(observations)
    market_registry_sha256 = canonical_sha256(market_source_registry)
    capital_flow_inputs_sha256 = None
    if capital_flow_events is not None:
        capital_flow_inputs_sha256 = {
            "events": canonical_sha256(capital_flow_events),
            "reviews": canonical_sha256(capital_flow_reviews or []),
            "source_registry": canonical_sha256(capital_flow_source_registry or {}),
        }
    return {
        "schema_version": "1.2.0",
        "run_type": "offline_multi_desk_replay",
        "as_of_utc": now_utc,
        "status": occ["status"],
        "desk_packets": packets,
        "occ": occ,
        "evidence_gate": {
            "status": gate_report["status"],
            "authority": gate_report["authority"],
            "method": "rerun_from_raw_observation_and_source_registry",
            "market_observation_count": len(gate_rows),
            "max_market_age_seconds": max_market_age_seconds,
            "max_clock_skew_seconds": max_clock_skew_seconds,
            "observations_sha256": observations_sha256,
            "market_source_registry_sha256": market_registry_sha256,
            "gate_implementation_sha256": gate_code_sha256,
            "capital_flow_inputs_sha256": capital_flow_inputs_sha256,
            "evaluation_time_utc": now_utc,
            "digest_note": "Reproducibility/integrity identifiers only; not signatures or source authentication",
        },
        "capital_flow_handoff": {
            "status": flow_status, "accepted_event_count": accepted,
            "reason": ("Validated exact-identity research context attached to Crypto packets"
                       if accepted else
                       "No eligible Capital Flow event was attached; market evidence gate remains independent"),
            "trade_authority": False,
        },
        "authority": "research_only_no_execution_authority",
        "trade_authority": False,
        "live_readiness": False,
        "limitations": [
            "OCC evidence gate is rerun from local raw observations and source registry; no supplied gate report is trusted",
            "Passing evidence gates is not live readiness or execution permission",
            "Capital-flow handoff is separate research context and never replaces the market evidence gate",
            "Local registry assertions are not independent proof of source authenticity or legal rights",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline OCC multi-desk replay with internally rerun evidence gate")
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--market-source-registry", type=Path, required=True)
    parser.add_argument("--now-utc", required=True)
    parser.add_argument("--max-market-age-seconds", type=float, default=120)
    parser.add_argument("--max-clock-skew-seconds", type=float, default=5)
    parser.add_argument("--capital-flow-events", type=Path)
    parser.add_argument("--capital-flow-reviews", type=Path)
    parser.add_argument("--capital-flow-source-registry", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        observations = _read_jsonl(args.observations)
        market_registry = json.loads(args.market_source_registry.read_text(encoding="utf-8"))
        flow_args = (args.capital_flow_events, args.capital_flow_reviews,
                     args.capital_flow_source_registry)
        if any(flow_args) and not all(flow_args):
            raise ValueError("all three Capital Flow inputs must be supplied together")
        flow_events = _read_jsonl(args.capital_flow_events) if args.capital_flow_events else None
        flow_reviews = _read_jsonl(args.capital_flow_reviews) if args.capital_flow_reviews else None
        flow_registry = (json.loads(args.capital_flow_source_registry.read_text(encoding="utf-8"))
                         if args.capital_flow_source_registry else None)
        result = replay(
            observations, args.now_utc, market_registry, flow_events, flow_reviews,
            flow_registry, args.max_market_age_seconds, args.max_clock_skew_seconds,
        )
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": result["status"], "desk_packets": len(result["desk_packets"]),
                          "output": str(args.output), "authority": result["authority"],
                          "evidence_gate": result["evidence_gate"]}, indent=2))
        return 0 if result["status"] in {"research", "unverified"} else 1
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Offline multi-desk replay harness joining OCC evidence-gate output to desk engines."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .engines import ASSESSORS, coordinate
except ImportError:  # direct script execution
    from engines import ASSESSORS, coordinate


def replay(observations: list[dict[str, Any]], gate_report: dict[str, Any],
           now_utc: str) -> dict[str, Any]:
    """Run desk assessors only for observations explicitly eligible in gate report."""
    errors: list[str] = []
    if gate_report.get("authority") != "research_only_no_execution_authority":
        errors.append("evidence gate report authority marker missing or invalid")
    if gate_report.get("status") != "PASS_RESEARCH_GATES":
        errors.append("evidence gate did not pass all supplied research gates")
    gate_rows = gate_report.get("market_observations")
    if not isinstance(gate_rows, list):
        errors.append("evidence gate market_observations array missing")
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
        gate_matches = gate_by_id.get(instrument_id, [])
        if len(gate_matches) != 1 or gate_matches[0].get("eligible") is not True:
            desk = next((name for name, kinds in {
                "crypto": {"crypto_spot", "crypto_perpetual"},
                "forex": {"fx_spot"},
                "indices": {"index_cash", "index_future", "index_cfd"},
                "gold": {"xauusd_spot", "gold_future", "gold_cfd"},
            }.items() if obs.get("instrument_type") in kinds), "unknown")
            packets.append({
                "desk_id": desk, "instrument_id": instrument_id,
                "instrument_type": obs.get("instrument_type"),
                "as_of_utc": now_utc, "mode": "research_only",
                "status": "halt", "trade_authority": False,
                "data_quality": {"errors": ["observation lacks exactly one eligible OCC evidence-gate result"],
                                 "warnings": []},
                "risk_flags": ["EVIDENCE_GATE_BLOCK"],
            })
            continue
        desk = next((name for name, kinds in {
            "crypto": {"crypto_spot", "crypto_perpetual"},
            "forex": {"fx_spot"},
            "indices": {"index_cash", "index_future", "index_cfd"},
            "gold": {"xauusd_spot", "gold_future", "gold_cfd"},
        }.items() if obs.get("instrument_type") in kinds), None)
        if desk is None:
            errors.append(f"unsupported instrument type for {instrument_id}")
            continue
        assessor = ASSESSORS[desk]
        packet = assessor(obs, now_utc)
        gate_warnings = gate_matches[0].get("warnings", [])
        packet["data_quality"]["warnings"] = sorted(set(
            packet["data_quality"]["warnings"] + [f"OCC_GATE: {w}" for w in gate_warnings]
        ))
        if packet["status"] == "research" and packet["data_quality"]["warnings"]:
            packet["status"] = "unverified"
        packet["evidence_gate"] = {"eligible": True, "warnings": gate_warnings}
        packets.append(packet)

    # Cross-desk identity collisions are not silently resolved.
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
    return {
        "schema_version": "1.0.0",
        "run_type": "offline_multi_desk_replay",
        "as_of_utc": now_utc,
        "status": occ["status"],
        "desk_packets": packets,
        "occ": occ,
        "capital_flow_handoff": {
            "status": "not_consumed",
            "reason": "No verified capital-flow-to-Crypto handoff supplied to this replay",
            "trade_authority": False,
        },
        "authority": "research_only_no_execution_authority",
        "live_readiness": False,
        "limitations": [
            "Replay only; no live feed or unattended monitoring",
            "Passing evidence gates is not live readiness or execution permission",
            "Capital-flow handoff is not implicitly inferred from market observations",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline OCC multi-desk replay")
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--gate-report", type=Path, required=True)
    parser.add_argument("--now-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        observations = [json.loads(line) for line in args.observations.read_text(encoding="utf-8").splitlines() if line.strip()]
        gate_report = json.loads(args.gate_report.read_text(encoding="utf-8"))
        result = replay(observations, gate_report, args.now_utc)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": result["status"], "desk_packets": len(result["desk_packets"]),
                          "output": str(args.output), "authority": result["authority"]}, indent=2))
        return 0 if result["status"] in {"research", "unverified"} else 1
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

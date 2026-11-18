"""Unified offline OCC research-intelligence intake.

Composes the canonical raw-input evidence gate, specialist replay, Capital Flow
research context, evidence provenance index, global stop propagation and
explicit day/night handover validation. No network or execution capability.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MARKET_DIVISIONS = HERE.parent
if str(MARKET_DIVISIONS) not in sys.path:
    sys.path.insert(0, str(MARKET_DIVISIONS))

try:
    from .replay import replay
    from .capital_flow_handoff import _read_jsonl
    from .portfolio_risk import assess_portfolio_risk
except ImportError:
    from replay import replay
    from capital_flow_handoff import _read_jsonl
    from portfolio_risk import assess_portfolio_risk


DESK_IDS = ("crypto", "forex", "indices", "gold")
STOP_STATES = {"HALT", "STOP", "VETO", "ACTIVE_HALT"}


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field} must be a UTC ISO-8601 timestamp ending Z")
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid UTC timestamp") from exc
    if result.utcoffset() != timezone.utc.utcoffset(result):
        raise ValueError(f"{field} must be UTC")
    return result


def validate_handover(record: dict[str, Any] | None, now_utc: str,
                      expected_portfolio_version: Any = None) -> dict[str, Any]:
    """Validate explicit shift acceptance; absence never implies handover."""
    if record is None:
        return {"status": "not_provided", "accepted": False,
                "errors": ["no explicit day/night handover record supplied"]}
    errors: list[str] = []
    required_text = ("outgoing_shift_id", "incoming_shift_id", "snapshot_id")
    for key in required_text:
        if not isinstance(record.get(key), str) or not record[key].strip():
            errors.append(f"{key} missing")
    if record.get("outgoing_shift_id") == record.get("incoming_shift_id"):
        errors.append("outgoing and incoming shift identifiers must differ")
    try:
        handover_time = _utc(record.get("handover_at_utc"), "handover_at_utc")
        if handover_time > _utc(now_utc, "now_utc"):
            errors.append("handover timestamp is in the future")
    except ValueError as exc:
        errors.append(str(exc))
    version = record.get("portfolio_version")
    if not isinstance(version, (str, int)) or isinstance(version, bool):
        errors.append("handover portfolio_version missing or invalid")
    if expected_portfolio_version is not None and version != expected_portfolio_version:
        errors.append("handover portfolio_version does not match intake snapshot")
    for key in ("outgoing_acknowledged", "incoming_acknowledged", "positions_reconciled"):
        if record.get(key) is not True:
            errors.append(f"{key} must be explicitly true")
    expected_desks = {"crypto", "forex", "indices", "gold"}
    coverage = record.get("desk_coverage")
    if (not isinstance(coverage, dict) or set(coverage) != expected_desks
            or any(not isinstance(coverage.get(desk), int)
                   or isinstance(coverage.get(desk), bool)
                   or coverage[desk] < 1 for desk in expected_desks)):
        errors.append("desk_coverage must include positive instrument counts for Crypto, Forex, indices and Gold")
    reconciled = record.get("positions_reconciled_by_desk")
    if (not isinstance(reconciled, dict) or set(reconciled) != expected_desks
            or any(reconciled.get(desk) is not True for desk in expected_desks)):
        errors.append("positions_reconciled_by_desk must explicitly confirm all four specialist desks")
    if record.get("dependency_health") != "healthy":
        errors.append("critical dependency health is not explicitly healthy")
    vetoes = record.get("active_veto_ids")
    critical = record.get("unresolved_critical_items")
    if not isinstance(vetoes, list) or any(not isinstance(x, str) or not x for x in vetoes):
        errors.append("active_veto_ids must be an array of identifiers")
    if not isinstance(critical, list) or critical:
        errors.append("unresolved_critical_items must be an explicitly empty array")
    return {"status": "accepted" if not errors else "blocked",
            "accepted": not errors, "errors": errors,
            "active_veto_ids": vetoes if isinstance(vetoes, list) else [],
            "snapshot_id": record.get("snapshot_id"),
            "outgoing_shift_id": record.get("outgoing_shift_id"),
            "incoming_shift_id": record.get("incoming_shift_id")}


def _packet_errors(packet: dict[str, Any], now_utc: str,
                   expected_portfolio_version: Any) -> list[str]:
    errors = []
    if packet.get("mode") != "research_only":
        errors.append("specialist packet is not research_only")
    if packet.get("trade_authority") is not False:
        errors.append("specialist packet trade_authority must be false")
    if packet.get("live_readiness") not in (None, False):
        errors.append("specialist packet cannot assert live readiness")
    if packet.get("as_of_utc") != now_utc:
        errors.append("specialist packet evaluation time mismatch")
    if expected_portfolio_version is not None and packet.get("portfolio_version") != expected_portfolio_version:
        errors.append("specialist packet portfolio version mismatch")
    if not isinstance(packet.get("evidence_refs"), list):
        errors.append("specialist packet evidence_refs missing or invalid")
    if not isinstance(packet.get("risk_flags"), list):
        errors.append("specialist packet risk_flags missing or invalid")
    return errors


def build_unified_intake(observations: list[dict[str, Any]], now_utc: str,
                         market_source_registry: dict[str, Any],
                         capital_flow_events: list[dict[str, Any]] | None = None,
                         capital_flow_reviews: list[dict[str, Any]] | None = None,
                         capital_flow_source_registry: dict[str, Any] | None = None,
                         handover: dict[str, Any] | None = None,
                         expected_portfolio_version: Any = None,
                         previous_global_stop: bool = False,
                         occ_stop_state: str | None = None,
                         max_market_age_seconds: float = 120,
                         max_clock_skew_seconds: float = 5,
                         require_full_coverage: bool = False,
                         control_health_snapshot_history: Path | None = None,
                         control_health_event_ledger: Path | None = None,
                         portfolio_risk_config: dict[str, Any] | None = None,
                         correlation_evidence: list[dict[str, Any]] | None = None,
                         oanda_account_margin_replay: dict[str, Any] | None = None,
                         oanda_pending_order_snapshot: dict[str, Any] | None = None,
                         oanda_closeout_transaction_replay: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build one immutable-style research snapshot from local source snapshots."""
    evaluation_time = _utc(now_utc, "now_utc")
    audit_paths = (control_health_snapshot_history, control_health_event_ledger)
    if any(value is not None for value in audit_paths) and not all(value is not None for value in audit_paths):
        raise ValueError("control-health snapshot history and event ledger paths must be supplied together")
    flow_args = (capital_flow_events, capital_flow_reviews, capital_flow_source_registry)
    if any(value is not None for value in flow_args) and not all(value is not None for value in flow_args):
        raise ValueError("Capital Flow events, reviews and source registry must be supplied together")
    if expected_portfolio_version is not None:
        for obs in observations:
            if obs.get("portfolio_version") != expected_portfolio_version:
                raise ValueError("observation portfolio version mismatch before replay")

    replay_result = replay(
        observations, now_utc, market_source_registry,
        capital_flow_events, capital_flow_reviews, capital_flow_source_registry,
        max_market_age_seconds, max_clock_skew_seconds,
    )
    packets = replay_result.get("desk_packets", [])
    packet_errors: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    evidence_index: dict[str, list[dict[str, str]]] = {}
    desk_coverage = {desk: 0 for desk in DESK_IDS}
    active_stops: list[dict[str, str]] = []

    for packet in packets:
        if not isinstance(packet, dict):
            packet_errors.append({"instrument_id": "unknown", "errors": ["packet is not an object"]})
            continue
        instrument_id = packet.get("instrument_id")
        desk_id = packet.get("desk_id")
        if isinstance(instrument_id, str):
            if instrument_id in seen_ids:
                packet_errors.append({"instrument_id": instrument_id, "errors": ["duplicate instrument ID"]})
            seen_ids.add(instrument_id)
        if desk_id in desk_coverage:
            desk_coverage[desk_id] += 1
        errors = _packet_errors(packet, now_utc, expected_portfolio_version)
        if errors:
            packet_errors.append({"instrument_id": str(instrument_id), "errors": errors})
        for ref in packet.get("evidence_refs", []) if isinstance(packet.get("evidence_refs"), list) else []:
            evidence_index.setdefault(ref, []).append({
                "desk_id": str(desk_id), "instrument_id": str(instrument_id),
                "evidence_type": "market_observation",
            })
        handoff = packet.get("capital_flow_handoff")
        if isinstance(handoff, dict):
            for event_record in handoff.get("event_records", []) if isinstance(handoff.get("event_records"), list) else []:
                for ref in event_record.get("evidence_refs", []) if isinstance(event_record, dict) else []:
                    evidence_index.setdefault(ref, []).append({
                        "desk_id": "crypto", "instrument_id": str(instrument_id),
                        "evidence_type": "capital_flow_event",
                    })
        if packet.get("status") == "halt" or "STOP_CHALLENGE" in packet.get("risk_flags", []):
            active_stops.append({"source": str(desk_id), "instrument_id": str(instrument_id),
                                 "reason": "specialist_halt_or_stop_challenge"})
    capital_flow_packets = []
    capital_flow_boundary_errors = []
    for packet in packets:
        if not isinstance(packet, dict) or packet.get("desk_id") != "crypto":
            continue
        handoff = packet.get("capital_flow_handoff")
        if handoff is None:
            continue
        if (not isinstance(handoff, dict)
                or handoff.get("mode") != "research_only"
                or handoff.get("destination_desk") != "crypto"
                or handoff.get("trade_authority") is not False
                or handoff.get("live_readiness") is not False
                or not isinstance(handoff.get("event_records"), list)
                or not isinstance(handoff.get("rejected_matching_events"), list)):
            capital_flow_boundary_errors.append(
                f"{packet.get('instrument_id')}: malformed or authority-violating Capital Flow handoff"
            )
            continue
        capital_flow_packets.append({
            "instrument_id": packet.get("instrument_id"),
            "status": handoff.get("status", "provided"),
            "accepted_event_ids": sorted(
                item["event_id"] for item in handoff["event_records"]
                if isinstance(item, dict) and isinstance(item.get("event_id"), str)
            ),
            "accepted_event_summaries": [
                {"event_id": item.get("event_id"),
                 "event_classification": item.get("event_classification"),
                 "evidence_provenance": item.get("evidence_provenance"),
                 "research_priority": item.get("research_priority")}
                for item in handoff["event_records"] if isinstance(item, dict)
            ],
            "rejected_events": [
                {"event_id": item.get("event_id"), "reason": item.get("reason")}
                for item in handoff["rejected_matching_events"] if isinstance(item, dict)
            ],
            "review_ledger": handoff.get("review_ledger"),
            "trade_authority": False,
            "live_readiness": False,
        })
    if capital_flow_boundary_errors:
        packet_errors.append({"instrument_id": "capital_flow_boundary",
                              "errors": capital_flow_boundary_errors})

    capital_flow_audit = {
        "status": ("blocked" if capital_flow_boundary_errors or any(x["status"] == "blocked" for x in capital_flow_packets) else
                   "consumed_research_context" if any(x["accepted_event_ids"] for x in capital_flow_packets) else
                   "provided_no_eligible_match" if capital_flow_packets else "not_consumed"),
        "instrument_count": len(capital_flow_packets),
        "accepted_event_count": sum(len(x["accepted_event_ids"]) for x in capital_flow_packets),
        "rejected_event_count": sum(len(x["rejected_events"]) for x in capital_flow_packets),
        "instruments": capital_flow_packets,
        "boundary_errors": capital_flow_boundary_errors,
        "mode": "research_only",
        "trade_authority": False,
        "live_readiness": False,
    }

    gold_specialist_packets = []
    for packet in packets:
        if not isinstance(packet, dict) or packet.get("desk_id") != "gold":
            continue
        context = packet.get("context", {})
        specialist = context.get("gold_specialist_research") if isinstance(context, dict) else None
        if not isinstance(specialist, dict):
            gold_specialist_packets.append({
                "instrument_id": packet.get("instrument_id"),
                "status": "NOT_PROVIDED",
                "macro_factor_count": 0,
                "macro_factor_coverage": {},
                "errors": [],
                "warnings": ["Structured Gold specialist context was not supplied."],
                "trade_authority": False,
                "live_readiness": False,
            })
            continue
        specialist_status = specialist.get("status")
        specialist_errors = specialist.get("errors")
        specialist_warnings = specialist.get("warnings")
        macro_count = specialist.get("macro_factor_count")
        macro_coverage = specialist.get("macro_factor_coverage")
        boundary_errors = []
        if specialist_status not in {"research", "unverified", "halt"}:
            boundary_errors.append("Gold specialist status is missing or unrecognized")
            specialist_status = "halt"
        if (specialist.get("trade_authority") is not False
                or specialist.get("live_readiness") is not False
                or specialist.get("authority") != "research_only_no_execution_authority"):
            boundary_errors.append("Gold specialist context violates research-only authority boundary")
        if not isinstance(macro_count, int) or isinstance(macro_count, bool) or not 0 <= macro_count <= 8:
            boundary_errors.append("Gold macro_factor_count is invalid")
            macro_count = 0
        if not isinstance(macro_coverage, dict):
            boundary_errors.append("Gold macro_factor_coverage must be an object")
            macro_coverage = {}
        if not isinstance(specialist_errors, list) or any(not isinstance(x, str) for x in specialist_errors):
            boundary_errors.append("Gold specialist errors must be an array of strings")
            specialist_errors = ["Gold specialist errors field is malformed"]
        if not isinstance(specialist_warnings, list) or any(not isinstance(x, str) for x in specialist_warnings):
            boundary_errors.append("Gold specialist warnings must be an array of strings")
            specialist_warnings = ["Gold specialist warnings field is malformed"]
        if boundary_errors:
            packet_errors.append({
                "instrument_id": str(packet.get("instrument_id")),
                "errors": boundary_errors,
            })
            specialist_status = "halt"
            specialist_errors = list(specialist_errors) + boundary_errors
        gold_specialist_packets.append({
            "instrument_id": packet.get("instrument_id"),
            "status": specialist_status,
            "price_basis": specialist.get("price_basis"),
            "macro_factor_count": macro_count,
            "macro_factor_coverage": macro_coverage,
            "source_independence_verified": specialist.get("source_independence_verified", False),
            "errors": specialist_errors,
            "warnings": specialist_warnings,
            "trade_authority": False,
            "live_readiness": False,
        })
    gold_statuses = [item["status"] for item in gold_specialist_packets]
    gold_specialist_audit = {
        "status": ("NOT_PROVIDED" if not gold_specialist_packets
                   or all(item["status"] == "NOT_PROVIDED" for item in gold_specialist_packets)
                   else "HALT" if any(item["status"] == "halt" for item in gold_specialist_packets)
                   else "WARN" if any(item["status"] == "unverified" for item in gold_specialist_packets)
                   else "PASS"),
        "instrument_count": len(gold_specialist_packets),
        "instruments": gold_specialist_packets,
        "trade_authority": False,
        "live_readiness": False,
    }

    missing_desks = [desk for desk, count in desk_coverage.items() if count == 0]
    if require_full_coverage and missing_desks:
        packet_errors.append({"instrument_id": "coverage", "errors": [
            "required specialist desk coverage missing: " + ", ".join(missing_desks)
        ]})

    if occ_stop_state is not None:
        normalized_stop = occ_stop_state.upper()
        if normalized_stop in STOP_STATES:
            active_stops.append({"source": "occ_control", "instrument_id": "all",
                                 "reason": "explicit_OCC_stop_state_" + normalized_stop})
        elif normalized_stop not in {"CLEAR", "INACTIVE", "NONE"}:
            packet_errors.append({"instrument_id": "occ_control", "errors": ["unknown OCC stop state"]})
    portfolio_risk_audit = assess_portfolio_risk(packets, now_utc, portfolio_risk_config, correlation_evidence)
    oanda_account_margin_audit = {
        "status": "NOT_PROVIDED", "report": None,
        "errors": ["OANDA account-level margin replay was not supplied"],
        "trade_authority": False, "live_readiness": False,
    }
    if oanda_account_margin_replay is not None:
        try:
            from .oanda_account_margin_closeout import replay_oanda_account_margin_closeout
        except ImportError:
            from oanda_account_margin_closeout import replay_oanda_account_margin_closeout
        if not isinstance(oanda_account_margin_replay, dict):
            margin_report = {
                "status": "BLOCKED_INVALID_OR_INCOMPLETE_INPUT",
                "errors": ["oanda_account_margin_replay must be an object"],
                "trade_authority": False, "live_readiness": False,
                "research_only": True,
                "authority": "research_only_no_execution_authority",
            }
        else:
            try:
                margin_report = replay_oanda_account_margin_closeout(**oanda_account_margin_replay)
            except TypeError as exc:
                margin_report = {
                    "status": "BLOCKED_INVALID_OR_INCOMPLETE_INPUT",
                    "errors": [f"invalid OANDA account margin replay input shape: {exc}"],
                    "trade_authority": False, "live_readiness": False,
                    "research_only": True,
                    "authority": "research_only_no_execution_authority",
                }
        if isinstance(oanda_account_margin_replay, dict) and isinstance(oanda_account_margin_replay.get("observations"), list):
            future_observations = []
            for index, observation in enumerate(oanda_account_margin_replay["observations"]):
                if isinstance(observation, dict):
                    try:
                        if _utc(observation.get("timestamp_utc"), f"oanda_account_margin_replay.observations[{index}].timestamp_utc") > evaluation_time:
                            future_observations.append(index)
                    except ValueError:
                        pass
            if future_observations:
                margin_report["status"] = "BLOCKED_INVALID_OR_INCOMPLETE_INPUT"
                margin_report.setdefault("errors", []).append("OANDA account-margin observations cannot be later than the unified snapshot evaluation time")
        margin_status = margin_report.get("status")
        oanda_account_margin_audit = {
            "status": "PASS" if margin_status == "WITHIN_MARGIN_REQUIREMENTS" else "HALT",
            "report": margin_report,
            "errors": margin_report.get("errors", []),
            "trade_authority": False, "live_readiness": False,
        }
        if oanda_account_margin_audit["status"] == "HALT":
            active_stops.append({
                "source": "oanda_account_margin", "instrument_id": "account",
                "reason": "OANDA_ACCOUNT_MARGIN_CALL_CLOSEOUT_OR_INVALID_REPLAY",
            })
    oanda_pending_order_audit = {
        "status": "NOT_PROVIDED", "report": None,
        "errors": ["OANDA post-closeout pending-order snapshot was not supplied"],
        "trade_authority": False, "live_readiness": False,
    }
    margin_replay_report = oanda_account_margin_audit.get("report")
    closeout_batches = margin_replay_report.get("closeout_batches") if isinstance(margin_replay_report, dict) else None
    if oanda_pending_order_snapshot is None and isinstance(closeout_batches, list) and closeout_batches:
        missing_pending_report = {
            "status": "HALT",
            "errors": ["A margin closeout was recorded but no post-closeout pending-order snapshot was supplied."],
            "warnings": [], "closeout_occurred": True,
            "pending_orders_complete": False, "possible_exposure_reopening": True,
            "order_cancellation_performed": False,
            "trade_authority": False, "live_readiness": False,
            "research_only": True, "authority": "research_only_no_execution_authority",
        }
        oanda_pending_order_audit = {
            "status": "HALT", "report": missing_pending_report,
            "errors": missing_pending_report["errors"],
            "trade_authority": False, "live_readiness": False,
        }
        active_stops.append({
            "source": "oanda_pending_orders", "instrument_id": "account",
            "reason": "POST_CLOSEOUT_PENDING_ORDER_RECONCILIATION_MISSING",
        })
    if oanda_pending_order_snapshot is not None:
        try:
            from .oanda_pending_order_exposure import assess_oanda_post_closeout_pending_orders
        except ImportError:
            from oanda_pending_order_exposure import assess_oanda_post_closeout_pending_orders
        if not isinstance(oanda_pending_order_snapshot, dict):
            pending_report = {
                "status": "HALT", "errors": ["oanda_pending_order_snapshot must be an object"],
                "warnings": [], "trade_authority": False, "live_readiness": False,
                "research_only": True, "authority": "research_only_no_execution_authority",
            }
        else:
            try:
                pending_report = assess_oanda_post_closeout_pending_orders(**oanda_pending_order_snapshot)
            except TypeError as exc:
                pending_report = {
                    "status": "HALT", "errors": [f"invalid OANDA pending-order snapshot shape: {exc}"],
                    "warnings": [], "trade_authority": False, "live_readiness": False,
                    "research_only": True, "authority": "research_only_no_execution_authority",
                }
        if isinstance(oanda_pending_order_snapshot, dict):
            try:
                if _utc(oanda_pending_order_snapshot.get("evaluated_at_utc"), "oanda_pending_order_snapshot.evaluated_at_utc") > evaluation_time:
                    pending_report["status"] = "HALT"
                    pending_report.setdefault("errors", []).append("OANDA pending-order audit evaluation cannot be later than the unified snapshot time")
            except ValueError:
                pass
        pending_status = pending_report.get("status")
        oanda_pending_order_audit = {
            "status": "PASS" if pending_status == "PASS" else "HALT",
            "report": pending_report,
            "errors": pending_report.get("errors", []),
            "trade_authority": False, "live_readiness": False,
        }
        if oanda_pending_order_audit["status"] == "HALT":
            active_stops.append({
                "source": "oanda_pending_orders", "instrument_id": "account",
                "reason": "OANDA_POST_CLOSEOUT_PENDING_ORDERS_MAY_REOPEN_EXPOSURE_OR_AUDIT_INVALID",
            })
    oanda_closeout_transaction_audit = {
        "status": "NOT_PROVIDED", "report": None,
        "errors": ["OANDA closeout transaction reconciliation was not supplied"],
        "trade_authority": False, "live_readiness": False,
    }
    if isinstance(closeout_batches, list) and closeout_batches and oanda_closeout_transaction_replay is None:
        missing_tx_report = {
            "status": "HALT",
            "errors": ["A margin closeout was recorded but no complete OANDA transaction-ID range was supplied."],
            "warnings": [], "transaction_range_complete": False,
            "cancellation_reconciliation_complete": False,
            "order_cancellation_performed": False, "trade_authority": False,
            "live_readiness": False, "research_only": True,
            "authority": "research_only_no_execution_authority",
        }
        oanda_closeout_transaction_audit = {
            "status": "HALT", "report": missing_tx_report,
            "errors": missing_tx_report["errors"],
            "trade_authority": False, "live_readiness": False,
        }
        active_stops.append({
            "source": "oanda_closeout_transactions", "instrument_id": "account",
            "reason": "POST_CLOSEOUT_TRANSACTION_RECONCILIATION_MISSING",
        })
    if oanda_closeout_transaction_replay is not None:
        try:
            from .oanda_closeout_transaction_reconciliation import assess_oanda_closeout_transaction_reconciliation
        except ImportError:
            from oanda_closeout_transaction_reconciliation import assess_oanda_closeout_transaction_reconciliation
        if not isinstance(oanda_closeout_transaction_replay, dict):
            transaction_report = {
                "status": "HALT", "errors": ["oanda_closeout_transaction_replay must be an object"],
                "warnings": [], "order_cancellation_performed": False,
                "trade_authority": False, "live_readiness": False,
                "research_only": True, "authority": "research_only_no_execution_authority",
            }
        else:
            try:
                transaction_report = assess_oanda_closeout_transaction_reconciliation(**oanda_closeout_transaction_replay)
            except TypeError as exc:
                transaction_report = {
                    "status": "HALT", "errors": [f"invalid OANDA closeout transaction replay input shape: {exc}"],
                    "warnings": [], "order_cancellation_performed": False,
                    "trade_authority": False, "live_readiness": False,
                    "research_only": True, "authority": "research_only_no_execution_authority",
                }
        if isinstance(oanda_closeout_transaction_replay, dict):
            try:
                if _utc(oanda_closeout_transaction_replay.get("evaluated_at_utc"), "oanda_closeout_transaction_replay.evaluated_at_utc") > evaluation_time:
                    transaction_report["status"] = "HALT"
                    transaction_report.setdefault("errors", []).append("OANDA transaction audit evaluation cannot be later than the unified snapshot time")
            except ValueError:
                pass
        consistency_errors = []
        if (isinstance(oanda_pending_order_snapshot, dict)
                and isinstance(oanda_closeout_transaction_replay, dict)
                and transaction_report.get("status") == "PASS"):
            pending_list = oanda_pending_order_snapshot.get("pending_orders")
            transaction_pending_list = oanda_closeout_transaction_replay.get("post_closeout_pending_orders")
            if not isinstance(pending_list, list) or not isinstance(transaction_pending_list, list) or pending_list != transaction_pending_list:
                consistency_errors.append("post-closeout pending-order snapshot differs between the exposure and transaction audits")
            pending_liquidated = oanda_pending_order_snapshot.get("liquidated_trade_ids")
            transaction_liquidated = transaction_report.get("liquidated_trade_ids")
            if (not isinstance(pending_liquidated, list) or not isinstance(transaction_liquidated, list)
                    or any(not isinstance(item, str) for item in pending_liquidated + transaction_liquidated)
                    or sorted(pending_liquidated) != sorted(transaction_liquidated)):
                consistency_errors.append("liquidated trade IDs differ between the pending-order and transaction audits")
            if oanda_pending_order_snapshot.get("source_timestamp_utc") != oanda_closeout_transaction_replay.get("post_closeout_snapshot_timestamp_utc"):
                consistency_errors.append("post-closeout snapshot timestamps differ between the exposure and transaction audits")
        if consistency_errors:
            transaction_report["status"] = "HALT"
            transaction_report.setdefault("errors", []).extend(consistency_errors)
        transaction_status = transaction_report.get("status")
        oanda_closeout_transaction_audit = {
            "status": "PASS" if transaction_status == "PASS" else "HALT",
            "report": transaction_report,
            "errors": transaction_report.get("errors", []),
            "trade_authority": False, "live_readiness": False,
        }
        if oanda_closeout_transaction_audit["status"] == "HALT":
            active_stops.append({
                "source": "oanda_closeout_transactions", "instrument_id": "account",
                "reason": "OANDA_CLOSEOUT_ORDER_TRANSACTION_RECONCILIATION_FAILED_OR_INVALID",
            })
    if portfolio_risk_audit["status"] == "HALT":
        active_stops.append({"source": "portfolio_risk", "instrument_id": "portfolio",
                             "reason": "portfolio_risk_halt_or_limit_breach"})
    handover_result = validate_handover(handover, now_utc, expected_portfolio_version)
    if handover_result.get("active_veto_ids"):
        active_stops.extend({"source": "handover", "instrument_id": "all",
                             "reason": "active_handover_veto:" + str(veto)}
                            for veto in handover_result["active_veto_ids"])
    if previous_global_stop:
        active_stops.append({"source": "prior_occ_state", "instrument_id": "all",
                             "reason": "previous_global_stop_persists_until_independent_clearance"})

    active_stops = sorted(active_stops, key=lambda item: (item["source"], item["instrument_id"], item["reason"]))
    coverage_complete = not missing_desks
    replay_failed = replay_result.get("status") == "halt" or replay_result.get("evidence_gate", {}).get("status") != "PASS_RESEARCH_GATES"
    if active_stops or replay_failed or packet_errors or portfolio_risk_audit["status"] == "HALT":
        status = "halt"
    elif (not coverage_complete or any(p.get("status") == "unverified" for p in packets)
          or portfolio_risk_audit["status"] == "UNKNOWN"):
        status = "unverified"
    else:
        status = "research"

    result = {
        "schema_version": "1.0.0",
        "snapshot_type": "unified_occ_research_intelligence",
        "generated_at_utc": now_utc,
        "status": status,
        "mode": "research_only",
        "desk_coverage": desk_coverage,
        "missing_desks": missing_desks,
        "coverage_complete": coverage_complete,
        "specialist_packets": packets,
        "capital_flow_audit": capital_flow_audit,
        "gold_specialist_audit": gold_specialist_audit,
        "portfolio_risk": portfolio_risk_audit,
        "oanda_account_margin_audit": oanda_account_margin_audit,
        "oanda_pending_order_audit": oanda_pending_order_audit,
        "oanda_closeout_transaction_audit": oanda_closeout_transaction_audit,
        "capital_flow_context": replay_result.get("capital_flow_handoff", {
            "status": "not_consumed", "accepted_event_count": 0, "trade_authority": False,
        }),
        "evidence_index": evidence_index,
        "packet_validation_errors": packet_errors,
        "active_stops": active_stops,
        "global_stop_active": bool(active_stops),
        "handover": handover_result,
        "replay_evidence_gate": replay_result.get("evidence_gate", {}),
        "occ": {
            "status": status,
            "desk_count": sum(1 for count in desk_coverage.values() if count),
            "packet_count": len(packets),
            "portfolio_version": expected_portfolio_version,
            "authority": "coordination_and_stop_veto_only",
            "trade_authority": False,
            "live_readiness": False,
        },
        "authority": "research_only_no_execution_authority",
        "trade_authority": False,
        "live_readiness": False,
        "limitations": [
            "This is a local snapshot builder, not a daemon, live feed, or unattended background monitor",
            "Evidence references are indexed, not independently authenticated by this module",
            "A prior global stop remains active; this intake has no authority to clear it",
            "Day/night handover requires explicit acknowledgements and position reconciliation",
            "Capital Flow is research context only and is attached only by the separate exact-identity adapter",
            "Gold macro and instrument context is descriptive research only and is not independently authenticated",
            "Missing desk coverage is visible and prevents a fully covered research status",
            "Portfolio exposure, risk limits and correlation are unknown unless explicit comparable evidence and OCC limits are supplied",
            "OANDA account-level margin rules are audited only when an explicit same-account position set and verified trading-day observations are supplied",
        ],
    }


    result["control_health"] = {
        "schema_version": "1.0.0",
        "status": "NOT_PROVIDED",
        "snapshot_history_integrity": "invalid_or_missing",
        "event_ledger_integrity": "invalid_or_missing",
        "cross_ledger_consistency": "inconsistent",
        "handover_acceptance": "not_provided",
        "handover_count": 0,
        "latest_verified_snapshot_id": None,
        "active_stop_ids": [],
        "open_incidents": [],
        "unresolved_critical_items": [],
        "continuity_gaps": [],
        "errors": ["persistent OCC audit journals were not supplied to this intake run"],
        "warnings": [],
        "authority": "research_only_no_execution_authority",
        "trade_authority": False,
        "live_readiness": False,
        "limitations": ["Control-health audit was not requested; no verified audit status is implied"],
    }

    if control_health_snapshot_history is not None and control_health_event_ledger is not None:
        try:
            from .control_health import build_control_health
        except ImportError:
            from control_health import build_control_health
        result = build_control_health(
            result, Path(control_health_snapshot_history), Path(control_health_event_ledger)
        )
    return result



def main() -> int:
    parser = argparse.ArgumentParser(description="Build unified offline OCC research-intelligence snapshot")
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--market-source-registry", type=Path, required=True)
    parser.add_argument("--now-utc", required=True)
    parser.add_argument("--portfolio-version")
    parser.add_argument("--capital-flow-events", type=Path)
    parser.add_argument("--capital-flow-reviews", type=Path)
    parser.add_argument("--capital-flow-source-registry", type=Path)
    parser.add_argument("--handover", type=Path)
    parser.add_argument("--previous-global-stop", action="store_true")
    parser.add_argument("--occ-stop-state")
    parser.add_argument("--require-full-coverage", action="store_true")
    parser.add_argument("--control-health-snapshot-history", type=Path)
    parser.add_argument("--control-health-event-ledger", type=Path)
    parser.add_argument("--portfolio-risk-config", type=Path)
    parser.add_argument("--correlation-evidence", type=Path)
    parser.add_argument("--oanda-account-margin-replay", type=Path,
                        help="JSON object with account_currency, initial_positions and observations")
    parser.add_argument("--oanda-pending-order-snapshot", type=Path,
                        help="Complete post-closeout pending-order snapshot JSON")
    parser.add_argument("--oanda-closeout-transaction-replay", type=Path,
                        help="JSON object with pre/post pending-order snapshots and complete OANDA transaction-ID range")
    parser.add_argument("--max-market-age-seconds", type=float, default=120)
    parser.add_argument("--max-clock-skew-seconds", type=float, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        observations = _read_jsonl(args.observations)
        market_registry = json.loads(args.market_source_registry.read_text(encoding="utf-8"))
        flow_paths = (args.capital_flow_events, args.capital_flow_reviews, args.capital_flow_source_registry)
        if any(flow_paths) and not all(flow_paths):
            raise ValueError("all three Capital Flow files must be supplied together")
        flow_events = _read_jsonl(args.capital_flow_events) if args.capital_flow_events else None
        flow_reviews = _read_jsonl(args.capital_flow_reviews) if args.capital_flow_reviews else None
        flow_registry = json.loads(args.capital_flow_source_registry.read_text(encoding="utf-8")) if args.capital_flow_source_registry else None
        handover = json.loads(args.handover.read_text(encoding="utf-8")) if args.handover else None
        version = args.portfolio_version
        if version is not None:
            try:
                version = int(version)
            except ValueError:
                pass
        risk_config = json.loads(args.portfolio_risk_config.read_text(encoding="utf-8")) if args.portfolio_risk_config else None
        correlations = _read_jsonl(args.correlation_evidence) if args.correlation_evidence else None
        oanda_margin_replay = json.loads(args.oanda_account_margin_replay.read_text(encoding="utf-8")) if args.oanda_account_margin_replay else None
        oanda_pending_snapshot = json.loads(args.oanda_pending_order_snapshot.read_text(encoding="utf-8")) if args.oanda_pending_order_snapshot else None
        oanda_transaction_replay = json.loads(args.oanda_closeout_transaction_replay.read_text(encoding="utf-8")) if args.oanda_closeout_transaction_replay else None
        result = build_unified_intake(
            observations, args.now_utc, market_registry, flow_events, flow_reviews,
            flow_registry, handover, version, args.previous_global_stop, args.occ_stop_state,
            args.max_market_age_seconds, args.max_clock_skew_seconds, args.require_full_coverage,
            args.control_health_snapshot_history, args.control_health_event_ledger, risk_config, correlations,
            oanda_account_margin_replay=oanda_margin_replay,
            oanda_pending_order_snapshot=oanda_pending_snapshot,
            oanda_closeout_transaction_replay=oanda_transaction_replay,
        )
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": result["status"], "desk_coverage": result["desk_coverage"],
                          "global_stop_active": result["global_stop_active"],
                          "handover": result["handover"]["status"],
                          "control_health": result.get("control_health", {}).get("status", "not_requested"),
                          "portfolio_risk": result.get("portfolio_risk", {}).get("status", "not_provided"),
                          "oanda_account_margin": result.get("oanda_account_margin_audit", {}).get("status", "not_provided"),
                          "oanda_pending_orders": result.get("oanda_pending_order_audit", {}).get("status", "not_provided"),
                          "oanda_closeout_transactions": result.get("oanda_closeout_transaction_audit", {}).get("status", "not_provided"),
                          "output": str(args.output),
                          "authority": result["authority"]}, indent=2))
        return 0 if result["status"] in {"research", "unverified"} else 1
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

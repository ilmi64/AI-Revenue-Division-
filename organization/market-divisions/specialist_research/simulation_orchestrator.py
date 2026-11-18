"""Fail-closed orchestration and reconciliation of derivative simulations.

The venue path engine owns price P&L, margin and liquidation estimates.
The contract lifecycle ledger owns funding/financing, rolls and settlement.
To prevent duplicate carry, this orchestrator requires zero funding rates in
all path steps and rejects any path output with non-zero funding cost.
"""
from __future__ import annotations

from datetime import datetime
from math import isclose
from typing import Any

from specialist_research.contract_lifecycle import (
    AUTHORITY, replay_contract_lifecycle, validate_contract_profile,
)
from specialist_research.venue_risk_simulation import (
    simulate_derivative_path, validate_venue_spec,
)


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None


def _blocked(status: str, errors: list[str]) -> dict[str, Any]:
    return {
        "status": status, "errors": errors, "venue_simulation": None,
        "lifecycle_replay": None, "reconciliation": {
            "status": "NOT_PERFORMED", "checks": [], "errors": errors,
        },
        "authority": AUTHORITY, "trade_authority": False,
        "live_readiness": False, "simulation_only": True,
    }


def simulate_unified_derivative(
    venue_spec: dict[str, Any],
    contract_profile: dict[str, Any],
    position: dict[str, Any],
    price_path: list[dict[str, Any]],
    lifecycle_events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run both research engines and reconcile their outputs without double-counting.

    price_path funding_rate must be exactly zero: all carry belongs in
    lifecycle_events. Cashflow is kept in settlement_currency and is not added
    to mark-to-market equity unless currencies are explicitly the same.
    """
    errors: list[str] = []
    errors.extend(f"venue: {item}" for item in validate_venue_spec(venue_spec))
    errors.extend(f"contract: {item}" for item in validate_contract_profile(contract_profile))
    if not isinstance(position, dict):
        errors.append("position must be an object")
        position = {}
    if not isinstance(price_path, list) or not price_path:
        errors.append("price_path must be a non-empty array")
        price_path = []
    if not isinstance(lifecycle_events, list):
        errors.append("lifecycle_events must be an array")
        lifecycle_events = []
    if venue_spec.get("instrument_type") != contract_profile.get("instrument_type"):
        errors.append("venue and contract instrument_type must match")
    if position.get("instrument_id") != contract_profile.get("instrument_id"):
        errors.append("position.instrument_id must match contract profile")
    if venue_spec.get("quote_currency") != contract_profile.get("quote_currency"):
        errors.append("venue and contract quote currencies must match")
    if not isinstance(position.get("contract_id"), str) or not position.get("contract_id"):
        errors.append("position.contract_id is required for lifecycle reconciliation")

    for index, step in enumerate(price_path):
        if not isinstance(step, dict):
            errors.append(f"price_path[{index}] must be an object")
            continue
        rate = step.get("funding_rate")
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate != 0:
            errors.append(f"price_path[{index}].funding_rate must be exactly zero; lifecycle ledger owns carry")

    if errors:
        return _blocked("BLOCKED_INPUT_RECONCILIATION", errors)

    venue_result = simulate_derivative_path(venue_spec, position, price_path)
    lifecycle_result = replay_contract_lifecycle(contract_profile, position, lifecycle_events)
    errors = []
    if venue_result.get("status") not in {"SIMULATED_NO_LIQUIDATION", "LIQUIDATION_MODEL_TRIGGERED"}:
        errors.extend(f"venue simulation: {item}" for item in venue_result.get("errors", []))
        if not errors:
            errors.append(f"venue simulation returned {venue_result.get('status')}")
    if lifecycle_result.get("status") not in {"LIFECYCLE_REPLAYED", "SETTLED"}:
        errors.extend(f"lifecycle replay: {item}" for item in lifecycle_result.get("errors", []))
        if not errors:
            errors.append(f"lifecycle replay returned {lifecycle_result.get('status')}")
    if errors:
        return {
            "status": "BLOCKED_COMPONENT_FAILURE", "errors": errors,
            "venue_simulation": venue_result, "lifecycle_replay": lifecycle_result,
            "reconciliation": {"status": "FAILED", "checks": [], "errors": errors},
            "authority": AUTHORITY, "trade_authority": False,
            "live_readiness": False, "simulation_only": True,
        }

    checks: list[dict[str, Any]] = []
    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})
        if not passed:
            errors.append(name)

    check("position_identity", venue_result.get("position_id") == position.get("position_id")
          and lifecycle_result.get("ending_quantity") is not None,
          "Both engines accepted the same position identity.")
    check("instrument_identity", venue_result.get("instrument_id") == contract_profile.get("instrument_id"),
          "Venue path and lifecycle profile refer to the same instrument.")
    carry = venue_result.get("cumulative_funding_cost")
    check("carry_not_double_counted", isinstance(carry, (int, float)) and isclose(carry, 0.0, abs_tol=1e-12),
          "Path simulator carry is zero; lifecycle ledger is the sole carry source.")
    check("carry_currency", lifecycle_result.get("settlement_currency") == contract_profile.get("settlement_currency"),
          "Lifecycle cashflows remain denominated in the declared settlement currency.")

    settlement_rows = [row for row in lifecycle_result.get("events", [])
                       if row.get("event_type") == "expiry_settlement"]
    if settlement_rows:
        settlement_time = _timestamp(settlement_rows[-1].get("timestamp_utc"))
        path_times = [_timestamp(step.get("timestamp_utc")) for step in price_path]
        if settlement_time is None or any(ts is None or ts > settlement_time for ts in path_times):
            check("path_ends_before_settlement", False,
                  "Price path must not continue after expiry settlement.")
        else:
            check("path_ends_before_settlement", True,
                  "Price path does not continue beyond expiry settlement.")
    else:
        check("path_settlement_consistency", lifecycle_result.get("ending_quantity") == position.get("quantity")
              or venue_result.get("liquidation_occurred"),
              "No expiry settlement was recorded; lifecycle quantity remains open unless path liquidation occurred.")

    check("contract_identity", lifecycle_result.get("ending_contract_id") is not None,
          "Lifecycle contract identity remains explicit after any roll.")

    if errors:
        reconciliation_status = "FAILED"
        status = "BLOCKED_RECONCILIATION"
    else:
        reconciliation_status = "PASS_RECONCILIATION"
        status = "SIMULATED_LIQUIDATION" if venue_result.get("liquidation_occurred") else (
            "SIMULATED_SETTLEMENT" if lifecycle_result.get("settled") else "SIMULATED_OK"
        )

    # Keep unlike currencies separate; no implicit FX conversion or equity merge.
    settlement_cashflow = lifecycle_result.get("cashflow_total")
    same_currency = contract_profile.get("settlement_currency") == venue_spec.get("quote_currency")
    combined_equity = None
    if same_currency and isinstance(settlement_cashflow, (int, float)):
        combined_equity = venue_result.get("ending_equity_estimate")
        if isinstance(combined_equity, (int, float)):
            combined_equity += settlement_cashflow

    return {
        "status": status, "errors": errors,
        "position_id": position.get("position_id"),
        "instrument_id": position.get("instrument_id"),
        "venue_simulation": venue_result,
        "lifecycle_replay": lifecycle_result,
        "reconciliation": {
            "status": reconciliation_status, "checks": checks, "errors": errors,
            "carry_source": "contract_lifecycle_only",
            "cashflow_currency": contract_profile.get("settlement_currency"),
            "combined_equity_estimate": combined_equity,
            "combined_equity_currency": contract_profile.get("settlement_currency") if combined_equity is not None else None,
            "currency_merge_performed": combined_equity is not None,
        },
        "limitations": [
            "The venue and contract profiles and all market/event inputs are caller-supplied and unauthenticated.",
            "Venue path equity excludes carry; lifecycle cashflows are reconciled separately.",
            "Combined equity is shown only when quote and settlement currencies match.",
            "A successful reconciliation validates internal consistency, not venue accuracy or model validity.",
            "No broker/exchange connection, order routing, live risk authority or stop clearance exists.",
        ],
        "authority": AUTHORITY, "trade_authority": False,
        "live_readiness": False, "simulation_only": True,
    }

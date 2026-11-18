"""Venue-parameterised, offline risk-path simulator.

All venue rules and market paths are explicit caller-supplied inputs. This module
never fetches prices, invents contract terms, routes orders or manages positions.
Its outputs are synthetic research estimates, not broker liquidation guarantees.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

AUTHORITY = "research_only_no_execution_authority"
DERIVATIVE_TYPES = {
    "crypto_perpetual", "forex_cfd", "index_future", "index_cfd",
    "gold_future", "gold_cfd",
}
MARK_RULES = {"index", "mark", "last", "bid_ask_mid"}


def _finite(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and isfinite(float(value)))


def _utc(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        return parsed.utcoffset() == timezone.utc.utcoffset(parsed)
    except ValueError:
        return False


def _positive(value: Any) -> bool:
    return _finite(value) and float(value) > 0


def validate_venue_spec(spec: Any) -> list[str]:
    """Validate a fully explicit venue/contract model; return blocking errors."""
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["venue_spec must be an object"]
    for key in ("schema_version", "venue_id", "instrument_type", "quote_currency"):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            errors.append(f"{key} is required")
    if spec.get("instrument_type") not in DERIVATIVE_TYPES:
        errors.append("instrument_type is unsupported by this derivative simulator")
    if spec.get("mark_price_rule") not in MARK_RULES:
        errors.append("mark_price_rule must be an explicit supported rule")
    for key in ("contract_multiplier", "initial_margin_rate", "liquidation_fee_rate",
                "max_impact_bps", "impact_coefficient", "liquidation_buffer_ratio"):
        if not _finite(spec.get(key)) or float(spec[key]) < 0:
            errors.append(f"{key} must be a finite non-negative number")
    if _positive(spec.get("contract_multiplier")) is False:
        errors.append("contract_multiplier must be greater than zero")
    if _finite(spec.get("initial_margin_rate")) and not 0 < float(spec["initial_margin_rate"]) <= 1:
        errors.append("initial_margin_rate must be in (0, 1]")
    if _finite(spec.get("liquidation_buffer_ratio")) and float(spec["liquidation_buffer_ratio"]) < 1:
        errors.append("liquidation_buffer_ratio must be at least 1")
    if _finite(spec.get("max_impact_bps")) and float(spec["max_impact_bps"]) > 10000:
        errors.append("max_impact_bps cannot exceed 10000")
    if _finite(spec.get("liquidation_fee_rate")) and float(spec["liquidation_fee_rate"]) > 1:
        errors.append("liquidation_fee_rate cannot exceed 1")
    if not isinstance(spec.get("partial_liquidation_supported"), bool):
        errors.append("partial_liquidation_supported must be boolean")
    tiers = spec.get("maintenance_tiers")
    if not isinstance(tiers, list) or not tiers:
        errors.append("maintenance_tiers must be a non-empty array")
    else:
        previous = 0.0
        for index, tier in enumerate(tiers):
            if not isinstance(tier, dict):
                errors.append(f"maintenance_tiers[{index}] must be an object")
                continue
            cap, rate = tier.get("notional_cap"), tier.get("maintenance_rate")
            if cap is not None and (not _positive(cap) or float(cap) <= previous):
                errors.append(f"maintenance_tiers[{index}].notional_cap must increase")
            if cap is None and index != len(tiers) - 1:
                errors.append("only the final maintenance tier may have an unbounded cap")
            if index == len(tiers) - 1 and cap is not None:
                errors.append("final maintenance tier must have an unbounded cap")
            if not _finite(rate) or not 0 < float(rate) <= 1:
                errors.append(f"maintenance_tiers[{index}].maintenance_rate must be in (0, 1]")
            if cap is not None and _positive(cap):
                previous = float(cap)
    return errors


def _maintenance(notional: float, tiers: list[dict[str, Any]]) -> float:
    for tier in tiers:
        cap = tier.get("notional_cap")
        if cap is None or notional <= float(cap):
            return notional * float(tier["maintenance_rate"])
    raise ValueError("maintenance tier schedule does not cover notional")


def _impact_cost(notional: float, depth: float, spec: dict[str, Any]) -> tuple[float, float]:
    if not _positive(depth):
        raise ValueError("executable_depth_notional must be greater than zero")
    ratio = notional / depth
    bps = min(float(spec["max_impact_bps"]),
              float(spec["impact_coefficient"]) * ratio * ratio)
    return notional * bps / 10000.0, bps


def _partial_reduction(quantity: float, multiplier: float, price: float,
                       equity: float, spec: dict[str, Any], depth: float) -> float:
    """Find the smallest quantity reduction meeting the configured equity buffer."""
    if equity <= 0:
        return quantity
    low, high = 0.0, quantity
    for _ in range(64):
        reduce_qty = (low + high) / 2.0
        remaining_notional = (quantity - reduce_qty) * multiplier * price
        maintenance = _maintenance(remaining_notional, spec["maintenance_tiers"])
        cost, _ = _impact_cost(reduce_qty * multiplier * price, depth, spec)
        fee = reduce_qty * multiplier * price * float(spec["liquidation_fee_rate"])
        if maintenance * float(spec["liquidation_buffer_ratio"]) <= equity - cost - fee:
            high = reduce_qty
        else:
            low = reduce_qty
    return high


def simulate_derivative_path(venue_spec: dict[str, Any], position: dict[str, Any],
                             path: list[dict[str, Any]]) -> dict[str, Any]:
    """Replay one synthetic/recorded mark path with explicit venue assumptions.

    Each path step requires timestamp_utc, mark_price, executable_depth_notional,
    funding_rate and funding_interval_hours. funding_rate is the signed rate paid
    by longs per funding interval; shorts receive the opposite amount.
    """
    spec_errors = validate_venue_spec(venue_spec)
    errors = list(spec_errors)
    if not isinstance(position, dict):
        errors.append("position must be an object")
        position = {}
    if position.get("side") not in {"long", "short"}:
        errors.append("position.side must be long or short")
    for key in ("position_id", "instrument_id"):
        if not isinstance(position.get(key), str) or not position[key].strip():
            errors.append(f"position.{key} is required")
    for key in ("quantity", "entry_price", "initial_margin", "available_margin"):
        if key == "available_margin":
            if not _finite(position.get(key)) or float(position[key]) < 0:
                errors.append("position.available_margin must be finite and non-negative")
        elif not _positive(position.get(key)):
            errors.append(f"position.{key} must be greater than zero")
    if not isinstance(path, list) or not path:
        errors.append("path must be a non-empty array")
        path = []
    if errors:
        return {
            "status": "BLOCKED_INVALID_MODEL_INPUTS", "errors": errors,
            "steps": [], "final_position_quantity": None,
            "authority": AUTHORITY, "trade_authority": False,
            "live_readiness": False, "simulation_only": True,
        }

    multiplier = float(venue_spec["contract_multiplier"])
    quantity = float(position["quantity"])
    initial_quantity = quantity
    entry = float(position["entry_price"])
    side_sign = 1.0 if position["side"] == "long" else -1.0
    required_initial_margin = quantity * multiplier * entry * float(venue_spec["initial_margin_rate"])
    if float(position["initial_margin"]) < required_initial_margin:
        return {
            "status": "BLOCKED_INVALID_MODEL_INPUTS",
            "errors": ["position.initial_margin is below the venue-spec initial-margin requirement"],
            "steps": [], "final_position_quantity": None,
            "authority": AUTHORITY, "trade_authority": False,
            "live_readiness": False, "simulation_only": True,
        }
    equity = float(position["initial_margin"]) + float(position["available_margin"])
    cumulative_funding = cumulative_fees = cumulative_impact = 0.0
    previous_time: datetime | None = None
    previous_mark = entry
    rows: list[dict[str, Any]] = []
    status = "SIMULATED_NO_LIQUIDATION"
    liquidation_occurred = False

    for index, step in enumerate(path):
        prefix = f"path[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{prefix} must be an object")
            break
        timestamp = step.get("timestamp_utc")
        mark = step.get("mark_price")
        mark_basis = step.get("mark_price_basis")
        depth = step.get("executable_depth_notional")
        rate = step.get("funding_rate")
        interval = step.get("funding_interval_hours")
        if not _utc(timestamp):
            errors.append(f"{prefix}.timestamp_utc must be UTC ISO-8601 ending Z")
        if not _positive(mark):
            errors.append(f"{prefix}.mark_price must be positive")
        if mark_basis != venue_spec.get("mark_price_rule"):
            errors.append(f"{prefix}.mark_price_basis must match the venue mark_price_rule")
        if not _positive(depth):
            errors.append(f"{prefix}.executable_depth_notional must be positive")
        if not _finite(rate):
            errors.append(f"{prefix}.funding_rate must be finite")
        if not _positive(interval):
            errors.append(f"{prefix}.funding_interval_hours must be positive")
        if errors:
            break
        current_time = datetime.fromisoformat(timestamp[:-1] + "+00:00")
        if previous_time is not None and current_time <= previous_time:
            errors.append(f"{prefix}.timestamp_utc must increase strictly")
            break
        if step.get("gap_flag", False) not in (True, False):
            errors.append(f"{prefix}.gap_flag must be boolean")
            break

        mark = float(mark)
        quantity_before = quantity
        notional = quantity_before * multiplier * mark
        price_pnl = quantity * multiplier * (mark - previous_mark) * side_sign
        elapsed_hours = (current_time - previous_time).total_seconds() / 3600.0 if previous_time else 0.0
        funding_intervals = elapsed_hours / float(interval)
        funding = notional * float(rate) * funding_intervals * side_sign
        # Positive funding_rate means longs pay; negative means shorts pay.
        funding_cost = funding
        impact_cost, impact_bps = _impact_cost(notional, float(depth), venue_spec)
        equity += price_pnl - funding_cost
        cumulative_funding += funding_cost
        maintenance = _maintenance(notional, venue_spec["maintenance_tiers"])
        event = "NONE"
        step_fee = step_impact = 0.0

        if equity <= maintenance:
            liquidation_occurred = True
            if venue_spec["partial_liquidation_supported"] and quantity > 0:
                reduce_qty = _partial_reduction(
                    quantity, multiplier, mark, equity, venue_spec, float(depth))
                remaining_notional = max(0.0, (quantity - reduce_qty) * multiplier * mark)
                reduction_cost, _ = _impact_cost(reduce_qty * multiplier * mark, float(depth), venue_spec)
                reduction_fee = reduce_qty * multiplier * mark * float(venue_spec["liquidation_fee_rate"])
                restored = (_maintenance(remaining_notional, venue_spec["maintenance_tiers"])
                            * float(venue_spec["liquidation_buffer_ratio"])
                            <= equity - reduction_cost - reduction_fee)
                if 0 < reduce_qty < quantity and restored:
                    reduced_notional = reduce_qty * multiplier * mark
                    step_impact, impact_bps = _impact_cost(reduced_notional, float(depth), venue_spec)
                    step_fee = reduced_notional * float(venue_spec["liquidation_fee_rate"])
                    equity -= step_impact + step_fee
                    quantity -= reduce_qty
                    event = "PARTIAL_LIQUIDATION"
                else:
                    step_impact, impact_bps = _impact_cost(notional, float(depth), venue_spec)
                    step_fee = notional * float(venue_spec["liquidation_fee_rate"])
                    equity -= step_impact + step_fee
                    quantity = 0.0
                    event = "FULL_LIQUIDATION"
            else:
                step_impact, impact_bps = _impact_cost(notional, float(depth), venue_spec)
                step_fee = notional * float(venue_spec["liquidation_fee_rate"])
                equity -= step_impact + step_fee
                quantity = 0.0
                event = "FULL_LIQUIDATION"
            status = "LIQUIDATION_MODEL_TRIGGERED"
        cumulative_fees += step_fee
        cumulative_impact += step_impact
        rows.append({
            "timestamp_utc": timestamp, "mark_price": mark,
            "quantity_before": quantity_before,
            "quantity_after": quantity, "notional_before": notional,
            "price_pnl": price_pnl, "funding_cost": funding_cost,
            "maintenance_requirement": maintenance, "equity_after_costs": equity,
            "liquidation_event": event, "liquidation_fee": step_fee,
            "estimated_impact_cost": step_impact, "impact_bps": impact_bps,
            "gap_flag": step.get("gap_flag", False),
        })
        previous_time, previous_mark = current_time, mark
        if quantity == 0:
            break

    if errors:
        return {
            "status": "BLOCKED_INVALID_PATH", "errors": errors, "steps": rows,
            "final_position_quantity": quantity, "authority": AUTHORITY,
            "trade_authority": False, "live_readiness": False, "simulation_only": True,
        }
    return {
        "status": status, "errors": [], "steps": rows,
        "position_id": position["position_id"], "instrument_id": position["instrument_id"],
        "initial_quantity": initial_quantity, "final_position_quantity": quantity,
        "liquidation_occurred": liquidation_occurred,
        "cumulative_funding_cost": cumulative_funding,
        "cumulative_liquidation_fees": cumulative_fees,
        "cumulative_estimated_impact_cost": cumulative_impact,
        "ending_equity_estimate": equity,
        "model_limitations": [
            "Caller-supplied venue rules, mark path, funding and depth are not authenticated.",
            "Impact is a configurable heuristic, not an order-book replay or execution guarantee.",
            "Gap flags are reported; intrabar path, queue priority and gap-fill prices are not inferred.",
            "Insurance funds, ADL, bankruptcy pricing, cross-collateral and venue-specific liquidation sequencing are not modelled.",
            "Partial liquidation is simulated only when the supplied venue spec explicitly enables it.",
        ],
        "authority": AUTHORITY, "trade_authority": False,
        "live_readiness": False, "simulation_only": True,
    }

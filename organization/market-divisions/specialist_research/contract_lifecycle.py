"""Explicit contract lifecycle and carry-event replay.

This module validates and replays caller-supplied lifecycle events for futures,
perpetuals and CFDs. It does not infer exchange calendars, broker financing,
settlement conventions or contract rolls.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any

AUTHORITY = "research_only_no_execution_authority"
SUPPORTED_TYPES = {
    "crypto_perpetual", "forex_cfd", "index_future", "index_cfd",
    "gold_future", "gold_cfd",
}
EVENT_TYPES = {"funding", "financing", "roll", "expiry_settlement"}


def _number(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and isfinite(float(value)))


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed


def validate_contract_profile(profile: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(profile, dict):
        return ["contract_profile must be an object"]
    for key in ("schema_version", "profile_id", "venue_id", "instrument_id",
                "instrument_type", "quote_currency", "settlement_currency"):
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            errors.append(f"{key} is required")
    if profile.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    kind = profile.get("instrument_type")
    if kind not in SUPPORTED_TYPES:
        errors.append("instrument_type is unsupported")
    if profile.get("settlement_method") not in {
        "cash", "physical", "broker_cash_adjustment", "not_applicable"
    }:
        errors.append("settlement_method must be explicit")
    if profile.get("roll_method") not in {
        "manual_close_open", "venue_defined", "not_applicable"
    }:
        errors.append("roll_method must be explicit")
    if profile.get("financing_convention") not in {
        "funding_rate", "annualized_rate", "daily_rate", "none"
    }:
        errors.append("financing_convention must be explicit")
    if kind in {"index_future", "gold_future"}:
        if not isinstance(profile.get("contract_code"), str) or not profile["contract_code"].strip():
            errors.append("dated futures require contract_code")
        if _utc(profile.get("expiry_utc")) is None:
            errors.append("dated futures require expiry_utc in UTC")
        if profile.get("settlement_method") == "not_applicable":
            errors.append("dated futures require an explicit settlement method")
    elif profile.get("expiry_utc") is not None and _utc(profile.get("expiry_utc")) is None:
        errors.append("expiry_utc must be UTC when supplied")
    if kind in {"crypto_perpetual", "forex_cfd", "index_cfd", "gold_cfd"}:
        if profile.get("settlement_method") == "physical":
            errors.append("perpetuals and CFDs cannot declare physical settlement here")
    if kind == "crypto_perpetual" and profile.get("financing_convention") != "funding_rate":
        errors.append("Crypto perpetual requires funding_rate convention")
    if kind in {"forex_cfd", "index_cfd", "gold_cfd"} and profile.get("financing_convention") not in {
        "annualized_rate", "daily_rate", "none"
    }:
        errors.append("CFD financing convention must be explicit")
    if kind in {"index_future", "gold_future"} and profile.get("roll_method") == "not_applicable":
        errors.append("dated futures require an explicit roll method")
    return errors


def replay_contract_lifecycle(profile: dict[str, Any], position: dict[str, Any],
                              events: list[dict[str, Any]]) -> dict[str, Any]:
    """Replay explicit carry, roll and settlement events.

    Event cashflow is positive when credited to the position and negative when
    charged. Funding/financing events must supply signed cashflow directly OR
    a rate, notional and day/hour basis. The module does not decide rate signs.
    Roll events require old/new contract IDs, old/new reference prices, an
    explicit cash adjustment and a validated successor contract profile.
    Expiry settlement requires an explicit settlement
    price and cash/physical/broker adjustment method.
    """
    errors = validate_contract_profile(profile)
    if not isinstance(position, dict):
        errors.append("position must be an object")
        position = {}
    for key in ("position_id", "instrument_id", "side", "quantity", "contract_id"):
        if key not in position:
            errors.append(f"position.{key} is required")
    for key in ("position_id", "instrument_id", "contract_id"):
        if key in position and (not isinstance(position[key], str) or not position[key].strip()):
            errors.append(f"position.{key} must be a non-empty string")
    if position.get("side") not in {"long", "short"}:
        errors.append("position.side must be long or short")
    if not _number(position.get("quantity")) or float(position.get("quantity", 0)) <= 0:
        errors.append("position.quantity must be positive and finite")
    if position.get("instrument_id") != profile.get("instrument_id"):
        errors.append("position.instrument_id must match contract profile")
    if profile.get("contract_code") and position.get("contract_id") != profile.get("contract_code"):
        errors.append("position.contract_id must match the profile contract_code initially")
    if not isinstance(events, list):
        errors.append("events must be an array")
        events = []
    if errors:
        return {
            "status": "BLOCKED_INVALID_PROFILE_OR_POSITION", "errors": errors,
            "events": [], "ending_quantity": None, "authority": AUTHORITY,
            "trade_authority": False, "live_readiness": False, "simulation_only": True,
        }

    quantity = float(position["quantity"])
    contract_id = position["contract_id"]
    active_profile = dict(profile)
    cashflow_total = 0.0
    previous_time: datetime | None = None
    rows: list[dict[str, Any]] = []
    settled = False

    for index, event in enumerate(events):
        prefix = f"events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix} must be an object")
            break
        timestamp = _utc(event.get("timestamp_utc"))
        if timestamp is None:
            errors.append(f"{prefix}.timestamp_utc must be UTC ISO-8601 ending Z")
            break
        if previous_time is not None and timestamp <= previous_time:
            errors.append(f"{prefix}.timestamp_utc must increase strictly")
            break
        event_type = event.get("event_type")
        expiry_time = _utc(active_profile.get("expiry_utc"))
        if expiry_time is not None and timestamp >= expiry_time and event_type != "expiry_settlement":
            errors.append(f"{prefix} is at/after expiry and must be an expiry_settlement event")
            break
        if event_type not in EVENT_TYPES:
            errors.append(f"{prefix}.event_type is unsupported")
            break
        if settled:
            errors.append(f"{prefix} cannot follow expiry settlement")
            break
        if event_type == "funding" and active_profile["financing_convention"] != "funding_rate":
            errors.append(f"{prefix} funding event conflicts with profile convention")
            break
        if event_type == "financing" and active_profile["financing_convention"] not in {
            "annualized_rate", "daily_rate"
        }:
            errors.append(f"{prefix} financing event conflicts with profile convention")
            break
        if event_type in {"funding", "financing"}:
            if _number(event.get("cashflow")):
                cashflow = float(event["cashflow"])
            else:
                rate, notional, basis = event.get("rate"), event.get("notional"), event.get("basis_units")
                if not all(_number(x) for x in (rate, notional, basis)) or float(notional) <= 0 or float(basis) <= 0:
                    errors.append(f"{prefix} requires cashflow or finite rate/notional/positive basis_units")
                    break
                # Rate sign is already the signed cashflow convention for this
                # position; applying side_sign here would invert short-position
                # cashflows a second time. Venue-specific payer/receiver rules
                # must be normalized by the caller before this replay.
                cashflow = float(rate) * float(notional) * float(basis)
            if event.get("currency") != active_profile["settlement_currency"]:
                errors.append(f"{prefix}.currency must match settlement_currency")
                break
            cashflow_total += cashflow
            rows.append({"event_id": event.get("event_id"), "event_type": event_type,
                         "timestamp_utc": event["timestamp_utc"], "cashflow": cashflow,
                         "currency": event["currency"], "contract_id": contract_id})
        elif event_type == "roll":
            if active_profile["roll_method"] == "not_applicable":
                errors.append(f"{prefix} roll conflicts with profile")
                break
            old_id, new_id = event.get("old_contract_id"), event.get("new_contract_id")
            old_price, new_price = event.get("old_reference_price"), event.get("new_reference_price")
            adjustment = event.get("cash_adjustment")
            if old_id != contract_id or not isinstance(new_id, str) or not new_id.strip():
                errors.append(f"{prefix} contract IDs do not match current position")
                break
            if not _number(old_price) or float(old_price) <= 0 or not _number(new_price) or float(new_price) <= 0:
                errors.append(f"{prefix} requires positive old/new reference prices")
                break
            if not _number(adjustment):
                errors.append(f"{prefix}.cash_adjustment must be finite and explicit")
                break
            if event.get("currency") != active_profile["settlement_currency"]:
                errors.append(f"{prefix}.currency must match settlement_currency")
                break
            next_profile = event.get("new_contract_profile")
            next_profile_errors = validate_contract_profile(next_profile)
            if next_profile_errors:
                errors.append(f"{prefix}.new_contract_profile is missing or invalid: " + "; ".join(next_profile_errors))
                break
            identity_fields = (
                "venue_id", "instrument_id", "instrument_type", "quote_currency",
                "settlement_currency", "settlement_method", "roll_method",
                "financing_convention",
            )
            if any(next_profile.get(key) != active_profile.get(key) for key in identity_fields):
                errors.append(f"{prefix}.new_contract_profile changes the instrument or venue identity")
                break
            if next_profile.get("profile_id") == active_profile.get("profile_id"):
                errors.append(f"{prefix}.new_contract_profile must have a distinct profile_id")
                break
            if next_profile.get("instrument_type") in {"index_future", "gold_future"}:
                if next_profile.get("contract_code") != new_id:
                    errors.append(f"{prefix}.new_contract_profile.contract_code must match new_contract_id")
                    break
                old_expiry = _utc(active_profile.get("expiry_utc"))
                new_expiry = _utc(next_profile.get("expiry_utc"))
                if old_expiry is None or new_expiry is None or new_expiry <= old_expiry:
                    errors.append(f"{prefix}.new_contract_profile expiry must be later than the current contract expiry")
                    break
            elif next_profile.get("contract_code") and next_profile.get("contract_code") != new_id:
                errors.append(f"{prefix}.new_contract_profile.contract_code must match new_contract_id")
                break
            cashflow_total += float(adjustment)
            rows.append({"event_id": event.get("event_id"), "event_type": "roll",
                         "timestamp_utc": event["timestamp_utc"], "old_contract_id": old_id,
                         "new_contract_id": new_id, "old_reference_price": float(old_price),
                         "new_reference_price": float(new_price),
                         "cash_adjustment": float(adjustment), "currency": event["currency"],
                         "roll_method": active_profile["roll_method"]})
            contract_id = new_id
            active_profile = dict(next_profile)
        elif event_type == "expiry_settlement":
            expiry = _utc(active_profile.get("expiry_utc"))
            if expiry is None or timestamp < expiry:
                errors.append(f"{prefix} settlement cannot occur before a valid contract expiry")
                break
            settlement_price = event.get("settlement_price")
            if not _number(settlement_price) or float(settlement_price) <= 0:
                errors.append(f"{prefix}.settlement_price must be positive and finite")
                break
            if event.get("contract_id") != contract_id:
                errors.append(f"{prefix}.contract_id must match current contract")
                break
            if event.get("settlement_method") != active_profile["settlement_method"]:
                errors.append(f"{prefix}.settlement_method must match profile")
                break
            if not _number(event.get("realized_cashflow")):
                errors.append(f"{prefix}.realized_cashflow must be explicit and finite")
                break
            if event.get("currency") != active_profile["settlement_currency"]:
                errors.append(f"{prefix}.currency must match settlement_currency")
                break
            realized = float(event["realized_cashflow"])
            cashflow_total += realized
            rows.append({"event_id": event.get("event_id"), "event_type": "expiry_settlement",
                         "timestamp_utc": event["timestamp_utc"], "contract_id": contract_id,
                         "settlement_price": float(settlement_price),
                         "settlement_method": active_profile["settlement_method"],
                         "realized_cashflow": realized, "currency": event["currency"]})
            quantity = 0.0
            settled = True
        previous_time = timestamp

    if errors:
        return {
            "status": "BLOCKED_INVALID_EVENT_SEQUENCE", "errors": errors,
            "events": rows, "ending_quantity": quantity, "ending_contract_id": contract_id,
            "cashflow_total": cashflow_total, "authority": AUTHORITY,
            "trade_authority": False, "live_readiness": False, "simulation_only": True,
        }
    return {
        "status": "SETTLED" if settled else "LIFECYCLE_REPLAYED",
        "errors": [], "events": rows, "ending_quantity": quantity,
        "ending_contract_id": contract_id, "settled": settled,
        "cashflow_total": cashflow_total,
        "settlement_currency": active_profile["settlement_currency"],
        "authority": AUTHORITY, "trade_authority": False,
        "live_readiness": False, "simulation_only": True,
        "limitations": [
            "All events, rates, reference prices and cashflows are caller-supplied and unauthenticated.",
            "Cashflow replay does not infer venue funding signs, triple-swap calendars, tax or fees.",
            "Roll price differences are reported; only the explicit cash_adjustment changes cashflow.",
            "Expiry settlement cashflow is supplied, not calculated from an inferred contract multiplier or settlement formula.",
            "Physical delivery logistics, margin release, residual claims and broker close-out are not modelled.",
        ],
    }

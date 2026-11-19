"""Fail-closed validation for caller-supplied market-data observations."""
from __future__ import annotations
import math
from collections.abc import Mapping
from typing import Any
from .instrument_identity import InstrumentIdentityError, validate_instrument_identity

class MarketDataObservationError(ValueError):
    """An observation is incomplete, stale or inconsistent."""

_IDENTITY_FIELDS = ("market_class","product_type","venue","symbol","base_currency",
    "quote_currency","contract_unit","contract_multiplier","settlement_method",
    "expiry","custody_model","financing_model")

def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MarketDataObservationError(f"{field} must be a finite number")
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise MarketDataObservationError(f"{field} must be a finite number") from exc
    if not math.isfinite(result):
        raise MarketDataObservationError(f"{field} must be a finite number")
    return result

def _text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise MarketDataObservationError(f"{field} must be a non-empty string")
    return value.strip()

def _identity_key(identity: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(identity.get(field) for field in _IDENTITY_FIELDS)

def validate_market_data_observation(observation: Mapping[str, Any],
        expected_identity: Mapping[str, Any], *, now_epoch: int | float,
        max_age_seconds: int | float = 30,
        max_future_skew_seconds: int | float = 5) -> dict[str, Any]:
    """Validate one quote against an exact identity; never authenticate its source."""
    if not isinstance(observation, Mapping):
        raise MarketDataObservationError("observation must be a mapping")
    try:
        expected = validate_instrument_identity(expected_identity)
        supplied = validate_instrument_identity(observation.get("instrument_identity"))
    except InstrumentIdentityError as exc:
        raise MarketDataObservationError(f"invalid instrument identity: {exc}") from exc
    if _identity_key(supplied) != _identity_key(expected):
        raise MarketDataObservationError("observation instrument does not match expected identity")
    provider_id = _text(observation, "provider_id")
    event_id = _text(observation, "event_id")
    venue = _text(observation, "venue")
    if venue != expected["venue"]:
        raise MarketDataObservationError("observation venue does not match instrument venue")
    sequence = observation.get("sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence <= 0:
        raise MarketDataObservationError("sequence must be a positive integer")
    bid = _number(observation.get("bid"), "bid")
    ask = _number(observation.get("ask"), "ask")
    if bid <= 0 or ask <= 0 or bid > ask:
        raise MarketDataObservationError("bid and ask must be positive with bid <= ask")
    observed = _number(observation.get("observed_at_epoch"), "observed_at_epoch")
    received = _number(observation.get("received_at_epoch"), "received_at_epoch")
    now = _number(now_epoch, "now_epoch")
    max_age = _number(max_age_seconds, "max_age_seconds")
    future_skew = _number(max_future_skew_seconds, "max_future_skew_seconds")
    if max_age < 0 or future_skew < 0:
        raise MarketDataObservationError("age and future-skew limits cannot be negative")
    if observed > now + future_skew or received > now + future_skew:
        raise MarketDataObservationError("timestamp is too far in the future")
    if received < observed - future_skew:
        raise MarketDataObservationError("receive timestamp materially predates observation")
    age = now - observed
    if age > max_age:
        raise MarketDataObservationError("observation is stale")
    result = dict(observation)
    result.update({"provider_id": provider_id, "event_id": event_id, "venue": venue,
        "instrument_identity": supplied, "bid": bid, "ask": ask,
        "observed_at_epoch": observed, "received_at_epoch": received,
        "sequence": sequence, "age_seconds": max(0.0, age),
        "observation_shape_valid": True, "source_authenticated": False,
        "independent_source_verified": False, "market_data_trusted": False,
        "execution_eligible": False})
    return result

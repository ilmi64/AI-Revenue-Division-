"""Canonical, fail-closed instrument identity contract for OCC.

This module validates descriptive instrument specifications only. It does not
fetch quotes, authenticate venues, establish ownership, interpret contracts,
or authorize trading.
"""
from __future__ import annotations

import math
import re
from typing import Any, Mapping


MARKET_CLASSES = {"CRYPTO", "FOREX", "INDICES", "METALS", "EQUITIES", "OTHER"}
PRODUCT_TYPES = {
    "SPOT", "FX_SPOT", "INDEX_CASH", "CFD", "FUTURE", "OPTION",
    "TOKEN", "TOKENIZED_ASSET", "ETF", "OTHER",
}
SETTLEMENT_METHODS = {
    "CASH", "PHYSICAL_DELIVERY", "NET_CASH", "TOKEN_DELIVERY", "UNKNOWN",
}
CUSTODY_MODELS = {"ALLOCATED", "UNALLOCATED", "SELF_CUSTODY", "NOT_APPLICABLE", "UNKNOWN"}
FINANCING_MODELS = {
    "NONE_CONFIRMED", "OVERNIGHT_SWAP", "INTEREST_BEARING", "FUNDING_RATE",
    "MARGIN_FINANCING", "UNKNOWN",
}
_SYMBOL_RE = re.compile(r"^[A-Z0-9][A-Z0-9._:/-]{0,63}$")
_CURRENCY_RE = re.compile(r"^[A-Z0-9]{2,12}$")


class InstrumentIdentityError(ValueError):
    """An instrument identity is incomplete or internally inconsistent."""


def _required_text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise InstrumentIdentityError(f"{field} must be a non-empty string")
    return value.strip()


def _positive_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InstrumentIdentityError(f"{field} must be a finite positive number")
    try:
        number = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise InstrumentIdentityError(
            f"{field} must be a finite positive number"
        ) from exc
    if not math.isfinite(number) or number <= 0:
        raise InstrumentIdentityError(f"{field} must be a finite positive number")
    return number


def validate_instrument_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a normalized copy of one fully specified instrument identity.

    Caller-supplied venue and contract labels are descriptive, not authenticated.
    The function intentionally does not infer missing units, currencies,
    settlement, custody, financing, or delivery rights.
    """
    if not isinstance(record, Mapping):
        raise InstrumentIdentityError("instrument identity must be a mapping")

    market_class = _required_text(record, "market_class").upper()
    product_type = _required_text(record, "product_type").upper()
    venue = _required_text(record, "venue")
    symbol = _required_text(record, "symbol").upper()
    quote_currency = _required_text(record, "quote_currency").upper()
    contract_unit = _required_text(record, "contract_unit")
    settlement_method = _required_text(record, "settlement_method").upper()

    if market_class not in MARKET_CLASSES:
        raise InstrumentIdentityError("unsupported market_class")
    if product_type not in PRODUCT_TYPES:
        raise InstrumentIdentityError("unsupported product_type")
    if settlement_method not in SETTLEMENT_METHODS:
        raise InstrumentIdentityError("unsupported settlement_method")
    if not _SYMBOL_RE.fullmatch(symbol):
        raise InstrumentIdentityError("symbol contains unsupported characters")
    if not _CURRENCY_RE.fullmatch(quote_currency):
        raise InstrumentIdentityError("quote_currency must be a currency/code identifier")

    base_currency = record.get("base_currency")
    if base_currency is not None:
        if not isinstance(base_currency, str) or not _CURRENCY_RE.fullmatch(base_currency.strip().upper()):
            raise InstrumentIdentityError("base_currency must be omitted or a valid code")
        base_currency = base_currency.strip().upper()

    expiry = record.get("expiry")
    if expiry is not None:
        if not isinstance(expiry, str) or not expiry.strip():
            raise InstrumentIdentityError("expiry must be omitted or a non-empty string")
        expiry = expiry.strip()

    custody_model = str(record.get("custody_model", "UNKNOWN")).strip().upper()
    financing_model = str(record.get("financing_model", "UNKNOWN")).strip().upper()
    if custody_model not in CUSTODY_MODELS:
        raise InstrumentIdentityError("unsupported custody_model")
    if financing_model not in FINANCING_MODELS:
        raise InstrumentIdentityError("unsupported financing_model")

    multiplier = record.get("contract_multiplier")
    if multiplier is not None:
        multiplier = _positive_number(multiplier, "contract_multiplier")

    if product_type == "FX_SPOT" and base_currency is None:
        raise InstrumentIdentityError("FX spot identity requires an explicit base_currency")
    if product_type == "FUTURE" and expiry is None:
        raise InstrumentIdentityError("futures identity requires an explicit expiry")
    if product_type in {"SPOT", "FX_SPOT", "INDEX_CASH"} and expiry is not None:
        raise InstrumentIdentityError("cash/spot identity cannot carry a futures expiry")

    result = dict(record)
    result.update({
        "market_class": market_class,
        "product_type": product_type,
        "venue": venue,
        "symbol": symbol,
        "quote_currency": quote_currency,
        "contract_unit": contract_unit,
        "settlement_method": settlement_method,
        "base_currency": base_currency,
        "expiry": expiry,
        "contract_multiplier": multiplier,
        "custody_model": custody_model,
        "financing_model": financing_model,
        "identity_complete": True,
        "venue_authenticated": False,
        "contract_terms_verified": False,
        "ownership_verified": False,
        "financing_verified": False,
        "execution_eligible": False,
    })
    return result

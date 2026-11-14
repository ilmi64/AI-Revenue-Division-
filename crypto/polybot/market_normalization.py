"""Source-preserving normalization and comparison for PolyBot research data.

No network access, trading logic, or quote-currency conversion is performed here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


class MarketDataValidationError(ValueError):
    """Raised when a source observation cannot safely be normalized."""


def _utc(value: str | datetime, field: str) -> datetime:
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise MarketDataValidationError(f"{field} must be an ISO-8601 timestamp") from exc
    elif isinstance(value, datetime):
        parsed = value
    else:
        raise MarketDataValidationError(f"{field} must be an ISO-8601 timestamp")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise MarketDataValidationError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _decimal(value: Any, field: str, *, positive: bool = False) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise MarketDataValidationError(f"{field} must be numeric") from exc
    if not number.is_finite() or (positive and number <= 0):
        raise MarketDataValidationError(f"{field} must be finite" + (" and positive" if positive else ""))
    return number


def normalize_binance_klines(
    rows: Iterable[list[Any]],
    *,
    symbol: str,
    base_asset: str,
    quote_asset: str,
    interval: str,
    collected_at: str | datetime,
    include_unfinished: bool = False,
) -> list[dict[str, Any]]:
    """Normalize Binance kline rows; reject duplicates and malformed OHLCV."""
    collected = _utc(collected_at, "collected_at")
    if not all(isinstance(v, str) and v for v in (symbol, base_asset, quote_asset, interval)):
        raise MarketDataValidationError("symbol, assets, and interval are required")
    normalized = []
    seen_open_times: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            raise MarketDataValidationError(f"row {index} must contain at least six kline fields")
        try:
            open_ms, close_ms = int(row[0]), int(row[6]) if len(row) > 6 else None
        except (TypeError, ValueError) as exc:
            raise MarketDataValidationError(f"row {index} has invalid timestamps") from exc
        if open_ms < 0 or (close_ms is not None and close_ms < open_ms):
            raise MarketDataValidationError(f"row {index} has invalid timestamp ordering")
        if open_ms in seen_open_times:
            raise MarketDataValidationError(f"duplicate candle open time: {open_ms}")
        seen_open_times.add(open_ms)

        values = {
            "open": _decimal(row[1], "open", positive=True),
            "high": _decimal(row[2], "high", positive=True),
            "low": _decimal(row[3], "low", positive=True),
            "close": _decimal(row[4], "close", positive=True),
            "volume": _decimal(row[5], "volume"),
        }
        if values["volume"] < 0:
            raise MarketDataValidationError("volume cannot be negative")
        if values["high"] < max(values["open"], values["close"], values["low"]):
            raise MarketDataValidationError("high must be at least open, close, and low")
        if values["low"] > min(values["open"], values["close"], values["high"]):
            raise MarketDataValidationError("low must not exceed open, close, or high")

        unfinished = close_ms is not None and close_ms >= int(collected.timestamp() * 1000)
        if unfinished and not include_unfinished:
            continue
        payload = {
            "open_time_ms": open_ms,
            "close_time_ms": close_ms,
            **{key: str(value) for key, value in values.items()},
        }
        normalized.append({
            "source": "binance_spot",
            "venue_symbol": symbol,
            "base_asset": base_asset,
            "quote_asset": quote_asset,
            "data_type": "candle",
            "event_time": datetime.fromtimestamp(open_ms / 1000, timezone.utc).isoformat(),
            "close_time": (
                datetime.fromtimestamp(close_ms / 1000, timezone.utc).isoformat()
                if close_ms is not None else None
            ),
            "collected_at": collected.isoformat(),
            "interval": interval,
            "payload": payload,
            "is_snapshot": False,
            "is_complete": not unfinished,
            "quality_flags": ["missing_close_time"] if close_ms is None else [],
        })
    return sorted(normalized, key=lambda item: item["payload"]["open_time_ms"])


def normalize_last_price(
    *,
    source: str,
    venue_symbol: str,
    base_asset: str,
    quote_asset: str,
    price: Any,
    collected_at: str | datetime,
) -> dict[str, Any]:
    """Normalize a ticker price without inventing an exchange event timestamp."""
    collected = _utc(collected_at, "collected_at")
    value = _decimal(price, "price", positive=True)
    return {
        "source": source,
        "venue_symbol": venue_symbol,
        "base_asset": base_asset,
        "quote_asset": quote_asset,
        "data_type": "last_price",
        "event_time": None,
        "collected_at": collected.isoformat(),
        "interval": None,
        "payload": {"price": str(value)},
        "is_snapshot": False,
        "quality_flags": ["missing_event_time"],
    }


def normalize_order_book_snapshot(
    *,
    source: str,
    venue_symbol: str,
    base_asset: str,
    quote_asset: str,
    book: dict[str, Any],
    collected_at: str | datetime,
) -> dict[str, Any]:
    """Preserve a point-in-time book snapshot; it is not an order-flow stream."""
    collected = _utc(collected_at, "collected_at")
    if not isinstance(book, dict) or not isinstance(book.get("bids"), list) or not isinstance(book.get("asks"), list):
        raise MarketDataValidationError("order book must contain bids and asks arrays")
    return {
        "source": source,
        "venue_symbol": venue_symbol,
        "base_asset": base_asset,
        "quote_asset": quote_asset,
        "data_type": "order_book_snapshot",
        "event_time": None,
        "collected_at": collected.isoformat(),
        "interval": None,
        "payload": {"lastUpdateId": book.get("lastUpdateId"), "bids": book["bids"], "asks": book["asks"]},
        "is_snapshot": True,
        "quality_flags": ["snapshot_only", "not_synchronized_order_flow", "missing_event_time"],
    }


def freshness_status(observation: dict[str, Any], *, now: str | datetime, max_age_seconds: float) -> dict[str, Any]:
    """Return an explicit freshness decision based on collection time."""
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds cannot be negative")
    collected = _utc(observation["collected_at"], "collected_at")
    current = _utc(now, "now")
    age = (current - collected).total_seconds()
    if age < 0:
        return {"available": False, "age_seconds": age, "quality_flags": ["collection_time_in_future"]}
    stale = age > max_age_seconds
    return {
        "available": not stale,
        "age_seconds": age,
        "quality_flags": ["stale"] if stale else [],
    }


def compare_price_observations(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    max_collection_skew_seconds: float = 30.0,
) -> dict[str, Any]:
    """Compare two observed prices while explicitly preserving quote-asset differences.

    The percentage is a descriptive relative quote-price difference, not an
    executable spread, arbitrage signal, or currency-converted valuation.
    """
    required = ("source", "base_asset", "quote_asset", "collected_at", "payload")
    if any(any(key not in item for key in required) for item in (left, right)):
        raise MarketDataValidationError("both observations must contain source, assets, time, and payload")
    if left["data_type"] != "last_price" or right["data_type"] != "last_price":
        raise MarketDataValidationError("only last_price observations can be compared")
    if left["base_asset"] != right["base_asset"]:
        raise MarketDataValidationError("base assets must match")
    if max_collection_skew_seconds < 0:
        raise ValueError("max_collection_skew_seconds cannot be negative")
    left_time = _utc(left["collected_at"], "left.collected_at")
    right_time = _utc(right["collected_at"], "right.collected_at")
    skew = abs((left_time - right_time).total_seconds())
    left_price = _decimal(left["payload"].get("price"), "left price", positive=True)
    right_price = _decimal(right["payload"].get("price"), "right price", positive=True)
    pct = (right_price - left_price) / left_price * Decimal("100")
    return {
        "base_asset": left["base_asset"],
        "left": {"source": left["source"], "quote_asset": left["quote_asset"], "price": str(left_price)},
        "right": {"source": right["source"], "quote_asset": right["quote_asset"], "price": str(right_price)},
        "collection_skew_seconds": skew,
        "comparable_in_time": skew <= max_collection_skew_seconds,
        "relative_quote_price_difference_percent": str(pct),
        "quote_assets_match": left["quote_asset"] == right["quote_asset"],
        "executable_spread": False,
        "interpretation": "descriptive_only; no FX conversion, fees, slippage, or synchronization guarantee",
    }


def normalize_coinbase_candles(
    rows: Iterable[dict[str, Any]],
    *,
    pair: str,
    interval: str,
    collected_at: str | datetime,
) -> list[dict[str, Any]]:
    """Normalize the existing Coinbase candle rows without changing that collector."""
    collected = _utc(collected_at, "collected_at")
    if not isinstance(pair, str) or pair.count("-") != 1:
        raise MarketDataValidationError("Coinbase pair must use BASE-QUOTE notation")
    base_asset, quote_asset = pair.split("-", 1)
    if not base_asset or not quote_asset or not interval:
        raise MarketDataValidationError("pair assets and interval are required")
    normalized = []
    seen_times: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or "timestamp" not in row:
            raise MarketDataValidationError(f"Coinbase row {index} is missing timestamp")
        event_time = _utc(row["timestamp"], f"Coinbase row {index} timestamp")
        event_key = event_time.isoformat()
        if event_key in seen_times:
            raise MarketDataValidationError(f"duplicate Coinbase candle time: {event_key}")
        seen_times.add(event_key)
        values = {
            key: _decimal(row.get(key), key, positive=True)
            for key in ("open", "high", "low", "close")
        }
        values["volume"] = _decimal(row.get("volume"), "volume")
        if values["volume"] < 0:
            raise MarketDataValidationError("volume cannot be negative")
        if values["high"] < max(values["open"], values["close"], values["low"]):
            raise MarketDataValidationError("high must be at least open, close, and low")
        if values["low"] > min(values["open"], values["close"], values["high"]):
            raise MarketDataValidationError("low must not exceed open, close, or high")
        normalized.append({
            "source": "coinbase_exchange",
            "venue_symbol": pair,
            "base_asset": base_asset,
            "quote_asset": quote_asset,
            "data_type": "candle",
            "event_time": event_key,
            "collected_at": collected.isoformat(),
            "interval": interval,
            "payload": {key: str(value) for key, value in values.items()},
            "is_snapshot": False,
            "is_complete": True,
            "quality_flags": [],
        })
    return sorted(normalized, key=lambda item: item["event_time"])


def compare_candle_series(
    left: Iterable[dict[str, Any]],
    right: Iterable[dict[str, Any]],
    *,
    max_time_skew_seconds: float = 60.0,
) -> list[dict[str, Any]]:
    """Compare aligned candle returns, never conflating USD and USDT price levels."""
    if max_time_skew_seconds < 0:
        raise ValueError("max_time_skew_seconds cannot be negative")
    left_rows = list(left)
    right_rows = list(right)
    if not left_rows or not right_rows:
        return []
    left_meta, right_meta = left_rows[0], right_rows[0]
    if left_meta.get("base_asset") != right_meta.get("base_asset"):
        raise MarketDataValidationError("base assets must match")
    if left_meta.get("interval") != right_meta.get("interval"):
        raise MarketDataValidationError("candle intervals must match")
    for row in left_rows + right_rows:
        if row.get("data_type") != "candle" or not row.get("is_complete", False):
            raise MarketDataValidationError("only complete candle observations can be compared")
    left_by_time = {_utc(row["event_time"], "left event_time"): row for row in left_rows}
    right_by_time = {_utc(row["event_time"], "right event_time"): row for row in right_rows}
    common_times = sorted(set(left_by_time).intersection(right_by_time))
    output = []
    previous_left = previous_right = None
    for event_time in common_times:
        lrow, rrow = left_by_time[event_time], right_by_time[event_time]
        skew = abs((_utc(lrow["event_time"], "left event_time") -
                    _utc(rrow["event_time"], "right event_time")).total_seconds())
        lclose = _decimal(lrow["payload"]["close"], "left close", positive=True)
        rclose = _decimal(rrow["payload"]["close"], "right close", positive=True)
        lreturn = rreturn = None
        if previous_left is not None and previous_right is not None:
            lreturn = (lclose - previous_left) / previous_left * Decimal("100")
            rreturn = (rclose - previous_right) / previous_right * Decimal("100")
        output.append({
            "event_time": event_time.isoformat(),
            "base_asset": left_meta["base_asset"],
            "interval": left_meta["interval"],
            "left_source": lrow["source"],
            "left_quote_asset": lrow["quote_asset"],
            "left_close": str(lclose),
            "left_return_percent": str(lreturn) if lreturn is not None else None,
            "right_source": rrow["source"],
            "right_quote_asset": rrow["quote_asset"],
            "right_close": str(rclose),
            "right_return_percent": str(rreturn) if rreturn is not None else None,
            "return_difference_percentage_points": (
                str(rreturn - lreturn) if lreturn is not None and rreturn is not None else None
            ),
            "price_levels_comparable": lrow["quote_asset"] == rrow["quote_asset"],
            "time_aligned": skew <= max_time_skew_seconds,
            "time_skew_seconds": skew,
            "interpretation": "aligned_return_comparison_only; no FX conversion or executable spread",
        })
        previous_left, previous_right = lclose, rclose
    return output

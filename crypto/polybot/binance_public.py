"""Read-only Binance Spot market-data client for PolyBot.

This module deliberately uses Binance's unauthenticated market-data host.
It does not support account, wallet, order, margin, or futures endpoints.
"""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://data-api.binance.vision"
_ALLOWED_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h",
    "6h", "8h", "12h", "1d", "3d", "1w", "1M",
}
_SYMBOL_RE = re.compile(r"^[A-Z0-9]{5,20}$")


class BinanceMarketDataError(RuntimeError):
    """Raised when Binance public market data cannot be retrieved or validated."""


def _validate_symbol(symbol: str) -> str:
    if not isinstance(symbol, str) or not _SYMBOL_RE.fullmatch(symbol):
        raise ValueError("symbol must be an uppercase Binance symbol, e.g. BTCUSDT")
    return symbol


def _request_json(endpoint: str, params: dict[str, Any], timeout: float = 10.0) -> Any:
    query = urlencode(params)
    url = f"{BASE_URL}{endpoint}?{query}" if query else f"{BASE_URL}{endpoint}"
    request = Request(
        url,
        headers={"User-Agent": "PolyBot-Research/0.1", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BinanceMarketDataError(f"Binance public market-data request failed: {exc}") from exc


def get_price(symbol: str, timeout: float = 10.0) -> dict[str, str]:
    """Return the latest Spot price for one symbol."""
    symbol = _validate_symbol(symbol)
    data = _request_json("/api/v3/ticker/price", {"symbol": symbol}, timeout)
    if not isinstance(data, dict) or data.get("symbol") != symbol or "price" not in data:
        raise BinanceMarketDataError("Unexpected price response schema")
    return data


def get_24h_ticker(symbol: str, timeout: float = 10.0) -> dict[str, Any]:
    """Return 24-hour Spot ticker statistics for one symbol."""
    symbol = _validate_symbol(symbol)
    data = _request_json("/api/v3/ticker/24hr", {"symbol": symbol}, timeout)
    required = {"symbol", "priceChangePercent", "lastPrice", "volume", "quoteVolume"}
    if not isinstance(data, dict) or data.get("symbol") != symbol or not required.issubset(data):
        raise BinanceMarketDataError("Unexpected 24-hour ticker response schema")
    return data


def get_klines(
    symbol: str, interval: str = "1h", limit: int = 500, timeout: float = 10.0
) -> list[list[Any]]:
    """Return historical Spot candles; timestamps are Binance Unix milliseconds."""
    symbol = _validate_symbol(symbol)
    if interval not in _ALLOWED_INTERVALS:
        raise ValueError(f"unsupported interval: {interval}")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer from 1 to 1000")
    data = _request_json(
        "/api/v3/klines",
        {"symbol": symbol, "interval": interval, "limit": limit},
        timeout,
    )
    if not isinstance(data, list) or any(not isinstance(row, list) or len(row) < 6 for row in data):
        raise BinanceMarketDataError("Unexpected kline response schema")
    return data


def get_order_book(symbol: str, limit: int = 100, timeout: float = 10.0) -> dict[str, Any]:
    """Return a Spot order-book snapshot (not a synchronized live depth stream)."""
    symbol = _validate_symbol(symbol)
    if limit not in {5, 10, 20, 50, 100, 500, 1000, 5000}:
        raise ValueError("unsupported order-book limit")
    data = _request_json("/api/v3/depth", {"symbol": symbol, "limit": limit}, timeout)
    if not isinstance(data, dict) or not isinstance(data.get("bids"), list) or not isinstance(data.get("asks"), list):
        raise BinanceMarketDataError("Unexpected order-book response schema")
    return data

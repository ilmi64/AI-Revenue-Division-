# PolyBot — Binance Public Market Data

This is a read-only Spot market-data adapter. It uses Binance's public
`data-api.binance.vision` host and requires no API key.

## Supported data

- Latest Spot price
- 24-hour Spot ticker statistics
- Historical Spot klines/candles
- Spot order-book snapshots

## Safety boundary

- No API keys, account access, balances, wallet functions, orders, transfers,
  margin, derivatives, or trade execution.
- The order-book method returns a snapshot. It is not a synchronized depth
  stream; do not treat it as full order-flow reconstruction.
- Market data is informational and may be delayed, incomplete, or unavailable.
- Callers must timestamp observations, handle request failures, and fail closed
  rather than inventing or carrying forward stale values.

## Quick use

From the repository root:

```python
from crypto.polybot.binance_public import get_price, get_24h_ticker, get_klines, get_order_book

print(get_price("BTCUSDT"))
print(get_24h_ticker("BTCUSDT"))
candles = get_klines("BTCUSDT", interval="1h", limit=100)
book_snapshot = get_order_book("BTCUSDT", limit=100)
```

## Tests

Run without network access:

```bash
python -m unittest discover -s crypto/polybot/tests -v
```

This module is a data-source component only. Strategy decisions, backtesting,
paper execution, and risk controls remain separate PolyBot components.

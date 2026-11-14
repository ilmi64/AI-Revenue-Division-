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

## Historical data-quality evaluation

The offline `crypto/polybot/data_quality.py` evaluator checks one source and
one expected candle grid. It reports:

- Expected versus valid hourly candles and coverage percentage.
- Missing timestamps grouped into contiguous gap ranges.
- Duplicate timestamps, malformed records, incomplete candles, and records
  outside the requested window.
- Latest collection time, age, future timestamps, and stale-feed status.
- Optional cross-venue return-difference flags when enough aligned comparison
  samples are supplied.

The evaluator preserves source, base asset, quote asset, and interval labels.
It does not fill missing candles, convert USD to USDT, infer executable
spreads, or turn divergence into a strategy signal. A feed is marked usable
for research only when its configured coverage and quality gates pass.

Example:

```python
from crypto.polybot.data_quality import evaluate_candle_quality

report = evaluate_candle_quality(
    normalized_candles,
    expected_start="2026-11-14T10:00:00Z",
    expected_end="2026-11-14T18:00:00Z",
    now="2026-11-14T18:05:00Z",
    interval_seconds=3600,
    max_age_seconds=5400,
)
print(report["coverage_percent"], report["quality_flags"])
```

## Cross-venue research integration

The Polybot_Development.ipynb notebook keeps its original Coinbase USD hourly
collector. A separate Phase 3B cell clones this feature branch and fetches
bounded Binance Spot USDT hourly candles for BTC, ETH, and SOL. It normalizes
both feeds and writes source-labelled comparison CSVs to the existing local
and Google Drive data folders.

The comparison uses only exact matching UTC candle-open timestamps. It
compares per-venue percentage returns; USD and USDT close-price levels remain
separate and are not FX-converted. A missing Coinbase or Binance series is
reported as unavailable rather than filled or inferred. The notebook cell has
not been run in a live Colab session yet; its first execution remains an
owner-operated, public read-only data collection check.

The notebook integration now runs the offline candle-quality evaluator for
both normalized sources over their exact shared hourly history window. It writes
a separate `*_data_quality_hourly.csv` report per asset, alongside the
cross-venue return comparison CSV. The quality report preserves venue and quote
asset, expected/valid/missing candle counts, coverage, gap ranges, duplicate
and malformed counts, freshness, research-usability status, and divergence
review flags. The report evaluates the same bounded overlap window for both
venues; it does not silently extend one feed beyond the other's available data.

The notebook integration does not add trading, account access, wallet signing,
or transaction functionality.

## Tests

Run without network access:

```bash
python -m unittest discover -s crypto/polybot/tests -v
```

This module is a data-source and data-quality component only. Strategy
decisions, backtesting, paper execution, and risk controls remain separate
PolyBot components.

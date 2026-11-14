# PolyBot Market-Intelligence Integration Design

Status: design proposal for owner review. This document does not change the Colab notebook, replace Coinbase, or enable trading.

## 1. Current architecture found

The current `main` branch contains `Polybot_Development.ipynb`. Its Phase 3 market-intelligence cell:
- collects hourly candles from Coinbase Exchange for `BTC-USD`, `ETH-USD`, and `SOL-USD`;
- validates and sorts the candle rows with pandas;
- stores CSV files in the Colab workspace and Google Drive;
- records a local `collected_at` timestamp.

The Binance adapter is currently isolated in this draft PR under `crypto/polybot/binance_public.py`. It exposes public Spot price, 24-hour ticker, klines, and order-book snapshot methods. It is not yet called by the notebook.

## 2. Recommended integration strategy

Add Binance as a second, independently labelled research feed first. Do not silently replace Coinbase or combine observations from different quote assets.

Initial explicit symbol map:
- Coinbase `BTC-USD` <-> Binance `BTCUSDT`
- Coinbase `ETH-USD` <-> Binance `ETHUSDT`
- Coinbase `SOL-USD` <-> Binance `SOLUSDT`

Important: USD and USDT are not identical instruments. Keep `quote_asset` and `source` on every record. Do not calculate cross-exchange spreads or merge price series as though USD and USDT were interchangeable. Any later comparison must disclose the quote-asset basis and independently validate timestamps.

## 3. Normalized observation contract

Every observation passed into market intelligence should carry:
- `source`: e.g. `coinbase_exchange` or `binance_spot`
- `venue_symbol`: exact symbol used at the venue
- `base_asset` and `quote_asset`
- `data_type`: `candle`, `ticker_24h`, `last_price`, or `order_book_snapshot`
- `event_time`: venue timestamp when supplied; otherwise null, never fabricated
- `collected_at`: UTC timestamp recorded by the collector
- `interval`: candle interval where applicable
- `payload`: validated source payload
- `is_snapshot`: true for order-book snapshots
- `quality_flags`: explicit validation, missing-time, or stale-data flags

Keep original venue payload values and decimal strings where possible; convert to numeric values only in a separate analysis layer with validation.

## 4. Feed-specific rules

### Candles
- Use Binance klines as a separate `binance_spot` series, preserving open and close timestamps in Unix milliseconds before conversion to UTC.
- Preserve candle interval and quote asset.
- Sort ascending, reject malformed rows, reject duplicate open times, and validate positive OHLC values, high/low relationships, and non-negative volume.
- Do not treat an unfinished current candle as a completed historical candle.

### Ticker and last price
- Record `collected_at` for every response.
- Use venue event timestamps only when the endpoint provides them.
- Apply a configurable freshness threshold before any downstream signal; missing or stale data must be marked unavailable, not carried forward as current.

### Order book
- Treat `get_order_book` strictly as a point-in-time snapshot.
- Preserve `lastUpdateId` and collection time.
- Do not infer trade direction, queue position, cancellations, replenishment, or synchronized order flow from a single snapshot.
- Do not feed snapshot-derived imbalance into a strategy until its definition, freshness threshold, and historical validation are specified.

## 5. Pipeline placement

Proposed flow:

`public venue adapters -> source-specific validation -> normalized observations -> freshness/quality gate -> research features -> historical evaluation -> paper-only strategy evaluation`

The source adapters must not make trading decisions. The quality gate must fail closed: if data is missing, malformed, stale, or quote-asset ambiguous, downstream research receives an unavailable status rather than a guessed value.

## 6. Historical validation plan

Before using Binance-derived features:
1. Collect Coinbase USD and Binance USDT series separately for the same UTC intervals.
2. Check missing intervals, duplicates, ordering, malformed OHLCV, and timestamp alignment.
3. Measure data freshness and request failures.
4. Keep source and quote asset visible in every report and exported CSV.
5. Evaluate any proposed feature out-of-sample and include fees/slippage assumptions only when supported by documented inputs.
6. Compare paper results against a baseline that uses the existing Coinbase feed only.

## 7. Safety and operating boundaries

- Public unauthenticated Spot market data only.
- No API keys, private account endpoints, balances, wallets, signing, orders, transfers, margin, derivatives, leverage, or live execution.
- No automatic strategy execution. Research and paper evaluation only.
- No paid data services or subscriptions; default spend remains CAD $0.
- Keep the integration in this draft PR for review. No merge, deployment, or production changes without owner approval.

## 8. Implementation sequence

1. Review and approve this source-separation and normalized-schema design.
2. Add a small tested normalization layer and offline fixtures on this feature branch.
3. Integrate the Binance feed as a parallel dataset in the Colab Phase 3 workflow without removing Coinbase.
4. Run offline tests, then a bounded public-data collection check only if separately approved and rate-limited.
5. Complete historical data-quality review before any paper-strategy evaluation.

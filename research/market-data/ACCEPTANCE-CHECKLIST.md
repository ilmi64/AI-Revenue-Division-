# Market Data Source Acceptance Checklist

This is a research and paper-trading intake standard. It does not approve any feed for live execution.

## Required source dossier
1. Legal provider identity, official docs, current terms and API/product version.
2. Data class: executable bid/ask, venue quote, indicative spot, reference rate, index proxy, or historical bar.
3. Exact instruments, symbol mapping, venue, contract specifications and currency.
4. Provider timestamp, receive timestamp, timezone, cadence, delay, corrections and retention.
5. Free-tier quota, attribution, storage, redistribution and commercial-use rights.
6. Canadian/Ontario access and any KYC, account or geographic restrictions.
7. Credential scopes, secret storage, privacy, rate limits and incident contact.
8. Provider outage behaviour, retry/backoff, stale-data thresholds and independent fallback.
9. Sample captures with provenance and repeatable quality checks.
10. Approval record, owner, review date and permitted use.

## Instrument-specific acceptance
- Crypto: venue-specific symbols, quote currency, market status, order-book depth semantics, sequence gaps and exchange outages.
- Pump.fun/Solana: official permitted endpoints, mint/pool identity, migration handling, slot/block context, RPC commitment level, provider independence and no prohibited user profiling.
- Forex: distinguish indicative/reference rates from executable broker bid/ask; record session calendar and rollover.
- Indices: define cash index vs ETF vs futures vs CFD; record contract multiplier, currency, session and roll/adjustment policy.
- XAUUSD: distinguish bullion spot, benchmark fix, futures and broker CFD; record bid/ask, contract size, tick, trading hours, financing/swap and broker-specific spread.

## Fail-closed rules
- No source is production-approved until all required dossier fields are evidenced.
- No live trading from reference-only, delayed, indicative, synthetic, stale or incomplete data.
- No source mixing without explicit mapping and documented basis.
- No paid plan, trial with billing risk, account connection or credential use without owner approval.
- Source acceptance does not authorise live trading; Risk, Finance, Technology and owner gates remain separate.

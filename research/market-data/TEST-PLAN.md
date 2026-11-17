# Market Data Intake Test Plan

- Reject missing source identity, instrument mapping, timestamps, currency or price basis.
- Reject negative, non-finite and crossed quotes.
- Reject invalid OHLC relationships and incomplete bars presented as final.
- Mark delayed/reference/indicative feeds as non-executable regardless of numeric freshness.
- Simulate stale data, duplicate sequence, sequence gap, provider outage and clock skew.
- Demonstrate provider failover with genuinely independent operators before claiming redundancy.
- Verify FX reference rates cannot satisfy broker quote requirements.
- Verify bullion spot cannot satisfy XAUUSD broker quote requirements.
- Verify index proxies cannot be treated as CFD/futures contract quotes.
- Verify synthetic fixtures are clearly labelled and cannot satisfy source-readiness gates.
- Record every test with source version, fixture hash, run time and result.

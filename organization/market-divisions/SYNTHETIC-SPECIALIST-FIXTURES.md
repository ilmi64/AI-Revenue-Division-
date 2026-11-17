# Synthetic Specialist Desk Fixtures

These fixtures exercise the common market-observation contract for Crypto, Forex, Indices and Gold. Every price is invented deterministic test data. They are not historical, delayed, indicative or live market prices and must never be used for strategy evaluation, valuation, signals or execution.

## Files

- `synthetic-market-source-registry.json`: local fixture-only source declarations. The `approved_manual` state applies only to these locally generated fixtures and is explicitly not approval of any external provider.
- `fixtures/specialist-market-observations.synthetic.jsonl`: four observations, one for each specialist desk.
- `synthetic-fixture-manifest.json`: fixed reference timestamp, instrument identities and test-only policy.

## Reproducible offline gate run

From `organization/market-divisions`:

```bash
python evidence_to_desk_gate.py \
  --market-source-registry synthetic-market-source-registry.json \
  --observations fixtures/specialist-market-observations.synthetic.jsonl \
  --now-utc 2026-11-17T12:00:00Z \
  --output /tmp/occ-synthetic-gate-report.json
```

Expected: `PASS_RESEARCH_GATES` for these four fixtures only. The report will explicitly retain `research_only_no_execution_authority`. This expected result is a test fixture expectation, not a claim that tests were executed.

## Instrument coverage

| Desk | Fixture | Explicit identity controls |
|---|---|---|
| Crypto | SOL-USD spot | Venue, USD quote, synthetic provenance |
| Forex | EURUSD spot | EUR base / USD quote orientation |
| Indices | US500 cash reference | Cash index identity, not futures or CFD |
| Gold | XAUUSD synthetic spot | Synthetic basis, troy-ounce quote unit, named UTC test session, freshness, financing and settlement marked unreviewed/unknown |

Gold's unknown financing and settlement remain warnings, not a suitability approval. The indicative/broker quote distinction is preserved. No instrument is asserted to be halal or suitable.

## Safety boundaries

- No API, broker, wallet, exchange or external provider is contacted.
- No credentials, paid access, GitHub Actions, scheduler, network service or execution path is used.
- The fixture registry cannot authorize external data sources.
- Synthetic fixtures must never satisfy live-data, source independence, market replay or live-readiness requirements.
- Change the fixed timestamps only together with the documented reference time and tests.

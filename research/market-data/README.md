# Market Data Research and Intake

Research-only candidate inventory and canonical feed-quality contract for Crypto/Solana, Forex, indices and gold. No source in this package is approved for live execution or account connection.

- `source-registry.json`: instrument-by-instrument candidate sources and evidence gaps.
- `canonical-data-contract.json`: common quote/bar provenance, timestamp and price-basis requirements.
- `ACCEPTANCE-CHECKLIST.md`: provider due diligence and fail-closed adoption gates.
- `TEST-PLAN.md`: deterministic feed-quality and outage scenarios.
- `validate_source_registry.py`: fail-closed validator for candidate status, unique instruments, review gates and zero-spend policy.

Run the validator from the repository root: `python research/market-data/validate_source_registry.py`. Its test module is `organization/tests/test_market_data_registry.py`; tests are included but have not been executed.

XAUUSD is deliberately split into indicative bullion spot sources and a broker-specific executable quote stream. Forex reference rates and index proxies are likewise not treated as executable prices.

All source candidates require current official terms, Canadian availability, data-rights and security review. No paid service, trial, account connection or credential is authorised.
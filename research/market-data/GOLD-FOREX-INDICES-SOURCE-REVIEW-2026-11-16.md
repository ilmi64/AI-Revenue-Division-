# Gold, Forex and Indices source qualification — 2026-11-16

**Decision:** research-only. No provider is approved for live execution, account connection, trading or paid access. CAD 0 incremental spend remains in force.

## Gold / XAUUSD

### Public reference sources

- **Standard Bullion API** — official documentation describes keyless bid/ask dealer quotes and 15-minute intraday history from 2026, with older daily/monthly history. It requires visible attribution and prohibits bulk redistribution/resale of the raw feed. This is an indicative dealer quote, not a broker's XAUUSD CFD price. Suitable for a separately labelled gold reference series after terms review; not an execution-price source.
  - Docs: https://standardbullion.com/gold-price-api
  - Terms: https://standardbullion.com/market-data
- **GoldPrice.dev** — official docs dated 2026-10-20 describe XAU-USD spot, a 15-minute delay on free/keyless prices, 10 requests/minute and 100/hour per IP without a key, and 5,000 requests/month for a free key. Paid plans provide live prices. Keyless/delayed use is a possible research candidate only; no paid tier or key activation is authorized.
  - Docs: https://goldprice.dev/docs/endpoints/prices
- **XAUS** — public keyless spot endpoint with explicit data-state/age fields and documented last-known-price behaviour during upstream outages. Independence of its underlying price source has not been demonstrated; treat as corroborative reference only, never as an independent failover pair without provenance proof.
  - Project docs: https://github.com/misix-git/xaus-api

### Broker-specific XAUUSD candidates

- **FOREX.com Canada** publicly lists XAU/metals and describes spot-metals and CFD structures. Its Canada API overview advertises live streaming prices and historical data, but the workflow requires a standard account, funding and support activation for REST API access. No account or API request is authorized.
  - Metals: https://www.forex.com/en-ca/metals-trading/
  - API: https://www.forex.com/en-ca/trading-tools/api-trading/
- **OANDA Canada** publicly lists metals CFDs. OANDA's v20 API documentation describes real-time tradeable-pair rates and historical pricing, but requires a compatible v20 account and API-license acceptance; Canadian entity/account/API eligibility must be confirmed. No account, token or execution permission is authorized.
  - Canada metals: https://www.oanda.com/ca-en/trading/cfds/metals/
  - API intro: https://developer.oanda.com/rest-live-v20/introduction/
  - API comparison: https://developer.oanda.com/rest-live-v20/api-comparison/

**Gold data rule:** bullion spot, LBMA-style reference/fix, futures and broker CFD are distinct instruments. Do not merge their prices or treat a spot feed as executable XAUUSD. A broker-specific feed must provide bid/ask, exact symbol, contract size, tick size, session, spread, financing/holding costs and historical candle semantics.

## Forex / EURUSD

- **Frankfurter / ECB reference rates** — free, keyless, open-source API covering 219 currencies and 39 other assets from 112 central banks/official sources. The docs explicitly state that rates are reference rates, not live market quotes, and providers publish once or a few times daily. Pin the chosen provider and preserve its date/source. Useful for daily context and CAD accounting conversion, not intraday signal execution.
  - Docs: https://frankfurter.dev/
- **FOREX.com Canada REST API** — publicly describes streaming prices and historical data, but requires an account, funding and support activation. Candidate only.
- **OANDA v20** — publicly documents real-time rates and historical pricing, but compatible account and API license are prerequisites; Canadian division eligibility remains to be verified.

## Indices / US500

- **FOREX.com Canada** lists US SP 500 and documents API streaming/historical capability; exact index contract, symbol and API permissions need confirmation.
- **OANDA Canada** lists US SPX 500 index CFD products; exact contract and API eligibility need confirmation.
- A broker CFD is not the S&P 500 cash index, SPY ETF or CME E-mini/Micro futures. Record the instrument, venue, currency, multiplier, tick, hours, spread and any financing/rollover separately.
- Stooq remains a historical/delayed-data candidate only until symbol, terms, timestamps and automated-use rights are verified.

## Canada and regulatory context

CIRO's public dealer directory lists GAIN Capital - FOREX.com Canada Ltd. and OANDA (Canada) Corporation ULC as investment dealers. This is a useful entity check, not an endorsement, proof of a specific product/API entitlement, or a substitute for current registration and account terms.
- CIRO dealer directory: https://www.ciro.ca/office-investor/dealers-we-regulate
- FOREX.com Canada entity: https://www.ciro.ca/investors/choosing-investment-advisor/dealers-we-regulate/gain-capital-forexcom-canada-ltd

## Shariah and product-structure gate

A Canadian dealer's registration does not establish Shariah suitability. Spot/CFD classification, leverage, margin, overnight financing/swap, interest, shorting and settlement mechanics require separate qualified Shafi'i review before any product is considered. No automated classification is a fatwa. No account opening, funding or trade is proposed.

## Current disposition

- Reference sources: useful for historical/context research with labels and provenance; no production approval.
- Broker APIs: potentially useful only after account/API eligibility, API license, market-data rights, read-only scope, free access, and Canadian terms are confirmed. Some published onboarding flows require funding, so they are not compatible with the current zero-spend mandate.
- No broker token, API key, account or paid service was requested, created or connected.
- The source registry intentionally keeps `terms_review` and `canada_review` pending until a formal dossier and accountable owner review are complete.

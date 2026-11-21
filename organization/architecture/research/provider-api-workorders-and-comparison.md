# Public API Provider Work Orders & Existing-Capability Comparison

**Review date:** 2026-11-21  
**Parent decision:** Adopt `public-apis/public-apis` as a discovery/reference catalogue only.  
**Scope:** Provider-level research and candidate comparison; no API calls, accounts, keys, installations, data ingestion or integrations.

## 1. Selection principles

Prioritize the strongest candidates for no-cost research and business value, but do not add a provider merely because it is free or listed in the directory. Every candidate must pass the source-level gates in `public-apis-directory-evaluation.md`: authoritative documentation, actual free allowance, data/commercial rights, quota, freshness, privacy, security, runtime compatibility, fallback and recipient-company acceptance.

Use existing connected/approved sources first. Do not create duplicate market-data pipelines, add paid dependencies, or mix company-private data. API discovery is a Research & Intelligence service; each operating company retains its own adoption decision.

## 2. Candidate work orders

### R&I-API-01A — Frankfurter reference FX data

**Official docs:** https://frankfurter.dev/  
**Research finding:** keyless, no monthly/daily quota described by the provider; official blended central-bank/reference rates and commercial use are described as permitted. The data is reference/historical, not live executable pricing; update timing follows source publication and may be delayed, missing or revised.

**Recipients and use:**
- AI Revenue: optional internal bookkeeping, quote-context or reporting workflow where a reference conversion is suitable and source/date is shown.
- Research & Intelligence: historical macro/FX context and reference comparisons.
- Trading: macro/reference context only; never signal, price, size, margin, stop, risk, execution or live PnL feed.

**Acceptance evidence:** source currency coverage; timestamp/holiday behaviour; missing/revised rate behaviour; precision; provider terms and attribution; deterministic conversion test design (execution only after approval); comparison against central-bank source series.

**Fallback:** retain source provenance and date; do not silently substitute live exchange rates. If data is stale/missing, mark unavailable.

**Current state:** official documentation reviewed; no endpoint called, no API data fetched, no integration selected.

### R&I/TT-API-02A — SEC EDGAR public submissions and XBRL

**Official docs:** https://www.sec.gov/edgar/sec-api-documentation  
**Research finding:** public submissions and extracted XBRL APIs require no API key. SEC fair-access guidance requires a declared User-Agent and a maximum of 10 requests/second across machines. Data timing differs by endpoint; bulk archives update nightly.

**Recipients and use:**
- Research & Intelligence: US public issuer filing discovery, company disclosures and source-linked research.
- Trading: fundamental/company disclosure context for US issuers only, where relevant to a separately researched strategy.
- AI Revenue: possible public-company intelligence workflow only if customer demand and rights are established.

**Limits:** not Canadian issuer coverage or a substitute for SEDAR+; filings are not real-time market data; facts must retain filing accession, form, issuer/CIK, filing date, period and source URL. Never infer current market price or intraday conditions from filings.

**Acceptance evidence:** a declared client identity/User-Agent policy; central rate limiter; endpoint freshness and amendment handling; filing/accession provenance; XBRL taxonomy/context/unit validation; source citations; outage/backoff; no scraping beyond published fair-access rules.

**Fallback:** official filing archives and direct issuer filings; stale/missing records are marked explicitly.

**Current state:** official documentation reviewed; no endpoint called, no User-Agent registered, no integration selected.

### R&I-API-03A — OpenAlex research graph

**Official docs:** https://docs.openalex.org/  
**Research finding:** basic use can be keyless. A free key raises the daily budget and enables cursor paging; the free account has a defined $1/day usage allowance, after which usage is paid. No paid usage is permitted under the current resource policy.

**Recipients and use:**
- Research & Intelligence: scholarly literature, authors, institutions, concepts, citation graphs and technology/AI research.
- AI Revenue: market/product research only where scholarly evidence is relevant.
- Trading: limited use for quantitative-method and market-microstructure literature, not market data or signals.

**Acceptance evidence:** exact free-budget monitoring; no auto-upgrade or paid overage; provenance/DOI and versioning; deduplication; retraction/correction handling; coverage and ranking bias; rate limiting; privacy and terms review.

**Fallback:** publisher/open-access records and other public bibliographic sources with provenance. Keep search findings as literature evidence, not proof of a trading edge.

**Current state:** official docs reviewed; no account/key created, no API call, no integration selected.

### TT-API-04A — DefiLlama public crypto/DeFi data

**Official docs:** https://api-docs.defillama.com/  
**Research finding:** official docs describe free no-key endpoints and separate paid/API-plan offerings; some free yield endpoints are deprecated. Intended-use rights and redistribution restrictions require exact review before ingestion.

**Recipients and use:** Trading research and Research & Intelligence only. Potential protocol TVL, token/chain/protocol context and ecosystem capital-flow discovery; never sole source for price, liquidity, volume, solvency, smart-money attribution, execution or risk.

**Existing-source comparison:** compare with current Binance/Coinbase public exchange sources, Sanbase/Santiment, J7 and Buildix.trade. These are not interchangeable: centralized exchange feeds provide venue-specific market data; analytics platforms may offer on-chain/market metrics; DefiLlama may provide protocol/TVL context. Build a field-by-field overlap matrix before adoption.

**Acceptance evidence:** exact endpoint and current status; endpoint-specific terms and commercial/internal rights; methodology and source attribution; update cadence; chain/protocol coverage; historical revision behaviour; manipulation/labeling risks; free-tier stability; fallback to direct protocol/chain sources.

**Hard block:** no ingestion or redistribution until terms are cleared. Exclude deprecated yield endpoints.

**Current state:** official docs reviewed at a high level; terms review incomplete; no endpoint called or integrated.

### TT-API-05A — CoinGecko API

**Official pricing/licensing:** https://www.coingecko.com/en/api/pricing  
**Research finding:** free Demo limits are published, but CoinGecko's licensing FAQ says Demo does not include commercial API rights; commercial API use requires a paid plan.

**Disposition:** defer as a company integration. Do not build commercial AI Revenue or Trading services on Demo data and do not incur paid API costs under current policy. A public web page or free Demo tier is not a commercial data licence.

**Comparison:** first assess direct Binance/Coinbase exchange data and already researched analytics providers. Only revisit CoinGecko if a properly licensed commercial plan becomes permissible and is separately approved.

## 3. Existing-source duplication and dependency review

| Existing capability | Candidate overlap | Decision |
|---|---|---|
| Binance + Coinbase normalized comparison | CoinGecko, DefiLlama, CryptoCompare | Preserve direct exchange feeds for venue-specific data; add independent sources only for a clearly distinct field and after rights/freshness review. |
| Sanbase/Santiment | DefiLlama and other on-chain analytics | Compare metric definitions, coverage, history, update cadence, attribution and current entitlements; do not assume TVL, social, whale or smart-money metrics are equivalent. |
| J7 | DefiLlama and other crypto analytics | Inventory the exact existing J7 source/fields before adding duplicate protocol/flow metrics. |
| Buildix.trade | DefiLlama and public crypto datasets | Reconcile current Buildix functionality and source provenance before adoption. |
| PolyBot Phase 4 | Exchange data plus external analytics | Maintain a deterministic, auditable data hierarchy. No unverified third-party metric may directly authorize a signal or order. |
| AI Revenue business intelligence | SEC EDGAR, OpenAlex, Frankfurter | Choose by a concrete customer problem; avoid building a generic API aggregator before a paid/validated use case exists. |
| Research & Intelligence | All candidates | Maintain source provenance and recipient-scoped publication; R&I discovery is not a live data service until monitoring, staffing and validation exist. |

No candidate is a dependency for either company launch. Existing direct sources and manual/public documentation remain fallback paths.

## 4. Source record fields required before acceptance

For each provider and endpoint, record:
- provider legal entity, official documentation URL and review date;
- endpoint, API version, source revision and exact intended use;
- free-tier quota, rate limit, burst policy, billing trigger and hard spend guard;
- auth method, key lifecycle, secret handling and revocation;
- terms, commercial rights, redistribution, attribution, retention and privacy;
- data provenance, methodology, coverage, precision, timestamps and revision policy;
- service status/incidents, support/SLA and failure modes;
- runtime/platform compatibility and company tenant;
- duplicate fields versus existing sources;
- independent validation method, acceptance owner and fallback;
- status: candidate, conditional, approved for research, approved for production, deferred or rejected.

Do not store secrets or raw private company data in this registry.

## 5. Parallel next actions

1. R&I: create source records for Frankfurter, SEC EDGAR, OpenAlex and DefiLlama using official documentation and terms.
2. Trading: reconcile Binance/Coinbase, Sanbase/Santiment, J7, Buildix.trade and PolyBot data fields before choosing any new provider.
3. AI Revenue: identify one workflow that could use Frankfurter or SEC EDGAR and validate demand before building an integration.
4. R&I: keep CoinGecko deferred for commercial use and track any provider licensing change.
5. Policy/security: no endpoint call, account, API key, MCP connection, data transfer, installation or paid usage without separate approval.

**Current state:** documentation and candidate comparison only. No API calls, account creation, key issuance, provider connection, data ingestion, tests, installations, paid usage or deployment occurred.

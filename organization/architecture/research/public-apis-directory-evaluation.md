# Public APIs Directory — Strategic Evaluation & Adoption Plan

**Source:** https://github.com/public-apis/public-apis  
**Repository:** `public-apis/public-apis`  
**Review baseline:** 2026-11-21  
**Observed README blob:** `9374f27062f9fa239ba7a00a5b1ae8babe5536ff`  
**Observed LICENSE blob:** `196b23b178fbf71317fc55c3d3e01d481b5760e5`  
**Observed CONTRIBUTING blob:** `a8181acab01ac58ca80f3ef807b99fd5ec5e6e9d`  
**Disposition:** Adopt as a discovery/reference source only; no API integration or third-party connection authorized.

## 1. Executive decision

The repository is a high-value, low-cost discovery catalogue for the organization. It lists public APIs by category and records a short description, authentication requirement, HTTPS support and CORS availability. It also has a separate MCP server catalogue.

It is not:
- an API gateway, API aggregator or runtime;
- a guarantee that a provider is free, stable, secure, licensed for our use or commercially usable;
- a market-data quality certification or trading signal source;
- an uptime/SLA guarantee;
- permission to install an MCP server, create an account, issue API calls or transmit company data.

The repository's own MIT license applies to the catalogue repository's software/documentation. It does not grant rights to third-party API data, endpoints, brands or services. Each provider's terms, data licence, rate limits, attribution rules, retention rules and commercial-use conditions must be checked independently.

The contributing guide explicitly says entries should have full free access or at least a free tier, but the README's Auth/HTTPS/CORS columns do not disclose all plan limits, rate limits, fair-use restrictions, commercial rights or hidden costs. Therefore every entry is a lead, not an approved dependency.

## 2. Strategic value by organization

### AI Revenue Company — high potential

Potential uses:
- discover low-cost integrations for client workflows and small-business automation;
- enrich research briefs and business intelligence with public/open datasets;
- find public data sources for customer-facing prototypes where redistribution and commercial rights permit;
- discover email/domain validation, business data, document, productivity and developer APIs;
- identify public APIs that can support internal tooling and reproducible demos;
- discover AI/ML and MCP services, then compare them against local/open-source or existing model options.

Priority use is internal research and customer-problem validation. Do not promise a customer a third-party API feature until its terms, reliability, quota, privacy, cost and fallback are approved.

### Trading & Technology Company — high research value, low trust by default

Potential uses:
- discover crypto on-chain, DEX, protocol and public blockchain data sources;
- find public market, macroeconomic, FX, equity and news data leads;
- identify open economic, government and filing datasets;
- compare public data sources against direct exchange/provider documentation;
- discover data enrichment sources for capital-flow, token, project and ecosystem research.

**Trading data rule:** the directory is only a discovery index. Do not route orders, trigger signals, size positions, price instruments or calculate risk from a directory entry. Validate all market data directly against official provider/exchange documentation, licensing, timestamps, coverage, symbol mapping, precision, rate limits, outage behaviour and independent reference sources. Public does not mean real-time, complete, exchange-grade or licensed for trading use.

### Research & Intelligence Division — high strategic value

Use as a monitored discovery input across:
- API and MCP server discovery;
- new data providers and open datasets;
- business and product opportunity research;
- AI/model and developer ecosystem tracking;
- security, observability and infrastructure discovery.

Every discovery becomes a source-provenanced candidate record and, if worthwhile, a company-scoped research work order. Research publishes only approved recipient-scoped findings; it does not connect services or authorize adoption.

### Main Hub / OCC — metadata only

OCC may eventually display aggregate discovery counts, candidate status, source freshness and approved evidence references. It must not store API keys, call arbitrary endpoints, proxy unreviewed APIs or become a shared data ingestion point.

## 3. Initial shortlist from the current catalogue

The following are discovery candidates observed in the current README. The directory's own labels are reproduced as discovery metadata, not independently verified provider terms or uptime.

| Candidate | Catalogue category / listed auth | Potential value | Initial disposition |
|---|---|---|---|
| DefiLlama | Cryptocurrency; No auth | DeFi TVL, protocol, coin-price and volume research | P1 Trading research candidate; verify endpoints, methodology, freshness, licensing and limits |
| 0x | Cryptocurrency; No auth | DEX/token/pool data discovery | P1 Trading research candidate; verify exact product scope, endpoint quotas and permitted use |
| CoinGecko | Cryptocurrency; No auth in catalogue | Market, asset, developer/social metadata | P1 Trading comparison candidate; current key requirements and plan terms must be rechecked |
| CryptoCompare | Cryptocurrency; No auth in catalogue | Independent crypto comparison source | P2 Trading comparison candidate; verify current authentication, free quota and data rights |
| Binance public API documentation | Cryptocurrency; apiKey in catalogue | Direct exchange market-data reference | Existing exchange source; use official current documentation and preserve read-only scope |
| Coinbase developer API | Cryptocurrency; apiKey in catalogue | Exchange data comparison | Existing exchange source; verify current API product and market-data terms |
| SEC EDGAR Data | Finance; No auth | Public company filings and structured disclosures | P1 Research candidate for business/market intelligence; US issuer scope only |
| FRED | Finance; apiKey | Macro/economic series | P1 Trading macro research candidate; verify free account/key requirements and series licensing |
| Alpha Vantage | Finance; apiKey | Historical/realtime financial data | P2 only; free-tier quotas and market-data rights may constrain use |
| Twelve Data | Finance; apiKey | Financial market data | P2 only; verify free-tier limits and instrument coverage |
| MarketAux | News; apiKey | Tagged financial news and sentiment | P2 research candidate; verify quotas, attribution and redistribution rights |
| Currency-api | Currency Exchange; No auth | Reference currency rates | P1 non-execution FX reference candidate; verify update cadence, source and commercial terms |
| Frankfurter | Currency Exchange; No auth | Exchange rates, conversion and time series | P1 reference/macro candidate; not a live FX execution feed |
| OpenAlex | Open Data; No auth | Research papers, authors, institutions and concepts | P1 Research & Intelligence candidate |
| Canada Service Map | Government; No auth | Canadian public-service information | P2 AI Revenue/Research candidate; verify relevance, coverage and reuse terms |
| Hugging Face | Machine Learning; apiKey | Model discovery and inference ecosystem | Discovery only; do not assume inference is free or data can be sent to hosted models |
| CISA KEV catalogue entry | Security; apiKey in catalogue | Known-exploited vulnerability intelligence | Candidate only; prefer direct official CISA data source and verify endpoint provenance |
| GitHub APIs | Development / platform ecosystem | Repository metadata, release and issue intelligence | Existing GitHub connector is preferred where available; no extra token or app permissions |

The first shortlist deliberately emphasizes read-only public research and free/reference data. No API has been selected as a production dependency.

## 4. Candidate scoring and acceptance gates

Every candidate must be scored individually on:
1. provider identity and authoritative documentation;
2. current free tier and total cost, including inference, hosting, egress and support;
3. authentication, credential storage and revocation requirements;
4. data rights, commercial use, redistribution, retention and attribution;
5. rate limits, fair use, pagination and burst behaviour;
6. freshness, timestamps, coverage, precision and known gaps;
7. uptime history, incident transparency and support/SLA;
8. privacy, data residency, subprocessors and sensitive-data restrictions;
9. security posture, endpoint integrity, TLS and dependency risks;
10. platform/runtime compatibility and company isolation;
11. fallback, caching, provider replacement and exit cost;
12. recipient company's acceptance criteria and independent reviewer.

**Hard gates:** unknown cost, unknown commercial rights, unclear data provenance, unsupported runtime, sensitive-data exposure, mandatory paid account, credential risk or no safe fallback prevents adoption. A catalogue label of `No auth` does not remove these gates.

For Trading, add independent checks for market-data entitlement, exchange terms, timestamp/sequence integrity, symbol/contract mapping, gaps, outliers, survivorship/look-ahead bias and halal issue flags where relevant. No religious ruling is implied.

## 5. Safe operating pattern

1. Discover a candidate in Public APIs.
2. Record the README source revision, category, row and retrieval date.
3. Follow the link to the provider's official documentation and legal/plan pages.
4. Verify exact endpoints, auth, free tier, quota, rights, freshness and restrictions.
5. Assign a company-scoped research work order with synthetic/public data only.
6. Perform a limited, read-only proof of concept only after the relevant approval; no customer/private/trading secrets.
7. Compare the candidate with existing providers and direct official sources.
8. Independently review quality, privacy, security, reliability and total cost.
9. Decide adopt, adapt, retain as fallback, defer or reject.
10. Publish a scoped finding to the recipient company's queue and record evidence.

Never place API keys, OAuth refresh tokens, wallet credentials, customer records, private trading data or internal prompts in this shared directory or public issue/PR.

## 6. Integration with the existing organization

- Add Public APIs as a Research & Intelligence discovery source, not a new company or operational service.
- Keep a canonical discovery record in the organization capability registry, while each API candidate receives its own source-level record and owner.
- AI Revenue and Trading & Technology create separate work orders and make separate adoption decisions.
- REA may lawfully inspect public API documentation, public interface descriptions and authorized observable behaviour to understand capabilities and alternatives. REA must not bypass auth, paywalls, rate limits or access controls, or copy protected code/data.
- REA runtime restrictions remain unchanged: no installation/execution, REA repo changes, spending or PolyBot integration until a supported Windows/Mac/Linux runtime is available and the user separately authorizes.
- Existing GitHub, Binance and other connected integrations remain preferred where already authorized; do not create duplicate credentials or replace an existing source without comparative evidence.
- Any MCP entry is a separate software/server review. No MCP installation, server execution or agent permission is implied by inclusion in the catalogue.

## 7. Fast-track work orders

**R&I-API-01 — Catalogue baseline:** record source revision, categories, update freshness and known limitations; define a repeatable manual review process. No automation or scheduled job yet.

**TT-API-02 — Crypto/public-chain shortlist:** assess DefiLlama, 0x, CoinGecko, CryptoCompare and direct Binance/Coinbase documentation against existing capital-flow and PolyBot research. Compare coverage, timestamps, quotas, rights and data quality. No trading use.

**TT-API-03 — Macro/FX/market reference shortlist:** assess FRED, Frankfurter, Currency-api, Alpha Vantage and Twelve Data for reference research only. Direct market feeds and broker/exchange entitlements remain separate.

**AR-API-04 — Business and workflow shortlist:** identify a small number of business, open-data, email/domain-validation and productivity APIs that can support one commercially useful AI Revenue workflow. No customer data or external delivery.

**R&I-API-05 — Research/AI/security shortlist:** assess OpenAlex, Hugging Face, CISA/official security feeds and relevant MCP entries for research usefulness, data policy, hosting costs and security.

All work orders are preparation/research only. API calls, account creation, credentials, installations, third-party connections and external actions require separate approval.

## 8. Decision

**Adopt Public APIs as a permanent discovery/reference source.** It has broad coverage and useful metadata, and the catalogue itself is MIT-licensed. Do not adopt it as an operational dependency, and do not treat the provider APIs as MIT-licensed or universally free.

**Initial priority:** R&I-API-01 and TT-API-02 in parallel with AR-API-04. Keep the Trading Crypto/PolyBot workstream first within Trading, without making AI Revenue dependent on it.

**Current state:** reviewed the repository README, LICENSE and CONTRIBUTING guide at the recorded revisions; selected a research shortlist; no provider endpoint was called, no account or key was created, no package was installed, no MCP server was run, and no API integration or live data validation was performed.

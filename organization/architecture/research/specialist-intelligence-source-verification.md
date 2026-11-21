# Specialist Intelligence Source Verification — J7, Buildix.trade and Santiment

**Review date:** 2026-11-21. **Status:** Public documentation review only; no account, API, connector, trial, subscription, wallet or exchange connection used.

## Executive disposition

| Candidate | Verified identity and coverage | Current public/free access evidence | Risks and limitations | Decision |
|---|---|---|---|---|
| J7 / J7Tracker | Intended product remains ambiguous; same-name products/projects exist. | No dependable official source establishes the intended product, operator and free/API terms. | Identity collision and secondary reporting of a same-name browser-extension security issue; relationship to intended product unproven. | HOLD pending exact official domain/operator confirmation. No extension or wallet connection. |
| Buildix.trade | Official platform identifies Hyperliquid perpetual-futures analytics, including screener, pair metrics and specialist order-flow/whale tools. | Current official docs describe a no-key public MCP endpoint with six read-only tools and shared capacity; current API docs show no-key screener/pair endpoints, with wider API tools plan-gated. REST docs list a free quota of 20 requests/day, while public MCP separately states shared daily capacity of 20,000 calls across users. | Vendor-computed metrics; source cadences vary. CVD uses sampled fills, OBI top 10 levels, tracked accounts update on 10/30-minute cadence, and some metrics cover only the most active markets. Hyperliquid perps focus; estimates and paused free capacity possible. | CONDITIONAL CONTEXT RESEARCH ONLY. No connector/API key or strategy signal dependency. |
| Santiment / Sanbase | Official Santiment analytics and Sanbase/API documentation verified. | Current pricing page states Free Sanbase has a 30-day lag; current FAQ says Max is minimum for unrestricted real-time API. Older official access-plan pages list free API limits and a 30-day cutoff but are dated and differ in quotas. | Metric-specific access/lag, current API plan and commercial-use rights need endpoint-level confirmation. Older documentation must not be relied on as current quota authority. | CONDITIONAL SLOW-MOVING CONTEXT RESEARCH. No API integration until current terms and exact metric access are confirmed. |

## Official evidence reviewed

- Buildix API docs: https://www.buildix.trade/docs — screener and pair endpoints; plan/rate limits.
- Buildix MCP integration: https://www.buildix.trade/integrations — public no-key read-only MCP mode; six tools; source timestamps and data cadence notes.
- Buildix developer API: https://www.buildix.trade/developers — endpoint plans and quota detail; verify inconsistencies against current live docs before any use.
- Buildix terms: https://www.buildix.trade/legal/terms — describes analytics for Hyperliquid perpetual futures and non-custodial scope.
- Santiment current pricing: https://app.santiment.net/pricing — free Sanbase 30-day lag; real-time API access requires Max according to current FAQ.
- Santiment Academy access plans: https://academy.santiment.net/products-and-plans/sanbase-plans/ — free API historical cutoff and quotas; not a substitute for current endpoint entitlements.
- Santiment older access plans: https://santiment.github.io/articles/access-plans/ — dated 2019; historical reference only, not current quota authority.

## Source-specific controls

### J7
Do not proceed until the user-intended exact product is matched to an official domain and operator. Do not infer that third-party reports, browser extensions, GitHub repositories, wallet labels or Telegram accounts are the same entity.

### Buildix.trade
Potentially useful for Hyperliquid-specific context. Every metric must carry source timestamp, producer cadence, sample coverage, methodology and vendor attribution. CVD sample is not total traded volume; OBI top-10-level snapshot is not full-depth order book; liquidation clusters are estimates; tracked wallets are curated. Free no-key MCP is read-only and does not provide the plan-gated raw API surface. No copying portfolios, signals, webhook, API key, exchange key, wallet connection or bot builder.

Because the service focuses on perpetual futures, funding, leverage and derivatives, it triggers instrument-specific legal/platform and Shafi'i/halal review flags. No ruling is issued.

### Santiment
Use only for contextual, non-time-critical research if metric definitions and lag are visible. Do not use free Sanbase delayed data as a current signal. Treat API quota pages as conflicting until current official plan details and endpoint restrictions are reconciled. No paid plan under current zero-spend policy.

## Adoption gates

1. Exact product and legal operator confirmed.
2. Official current terms and intended research/commercial rights reviewed.
3. Endpoint/metric definition, source cadence, history, lag and rate limits documented.
4. Provenance and timestamp fields captured and validated.
5. Vendor output independently compared with a trusted baseline where possible.
6. No source becomes a strategy dependency without independent validation and company approval.

**Current disposition:** no provider is approved as a production dependency. Buildix and Santiment remain optional contextual research candidates; J7 remains on hold.

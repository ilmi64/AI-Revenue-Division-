# Specialist Intelligence Source Verification — J7, Buildix.trade and Santiment

**Review date:** 2026-11-21. **Status:** Public-source desk research only; no accounts, API calls, trials, subscriptions, extensions, wallet connections or data ingestion.

## Executive disposition
| Candidate | Verified identity / scope | Free access evidence | Risks / limitations | Decision |
|---|---|---|---|---|
| J7 / J7Tracker | Search results identify a product called J7Tracker, but the prior internal label “J7” is not yet conclusively tied to one canonical operator/product. A third-party review describes social tracking, token discovery and Solana-focused execution features. | No dependable current official free-tier and API terms verified. | Third-party reporting describes a same-name malicious browser-extension incident in 2026; relationship to the official product is not established. Identity and security ambiguity. | HOLD. Do not install extensions, connect wallets, import keys or integrate until canonical identity, operator, official domains and security posture are independently established. |
| Buildix.trade | Official site describes a Hyperliquid perpetual-futures analytics platform with order-flow, CVD, OI, funding, liquidation and wallet analytics. Terms say it is analytics, not a broker/custodian; some future bot-builder functionality is described. | Official site advertises a $0 screener/deep-view tier. API documentation says public screener/pair endpoints are accessible in free mode, with a stated 20 requests/day. | Narrow Hyperliquid perps coverage; signals and tracked-wallet outputs are vendor-defined; API documentation and terms should be rechecked before use. Terms mention exchange API keys for future bot-builder use, which is outside our scope. Perpetual futures and leverage raise serious risk and halal review flags. | CONDITIONAL RESEARCH CANDIDATE only. Free public viewing may be considered later; no account/API integration or signals into strategy without methodology validation. |
| Sanbase / Santiment | Official Santiment/Sanbase product and API are identifiable. Provides on-chain, social and market analytics. | Current pricing page advertises free Sanbase with 30-day data lag and restricted features. Separate API-plan documentation advertises free API access, but documentation is older and limits differ across pages. | Metrics have metric-specific definitions and restrictions. Current free API quota, freshness, commercial rights and endpoint-level access are not sufficiently reconciled from public pages. Paid plans are outside CAD $0 rule. | CONDITIONAL RESEARCH CANDIDATE. Free UI research may be possible; no API use until current exact limits, terms, metric definitions and commercial rights are confirmed. |

## Evidence reviewed
- Buildix official product page: https://www.buildix.trade/ — describes Hyperliquid analytics and advertised free screener features.
- Buildix official terms: https://www.buildix.trade/legal/terms — describes service scope, non-custodial positioning, and subscription tiers; terms are not an endorsement or security audit.
- Buildix official API documentation: https://www.buildix.trade/docs — describes read-only REST/MCP endpoints and published rate limits; page claims free screener/pair access and 20 requests/day.
- Buildix risk disclosure: https://www.buildix.trade/legal/risk — explicitly warns about perpetual futures, leverage and loss risk.
- Santiment official pricing: https://app.santiment.net/pricing — advertises free Sanbase with 30-day lag and restricted functionality; paid Pro/Max excluded.
- Santiment API pricing: https://api.santiment.net/ — paid business tiers are far outside current zero-spend policy.
- Santiment access-plan documentation: https://santiment.github.io/articles/access-plans/ — contains free API limits, but is dated and must not be treated as current without confirmation.
- J7Tracker third-party review: https://www.btcc.com/en-CA/academy/crypto-platform/review/j7-tracker-review — describes a J7Tracker product and reports security concerns about a same-name browser extension; it is secondary reporting, not an official incident attribution.
- Public GitHub search result for a separate project named j7tracker: https://github.com/0zgunner/j7tracker — demonstrates name collision; it does not establish connection to the product in the third-party review.

## Source-specific controls
### J7
Treat “J7” as ambiguous until the user’s intended exact product is matched to an official domain/operator. Do not assume a GitHub project, wallet label, Telegram account or third-party review refers to the same entity. No extension installation, wallet connection, API key, browser permission or account signup.

### Buildix.trade
Potentially useful as a specialist Hyperliquid order-flow/position context source, not a general all-chain capital-flow source. Do not interpret its signals as validated edge. No exchange API keys, wallet connections, copy-portfolio use, webhook, MCP connection or bot builder. The platform's perpetual-futures focus triggers leverage/derivatives and Shafi'i/halal review flags; no ruling is issued.

### Santiment
Potentially useful for independently defined on-chain and social metrics. Maintain metric-level definitions and freshness metadata. A 30-day lag on the free Sanbase interface makes it unsuitable for time-sensitive signals. Do not use outdated API quota pages as authority for current access; verify current API plan and commercial rights before any integration.

## Research registry update
These findings refine the named-source entries in the Crypto Capital Flow Source Registry. All three remain research candidates, not approved data dependencies. Buildix and Santiment may support contextual research after terms/methodology review; J7 remains on hold pending exact identity.

## Next verification questions
1. Which exact J7 product/domain did the original portfolio intend?
2. For Buildix, which exact metrics have documented formulas, sampling windows, historical retention and export rights?
3. For Santiment, what are the current free API quotas, endpoint-specific delays, metric restrictions and commercial-use terms?
4. Can each candidate be used without creating an account, submitting credentials or triggering payment obligations?

**Current status:** Public pages reviewed; no provider approved for production, no source connected, no data retrieved programmatically, and no trade signals authorized.
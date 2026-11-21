# Research & Intelligence — Crypto Capital Flow Source Registry

**Status:** Research registry design and candidate-source inventory; no provider accounts, subscriptions, API calls, wallet connections, data collection or alerts activated.  
**Service owner:** Organization-level Research & Intelligence Division.  
**Recipients:** Company-scoped, advisory-only outputs to Trading & Technology and AI Revenue.  
**Budget:** CAD $0 incremental by default.

## 1. Mission

Track where capital may be entering, leaving, rotating or becoming available across crypto ecosystems. Produce source-backed intelligence with provenance, uncertainty and alternative explanations. This is not a trade signal, wallet attribution service, investment recommendation or authorization to move funds.

Core coverage:
- fundraising rounds and venture investment;
- token launches, launchpad activity and initial liquidity;
- whale / large-wallet movements;
- exchange inflows and outflows;
- smart-money and sector rotation;
- token unlocks, vesting and emissions;
- project treasury deployments and grants;
- ecosystem, developer and infrastructure funding;
- protocol revenue, fees and liquidity changes;
- market-maker, liquidity-provider and bridge flows where observable.

## 2. Source hierarchy

| Tier | Source class | Examples | Default confidence |
|---|---|---|---|
| A | Primary / official | Project announcements, signed governance proposals, issuer disclosures, official token docs, regulator filings, chain-native transaction data | Highest for the specific fact disclosed; not necessarily complete |
| B | Direct technical data | Public chain explorers, verified contract events, public RPC, official exchange market data | High for raw observable event; attribution remains separate |
| C | Specialist analytics | Sanbase/Santiment, J7, Buildix.trade and other named specialist products after exact identity, methodology and terms are verified | Conditional; vendor methodology and coverage must be documented |
| D | Reputable reporting | Named publications quoting identifiable parties/documents | Medium; corroborate |
| E | Social / anonymous | X posts, Telegram, Discord, influencer claims, anonymous dashboards | Low until independently verified |

A source tier is not a truth score. A primary source can be incomplete or promotional; on-chain data can be accurately observed but wrongly attributed.

## 3. Candidate source register

| Candidate | Intended coverage | Required verification before use | Current status |
|---|---|---|---|
| Official project / foundation channels | Fundraising, treasury, grants, unlocks, launches | Canonical domain/account, publication date, primary document, conflicts and edits | Candidate class |
| Chain explorers and public RPC | Transactions, token transfers, contract events, treasury movement | Chain ID, contract address, event decoding, finality, reorg handling, endpoint terms and rate limits | Candidate class |
| Sanbase / Santiment | On-chain metrics, exchange flows, whale / holder metrics, social signals | Exact product/metric definitions, free-tier limits, historical coverage, API rights, attribution and commercial-use terms | Named specialist; not yet validated |
| J7 | Capital-flow / smart-money intelligence candidate | Exact canonical product and operator identity, supported chains, metric methodology, data freshness, access terms, free limits and provenance | Identity/methodology verification required |
| Buildix.trade | Trading / capital-flow intelligence candidate | Exact canonical product and operator identity, data sources, chain/venue coverage, signal construction, historical methodology and access terms | Identity/methodology verification required |
| Official launchpads | Launch calendars, allocations, token launch and liquidity events | Official project/launchpad source, chain/contract identity, eligibility, vesting and terms | Candidate class |
| Official governance forums | Treasury proposals, grants, ecosystem deployments | Forum authenticity, proposal status, vote outcome, execution transaction | Candidate class |
| Public filings / issuer disclosures | Corporate fundraising, treasury and risk disclosures | Jurisdiction, filing date, issuer identity, primary filing and materiality | Candidate class |
| Reputable news | Funding rounds, acquisitions, ecosystem investment | Named investor/company, amount/currency, stage, date, primary corroboration | Candidate class |

No provider is approved merely because it appears in this registry. Do not start trials requiring payment details or automatic billing.

## 4. Intelligence record requirements

Every item must record:
- stable record ID and workstream;
- company recipient scope (Trading, AI Revenue, or shared research);
- claim type: observation, attribution, interpretation, forecast or recommendation;
- subject entity, chain, contract, wallet or fund identifier as applicable;
- source URL / native transaction hash / filing ID;
- source class and source tier;
- published time, observed time, retrieved time and timezone;
- event time and chain block / finality when relevant;
- amount, currency, token units and valuation timestamp separately;
- source method, metric definition and version;
- direct evidence versus inferred attribution;
- confidence, freshness, coverage and limitations;
- corroborating and conflicting sources;
- alternative explanations;
- reviewer and review timestamp;
- expiry / revalidation date;
- permitted downstream use and licence/terms status.

Never copy secrets, private account data or personally identifying wallet-owner assumptions into shared intelligence. Public wallet addresses can still be sensitive when linked to an identifiable person; minimize and scope access.

## 5. Event-specific safeguards

### Fundraising
Distinguish announced, reportedly closed, legally closed and on-chain funded. Record amount, currency, round, date, investor names only when disclosed by reliable sources. Do not infer token allocation or treasury balance from an equity round.

### Whale movements
A large transfer is not automatically buying, selling or accumulation. It may be internal wallet consolidation, custody movement, exchange rebalancing, bridge activity, OTC settlement or contract migration. Label wallet ownership as VERIFIED, ATTRIBUTED or UNKNOWN; never promote an attribution to verified without strong evidence.

### Exchange flows
Record exchange wallet labels and their source/version. Inflows/outflows are not equivalent to market orders. Consider internal transfers, hot/cold wallet changes, custody and omnibus address behavior.

### Unlocks and vesting
Prefer official tokenomics, vesting contracts and governance disclosures. Compare scheduled unlock with actual on-chain distribution where possible. Distinguish unlock, claim, transfer and sale; they are not the same event.

### Treasury and grants
A proposal is not an executed deployment. Record proposal state, vote, execution transaction and recipient. Separate liquid treasury assets from restricted, vested or illiquid holdings.

### Smart-money / sector rotation
Document the vendor's wallet cohort, inclusion/exclusion logic, time window, realized/unrealized basis and entity labels. Avoid treating a selected cohort as representative or predictive.

## 6. Research workflow

1. Discover candidate event from a source.
2. Capture source and timestamp without changing its meaning.
3. Verify identity, chain, contract, token and event.
4. Corroborate with an independent primary or technical source where possible.
5. Check alternative explanations and counter-evidence.
6. Score confidence and freshness separately.
7. Classify as OBSERVED, ATTRIBUTED, INTERPRETED or HYPOTHESIS.
8. Publish only the minimum recipient-scoped summary.
9. Revisit on expiry, correction, source change or conflicting evidence.
10. Preserve the original record and append corrections; never silently overwrite.

## 7. Priority dashboards / registers

Initial research backlog:
- fundraising and venture-round timeline;
- token launch / launchpad calendar;
- unlock and vesting calendar;
- project treasury and grant movements;
- large-wallet transfer watchlist with attribution confidence;
- exchange inflow/outflow evidence register;
- sector rotation and ecosystem capital map;
- developer / ecosystem funding activity;
- source health, freshness and methodology change log.

Do not activate live alerts or monitor private groups without explicit authorization and lawful access.

## 8. Recipient boundaries

- Trading & Technology receives market/chain intelligence relevant to its research queues. It must independently validate any hypothesis before backtesting or paper use.
- AI Revenue receives commercial/product/market intelligence relevant to AI business opportunities, not wallet-level private details or Trading strategy records.
- Main Hub/OCC receives only allowlisted aggregate status and evidence references, not raw private research records.
- Research & Intelligence cannot authorize trades, spending, customer contact or company operations.

## 9. Named workstreams preserved

Keep these visible as specialist workstreams:
- **Crypto Capital Flow & Opportunity Intelligence** — this registry's primary programme;
- **J7** — candidate specialist intelligence source pending exact identity and methodology verification;
- **Buildix.trade** — candidate specialist trading-intelligence source pending exact identity and methodology verification;
- **Sanbase / Santiment** — candidate on-chain and social analytics source pending metric, access and terms review;
- **Grok Desk / HyperGrok** — continuous research and synthesis concepts, not operational until staffed, access-approved, monitored and rehearsed.

## 10. Current disposition

**REGISTRY FRAMEWORK PREPARED; NAMED SOURCES NOT YET VERIFIED; NO API USE, SUBSCRIPTIONS, PRIVATE GROUP ACCESS, WALLET CONNECTIONS OR TRADE SIGNALS.**

## 11. Specialist source verification

See [Specialist Intelligence Source Verification](specialist-intelligence-source-verification.md) for the public-source review of J7, Buildix.trade and Sanbase/Santiment, including current limitations and adoption gates. All remain research candidates; no integration or paid access is approved.

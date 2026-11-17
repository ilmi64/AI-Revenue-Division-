# Crypto Capital Flow & Opportunity Intelligence

**Status:** Architecture and research specification. Internal research only; not a signal service, trade recommendation, risk approval, or execution authority.

## 1. Mission

Build a source-aware intelligence capability that observes where capital, liquidity, development effort, and launch activity are moving across digital-asset ecosystems. Convert observations into timestamped, evidence-linked research leads for specialist desks and OCC review.

The workstream supplements—not replaces—market data, portfolio risk, security review, or independent desk analysis. It must never authorize an order, increase exposure, clear a veto, or override a risk controller.

## 2. Coverage domains

1. **Fundraising and launches:** disclosed funding rounds, strategic investments, grants, token generation events, launchpad allocations, vesting schedules, unlocks, and distribution changes.
2. **Whale and large-wallet activity:** material transfers, accumulation/distribution patterns, exchange inflows/outflows, bridge movements, treasury transfers, and concentration changes.
3. **Smart-money and sector rotation:** observable wallet cohorts, fund/VC-linked addresses where attribution is defensible, sector-level flow changes, and divergence between price, volume, and wallet activity.
4. **Protocol and project treasuries:** treasury balances, material deployments, grants, buybacks, liquidity provisioning, and transfers to custodians or exchanges.
5. **Ecosystem development capital:** grants, developer activity indicators, new deployments, integrations, and other verifiable evidence of ecosystem investment.
6. **Market-structure context:** liquidity depth, stablecoin supply/flows, bridge activity, exchange reserves where methodology is disclosed, and token supply/unlock pressure.

A large transfer is not automatically a buy or sell. Wallet labels, ownership, intent, and beneficial control are uncertain unless supported by reliable evidence.

## 3. Source roles and trust model

Use a source registry with explicit access, provenance, and limitations. Candidate specialist sources include:

- **J7:** evaluate as a specialist smart-money/on-chain intelligence input. Record exactly which metrics, chains, wallet labels, historical depth, export paths, and free-tier limits are actually available before relying on it.
- **Buildix.trade:** evaluate as a separate opportunity/discovery input. Verify its data origin, methodology, supported assets, refresh cadence, and whether displayed signals can be independently reproduced.
- **Sanbase / Santiment:** evaluate for on-chain, social, development, and market-behaviour context. Record metric definitions, chain coverage, plan restrictions, and whether historical/API access is available without paid usage.
- **Primary evidence:** project treasury disclosures, official tokenomics/unlock schedules, foundation and governance proposals, exchange/launchpad announcements, block explorers, verified contract events, and public filings or investor announcements.
- **Independent corroboration:** a second unrelated data provider or primary-chain evidence for material events.

No candidate provider is assumed connected, free, complete, accurate, or approved. Do not create an account, start a trial requiring payment details, call paid endpoints, or consume credits without explicit approval. Prefer public pages, existing authorized access, and open data. Respect provider terms and rate limits.

### Source registry fields

Each source record must contain: source ID, provider, product/dataset, access mode, public/connected status, free/paid status, terms/licence review, chain/asset coverage, metric definitions, update cadence, historical depth, known blind spots, attribution methodology, last checked time, and operational status.

## 4. Canonical event record

Every observation is normalized into a common record before it can be compared or escalated:

- Event ID: stable unique identifier.
- Event type: controlled taxonomy from section 5.
- Chain, asset ID, contract address, transaction hash, and block height where applicable.
- Subject entity ID and counterparty entity ID only when attribution confidence is recorded.
- Observed at, occurred at, ingested at, and source timestamp timezone/precision.
- Native value/unit, USD estimate, CAD estimate, and valuation timestamp/source. Unknown values remain null, never zero.
- Direction: explicitly defined relative to a named entity or venue; otherwise unknown.
- Evidence references: immutable source URLs, transaction IDs, or document identifiers.
- Source IDs, source quality, corroboration count, and raw-evidence hash where feasible.
- Attribution confidence, event confidence, and materiality as separate fields.
- Limitations, conflicts, review status, and expiry/revalidation time.

Do not store secrets, private keys, wallet seed phrases, or personal data. Public wallet addresses may still be sensitive when linked to an identifiable person; avoid unnecessary identity claims.

## 5. Event taxonomy

Use explicit event types rather than a single vague "whale activity" label:

- Fundraise announced, grant announced, investment disclosed.
- Token launch announced, token distribution, vesting unlock scheduled, vesting unlock observed.
- Treasury transfer, treasury deployment, treasury withdrawal.
- Large wallet transfer, exchange inflow, exchange outflow, bridge inflow, bridge outflow.
- Wallet accumulation candidate, wallet distribution candidate.
- Liquidity added, liquidity removed, market-maker transfer.
- Stablecoin supply change, stablecoin netflow.
- Developer activity change, grant activity change, ecosystem integration.
- Governance treasury proposal, buyback announced, buyback executed.

Candidate accumulation/distribution labels are hypotheses, not verified intent. The event record must preserve the underlying transfers and the rule that produced the candidate label.

## 6. Evidence, confidence, and anti-manipulation controls

Keep three separate assessments:

- **Source reliability:** identity, methodology, coverage, freshness, licensing, and historical reliability of the source.
- **Attribution confidence:** confidence that a wallet/entity label is correct. Unlabelled or weakly labelled wallets remain unknown.
- **Event confidence:** confidence that the described event actually occurred and its interpretation is supported.

Minimum controls:

1. Require transaction-level evidence for on-chain claims whenever available.
2. Treat provider labels as claims with provenance, not ground truth.
3. Corroborate high-materiality events with primary sources or independent providers.
4. Deduplicate the same transaction/event across feeds.
5. Detect self-transfers, internal treasury movements, bridge hops, exchange hot-wallet reshuffles, wrapped-token mint/burn, and contract migrations before describing net flows.
6. Separate gross transfer volume from estimated net economic flow; do not net unrelated counterparties.
7. Preserve conflicting sources and uncertainty instead of selecting the more exciting narrative.
8. Apply chain reorg/finality checks and mark provisional observations.
9. Detect stale timestamps, delayed indexing, missing blocks, and suspicious sudden label changes.
10. Use robust baselines and percentile/context comparisons; never treat a universal USD threshold as meaningful across all assets.
11. Do not infer insider status, illicit conduct, beneficial ownership, or intent from transfer size alone.
12. Every generated narrative must link back to its supporting evidence and identify unsupported inferences.

## 7. Research workflow

1. Discover: ingest public/authorized observations and disclosed events.
2. Normalize: map assets, chains, units, timestamps, entities, and event taxonomy.
3. Validate: check transaction/document evidence, finality, duplicate status, source health, and attribution.
4. Contextualize: compare to asset liquidity, market cap, historical baseline, unlock calendar, sector activity, and broader market conditions.
5. Corroborate: seek primary or independent confirmation for material events.
6. Score for research priority: use transparent components for materiality, novelty, corroboration, freshness, and source reliability. Keep attribution confidence separate. Never output a directional trade score.
7. Escalate: deliver a concise evidence pack to the relevant specialist desk and OCC. The desk may accept, reject, or request more evidence.
8. Expire: stale events lose priority and must be revalidated before reuse.

## 8. Research-priority rubric (not a trading signal)

A research lead may be ranked using five documented dimensions, each on a 0–5 scale:

- Materiality relative to the asset's normal liquidity/size.
- Novelty versus the source's historical baseline.
- Corroboration quality and independence.
- Freshness and finality.
- Source reliability and reproducibility.

Store raw component values, rationale, and missing-data penalties. Do not average away a critical weakness: absent primary evidence, weak wallet attribution, stale data, or unresolved source conflict must cap the lead at unverified regardless of total score.

Outputs are limited to watch, research, unverified, corroborated, rejected, and expired. No buy, sell, long, short, or execution-ready label is produced by this workstream.

## 9. Desk and OCC integration

- Crypto desk receives asset/chain-specific evidence and source limitations.
- Forex, indices, and Gold desks may receive macro/flow context only where the relationship is documented; no crypto-wallet observation is treated as a direct signal for those markets.
- Gold/XAUUSD remains a distinct market family with its own instrument units, contract metadata, and risk limits. Macro narrative does not replace verified XAU quote/contract data.
- OCC receives material incidents, data-quality failures, concentration changes, and unresolved cross-desk conflicts.
- Grok Desk may summarize; HyperGrok may challenge assumptions. Neither may change source facts, override risk controls, clear vetoes, or authorize trades.
- Every handoff carries event IDs, evidence references, timestamps, confidence dimensions, unresolved questions, and expiry.

## 10. Initial no-cost implementation sequence

**Phase A — specification and manual research ledger**
- Maintain source registry, event taxonomy, evidence pack template, and unlock/fundraising calendar.
- Use public pages and block explorers manually; record retrieval time and links.
- No API keys or scheduled external collection.

**Phase B — offline normalizer**
- Build deterministic parsers for user-supplied/public CSV or JSON exports.
- Validate schemas, units, timestamps, duplicate IDs, event types, and evidence references.
- Keep ingestion read-only; never sign transactions or connect a wallet.

**Phase C — reproducible analytics**
- Add rolling baselines, cohort comparisons, deduplication, flow classification, and confidence reporting.
- Test with synthetic fixtures and archived public examples whose terms permit reuse.
- Include adversarial fixtures for self-transfers, exchange wallet reshuffles, bridge hops, reorgs, spoof labels, and missing timestamps.

**Phase D — controlled source adapters**
- Only after access, terms, and cost are independently verified. Every adapter has explicit rate limits, source health, retries, provenance, and a kill switch.
- No paid endpoint, trial, subscription, credit, or API spend without separate owner approval.

## 11. Acceptance gates

The workstream is not considered operational until all applicable gates are evidenced:

- [ ] Source registry complete; terms/licensing and free/paid status checked.
- [ ] Event schema and taxonomy validated.
- [ ] Transaction/document evidence retained and reproducible.
- [ ] Unit conversion and valuation timestamps verified.
- [ ] Deduplication and internal-transfer filters tested.
- [ ] Wallet attribution uncertainty retained end-to-end.
- [ ] Reorg/finality and stale-source handling tested.
- [ ] Confidence components and research ranking are explainable.
- [ ] No directional trade or execution authority in the output schema.
- [ ] Specialist and OCC handoff tested with fail-closed behaviour.
- [ ] Independent security, data-quality, and risk review completed.

All gates currently remain not validated until evidence is recorded. This document is a design baseline, not a claim that source integrations or automated monitoring are running.

## 12. Operating restrictions

Research and offline development only. No exchange/broker/wallet connection with spending authority, no trading, no deposits, no leverage, no publishing, no external outreach, no paid APIs, and no background monitoring claim. Any external action or spending requires explicit owner approval.

## 13. Initial repository artifacts

- `capital-flow-event.schema.json`: canonical normalized event record schema.
- `capital-flow-source.schema.json`: source-registry entry schema.
- `capital-flow-source-registry.template.json`: starter registry for J7, Buildix.trade and Sanbase/Santiment. All three are explicitly marked unverified, not accessible, cost unknown, terms not reviewed, and research-only. No provider capability or free access is asserted.

The two JSON schema files were fetched back from the development branch and confirmed to parse as JSON. This is only a JSON syntax check, not a JSON Schema metaschema validation or functional test. The source registry template is a planning artifact, not evidence of connected or approved sources.


## 14. Offline normalisation implementation

A standard-library-only JSON Lines normalizer and regression-test suite now live in `organization/intelligence/capital_flow/`:

- `capital_flow_normalizer.py`: deterministic timestamp/identifier normalization, conservative quality flags, validation, and duplicate consolidation.
- `test_capital_flow_normalizer.py`: regression cases for missing/unknown values, timezone handling, self-transfers, exchange reshuffles, bridge hops, wrapped-token mint/burn, stale observations, duplicate evidence and conflicting duplicate values.
- `README.md`: local usage, input contract, deduplication policy and limitations.

The normalizer is deliberately offline. It does not connect to J7, Buildix.trade, Sanbase/Santiment, RPC nodes, exchanges, wallets or any external service. It does not infer wallet ownership or intent. Duplicate consolidation requires chain, transaction hash and event type; conflicting observations are retained as explicit conflicts for human review. Quality flags are part of the event schema.

**Verification status:** files committed; source and test suite have not been executed in this environment. No CI workflow was triggered. The implementation remains a development artifact and is not an operational monitoring service.


## 15. Append-only evidence review history

The offline review-history prototype is in `organization/intelligence/capital_flow/`:

- `capital_flow_review.py` appends reviewer actions to a JSONL ledger, with sequential entry numbers and a SHA-256 hash chain.
- `test_capital_flow_review.py` covers valid chain construction, sequence linkage, tampering, broken links, action/status constraints, timezone enforcement and append/read integrity.
- `REVIEW-LEDGER.md` documents commands, controls and limitations.

A review entry references the stable event ID, reviewer ID, action, reason, status and supporting evidence references. Corrections are new entries, not silent edits to the original event. Hash chaining detects accidental or unsophisticated alteration but is not a digital signature or tamper-proof storage. The prototype requires single-writer use and has no authentication, access control, encryption, distributed locking or protected backup.

**Verification status:** implementation and tests committed; tests have not been executed in this hosted repository session. No CI workflow was triggered. This is an offline development prototype, not an operational evidence vault.

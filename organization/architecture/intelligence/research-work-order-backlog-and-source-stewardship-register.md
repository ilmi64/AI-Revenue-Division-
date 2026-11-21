# Research & Intelligence — Work-Order Backlog and Source Stewardship Register

**Status:** Initial role-based queue prepared from the existing high-priority research portfolio; no people or agents are staffed or assigned, no sources are approved by this register, and no continuous monitoring is active.  
**Service:** Organization-level Research & Intelligence Division.  
**Boundary:** Advisory only; recipient-scoped delivery to each independent company.  
**Budget:** CAD $0 incremental. No paid services, installs, API calls, data collection, tests, deployments, customer contact, publishing or financial actions are authorized.

## 1. Work-order record standard

Every work order must record: ID/version; requester role; exact recipient; decision to inform; research question; scope/exclusions; P0–P3 priority and rationale; due/freshness window; proposed accountable desk role; independent challenger role; permitted source classes; privacy/data class; cost estimate; dependencies/blockers; acceptance criteria; status; disposition/archive link.

Recipients are `AI_REVENUE`, `TRADING_TECH` or `SHARED_GOVERNANCE`. A shared public fact may be researched once at the source layer, but company-specific interpretation and publication remain separate. Proposed role ownership is an accountability design only; it is not evidence of staffing or assignment to an active agent.

## 2. Priority and hard-stop rules

- **P0:** security, privacy, cross-tenant, integrity or unexpected-cost incident. Stop affected work and escalate through the appropriate independent company authority.
- **P1:** narrow-window event that may materially affect a near-term decision; rapid verification, never verification bypass.
- **P2:** important planned work with a clear decision use.
- **P3:** exploratory or low-urgency work.

Priority is not evidence confidence or authority to act. BLOCK if identity, legality, licence/terms, privacy, cost, provenance or recipient scope is unresolved. A hard stop cannot be offset by a high score.

## 3. Seeded work queue — proposed role ownership

| Work-order | Recipient | Priority | Proposed accountable desk role | Independent challenger | Next deliverable / acceptance criteria | Dependencies and current state |
|---|---|---|---|---|---|---|
| `TT-RI-01` — Crypto source and semantic integrity | TRADING_TECH | P2 (portfolio provisional 90) | Market Data & Microstructure Lead | Source Registry & Provenance Lead | Reconcile Coinbase/Binance exact product, quote, timestamp, candle finality, gap, volume-unit and source-revision mappings; produce a versioned pass/hold matrix. | Existing provenance plan and source-feature checklist. Public documentation only; no API calls or data collection. `QUEUED_PREPARATION`. |
| `TT-RI-02` — PolyBot Phase 4 indicator semantics | TRADING_TECH | P2 (portfolio provisional 88) | Quantitative & Strategy Research Lead | Market Data & Microstructure Lead plus independent arithmetic challenger | Resolve EMA/RSI/ATR/volume/regime conventions; reconcile all known-answer fixtures; explicitly close the ATR first-bar discrepancy; publish frozen version and unresolved issue list. | Depends on TT-RI-01 and instrument identity. Independent review pending; tests and fixtures remain NOT_RUN. `DOCUMENT_RECONCILIATION_PREPARED_REVIEW_PENDING`. |
| `TT-RI-03` — Strategy hypothesis and falsification gate | TRADING_TECH | P2 (portfolio provisional 86) | Quantitative & Strategy Research Lead | Risk & Independent Performance Audit Lead | Ensure each future hypothesis has exact instrument, timeframe, rationale, null/baseline, falsification conditions, costs, data needs and halal issue flags before any authorized dataset/backtest request. | Existing hypothesis registry and protocol; no hypotheses currently registered, no backtest authorized. `QUEUED_PREPARATION`. |
| `AR-RI-01/02` — Mini-review rehearsal and delivery economics | AI_REVENUE | P2 (portfolio provisional 86/84) | Product & Service Intelligence Lead | Delivery QA & Evidence Review Lead; Finance/Economics reviewer | Prepare a bounded authorization-ready rehearsal packet; ensure scenario version, scope, timing capture, defect/rework, QA evidence and cost fields are ready; retain NOT_RUN until separately authorized. | Existing two fictional scenario packs, QA standard, economics worksheet and blank scorecard. No pricing or buyer validation. `PREPARATION_QUEUED`. |
| `AR-RI-04` — AI Creative Studio capability shortlist | AI_REVENUE | P2 (portfolio provisional 78) | Technology & AI Systems Intelligence Lead | Licensing, Security & Commercial-Use Challenger | Compare HyperFrames, ComfyUI and no-cost alternatives for Android/desktop compatibility, output quality, commercial-use rights, hardware/runtime, workflow reproducibility and zero-cost limits. | Research only. No installation, rendering, paid credits, account connection or publishing. `QUEUED_PREPARATION`. |
| `RI-03/04` — Recipient-scoped queue and source-quality rollout | SHARED_GOVERNANCE | P2 (portfolio provisional 88/85) | Research Operations & Intelligence Director with Source Registry & Provenance Steward | Evidence & Reproducibility Lead | Maintain this role-based queue; select only priority sources for future scorecard review; every finding has source identity, terms, freshness, evidence grade, challenger and one-recipient publication record. | Existing scoring protocol, source scorecard and unified registry. No sources approved or scored by this queue. `QUEUE_DESIGN_PREPARED; SOURCE_SCORING_NOT_STARTED`. |
| `RI-02/05` — Grok Desk / HyperGrok and capital-flow intelligence | TRADING_TECH (separate work orders/publications) | P2 (portfolio provisional 90/78) | Crypto Capital Flow Intelligence Lead; Research Operations Lead for desk topology | Source Verification & Challenge Lead | Preserve event discovery, source verification, whale/fundraising/unlock/treasury categories, alternative explanations, freshness and separate recipient briefs; maintain J7 HOLD and Buildix/Santiment context-only. | Existing source registry and Grok Desk design. No live monitors, feeds, API, wallet or private-group access. `QUEUED_PREPARATION`. |
| `OCC-RI-01` — Read-only OCC acceptance gap map | SHARED_GOVERNANCE | P2 | Main Hub/OCC Architecture Lead | Security & Recovery Assurance Lead plus both company representatives | Map each M2 acceptance criterion to existing schema, prototype, fixtures, authored tests, missing evidence and safe next gate; identify read-only boundary violations without executing tests. | Existing M2 prototype and build plan. Latest suite and formal schema validation remain NOT_RUN. `QUEUED_DOCUMENT_REVIEW`. |
| `SEC-RI-01` — Company-scoped security/recovery readiness catalogue | SHARED_GOVERNANCE (separate company evidence) | P2 | Security & Recovery Division Lead | Each company's independent security/risk authority | Map required control families, asset owners, evidence, test method, recovery dependencies and approval authority; preserve blank control/recovery records until evidence exists. | Existing division charter, incident standard, loss recovery playbook and blank readiness register. No control effectiveness or backup/restore claims. `QUEUED_DOCUMENT_REVIEW`. |

The queue is seeded from the existing [Initial High-Priority Research Portfolio & Grok Desk Blueprint](https://github.com/ilmi64/Solana-memecoins/blob/architecture/shared-ai-workforce-integration/docs/architecture/research/initial-high-priority-research-portfolio-and-grok-desk-blueprint.md) and the existing [Desk Roster & Assignment Protocol](https://github.com/ilmi64/Solana-memecoins/blob/architecture/shared-ai-workforce-integration/docs/architecture/research/research-intelligence-desk-roster-and-assignment-protocol.md). Provisional scores are copied as ordering context, not independently re-scored or treated as measured value.

## 4. Status semantics

- `QUEUED_PREPARATION`: accepted into the documentation/research backlog; no work execution implied.
- `DOCUMENT_RECONCILIATION_PREPARED_REVIEW_PENDING`: documentation crosswalk prepared; independent challenge still required.
- `QUEUED_DOCUMENT_REVIEW`: existing artifacts await read-only review; no test or runtime action.
- `PREPARATION_QUEUED`: preparatory work remains to be completed.
- `SOURCE_SCORING_NOT_STARTED`: source quality review has not been performed.
- `NOT_RUN` / `NOT_EXECUTED`: no tests, rehearsals, API calls, monitoring or runtime operation occurred.
- `BLOCKED` / `HOLD_*`: record exact blocker and restart condition; never silently substitute a source or tool.

## 5. Source stewardship record

| Field | Value |
|---|---|
| Source ID / version | NOT_REGISTERED |
| Publisher / legal entity | UNKNOWN |
| Exact source / endpoint / document | UNKNOWN |
| Source class | UNKNOWN |
| Original publication / update date | UNKNOWN |
| Last checked / freshness expiry | NOT_RECORDED |
| Methodology / scope | UNKNOWN |
| Terms / data rights | NOT_REVIEWED |
| Company recipient(s) | MUST_BE_SCOPED |
| Quality and provenance evidence | NONE |
| Contradictions / limitations | UNKNOWN |
| Steward / independent challenger | UNASSIGNED |
| Disposition | UNREGISTERED |

## 6. Evidence and challenge

Claim grades: `PRIMARY_CONFIRMED`, `CORROBORATED`, `SINGLE_SOURCE`, `VENDOR_ESTIMATE`, `PUBLIC_CLAIM`, `ATTRIBUTED`, `HYPOTHESIS`, `CONTRADICTED`, `SUPERSEDED`.

Record claim-level evidence separately from source quality. Challenge exact entity/product/version, publication date, methodology, independent corroboration, selection bias, missing data, alternative explanations, terms, privacy and recipient scope. Material work cannot be self-challenged or self-approved by its author.

## 7. Queue and publication safeguards

One publication has one recipient. If both companies need a finding, create two separately reviewed reports. OCC receives allowlisted aggregate metadata only. No raw customer records, private strategies, credentials, full report bodies or cross-company memory. Research cannot authorize company spending, customer contact, publishing, deployment, trading, financial action or launch.

## 8. Handover and service health

Future handovers record actual coverage window/timezone; outgoing/incoming lead; staffed and unstaffed desks; active work-order IDs and next actions; source health/freshness; unresolved contradictions; incidents/quarantines; resource/cost status; recipient publications; and incoming acknowledgement. Missed coverage is recorded as a gap, not inferred continuous coverage.

## 9. Initialization and operating truth

- People/agents staffed: `NONE_VERIFIED`.
- Active source monitors or continuous day/night coverage: `NONE_VERIFIED`.
- Approved sources through this queue: `NONE`.
- Work orders seeded: 9 grouped entries as listed above.
- Published intelligence through this queue: `NONE`.
- API/data collection, tests, backtests, rehearsals or deployments: `NOT_RUN / NOT_AUTHORIZED`.
- Incremental budget: CAD $0.
- Last review: 2026-11-21.

**Disposition:** ROLE-BASED PREPARATION QUEUE ONLY. It does not prove staffing, live monitoring, source approval, test completion or operational service.

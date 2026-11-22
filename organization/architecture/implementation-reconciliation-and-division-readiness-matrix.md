# Implementation Reconciliation and Division Readiness Matrix

**Status:** Evidence-based architecture/codebase reconciliation; no tests executed, no production systems activated.  
**Scope:** Trading & Technology and AI Revenue, with independent company boundaries.  
**Companion documents:** [Implementation Dependency Map](implementation-dependency-map.md) and [Canonical Interface Register](canonical-interface-register.md).

## 1. Purpose and operating rule

This document converts the dependency map and 41-interface register into a working implementation backlog. It maps existing repository artifacts to interface contracts, distinguishes design from reference code and verified operation, records division-level readiness gaps, and defines the next bounded work packages.

This is a continuation of existing work, not a restart. Existing contracts, role IDs, research work orders, security reference implementations, acceptance fixtures, Gold specialist work and prior decisions are preserved. New work must reconcile with them rather than duplicate or silently replace them.

### Authoritative company and launch rules

- AI Revenue and Trading & Technology are independent companies and are prepared in parallel.
- **AI Revenue revenue is not a prerequisite for Trading to launch.** Trading may launch independently when sufficient lawful starting capital is available and all Trading company/division readiness gates are met with explicit owner approval.
- If sufficient lawful starting capital is unavailable, Trading goes on standby while AI Revenue continues its own revenue work as one possible future capital source. Any intercompany support is optional and requires a separate lawful, documented, accounted-for and explicitly owner-approved arrangement that protects AI Revenue solvency. No automatic transfers, shared treasury or commingling.
- Trading's planned divisions are prepared in parallel and launch together as a coordinated organisation-wide launch when every required division passes its own gates. No crypto-first or silent phased launch.
- The organisation targets 24/7 coverage across supported markets through complementary day operations and night Grok Desk/HyperGrok. Each desk follows its own market calendar and source availability. The target is not an assertion of live staffing or continuous operation.
- CAD $0 incremental spending remains in force. No paid hosting/API/data, payment-backed trials, purchases, deposits, borrowing, leverage, installs, deployments, tests or consequential external actions without separate explicit approval.
- Trading remains research/paper-only. No live execution, broker/exchange order access, private keys or signing.
- OCC is read-only; independent CRO veto and Security & Recovery boundaries remain intact.

## 2. Evidence status vocabulary

| Status | Meaning |
|---|---|
| DESIGN_PRESENT | A relevant contract, architecture or workflow document exists. It is not implementation evidence. |
| REFERENCE_CODE_PRESENT_UNVERIFIED | Reference/prototype code exists in the repository; it has not been represented as deployed or validated here. |
| FIXTURE_OR_TEST_SPEC_PRESENT_NOT_RUN | Synthetic fixtures, acceptance vectors or test files exist, but no execution result is claimed. |
| PARTIAL | Some components exist, but one or more material contract, ownership, integration or evidence requirements remain unresolved. |
| GAP_TO_SPECIFY | No adequate domain-specific artifact was identified in the reviewed PR change inventory; create only after confirming no authoritative artifact exists elsewhere in the repository. |
| BLOCKED | A known issue prevents the next stage; record exact restart condition. |
| NOT_OPERATIONAL | No evidence of production connection, staffing, monitoring, deployment or operational service. |

**Important:** A file in a draft PR or architecture branch is a repository artifact, not a merged or deployed system. A test file is not a passing test. A prototype is not a production service.

## 3. Interface-to-artifact reconciliation

The following crosswalk records the best existing evidence located in the current company architecture branches and draft PR change inventories. Related files are linked by repository-relative path so maintainers can navigate to the source of truth. Where a row says PARTIAL, the listed artifacts are inputs to reconciliation, not proof that every field in the interface is complete.

### 3.1 Identity, policy, approvals, tasks and workforce (IF-001–015)

| Interface | Existing artifacts / evidence | Status | Remaining implementation work |
|---|---|---|---|
| IF-001 Principal Identity | `docs/security/identity-lifecycle-production-requirements.md`; `docs/security/identity_lifecycle_reference.py`; `docs/security/agent-identity-and-task-handoff-contract.json`; `docs/security/company-isolation-and-agent-authority.md` | REFERENCE_CODE_PRESENT_UNVERIFIED | Reconcile principal schema, issuer/tenant binding, lifecycle, expiry and revocation epoch; identify the single authoritative identity service boundary. |
| IF-002 Policy Decision | `docs/security/deterministic-policy-enforcement-interface.json`; `docs/security/policy-gateway-production-contract.md`; `docs/security/reference_policy_engine.py`; `docs/security/pg1-pg7-evidence-and-blocker-crosswalk.md` | REFERENCE_CODE_PRESENT_UNVERIFIED | Crosswalk decision inputs/outputs to the 41-interface contract; verify deny-by-default and tenant/role/parent intersection by static review before any authorised tests. |
| IF-003 Tool Enforcement | `docs/security/pg4-enforcement-and-bypass-resistance-architecture.md`; `docs/security/policy-gateway-integration-and-gap-closure-plan.md`; `docs/security/authorized-outbox-integration-contract.md` | PARTIAL | Complete connector/tool inventory, identify bypass paths, map every external adapter through enforcement gateway. |
| IF-004 Owner Approval | `docs/security/durable-approval-audit-contract.md`; `docs/security/owner-approval-repository-schema-contract.md`; `docs/security/owner_approval_postgres_repository.py`; `docs/security/approval_consumption_reference.py` | REFERENCE_CODE_PRESENT_UNVERIFIED | Reconcile approval binding, one-time consumption, expiry, payload digest and action-specific owner approval. |
| IF-005 Parent-Child Task Envelope | `docs/architecture/workforce-parent-child-task-envelope-contract.md`; `docs/architecture/workforce/schemas/agent-task.schema.json`; `docs/security/agent-identity-and-task-handoff-contract.json` | DESIGN_PRESENT | Align exact field names, versioning, authority intersection, budgets, reviewer independence and cancellation references. |
| IF-006 Task Lifecycle | `docs/architecture/paperclip-role-id-and-org-chart-configuration-draft.md`; `docs/architecture/workforce/queue-and-risk-workflows.md`; workforce parent-child contract | PARTIAL | Define canonical lifecycle/state transitions and map Paperclip lifecycle events to deterministic policy/audit events. Paperclip remains a candidate, not an active service. |
| IF-007 Audit Event | `docs/security/durable-audit-and-approval-production-contract.md`; `docs/security/audit_chain_reference.py`; `docs/security/signed-audit-checkpoint-contract.md` | REFERENCE_CODE_PRESENT_UNVERIFIED | Consolidate event envelope, append-only/tamper-evident storage, retention, integrity checkpoints and failure behaviour. |
| IF-008 Revocation Epoch | `docs/security/identity-lifecycle-production-requirements.md`; `docs/security/trusted-identity-approval-clock-and-receiver-boundary-contract.md`; security service contract | PARTIAL | Specify authoritative epoch store, propagation acknowledgements, cache invalidation and bounded stale-authority rejection. |
| IF-009 Cancellation Propagation | workforce parent-child contract; `docs/security/recovery-authority-and-quarantine-contract.md`; `docs/security/transactional-dispatch-recovery-contract.md` | PARTIAL | Join parent/descendant task cancellation with queue, adapter, session and late-output quarantine semantics. |
| IF-010 Service Health / Safe Mode | `docs/architecture/shared-infrastructure-tenancy-and-failover.md`; `docs/architecture/research/specialist-desk-coverage-and-shift-handover.md`; `docs/architecture/main-hub/occ-workforce-observability-contract.md` | DESIGN_PRESENT | Define machine-readable health states, freshness limits, stop conditions, alert routing and recovery owner. |
| IF-011 Tenant Registry | `docs/security/company-isolation-and-agent-authority.md`; `docs/security/two-company-isolation-verification-plan.md`; company registry/authority contracts | DESIGN_PRESENT | Reconcile tenant IDs across identity, data, queue, audit and service identities; retain strict AI Revenue/Trading separation. |
| IF-012 Role/Capability Registry | `docs/architecture/initial-workforce-roster-and-tenant-blueprint.md`; `docs/architecture/paperclip-role-id-and-org-chart-configuration-draft.md`; role catalogues | DESIGN_PRESENT | Bind role IDs to capability allowlists and prohibitions; no role itself grants authority. |
| IF-013 Worker Adapter | `docs/architecture/workforce-platform-adapter-contract.json`; `docs/architecture/workforce-platform-current-technical-assessment.md`; `docs/security/workforce-platform-adapter-acceptance-tests.json` | DESIGN_PRESENT / FIXTURE_OR_TEST_SPEC_PRESENT_NOT_RUN | Complete adapter-specific permission review and cancellation/revocation contract. No adapter installation or model account connection. |
| IF-014 Orchestration Handoff | `docs/architecture/ruflo-bounded-swarm-profile-registry-draft.md`; parent-child task envelope; `docs/architecture/workforce/queue-and-risk-workflows.md` | DESIGN_PRESENT | Convert bounded profiles to versioned, policy-enforced workflow definitions only after deterministic enforcement exists. |
| IF-015 Output Review / Commit | `docs/architecture/research/research-evidence-and-publication-envelope-contract.md`; `docs/security/atomic-evidence-reconciliation-contract.md`; `docs/security/recovery-authority-and-quarantine-contract.md` | PARTIAL | Define common output provenance, reviewer separation, quarantine and commit gates for non-research worker outputs. |

### 3.2 Research, evidence and knowledge (IF-016–022)

| Interface | Existing artifacts / evidence | Status | Remaining implementation work |
|---|---|---|---|
| IF-016 Research Work Order | `docs/architecture/research/research-work-order-backlog-and-source-stewardship-register.md`; `docs/architecture/research/research-task-prioritization-and-opportunity-scoring.md` | DESIGN_PRESENT | Map queue IDs to validated work-order schema, exact recipient, priority, dependencies and approval status. |
| IF-017 Source Record | `docs/architecture/research/instrument-and-source-register-template.md`; `docs/architecture/research/source-quality-scorecard-and-review-protocol.md`; unified source registry | DESIGN_PRESENT | Complete source-specific terms/licence, owner, freshness, status and permitted-use records. Candidates are not approved sources. |
| IF-018 Evidence Capture | `docs/architecture/research/research-evidence-and-publication-envelope-contract.md`; `docs/architecture/research/schemas/research-records.schema.json`; `docs/architecture/security/atomic-evidence-reconciliation-contract.md` | DESIGN_PRESENT / REFERENCE_CODE_PRESENT_UNVERIFIED | Align evidence record identity, source revision, capture digest, method, context and reproducibility requirements. |
| IF-019 Claim Record | research evidence contract; research records schema; Grok Desk event verification/challenge record | DESIGN_PRESENT | Ensure atomic claim status, confidence, counter-evidence, expiry and evidence references are consistent across company queues. |
| IF-020 Independent Challenge | `docs/architecture/research/specialist-intelligence-source-verification.md`; `docs/architecture/research/grok-desk-event-verification-and-challenge-record.md` | DESIGN_PRESENT | Define reviewer independence and shared-upstream-source detection; do not count correlated model outputs as independent corroboration. |
| IF-021 Research Publication | `docs/architecture/research/recipient-scoped-intelligence-delivery-contract.md`; research evidence contract | DESIGN_PRESENT | Complete recipient access enforcement, sanitisation, expiry/correction and publication approval mapping. |
| IF-022 Distribution Receipt | recipient-scoped delivery contract; specialist shift-handover contract | PARTIAL | Specify acknowledgement, idempotency, retry limits, non-delivery state and audit event. |

### 3.3 Trading market, portfolio and risk (IF-023–032)

| Interface | Existing artifacts / evidence | Status | Remaining implementation work |
|---|---|---|---|
| IF-023 Market Data Adapter | `docs/architecture/research/crypto-market-data-normalization-and-provenance-plan.md`; `docs/architecture/research/coinbase-binance-source-to-feature-mapping.md`; provider API work orders | PARTIAL | Complete source eligibility, licence/terms, timestamp, venue/product identity, units, candle finality, sequence/gap and freshness acceptance. Current detailed mapping is crypto-focused. |
| IF-024 Market Session Calendar | specialist desk coverage and shift handover; trading operating blueprint; market classification matrix | PARTIAL | Produce separate verified calendar/instrument/session contracts for Crypto, Forex, Indices and Gold/XAUUSD, including holidays and daylight-saving rules. |
| IF-025 Specialist Desk Contract | `docs/architecture/workforce/trading-specialist-agent-role-catalogue.md`; R&I operating model specialist desk map; division charter | PARTIAL | Turn role descriptions into division-owned contracts with instrument scope, data dependencies, session rules, accountable lead, risk profile and readiness evidence. Preserve existing Gold specialist work as source of truth. |
| IF-026 Indicator / Signal Semantics | `docs/architecture/research/polybot-phase-4-indicator-data-contract.md`; `docs/architecture/research/polybot-source-to-feature-acceptance-checklist.md`; known-answer fixture specification | PARTIAL / BLOCKED | Resolve ATR first-bar/previous-close discrepancy before implementation. No indicator tests or paper signals are authorised by this reconciliation. |
| IF-027 Paper Portfolio / Ledger | `docs/architecture/trading-technology-operating-blueprint.md`; Main Hub Trading snapshot fixture; trading loss reconciliation playbook | PARTIAL | Specify authoritative paper ledger schema, event ordering, fee/slippage assumptions, valuation freshness, reconciliation and audit invariants. |
| IF-028 Risk Decision / CRO Veto | `docs/architecture/workforce/queue-and-risk-workflows.md`; trading specialist role catalogue; Trading organisation charter | DESIGN_PRESENT | Map independent CRO veto to a deterministic policy stop and ensure strategy/orchestration cannot override it. |
| IF-029 Strategy Evaluation | `docs/architecture/research/trading-strategy-hypothesis-registry.md`; `docs/architecture/research/polybot-strategy-backtesting-protocol.md`; hypothesis intake/falsification template | DESIGN_PRESENT | No hypotheses currently registered and no backtest authorised. Next is documentation/contract review, then separately approved synthetic fixture work. |
| IF-030 Shift Handover | `docs/architecture/research/specialist-desk-coverage-and-shift-handover.md`; `docs/architecture/research/priority-source-assessment-and-synthetic-shift-handover-pack.md` | DESIGN_PRESENT / FIXTURE_OR_TEST_SPEC_PRESENT_NOT_RUN | Map every handover field to shared portfolio/risk state, market sessions, alert state, acknowledgements and audit. Rehearsal remains unexecuted. |
| IF-031 Market Alert / Escalation | `docs/architecture/research/specialist-desk-coverage-and-shift-handover.md`; security incident register and OCC observability contract | PARTIAL | Define event severity, delivery channel, acknowledgement deadline, escalation chain and alert-health monitoring. |
| IF-032 Capital Flow Intelligence | `docs/architecture/research/crypto-capital-flow-source-registry.md`; Grok Desk event verification/challenge record; R&I backlog | DESIGN_PRESENT | Keep J7 identity HOLD; Buildix.trade and Santiment provisional/context-only. Add source-level terms, evidence, entity resolution and challenge before any live use. |

### 3.4 Security, recovery and OCC (IF-033–039)

| Interface | Existing artifacts / evidence | Status | Remaining implementation work |
|---|---|---|---|
| IF-033 Incident Record | `docs/architecture/security-recovery/incident-register-and-recovery-assurance-standard.md`; Security & Recovery service contract | DESIGN_PRESENT | Reconcile severity, owner, containment, evidence retention, escalation and company-scoped incident records. |
| IF-034 Backup / Restore Manifest | `docs/architecture/shared-infrastructure-tenancy-and-failover.md`; Security & Recovery service contract | PARTIAL | Specify concrete backup inventory, integrity, encryption/key custody, retention, restore dependencies and RPO/RTO. No restore has been tested. |
| IF-035 Recovery / Reconciliation Case | `docs/architecture/security-recovery/trading-loss-recovery-and-capital-reconciliation-playbook.md`; case record template | DESIGN_PRESENT | Preserve classification boundaries; ordinary market/strategy losses are not represented as recoverable; no external recovery action without separate authority. |
| IF-036 Security Boundary Audit | `docs/architecture/security-recovery/security-control-and-recovery-readiness-register.md`; company isolation verification plan; security contract | PARTIAL | Assign control owners/evidence and review expiry. Current readiness register is not proof of control effectiveness. |
| IF-037 Signed Status Envelope | `docs/architecture/main-hub/security/authenticated-publisher-design.md`; `docs/architecture/main-hub/schema/records.schema.json`; M2 verification matrix | DESIGN_PRESENT / REFERENCE_CODE_PRESENT_UNVERIFIED | Align issuer, audience, sequence, expiry, source revision, digest, key lifecycle and anti-replay requirements. |
| IF-038 OCC Read-only Query | `docs/architecture/main-hub/occ-readonly-operator-console-spec.md`; `docs/architecture/main-hub/occ-workforce-observability-contract.md`; `organization/architecture/main-hub/prototype/occ_readonly.py` in AI Revenue repo | REFERENCE_CODE_PRESENT_UNVERIFIED | Verify read-only boundary and recipient scoping through authorised synthetic review; no current production OCC is claimed. |
| IF-039 Cross-company Sanitised Report | `docs/architecture/research/recipient-scoped-intelligence-delivery-contract.md`; company isolation and authority contracts | PARTIAL | Define explicit sanitisation policy, allowed fields, re-identification review, recipient approval and delivery receipt. |

### 3.5 Commercial readiness and optional capital (IF-040–041)

| Interface | Existing artifacts / evidence | Status | Remaining implementation work |
|---|---|---|---|
| IF-040 AI Revenue Commercial Readiness | AI Revenue offer specification, delivery QA/time-capture standard, full-cycle economics worksheet, mini-review economics, synthetic rehearsal input packs and blank scorecard | DESIGN_PRESENT / NOT_OPERATIONAL | Rehearsals remain NOT_RUN; no customer validation, customer contact, paid pilot or verified revenue is claimed. This interface reports AI Revenue's own state and is not a Trading launch gate. |
| IF-041 Optional Intercompany Capital Support | Independent company authority contract; finance/solvency boundary in company architecture | DESIGN_PRESENT | No transfer or commitment. If ever considered, require separate legal/accounting review, instrument, amount, terms, solvency impact and explicit owner approval. Trading can use another lawful capital source. |

## 4. Trading division readiness matrix

This matrix is a planning snapshot, not an operational certification. Divisions continue in parallel. The coordinated Trading launch remains blocked until every required division independently passes its gates. A blocker in one division must be stated precisely; it must not be used to silently switch to a phased launch.

| Division / capability | Existing evidence located | Current state | Next concrete work package | Launch gate evidence |
|---|---|---|---|---|
| Crypto Research / PolyBot | Crypto normalization/provenance plan; Coinbase/Binance mapping; PolyBot Phase 4 contract; source-to-feature checklist; known-answer fixture specification; synthetic indicator fixture notes; strategy protocol | Strongest domain contract set; source eligibility still provisional; ATR first-bar policy is BLOCKED; fixtures/tests NOT_RUN; no paper signals authorised | Reconcile the ATR discrepancy; freeze indicator and candle semantics; complete source/product/units/finality matrix; align fixtures and checklist without executing them | Approved source and terms; closed semantic discrepancy; independently reviewed fixtures; authorised test results; paper-only risk controls |
| Forex Research | Specialist role and research remit in desk roster/R&I operating model | Specialist coverage defined at role level; a complete Forex-specific instrument/source/session/data contract was not identified in the reviewed implementation inventory | Create/locate the authoritative Forex work package; specify pairs/instruments, quote conventions, session/holiday calendar, macro/rates inputs, source/licence matrix and paper-hypothesis intake | Qualified data, instrument semantics, calendars, legal scope, risk limits, desk owner and independent review |
| Indices Research | Specialist role and remit in desk roster/R&I operating model | Specialist coverage defined at role level; a complete index-specific instrument/source/session contract was not identified in the reviewed inventory | Create/locate index instrument taxonomy, index vs CFD/futures distinctions, provider mapping, session/holiday calendars, constituent/roll semantics where applicable and hypothesis intake | Qualified data and instrument definitions, calendars, source terms, risk limits, desk owner and independent review |
| Gold / XAUUSD Research | Dedicated Gold/XAUUSD specialist role and workstream explicitly preserved in R&I desk map and workforce architecture; user-confirmed substantial prior specialist work | Existing specialist work is authoritative and must be preserved. The reviewed PR change inventory did not expose its full underlying specialist artifact set; do not classify it as absent or recreate it | Inventory and cross-reference the existing Gold specialist artifacts first; map them into IF-023–026, IF-030 and division-specific readiness. Only then identify genuine gaps | Gold-specific instrument/provider/session semantics, macro/real-rate/USD/liquidity coverage, risk and source evidence, desk ownership, independent review |
| Quant / Strategy Research | Strategy hypothesis registry; intake/falsification template; PolyBot backtesting protocol; CRO role and risk workflows | Research method exists; no hypotheses registered; no backtest authorised; no predictive performance claim | Reconcile strategy metadata, pre-registration, benchmark/null, costs, chronological partitions, out-of-sample and independent challenge contract | Reproducible evidence, realistic costs, bias/leakage review, independent challenge and CRO approval |
| Market Data & Source Integrity | Crypto normalization plan; venue/source mapping; source registry template; source quality scorecard; provider work orders; synthetic data fixtures | Governance and crypto-focused data work exists; no sources approved for live use and no live feeds connected | Extend canonical market data contract across Forex, Indices and Gold; define timestamps, units, session, gaps, revisions, entitlements and freshness by provider/instrument | Licensed/approved source, continuity and freshness evidence, data-quality monitoring, recovery and owner approval |
| Portfolio & Capital Flow Intelligence | Crypto capital-flow source registry; Grok Desk verification/challenge record; research backlog | Workstream exists; J7 HOLD, Buildix/Santiment provisional; no live monitoring or connected wallets/APIs | Qualify each source and entity-resolution method; formalise event schema, evidence grades, alternate explanations, freshness and recipient-specific output | Approved source terms, reproducible evidence, independent challenge, privacy/security review |
| PolyBot / Trading Systems | Phase 4 contract, workforce role catalogue, platform adapter and swarm profile contracts | Design artifacts present; not installed or running; no production data, paper signal or execution | Reconcile platform adapter/task envelope with deterministic policy, indicator contracts and paper-ledger interface | Bounded adapter, revocation, audit, source integrity, paper workflow and CRO veto evidence |
| Research & Intelligence / Grok Desk / HyperGrok | Division charter, operating model, queue, source registry, evidence/publication contract, shift handover and specialist desk roster | First-class division designed; NOT_STAFFED / NOT_CONTINUOUS; no live source monitoring | Preserve current work-order IDs; map work-order and source records to IF-016–022; complete day/night role handover and source qualification | Approved sources, staffed ownership, persistent runtime, alerting, multi-shift rehearsal and evidence quality |
| Security & Recovery | Charter, service contracts, incident standard, readiness register, loss-recovery playbook; multiple security reference modules and acceptance vectors | Extensive design/reference-code artifacts; no production control plane or security certification claimed; tests not run | Reconcile PG-1–PG-7 and reference modules to IF-001–010/033–036; produce one evidence/blocker crosswalk and dependency order | Independent security review, identity/policy/revocation enforcement, audit integrity, backup/restore and incident rehearsal |
| Main Hub / OCC | M0–M6 build plan; M1 schemas/fixtures; M2 Python prototype and authored tests; signed publisher design and verification matrix | Prototype/design artifacts exist; latest test suite and schema validation NOT_RUN; no production publisher/receiver | Map M2 acceptance criteria to exact schema, prototype, fixtures and gaps; preserve read-only and recipient boundaries | Authorised synthetic validation, signature/key lifecycle review, replay/audience denial, read-only enforcement and recovery |
| Operations / 24/7 coverage | Day/night operating model; specialist shift handover; synthetic handover pack; market desk map | Target design only; NOT_STAFFED / NOT_CONTINUOUS; no persistent zero-cost host verified | Build per-market calendar matrix and shared handover payload; resolve hosting, monitoring, on-call and backup dependencies without paid trial | Persistent host, approved source health monitoring, day/night staffing, alerts, handover acknowledgement, safe mode and recovery rehearsal |

## 5. AI Revenue parallel readiness workstream

AI Revenue continues independently and in parallel. It is not a prerequisite gate for Trading.

| Workstream | Existing evidence | Current state | Next concrete work |
|---|---|---|---|
| Practical Operations Improvement Mini-Review | Offer spec, internal service brief, QA/time-capture standard, synthetic samples, economics worksheets, rehearsal inputs and blank scorecard | Offer and delivery architecture prepared; synthetic rehearsals NOT_RUN; no buyer validation or revenue claimed | Reconcile rehearsal packet to acceptance scorecard; prepare a bounded authorization-ready rehearsal plan; no execution until separately approved |
| Delivery economics / CFO | Full-cycle economics worksheet, mini-review economics and commercialisation plan | Model prepared; actual time/cost/economic floor not validated | Map required measurement fields and decision thresholds; do not set customer pricing from unvalidated estimates |
| AI Creative Studio | Capability research backlog and prior tool shortlist | Research/preparation only | Continue zero-cost capability, rights, hardware and reproducibility assessment; no installs, credits or publishing |
| Workforce and control plane | Shared architecture, task envelope, security reference modules and AI Revenue tenant artifacts | Design and reference code present; no deployed workforce | Maintain company isolation and reconcile common control-plane contracts without enabling workers |

## 6. Priority implementation backlog — next work packages

These are bounded deliverables with explicit dependencies. They do not require tests, installs, paid services or external account connections.

| Priority | Work package | Owner role | Inputs | Output / completion definition | Gate |
|---|---|---|---|---|---|
| P0 | Gold specialist artifact inventory and traceability | Trading CTO + Gold/XAUUSD desk lead | Existing Gold artifacts, desk roster, this matrix | Exact file/path inventory, current status, completed work preserved, gaps mapped to IF-023–026/030; no rewrite before inventory | Documentation-only |
| P0 | PolyBot ATR discrepancy resolution packet | Quant lead + Market Data lead + independent challenger | Phase 4 contract, source-to-feature checklist, known-answer fixtures | Explicit candidate policies, impact analysis, revised proposed fixture and owner/challenger decision record; no code/test run | Documentation review only |
| P0 | Security implementation evidence crosswalk | Security & Recovery lead + CTO | PG-1–PG-7, reference code, acceptance vectors, identity/policy contracts | Component-by-component status: contract, reference implementation, tests authored, tests run (currently not run), unresolved threat/production gaps | Static review only |
| P1 | Multi-market instrument and calendar contract | Market Data & Source Integrity + Forex/Indices/Gold desk leads | Desk roster, market classification, source registry | Shared schema plus market-specific annexes for Crypto, Forex, Indices and Gold; session, holiday, timezone, units, instrument identity and source fields | Research/design only |
| P1 | Paper portfolio ledger contract | Trading CTO + Portfolio/CFO + CRO | Trading operating blueprint, Main Hub snapshot, risk workflows | Event model, position/valuation/fee/slippage/reconciliation invariants and stale-data safe mode | Design only |
| P1 | Day/night coverage and handover matrix | COO + R&I Director + specialist desk leads | Specialist shift handover, HyperGrok role model, market calendars | Market-by-market coverage state, shift owner, handover payload, alerts, escalation, safe mode and staffing dependencies | Design only |
| P1 | 41-interface status and ownership register | Architecture steward + service owners | Canonical interface register and this crosswalk | Each IF-ID assigned producer/consumer, owner, version, exact artifact, status, blocker and acceptance evidence | Documentation-only |
| P1 | OCC M2 evidence crosswalk | Main Hub/OCC lead + Security & Recovery reviewer | M2 matrix, schema, fixtures, prototype, authored tests | Criterion-by-criterion map to code/fixture and unexecuted validation status | Static review only |
| P2 | AI Revenue rehearsal authorization packet | AI Revenue COO/CFO + QA lead | Existing scenario packs, QA standard, economics worksheet, blank scorecard | One versioned, bounded rehearsal plan with success/failure criteria, data boundaries and stop conditions | Requires separate owner approval before execution |

## 7. Workstream dependencies and parallelism

- Identity, policy, audit and revocation contracts are foundational for any executable workforce.
- Existing reference security code can be statically reconciled now; tests and runtime activation remain separately gated.
- Trading market divisions continue their domain research in parallel. Forex, Indices and Gold must not wait for PolyBot completion to prepare their own data, calendar, instrument and risk contracts.
- Gold work must be inventoried and preserved before creating or replacing any Gold artifacts.
- Quant/Strategy, Market Data, R&I, Security & Recovery, OCC and Portfolio/Capital Flow remain parallel workstreams with explicit interfaces.
- AI Revenue commercial readiness proceeds in parallel. Its revenue status is not a Trading launch dependency.
- Hosting is a shared runtime dependency, not a reason to stop documentation, schema reconciliation, static review or domain-specific preparation. No zero-cost persistent host has been verified.
- The simultaneous Trading division launch gate remains: every required division passes independently; no phased fallback is implied.

## 8. Current blockers — exact and bounded

1. **PolyBot ATR semantics:** first-bar true-range treatment conflicts with the source-to-feature acceptance checklist's requirement for a valid previous close. Restart condition: Quant proposal + Market Data continuity assessment + independent challenger approval of a consistent fixture/contract version.
2. **Market source qualification:** current crypto source mappings are not equivalent to approved live data entitlements. Restart condition: per-provider terms/licence, exact product/instrument identity, timestamps, units, finality, gaps and freshness reviewed.
3. **Forex/Indices market-specific contracts:** specialist roles exist, but complete domain contracts were not identified in the reviewed change inventory. Restart condition: search and inventory authoritative existing artifacts first; only then create missing annexes.
4. **Gold traceability:** user-confirmed substantial specialist work exists and is authoritative. The reviewed PR file list did not expose its full underlying artifact set. Restart condition: inventory exact existing paths and status before any edits; no duplicate Gold architecture.
5. **Security execution evidence:** reference code and test specifications exist, but tests are not run and production controls are not active. Restart condition: static crosswalk and independent review, then separate explicit approval for synthetic tests.
6. **Persistent hosting:** no verified zero-cost always-on host for the full workforce/policy/audit/monitoring system. Restart condition: future host and cost decision with explicit owner approval.
7. **24/7 operation:** not staffed or continuous. Restart condition: approved persistent host, sources, staffing/on-call, monitoring, backups, recovery and multi-shift rehearsal.
8. **Capital:** Trading requires sufficient lawful starting capital. If unavailable, Trading remains on standby; this does not create an AI Revenue revenue prerequisite.

## 9. Implementation status and non-claims

- Existing Python reference modules, schemas, contracts, synthetic fixtures and acceptance-test files are tangible repository artifacts.
- No claim is made here that tests were executed, code is correct, services are deployed, credentials are connected, markets are monitored, workers are staffed, or the organisation is operating 24/7.
- No existing file is to be rewritten merely to match this crosswalk. If an authoritative artifact conflicts with this matrix, reconcile the source document and log the decision first.
- No merge, PR action, CI run, test execution, Python execution, installation, deployment, paid service, account connection, customer contact, financial transaction or live trading is authorised by this document.

## 10. Immediate next action

Begin with the **Gold specialist artifact inventory** and **Security implementation evidence crosswalk**, while separately preparing the **multi-market instrument/calendar contract** and **PolyBot ATR discrepancy resolution packet**. These four work packages turn existing material into actionable implementation requirements and expose genuine blockers without repeating completed architecture.

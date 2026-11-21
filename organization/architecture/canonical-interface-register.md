# Canonical Interface Register

**Status:** Interface planning only. These are proposed logical contracts and ownership boundaries, not implemented APIs, validated schemas or active connections. No tests, installation, deployment, credentials or external actions are authorised.

**Companion:** [Canonical Implementation Dependency Map](implementation-dependency-map.md)

## 1. Contract rules

- Every interface has a stable identifier, version, producer, consumer, tenant scope, data classification, authority class, schema owner, failure behaviour and acceptance evidence.
- No model, prompt, Paperclip role, Ruflo swarm or worker adapter is an authority source. Identity and policy services decide and enforce access.
- Effective permission is the intersection of company/tenant policy, parent task, role and deterministic policy decision. A child cannot widen its parent's scope.
- All cross-service calls carry correlation and audit identifiers, expiry and revocation epoch where applicable.
- Unknown schema, stale policy, expired identity, missing audit, unavailable risk control or ambiguous tenant => reject/fail closed.
- Shared service access is explicit and recipient-scoped; it does not grant cross-company browsing.
- Proposed interface names are logical labels. They are not claims that an API endpoint, database or service already exists.

## 2. Foundational identity, authority and task interfaces

| ID | Interface | Producer → consumer | Scope / minimum contract | Failure behaviour | Required acceptance evidence |
|---|---|---|---|---|---|
| IF-001 | Principal Identity | Identity Service → Policy Gateway, Paperclip, Ruflo, services | Principal ID, principal type, tenant, role/service identity, status, issuer, issued-at, expiry, identity version | Unknown, expired, disabled or mismatched identity denied | Lifecycle, issuer validation, tenant mismatch and expiry denial cases |
| IF-002 | Policy Decision | Policy Decision Point → Policy Enforcement Gateway | Principal, tenant, parent task, requested action, resource, classification, recipient, approval, expiry, revocation epoch; decision and reason | Missing/ambiguous policy or PDP unavailable => deny | Policy truth table, least privilege, negative cases, independent security review |
| IF-003 | Tool Enforcement | Policy Gateway → connector/tool/data adapter | Approved tool ID, action class, scoped resource, filtered arguments, decision ID, expiry, audit correlation | Direct/unmediated tool invocation denied; gateway failure => deny | Tool inventory, bypass analysis, argument/resource filtering evidence |
| IF-004 | Owner Approval | Owner Approval Registry → Policy Gateway, Paperclip lifecycle | Exact action, company, scope, amount/limits if relevant, recipient, expiry, one-time/reusable boundary, approver, decision and evidence | No approval, stale approval, changed payload or out-of-scope approval => deny | Approval binding, replay prevention, expiry and altered-payload denial |
| IF-005 | Parent-Child Task Envelope | Parent Orchestrator → Ruflo/worker adapters | Tenant, service/recipient scope, parent/child IDs, data references, classifications, allowlists, action classes, budgets, expiry, reviewer independence, revocation epoch, audit correlation | Missing field or scope widening => reject child | Schema review, inheritance proof, scope-escalation and over-budget denial |
| IF-006 | Task Lifecycle | Paperclip candidate → policy/audit/orchestrator | Task owner, company, role, state, parent, approval state, timestamps, cancellation and terminal reason | Unknown state or stale transition => reject | State-transition table, duplicate/replay handling, cancellation semantics |

## 3. Audit, revocation and event interfaces

| ID | Interface | Producer → consumer | Scope / minimum contract | Failure behaviour | Required acceptance evidence |
|---|---|---|---|---|---|
| IF-007 | Audit Event | Every service/gateway → Audit Event Store | Event ID, timestamp, actor, tenant, task, action, resource, policy decision, outcome, source refs, correlation, schema version | Required audit unavailable => consequential action denied; event buffered only under bounded approved rules | Integrity, completeness, ordering, access and retention design |
| IF-008 | Revocation Epoch | Revocation Service → gateways, orchestrators, adapters, workers | Tenant/principal/task scope, new epoch, reason, effective time, issuer | Epoch unknown or stale => deny; late output quarantined | Propagation matrix, cancellation and stale-token denial evidence |
| IF-009 | Cancellation Propagation | Parent lifecycle → descendants, queues, tools and sessions | Parent/descendant IDs, cancellation version, reason, deadline and acknowledgements | Unacknowledged cancellation => quarantine, safe mode and escalation | Descendant coverage, late completion quarantine and bounded propagation evidence |
| IF-010 | Service Health / Safe Mode | Health monitors → Policy Gateway, shift leads, OCC publisher | Service identity, health, freshness, last-success, degraded state, safe-mode reason | Critical dependency unhealthy => affected workflow stops or enters safe mode | Failure injection plan and alert/stop/recovery evidence, when authorised |

## 4. Tenant, workforce and orchestration interfaces

| ID | Interface | Producer → consumer | Scope / minimum contract | Failure behaviour | Required acceptance evidence |
|---|---|---|---|---|---|
| IF-011 | Tenant Registry | Company Authority → Identity, Paperclip, data stores | Tenant ID, legal entity label, status, data region/classification, permitted shared services | Unknown tenant or ambiguous mapping denied | Cross-tenant isolation and lifecycle review |
| IF-012 | Role/Capability Registry | Company workforce authority → Paperclip, Policy Gateway | Role ID, tenant, responsibilities, allowed capabilities, prohibited actions, reviewer independence, owner | Unregistered or conflicting role denied | Role-permission matrix and separation-of-duties review |
| IF-013 | Worker Adapter | Paperclip/Ruflo → model/runtime adapter | Worker identity, task envelope, model/runtime ID, bounded tools, token/time/retry limits, output provenance | Adapter cannot verify scope or stop => no task dispatch | Version/license/permission inventory, isolation and cancellation evidence |
| IF-014 | Orchestration Handoff | Ruflo → child worker / parent | Parent ID, child assignment, bounded objective, allowed inputs/outputs, deadline, budget, reviewer and return contract | Child cannot expand scope; failed child returns explicit failure | Fan-out limits, retry/concurrency caps, handoff traceability |
| IF-015 | Output Review / Commit | Worker → reviewer → approved destination | Output digest, provenance, task scope, confidence, reviewer identity, policy decision, commit destination | Unreviewed, late, out-of-scope or untrusted output quarantined | Review independence, provenance and commit denial cases |

## 5. Research, evidence and knowledge interfaces

| ID | Interface | Producer → consumer | Scope / minimum contract | Failure behaviour | Required acceptance evidence |
|---|---|---|---|---|---|
| IF-016 | Research Work Order | R&I Operations → specialist desk / Grok Desk | Work order ID, tenant, question, bounded scope, recipient, priority, approved sources, deadline, output type, risk class | No approved scope/source/recipient => no collection or publication | Work-order validation and recipient boundary review |
| IF-017 | Source Record | Source Stewardship → research desks | Source ID, owner, domain, type, terms/licence, access method, tenant/recipient scope, status, last reviewed, limitations | Suspended/degraded/expired source excluded or clearly qualified | Source lifecycle and terms review |
| IF-018 | Evidence Capture | Research desk → evidence registry | Capture ID, source ID/revision, timestamp, method, exact reference, digest, context, limitations, collector identity | Missing provenance or unverifiable capture cannot support a published claim | Provenance, reproducibility and integrity review |
| IF-019 | Claim Record | Research desk → challenge/review | Atomic claim ID, wording, scope, confidence, evidence IDs, contrary evidence, freshness/expiry | Unsupported or stale claim marked unverified/expired; not silently promoted | Claim-to-evidence traceability and uncertainty review |
| IF-020 | Independent Challenge | Independent reviewer → claim/publication workflow | Claim IDs, reviewer independence, challenge method, counter-evidence, disposition and unresolved issues | Reviewer conflict or no independent challenge => publication restricted | Independence test, challenge completeness and resolution record |
| IF-021 | Research Publication | Research desk → approved recipient | Publication ID, tenant, recipient, scope, claims, evidence refs, challenge refs, confidence, expiry, sanitisation status | Recipient mismatch, expired evidence or failed sanitisation => reject | Recipient access, source lineage, correction/expiry and sanitisation evidence |
| IF-022 | Distribution Receipt | Publication service → audit/recipient | Publication ID, recipient, version/digest, delivery time, status, acknowledgement | Delivery unacknowledged => report not delivered; retry bounded and audited | Idempotency, acknowledgement and recipient isolation |

## 6. Market, portfolio and risk interfaces — Trading tenant

| ID | Interface | Producer → consumer | Scope / minimum contract | Failure behaviour | Required acceptance evidence |
|---|---|---|---|---|---|
| IF-023 | Market Data Adapter | Qualified provider adapter → Market Data & specialist desks | Provider, instrument, venue, timestamp, timezone, units, bid/ask/last/OHLCV as applicable, sequence/revision, quality flags, entitlement | Stale, gapped, mixed-unit, ambiguous or unauthorised data => no signal; safe mode as scoped | Provider/terms review, data dictionary, continuity and freshness evidence |
| IF-024 | Market Session Calendar | Market-specific desk → scheduler/operations | Market/instrument, venue, session, holiday, daylight-saving/timezone rules, special closures, source/version | Unknown calendar/session => no assumption of open market or valid signal | Per-market calendar verification and edge-case review |
| IF-025 | Specialist Desk Contract | Each market division → Trading operations / risk | Desk ID, market/instrument scope, data dependencies, session, strategy scope, risk profile, owner, readiness state | Unqualified desk remains disabled; no cross-market semantic substitution | Division-specific data, legal, risk and operational acceptance |
| IF-026 | Indicator / Signal Semantics | PolyBot or specialist strategy → Quant, Risk, paper engine | Indicator version, input bars, closed-bar policy, warm-up, units, formula, null/edge cases, signal timestamp, provenance | Ambiguous inputs or unresolved semantics => no signal | Independent semantic review, fixture approval and later authorised tests |
| IF-027 | Paper Portfolio / Ledger | Paper Trading service → portfolio, risk, OCC summary | Instrument, position, simulated fills, cash/equity, fees/slippage assumptions, valuation time, source, reconciliation state | Missing/stale valuation or reconciliation mismatch => freeze affected paper state and alert | Ledger invariants, reconciliation and audit evidence |
| IF-028 | Risk Decision / CRO Veto | Independent CRO/risk service → strategy, paper workflow, policy | Exposure, limits, scenario, data health, drawdown, decision, reason, veto state, expiry | Risk service unavailable or veto active => stop affected workflow | Independent authority, veto non-overridability and safe-stop evidence |
| IF-029 | Strategy Evaluation | Quant/Strategy → CRO, specialist desk | Hypothesis, version, sample, assumptions, costs, out-of-sample method, benchmark, falsification, reviewer | Missing costs, leakage or inadequate evidence => exploratory only | Reproducibility, bias checks, independent challenge; no performance claim without proof |
| IF-030 | Shift Handover | Outgoing day/night lead → incoming lead | Shift ID, owner/ack, market status, data health, paper positions/exposure, risk/veto, incidents, active work, expiries, unresolved claims, next actions | Missing acknowledgement or critical data => safe mode/escalation | Multi-shift rehearsal, completeness, acknowledgement and audit continuity |
| IF-031 | Market Alert / Escalation | Monitoring/risk/data health → shift lead, CRO, OCC status | Alert ID, market, severity, trigger, evidence, timestamp, acknowledgement, escalation state | Unacknowledged critical alert escalates; no silent drop | Delivery, escalation and false-positive/false-negative review |
| IF-032 | Capital Flow Intelligence | Approved sources / specialist desk → Portfolio & Capital Flow Intelligence | Event type, entity/project, evidence, time, amount/unit, confidence, source limitations, recipient | Unverified attribution or stale data remains unconfirmed | Entity resolution, provenance and independent challenge |

## 7. Security, recovery and continuity interfaces

| ID | Interface | Producer → consumer | Scope / minimum contract | Failure behaviour | Required acceptance evidence |
|---|---|---|---|---|---|
| IF-033 | Incident Record | Any service → Security & Recovery | Incident ID, tenant, severity, scope, evidence refs, containment, owner, status, timestamps | Unknown severity or evidence loss escalated; containment follows approved playbook | Tabletop, escalation and tenant isolation review |
| IF-034 | Backup / Restore Manifest | Backup service → recovery owner | Dataset/service, tenant, version, time, integrity digest, encryption/key reference, retention, restore dependencies | Invalid or stale backup not treated as recoverable | Restore rehearsal, integrity and RPO/RTO evidence when authorised |
| IF-035 | Recovery / Reconciliation Case | Security & Recovery → authorised company owner | Case type, affected tenant/accounting record, evidence, classification, reconciliation, actions, approvals | No proof/authority => no external contact, transfer or irreversible action | Evidence standard, lawful scope, approval and audit trail |
| IF-036 | Security Boundary Audit | Security & Recovery → company owner / OCC summary | Principal, tenant, resource, policy, access result, exception, remediation and evidence | Missing audit evidence blocks certification | Access review, exception expiry and remediation evidence |

## 8. Main Hub/OCC and cross-company interfaces

| ID | Interface | Producer → consumer | Scope / minimum contract | Failure behaviour | Required acceptance evidence |
|---|---|---|---|---|---|
| IF-037 | Signed Status Envelope | Company publisher → OCC receiver | Issuer, tenant, audience, sequence, expiry, source revision, digest, status, signature/key ID | Invalid signature, replay, wrong audience, expiry or revision mismatch => quarantine | Key lifecycle, signature, anti-replay and audience denial evidence |
| IF-038 | OCC Read-only Query | OCC → company reporting interface | Approved report type, recipient, time window, minimum necessary fields | Write/command/action request denied | Read-only enforcement and negative command tests later authorised |
| IF-039 | Cross-company Sanitised Report | Shared service → explicitly approved recipient in other tenant/OCC | Origin tenant, recipient, sanitisation policy/version, allowed claims, removed fields, approval and digest | No approval or failed sanitisation => no cross-tenant distribution | Re-identification/data leakage review and recipient-scope evidence |
| IF-040 | AI Revenue Commercial Readiness | AI Revenue operations/CFO → owner/OCC | Offer, delivery evidence, QA, actual revenue evidence, costs, liabilities, solvency, legal/tax/privacy/payment readiness | Unverified revenue or incomplete gate remains NOT_MET | Bank/payment reconciliation and evidence review; no revenue inferred from forecasts |
| IF-041 | Intercompany Capital Support | AI Revenue owner/finance → Trading finance, only if separately approved | Lawful instrument, amount, purpose, terms, approvals, accounting, solvency impact, repayment/transfer restrictions | No explicit separate approval or solvency protection => prohibited | Legal/accounting review, separate approval, recorded transaction and reconciliation |

## 9. Interface ownership and versioning

- **Architecture steward:** CTO/architecture authority for each company, coordinating shared standards without merging tenant authority.
- **Identity/policy:** Security & Recovery accountable owner, with company-specific policy owners and independent review.
- **Audit/revocation:** Security & Recovery, with deterministic service ownership outside model orchestration.
- **Paperclip lifecycle:** COO/workforce operations; it does not issue security authority.
- **Ruflo orchestration:** Engineering/workforce operations; it cannot widen parent authority.
- **Research/evidence:** Research & Intelligence Director and Source Stewardship; independent challenge remains separate.
- **Market data/sessions:** Market Data & Source Integrity with each specialist division.
- **Strategy/risk:** Quant/Strategy proposes; independent CRO controls risk veto.
- **Day/night handover:** Trading Operations; specialist desk owners remain accountable for market-specific status.
- **OCC:** Read-only interface owner; no operating authority.
- **Commercial readiness:** AI Revenue COO/CFO and owner; real revenue must be evidenced, not forecast.

Every change requires a version bump or documented backward-compatible amendment, schema owner, migration/rollback plan, consumer inventory, security impact, and decision-register entry. Breaking changes require explicit consumer acceptance. Do not update one company tenant's interface or policy by implication from the other.

## 10. Implementation status and next gate

All interfaces in this register are **PROPOSED / NOT IMPLEMENTED** unless an existing artifact separately proves otherwise. This register itself does not certify existing prototypes, schemas or tests.

Next architecture-only tasks:
1. Cross-reference every IF-ID to existing task-envelope, policy gateway, research evidence, Security & Recovery, market data, handover and OCC documents.
2. Mark each interface as EXISTING DESIGN, PARTIAL DESIGN, GAP or FUTURE; attach exact document references and owners.
3. Resolve known semantic blockers (including PolyBot first-bar true-range/previous-close fixture ambiguity) through the documented Quant, Market Data and independent-challenge process before implementation.
4. Preserve the dedicated Gold division's existing work and map its exact contracts into IF-023–026, IF-030 and division-specific readiness evidence.
5. Keep every runtime, test, connection, paid data source, deployment and external action behind separate explicit approval.

**Non-claim:** No interface here is an active endpoint, connected provider, deployed service, passing test, live market monitor or proof of 24/7 coverage.

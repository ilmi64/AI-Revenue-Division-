# Initial Workforce Roster and Tenant Blueprint

**Date:** 2026-11-21  
**Status:** Architecture preparation only — no agents are provisioned, staffed, installed, connected, or running.  
**Applies to:** AI Revenue Company, Trading & Technology Company, and explicitly scoped shared organisation-level services.

## 1. Design objective

Translate the approved shared AI workforce architecture into implementable company-specific organisation maps without creating competing orchestrators or merging company authority.

- **Paperclip** is the leading workforce-management/control-plane candidate for company org charts, role identities, goals, tasks, approval workflows, budgets and run records.
- **Ruflo** is the leading bounded orchestration candidate for decomposing an approved parent task and coordinating specialist subagents.
- **Claude Code and OpenAI Codex** are the first engineering-worker candidates.
- **Qwen, Llama, Gemini and other models** remain optional workers after adapter/runtime, cost, data-handling and permission compatibility is verified.
- **OpenHands** remains a bounded engineering-agent candidate, not a cloud-hosting provider.
- Memory and observability candidates (AgentMemory, Langfuse, OpenLIT and equivalents) are not enabled until tenant isolation, retention, deletion, secret redaction and recovery are reviewed.

This roster describes required accountabilities, not a claim that every role needs a separate model instance or independent agent process at launch. Small initial teams may have one worker perform several bounded roles, but accountability, review separation and escalation remain explicit.

## 2. Company and service boundary map

### 2.1 AI Revenue Company — complete AI-operated business

**Company authority:** AI Revenue CEO, COO, CFO, CTO and other executive roles under owner authority.

| Department / accountable role | Core responsibility | Initial specialist roles / workstreams |
|---|---|---|
| CEO / Executive Office | Strategy, objectives, executive decisions, launch readiness, owner reporting | Strategy analyst; decision-log steward |
| COO / Operations | Operating cadence, task routing, delivery coordination, service reliability, SOPs | Operations planner; workflow coordinator; quality operations |
| CFO / Finance | Budget, unit economics, pricing analysis, cash forecasts, internal ledgers and reconciliation drafts | Cost analyst; pricing analyst; finance controller (draft/review only) |
| CTO / Engineering & Product | Architecture, engineering, automation, product development, technical quality | Platform architect; coding workers; code reviewer; release planner |
| CMO / Marketing | Positioning, brand, content strategy, SEO, distribution and campaign analysis | Market researcher; content strategist; SEO analyst; creative producer |
| CRO / Sales & Partnerships | Offer design, lead research, qualification, pipeline and proposal preparation | Opportunity researcher; lead analyst; proposal drafter |
| CHRO / Workforce | Role definitions, assignment, capacity, performance evaluation and handovers | Workforce planner; agent evaluator; knowledge steward |
| CISO / Security & Privacy | Access control, threat modelling, privacy, security reviews and incident coordination | Security analyst; privacy reviewer; access auditor |
| Legal & Compliance Review | Issue spotting for contracts, IP, privacy, consumer/platform rules, tax and jurisdiction | Compliance researcher; contract issue-spotter; evidence/citation reviewer |
| Product & Service Delivery | Build, deliver, revise within approved scope, QA and acceptance evidence | Delivery lead; domain specialist; QA reviewer; handover writer |
| Customer Operations | Onboarding preparation, support triage, response drafts, issue analysis and retention insights | Support analyst; customer-journey analyst |
| Administration | Internal records, documentation, report preparation and process maintenance | Records clerk; documentation specialist |

**AI-operated lifecycle:** Research demand → qualify opportunities → design offer/product → build → QA → prepare marketing/sales → obtain owner approval for external contact/release → deliver → support → measure economics and quality → improve.

The company is intended to operate its ordinary internal business functions through AI workforce roles within policy. Owner approval remains required for spending, external commitments, customer contact, contracts, publishing, production releases, payment actions, sensitive data access and other consequential acts.

### 2.2 Trading & Technology Company — independent research and trading technology company

**Company authority:** Trading CEO/Executive Lead, COO, CTO, CFO and independent Chief Risk Officer. The CRO's stop/veto authority is independent of the trading strategy lead and cannot be overridden by a swarm vote.

| Department / accountable role | Core responsibility | Initial specialist roles / workstreams |
|---|---|---|
| CEO / Executive Office | Company objectives, strategy, launch gate, owner reporting | Strategy analyst; decision-log steward |
| COO / Operations | Research cadence, task coordination, operational controls and handovers | Operations planner; workflow coordinator |
| CTO / Trading Technology | Data pipelines, agent systems, simulation code, infrastructure and engineering QA | Platform architect; data engineer; coding workers; code reviewer |
| CFO / Finance & Capital | Separate company books, budget, cost tracking, capital availability and reconciliation drafts | Finance controller; cost analyst; capital ledger steward |
| Independent CRO / Risk | Independent risk review, exposure limits, kill-switch policy, challenge and veto | Risk analyst; drawdown auditor; strategy challenger; independent performance auditor |
| Crypto Research Desk | Crypto market structure, tokens, venues, liquidity, ecosystem and on-chain research | Token analyst; market-structure analyst; on-chain analyst; source validator |
| Forex Research Desk | FX macro, sessions, rates, pair research and paper strategies | Macro analyst; FX quant; session analyst |
| Equity Indices Desk | Index research, macro drivers, sessions and paper strategies | Index analyst; quantitative researcher |
| Gold / XAUUSD Desk | Gold drivers, macro/real rates, liquidity and paper strategy research | Metals analyst; macro cross-asset analyst |
| Quantitative Research & Simulation | Hypothesis specification, data quality, backtests, walk-forward and paper simulation | Quant researcher; statistician; data scientist; independent validation |
| PolyBot / Trading Systems | Indicator semantics, signal contracts, deterministic strategy components and paper-only integration | Indicator specialist; data-contract reviewer; simulator engineer |
| Market Data & Source Integrity | Provenance, timestamps, venue semantics, gaps, freshness, units and source reliability | Market-data steward; source-quality analyst |
| Portfolio & Capital Flow Intelligence | Fundraising, launches, VC/fund activity, whale flows, smart-money rotations, unlocks, treasury and developer capital flows | Capital-flow analyst; wallet/entity researcher; launchpad monitor; independent source challenger |
| Security & Recovery (company unit) | Trading-system security, incident response, recovery, reconciliation and access review | Security analyst; incident coordinator; recovery/reconciliation specialist |

**Trading boundary:** Current operating mode remains research and paper-trading only. No wallet, broker or exchange execution connections; no private keys, signing, deposits, withdrawals or live orders. Strategy and orchestration agents cannot alter risk policy, approve trades or override independent CRO controls.

### 2.3 Shared organisation-level service divisions

These services support both companies through explicitly scoped interfaces. They do not own either company's treasury, executive authority, private customer data or trading risk decisions.

#### Research & Intelligence Division — first-class shared service

**Leadership:** Head of Research & Intelligence; accountable to the organisation's governance structure while respecting recipient-company data boundaries.

- **Research Operations Desk:** work-order intake, priority, analyst assignment, deadlines, review and delivery tracking.
- **Grok Desk / HyperGrok research lane:** evaluate available Grok-family research capabilities and multi-pass research methods; do not assume continuous access, free API use or autonomous external browsing.
- **Source Stewardship & Verification:** source registry, provenance, freshness, confidence, conflicts, citation quality, licensing and lawful-use review.
- **Crypto Capital Flow & Opportunity Intelligence:** fundraising/token launches, VC/fund investment activity, whale wallet movements, smart-money sector rotation, launchpad activity, treasury deployment, unlock/vesting, ecosystem and developer capital flows.
- **Cross-Domain Intelligence:** AI/automation markets, customer demand, technologies, vendors, regulation, competitive signals and macro context.
- **Independent Challenge & Falsification:** counter-hypotheses, source independence, assumptions, uncertainty and evidence that would disprove a recommendation.
- **Knowledge Governance:** company-scoped registries, approved memory, retention, access, correction and expiry.

Research requests must be recipient-scoped. Shared intelligence may publish a sanitised general finding to both companies only when source rights and data classification allow it. Raw company-confidential findings remain in the originating tenant.

Day/night or 24/7 operation is a target only. It must not be claimed until persistent compute, approved source access, staffing/agent coverage, monitoring, failure alerts, restart/recovery, handover and quality review have been demonstrated.

#### Security & Recovery Division — first-class shared service

**Leadership:** Head of Security & Recovery with independent escalation path to the owner.

- Identity and access governance; company-specific agent identity lifecycle.
- Secrets architecture and rotation coordination (never store secrets in Git).
- Threat modelling, secure configuration, dependency and supply-chain review.
- Privacy/data classification, retention and deletion controls.
- Incident intake, triage, containment and evidence preservation.
- Backup, restore, disaster recovery and service continuity.
- Trading Loss Recovery & Capital Reconciliation specialist unit: investigate operational, custody, fraud, unauthorized access, payment and settlement failures; distinguish them from ordinary market losses; no recovery guarantee, revenge trading or unauthorised fund movement.
- Independent review of cross-company boundary and revocation controls.

Security & Recovery is not replaced by the Research Division's independent challenge desk. The two collaborate but retain separate mandates.

#### Main Hub / OCC — read-only oversight

- Receives authenticated, recipient-scoped, signed status/evidence envelopes from each company and shared service.
- Displays company-specific objectives, risks, research status, readiness gates, incidents, audit health and owner approvals.
- Maintains portfolio-level view without exposing raw private company data unnecessarily.
- **Cannot** issue commands to agents, grant permissions, alter risk limits, approve spending, publish, move funds, trade, or override company executives/CRO/owner.
- Every displayed status must preserve source identity, timestamp, sequence, revision, digest and freshness. Missing/stale/invalid messages are quarantined, not interpreted as healthy.

## 3. Paperclip tenant and organisation configuration

### 3.1 Tenant topology

Preferred initial safety posture:
- Two independent company instances/tenants, one for AI Revenue and one for Trading & Technology, unless and until Paperclip multi-company isolation is proven adequate for the exact version/configuration through an owner-approved synthetic test.
- Shared generic role templates and non-sensitive skills may be version-controlled in a neutral shared architecture area.
- Shared Research & Intelligence and Security & Recovery work through separate service identities and explicit scoped interfaces, not a global all-access agent.
- Main Hub/OCC consumes read-only status envelopes; it is not a privileged superuser tenant.

A single Paperclip deployment with two organisations is a possible future efficiency option only after tenant-isolation, access-control, task visibility, memory, logs, backup and revocation tests pass. If any boundary fails or cannot be demonstrated, use separate instances.

### 3.2 Minimum company identity fields

Every agent record and every task/run envelope should carry:
- immutable company_id (AI Revenue or Trading & Technology);
- service_scope (company department or explicitly shared service);
- agent_id and versioned role identifier;
- accountable executive and reviewer;
- parent task ID and permitted child-task scope;
- allowed tools and data classifications;
- maximum run time and resource/cost ceiling;
- expiry/revocation state;
- approval requirements and evidence references;
- audit correlation ID.

Identity must be issued/validated by an external deterministic identity/policy layer, not invented by a model or inferred from prompt text.

### 3.3 Paperclip permission profiles

- **Research/read-only:** read approved sources/files, draft analysis, cite evidence; no write to production systems or external communication.
- **Documentation worker:** propose repository patches/drafts; repository writes remain owner-approved unless separately delegated.
- **Engineering sandbox:** synthetic/test data only, scoped filesystem, no secrets, restricted network, no deployment or production access.
- **Finance analyst:** read approved accounting exports, prepare calculations and reconciliation drafts; no payments, transfers, purchases or account changes.
- **Marketing/sales drafter:** prepare content and outreach drafts; no send/publish/advertising/contract authority.
- **Trading research:** approved market data and paper simulator only; no wallet, broker, exchange execution, signing, capital movement or risk-policy edits.
- **Independent reviewer:** read-only access to the specific artifact and evidence needed to challenge it; cannot modify the artifact or approve its own work.
- **Shared service:** only the minimum recipient-scoped request and output fields; no broad cross-company browsing.

Default-deny all unlisted tools, networks, filesystem paths and data. No unattended broad shell, unrestricted browser, broad MCP, arbitrary API keys, plugin installation, autopilot or cross-company federation.

## 4. Ruflo bounded orchestration profiles

Ruflo is invoked only inside a valid parent task issued by the company workforce control plane. It cannot create new company identity, enlarge permissions, alter approvals or continue beyond parent expiry.

| Profile | Intended workflow | Required safeguards |
|---|---|---|
| Research synthesis | Decompose question into source retrieval, specialist analysis, independent challenge and synthesis | Source allowlist; citation/provenance; company-scoped inputs; no external side effects |
| Engineering review | Parallel code/document review, test plans as proposals, issue triage | Synthetic/scoped repo data; no test execution unless separately approved; no merge/deploy |
| Quant research | Hypothesis, data semantics, independent critique, simulation-plan drafting | Paper-only; deterministic datasets; CRO-defined boundaries; no execution |
| Business delivery | Draft offer/deliverable, QA review, economics check and handover pack | Synthetic until customer data access approved; no client contact or publishing |
| Security review | Threat model, permission review, incident playbook and remediation proposal | Read-only by default; no secret access or destructive remediation |
| Research intelligence | Source discovery, provenance check, conflict resolution and recipient-specific report | Licensed/approved sources; no credentialed scraping; no cross-company leakage |

Every child agent inherits the parent's immutable company identity, recipient scope, tool allowlist, data classification, cost ceiling, deadline and approval state. The orchestration layer must reject child tasks that widen any of these. Parent cancellation, expiry, incident or policy denial cancels all descendants.

Disable Ruflo autopilot, persistent background workers, broad hooks/plugins, federation, arbitrary MCP tools and unbounded swarms until individually reviewed and explicitly approved.

## 5. Initial worker sequence

1. **Phase A — role and policy definitions:** finalise named role IDs, ownership, reviewer independence, permission profiles, data classes and escalation.
2. **Phase B — control-plane mapping:** map company departments and role templates into Paperclip configuration drafts; no installation or account connection.
3. **Phase C — orchestration contracts:** define parent/child envelope, identity propagation, cost/time ceilings, cancellation and audit linkage for Ruflo.
4. **Phase D — worker adapters:** verify Claude Code and Codex adapter versions/permission behavior; only then evaluate optional Qwen/Llama/Gemini routes.
5. **Phase E — synthetic read-only pilot design:** prepare synthetic tasks that prove tenant separation, least privilege, parent-scope inheritance, refusal, audit and revocation.
6. **Phase F — owner gate:** obtain explicit approval before any installation, connection, test execution, compute use, repository permission change or deployment.

## 6. Required acceptance gates

No production or autonomous operation until all applicable gates are independently evidenced:
- Company identity and data isolation, including negative cross-tenant tests.
- Role-specific least privilege and default-deny behavior.
- Parent-child scope inheritance and cancellation.
- No model or swarm can grant permissions or self-approve.
- Independent review and CRO veto for Trading.
- Cost ceilings, resource limits, timeout and runaway-loop prevention.
- Immutable audit trail, traceability and source provenance.
- Secret isolation, redaction, rotation and revocation.
- Backup, restore, incident containment and recovery rehearsal.
- Monitoring, health checks, alerting and human escalation.
- Owner approval of any external action or change to authority.
- Separate company launch readiness and owner approval.

## 7. Explicit non-authorization

This document is a blueprint only. It does not authorize agent creation, Paperclip/Ruflo installation, model/API connections, account permission changes, compute execution, tests, code execution, secrets provisioning, repository workflow runs, merges, deployments, external publishing, customer contact, contracts, spending, wallet/broker/exchange connections or live trading.

# Research & Intelligence — Workforce, Desk Operations & Publication Boundaries

**Status:** Organization-level shared-service architecture; not a third company and not yet operational.
**Purpose:** Produce traceable, time-bounded intelligence for separately governed recipient companies.

## 1. Independence and service boundary

Research & Intelligence (R&I) is an organization-level division with its own accountable director, desk leads, agents, task queues, memory, source registry, audit and continuity plan. It is not a third operating company. It does not own either recipient company's decisions, budgets, customer relationships, trading risk or execution authority. Each company may decline, replace or operate without R&I.

R&I shares only approved intelligence products through recipient-scoped publication interfaces. It does not provide raw company memory, customer records, trading account data, credentials or unrestricted task content to another recipient. A research report is advisory, not authorization.

## 2. Workforce identity and roles

Every R&I principal has an immutable `research_intelligence` tenant identity, named accountable owner, desk, allowed source classes, data ceiling, approved runtime, permitted queues and lifecycle state. Lifecycle is PROPOSED → REVIEWED → ACTIVE_SCOPED → SUSPENDED → REVOKED/RETIRED. No identity is shared with either company. No credentials are embedded in prompts or research records.

Director of Research owns methodology, priorities, staffing and quality. Desk leads own domain queues and source stewardship. Analysts gather and synthesize evidence. Source stewards maintain provenance, license, reliability history and freshness. Independent reviewers challenge material claims and conflicts. Publication officers verify recipient scope, redactions and evidence references before release. Security/privacy reviewer handles sensitive-source and incident escalations.

## 3. Specialist desks and queue ownership

| Desk | Core coverage | Accountable lead |
|---|---|---|
| Crypto & PolyBot intelligence | Chains, venues, tokens, pools, bot strategies and protocol changes | Crypto desk lead |
| Crypto Capital Flow & Opportunity Intelligence | Fundraises, launches, VC/fund activity, whale flows, unlocks, treasuries, sector rotations and developer capital | Capital-flow lead |
| Forex intelligence | Pairs, sessions, macro events, liquidity and execution mechanics | FX desk lead |
| Indices intelligence | Index markets, volatility, breadth and macro sensitivity | Indices desk lead |
| Gold / XAUUSD intelligence | Metals, rates, dollar, macro drivers and market costs | Metals desk lead |
| Quant & strategy research | Strategy hypotheses, robustness, falsification and evidence reviews | Quant research lead |
| REA capability intelligence | Lawful public bot, tool and strategy capability analysis; reproduced mechanics | REA desk lead |
| AI, models & agent systems | Model releases, orchestration, agent frameworks, security and benchmarks | Technology intelligence lead |
| AI business & market intelligence | Customer problems, offer demand, competitors, distribution and pricing evidence | Commercial intelligence lead |
| Risk, security & governance | Threats, operational incidents, data integrity, jurisdiction and issue flags | Risk intelligence lead |

J7, Buildix.trade, Sanbase/Santiment, REA, Grok Desk and HyperGrok remain named research workstreams/concepts in their appropriate registries. They are not assumed installed, connected or continuously operating.

## 4. Task lifecycle and evidence stewardship

Research tasks use durable IDs, explicit requester scope, desk owner, priority, deadline, allowed/prohibited sources, data class, question, deliverable, acceptance criteria and evidence stage. States: INTAKE → TRIAGED → ASSIGNED → RESEARCHING → CHALLENGE → PUBLICATION_REVIEW → PUBLISHED or CLOSED; alternatives BLOCKED, CANCELLED, EXPIRED and DEAD_LETTER.

Every source record captures canonical source identity, URL/reference, publisher, retrieval time, publication time if known, content revision/digest when available, license/terms, source class, reliability history, limitations and freshness expiry. Claims link to supporting and contradicting sources, method, confidence rationale, uncertainty and reviewer. Conflicts are preserved, not silently reconciled. Estimates, vendor claims, hypotheses and reproduced findings remain distinct.

No unlawful access, credential extraction, access-control bypass, private-source scraping or proprietary source theft. Source licensing and terms are checked before use or redistribution. Sensitive information is minimized and quarantined.

## 5. Day/night coverage and shift handover

Continuous day/night research is a target service design, not a current operating claim. Coverage requires verified staffing/agent availability, monitored ingestion, escalation routing, health checks and rehearsed handovers. Grok Desk and HyperGrok are concepts to evaluate within this model; they do not bypass source review or publication policy.

Each shift handover records coverage window, desks staffed, active tasks, priority incidents, source freshness gaps, unresolved contradictions, blocked sources, decisions needed, next owner and acknowledgement. Missed coverage is explicitly recorded. No fabricated “24/7” status when a desk or monitor is unavailable.

## 6. Recipient-scoped publication

Publication is a separate controlled step. A publication record binds report ID/version/digest, recipient company, approved topic, data classification, evidence references, redactions, freshness window, reviewer and publication timestamp. A report prepared for Trading is not automatically visible to AI Revenue, and vice versa. Cross-recipient release requires a separately reviewed publication. No recipient gains access to R&I's raw source vault or another recipient's private information.

Trading-bound reports may include market/strategy/capital-flow intelligence but cannot approve risk or execution. AI Revenue-bound reports may include product/customer/competitor intelligence but cannot authorize outreach, pricing commitments or publishing. Both recipients independently decide whether and how to use a report.

## 7. Continuity, audit and security

R&I maintains its own queue state, source registry, memory, audit, backups and recovery. If shared orchestration or a model fails, work pauses or moves to a separately approved fallback without broadening access. If source provenance or publication controls fail, publication stops. Audit records identity lifecycle, source changes, evidence edits, reviewer decisions, publication scope, handovers and incidents.

The OCC receives only aggregate desk health, queue counts, freshness bands, incident severity and publication metadata explicitly allowlisted by R&I. It does not receive raw research content by default.

## 8. Readiness gates

Before claiming live or continuous operation: desk ownership and coverage roster verified; identity and queue isolation implemented; source licensing/provenance controls demonstrated; independent challenge and publication scoping tested; shift handover and missed-coverage alarms rehearsed; backup/restore and incident response proven; recipient interfaces authenticated and allowlisted. Until then status is PLANNED or NOT_RUN, not operational.

## 9. Source quality and shift continuity references

Use the [Source Quality Scorecard & Review Protocol](source-quality-scorecard-and-review-protocol.md) for source-level approval, evidence grading, freshness, terms and hard stops. Use [Specialist Desk Coverage & Shift Handover](specialist-desk-coverage-and-shift-handover.md) for coverage status, shift ownership, escalation and acknowledgement. Templates remain non-operational until separately staffed, approved and rehearsed.

## 10. Registry, prioritization and publication contract

Use the [Unified Source & Capability Registry](../intelligence/unified-source-and-capability-registry.md) as the canonical index, the [Task Prioritization Protocol](research-task-prioritization-and-opportunity-scoring.md) for triage and scoring, and the [Recipient-Scoped Delivery Contract](recipient-scoped-intelligence-delivery-contract.md) for publication envelopes and failure handling. Registry entries and priority scores do not grant access or authority.

## Initial research portfolio and Grok Desk blueprint

The current prioritized work orders, company-specific research sequences, Research & Intelligence shared-service backlog, and Grok Desk/HyperGrok day/night operating blueprint are recorded in `organization/architecture/research/initial-high-priority-research-portfolio-and-grok-desk-blueprint.md`. This is a planning artifact only: desk operations, source monitoring, 24/7 coverage and recipient delivery are not live. Use the existing task-prioritization, source-quality, shift-handover and recipient-scoped publication controls; OCC receives only allowlisted aggregate status.
## 11. Priority source assessment and synthetic handover pack

The [Priority Source Assessment & Synthetic Shift Handover Pack](priority-source-assessment-and-synthetic-shift-handover-pack.md) records the initial high-priority source queue, current holds/context-only dispositions and a fictional day/night handover. It does not approve any source, create operational coverage or claim 24/7 activity.

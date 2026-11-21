# Research & Intelligence Division — Operating System Specification

**Status:** Organization-level architecture; not staffed or continuously operating yet.  
**Classification:** Shared research service, not a third operating company.  
**Authority:** Research Division lead governs research methods and records; each recipient company governs its own use and decisions.

## 1. Mission and service boundary

Deliver reliable, traceable, timely intelligence to AI Revenue and Trading & Technology through separately scoped publications. Research is advisory: it cannot approve company spending, customer contact, deployments, trading, financial actions or company launch. Each company may decline, independently verify or request clarification.

## 2. Leadership and desk structure

- Research Director: priorities, methodology, staffing, service quality and escalations.
- Deputy / Operations Lead: intake, scheduling, handovers, backlog and coverage.
- Source & Provenance Steward: source registry, licensing, integrity and freshness.
- Evidence & Reproducibility Lead: confidence rubric, reproduction and challenge review.
- Archive & Knowledge Steward: versioning, deduplication, retention and supersession.
- Specialist desks: Crypto & PolyBot; Crypto Capital Flow & Opportunity Intelligence; Forex; Equity Indices; Gold; Quant/Strategy; Market Data; REA Bot Capability; AI/Models/Agents/Infrastructure; AI Business/Product/Customer Demand; Risk/Security; Organizational Intelligence.
- Grok Desk and HyperGrok: proposed continuous discovery/challenge concepts, not assumed connected or running. They operate under the same source, policy and company-scope controls as every other researcher.

## 3. Research intake record

Required fields:
- `research_id`, title, requesting organization/company, requester role, created/updated timestamps;
- question, decision it may inform, intended recipient(s), scope and exclusions;
- topic taxonomy, priority, urgency, due date and freshness requirement;
- allowed source classes, prohibited sources/actions, licensing constraints;
- sensitivity, company confidentiality scope, conflict-of-interest flags;
- assigned desk/analyst, reviewer, status, dependencies and handover owner;
- expected deliverable, acceptance criteria and closure reason.

Statuses: `NEW`, `TRIAGED`, `QUEUED`, `IN_PROGRESS`, `CHALLENGE_REVIEW`, `READY_TO_PUBLISH`, `PUBLISHED`, `BLOCKED`, `SUPERSEDED`, `CLOSED`. A published result is never silently overwritten; issue a new version and link the superseded record.

## 4. Source registry

Each source record includes source ID, canonical name, URL or local locator, publisher/owner, source type, access method, first-seen and last-checked timestamps, publication/update timestamp where available, license/terms, permitted use, collection method, reliability history, known bias, coverage, revision/hash, outage status, and source steward.

Source classes: primary/official; direct dataset/API; peer-reviewed/academic; established reporting; vendor documentation/claims; community/social; open-source repository; on-chain/public ledger; internal reproducible experiment. Class is not a substitute for source-specific reliability review.

## 5. Evidence record and confidence

Every material claim links to one or more source IDs and records exact excerpt/locator or dataset version, retrieval time, transformation steps, analyst, corroboration, contradiction, assumptions, uncertainty, confidence rationale and review status.

Confidence labels:
- `CONFIRMED_PRIMARY`: direct authoritative source supports the narrow claim.
- `CORROBORATED`: independent credible sources converge.
- `SUPPORTED`: evidence supports but material uncertainty remains.
- `TENTATIVE`: limited, indirect or early evidence.
- `DISPUTED`: credible sources conflict.
- `UNVERIFIED`: claim not independently substantiated.
- `REJECTED`: evidence does not support the claim.

Do not convert confidence labels into numeric precision without a defined calibration study. Separate fact, inference, hypothesis, forecast and opinion.

## 6. Publication contract

A publication includes research ID/version, recipient company scope, summary, key findings, decision relevance, evidence links, source freshness, confidence, counter-evidence, limitations, assumptions, risk flags, next review date, author/reviewer and content digest. Trading-specific confidential information is never included in an AI Revenue publication and vice versa. Publish only an allowlisted summary; never raw private records, credentials, wallet secrets, customer data or unrestricted memory.

## 7. Archive and registries

Maintain:
- source registry and source health history;
- research intake/task registry;
- claim/evidence registry;
- publication registry and company-scoped distribution log;
- strategy and bot-capability intelligence registries;
- decision/recommendation history and supersession graph;
- research archive with immutable versions and provenance;
- issue/challenge log, unresolved contradictions and watchlist;
- shift/handover log and service health register.

Preserve existing workstreams and identifiers, including Crypto Capital Flow & Opportunity Intelligence, J7, Buildix.trade, Sanbase/Santiment, REA, Grok Desk and HyperGrok. Inventory existing records before migration; do not recreate or overwrite prior research.

## 8. Day/night handover template

Each handover records: shift ID and timezone; outgoing/incoming lead; coverage window; critical developments; active research IDs and current state; new sources and freshness; unresolved claims/contradictions; watchlist triggers; blocked tasks and reason; company publications issued; recipient acknowledgements; incidents; next actions, owners and deadlines. The next shift explicitly accepts the handover. Missed coverage is marked as a gap, never represented as continuous monitoring.

## 9. Continuous-operations readiness

Day/night coverage is a target, not a current capability claim. Before describing the service as continuous, prove staffed/automated coverage, monitored source collection, queue durability, alerting, shift acceptance, reviewer coverage, outage handling, backup/restore, audit completeness and a successful multi-shift rehearsal. If a desk or source is unavailable, publish a coverage gap and last-verified timestamp.

## 10. Service-level measures

Track intake age, time-to-triage, time-to-publication, source freshness, evidence completeness, correction rate, reproducibility rate, unresolved contradiction age, duplicate research rate, recipient usefulness feedback, missed handovers and coverage gaps. Optimize reliability and decision usefulness, not output volume.

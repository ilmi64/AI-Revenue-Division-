# Research & Intelligence — Desk Roster, Work Assignment & Challenge Protocol

**Status:** Organization-level operating design; not staffed or operational.  
**Service boundary:** Shared Research & Intelligence Division serving two independent companies.  
**Authority:** Advisory and evidence production only. No company action, spend, publication, trading or external commitment authority.

## 1. Mission and governance

Research & Intelligence is a core shared service, not a third company and not an optional future add-on. It maintains disciplined research capability for both companies, with specialist desks, task ownership, evidence governance, independent challenge, shift handovers and recipient-scoped reporting.

The division does not own either company's commercial decisions, customer records, strategy secrets, funds, risk limits or launch authority. Each company retains its own executive, memory, policy, finances, audit, data and final decisions. Research recommendations are not instructions.

The operating design borrows lifecycle discipline from the NIST AI Risk Management Framework: Govern, Map, Measure and Manage. This is a voluntary reference, not a certification or claim of compliance. Human oversight, documented accountability, provenance, risk assessment and independent challenge are explicit requirements. References: https://www.nist.gov/itl/ai-risk-management-framework and https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf.

## 2. Proposed desk roster

| Desk | Core responsibilities | Primary recipient(s) | Hard boundary |
|---|---|---|---|
| Research Operations & Intelligence Director | Portfolio, capacity, priority arbitration, quality policy, coverage and escalation | Both companies via separate reports; OCC aggregate | Cannot override either company |
| Research Intake & Triage | Intake, clarify decision need, priority, scope, due window, recipient and resource estimate | Both | Cannot broaden scope or approve cost |
| Source Registry & Provenance | Canonical source identity, terms, data rights, freshness, revision, quality score and source-health history | Both | No source use solely because listed |
| Crypto & Digital Asset Intelligence | Protocols, tokens, launchpads, exchange flows, capital movements, ecosystem changes | Trading primarily | No wallet access, attribution or trading authority |
| Crypto Capital Flow & Opportunity Intelligence | Fundraising, token launches, VC/fund activity, whale movements, treasury deployment, unlocks, smart-money rotation, ecosystem capital | Trading | No claim of causality or wallet identity without evidence |
| Forex Intelligence | Currency pairs, sessions, macro drivers, venue/product mechanics, costs and data sources | Trading | Product-specific legal and Shafi'i holds |
| Equity Index Intelligence | Index methodology, constituents, macro catalysts, ETFs/futures/options/CFDs distinctions | Trading | Reference index is not itself an instrument approval |
| Gold & Precious Metals Intelligence | Gold/XAUUSD, physical/allocated/unallocated products, market structure and custody | Trading | Ownership/settlement and financing review mandatory |
| Quantitative & Strategy Research | Hypothesis design, falsification, data integrity, baseline, costs, backtest review protocol | Trading | No strategy approval or profitability claims |
| Market Data & Microstructure | Venue schemas, candle/order-book/trade semantics, data quality, gaps, latency and provenance | Trading | No feed/API ingestion without approval |
| Technology & AI Systems Intelligence | Models, agents, MCPs, orchestration, memory, evaluation, security, licensing and runtime comparisons | Both, separately scoped | No installation, connection or permission change |
| REA / Reverse Engineering Desk | Lawful public capability decomposition across apps, bots, services and AI workflows | Both, separately scoped | No protected code extraction, access bypass or private data |
| AI Business & Customer Intelligence | Canadian demand evidence, customer problems, competitor offers, business models and pricing claims | AI Revenue | No outreach or customer-data collection |
| Product & Service Intelligence | Offer design, delivery methods, customer journey, differentiation and service economics | AI Revenue | No unsupported demand or margin claims |
| Risk, Security & Integrity Challenge | Threats, source poisoning, privacy, conflicts, incident review and independent challenge | Both, separate records | Advisory; company risk officers retain veto |
| Grok Desk — Rapid Discovery | Candidate event discovery, change detection and urgent research intake | Routed separately | Planned only; no monitoring currently |
| HyperGrok — Cross-Desk Synthesis | Orchestrates specialist input and drafts decision-focused summaries | Routed separately | Cannot self-approve high-impact output |
| Publication & Recipient Control | Redaction, recipient, expiry, evidence links, review and publication-state validation | One recipient per publication | No live publication path currently |

J7 remains identity-HOLD. Buildix.trade and Sanbase/Santiment remain provisional context candidates. No API, private group, wallet or paid data connection is approved.

## 3. Task assignment record

Every work order contains unique ID/version; requester and exact recipient (AI_REVENUE, TRADING_TECH or SHARED_GOVERNANCE); decision being informed; question/scope/exclusions/artifact; priority/due window/freshness/expiry; assigned desk/accountable lead/independent challenger; approved source classes/restrictions; evidence/confidence requirements; privacy/data classification/permitted storage; resource/cost estimate and CAD $0 boundary; dependencies/blockers/escalation; acceptance criteria and closure disposition.

A shared public fact may be researched once at source layer, but each company's interpretation and report must be separately created, reviewed and stored. Shared governance documents are the only common private organizational scope.

## 4. Priority and assignment

- P0 — security, privacy, cross-tenant, integrity or unexpected-cost incident. Stop affected work and escalate.
- P1 — narrow-window event that may materially affect a near-term decision. Rapid review; never bypass verification.
- P2 — important planned work with a clear decision use. Normal queue.
- P3 — exploratory, low-urgency or speculative research. Queue behind P0–P2.

Priority is not confidence. Assignment sequence: confirm recipient and decision use; check existing evidence freshness; check source/legal/privacy/resource eligibility; assign one accountable desk lead; assign separate challenger for material work; set due window and acceptance criteria; record blocked/held state rather than silently substituting source or tool.

Research Director may reprioritize the Research queue but cannot reprioritize company commercial or trading decisions.

## 5. Evidence and independent challenge

Claim evidence grades: PRIMARY_CONFIRMED, CORROBORATED, SINGLE_SOURCE, VENDOR_ESTIMATE, PUBLIC_CLAIM, ATTRIBUTED, HYPOTHESIS, CONTRADICTED, SUPERSEDED.

Source quality and claim strength are separate. A reputable source can make an unsupported claim; a low-quality source can point to a claim worth checking.

The challenger must attempt to falsify the conclusion: verify exact entity/instrument/contract/product/version; locate primary evidence and inspect date/methodology/scope; seek independent corroboration rather than repeated syndication; identify contradictions, missing data, alternative explanations and selection bias; test for overstated causation/certainty/representativeness; check terms/data rights/privacy/recipient boundaries; record what evidence would change the disposition.

For high-impact work, author cannot be sole challenger or publication approver. Model-to-model disagreement is useful but does not establish independent verification.

## 6. Dispositions

DRAFT; NEEDS_CORROBORATION; HOLD_IDENTITY; HOLD_TERMS; HOLD_FRESHNESS; HOLD_PRIVACY; HOLD_JURISDICTION; QUARANTINE_CONTRADICTION; REJECT_UNSUPPORTED; ACCEPT_FOR_SCOPED_DRAFT; APPROVED_FOR_RECIPIENT_REVIEW; EXPIRED; SUPERSEDED.

ACCEPT_FOR_SCOPED_DRAFT means evidence is sufficient to prepare a bounded internal draft, not to execute a recommendation or publish externally.

## 7. Day/night coverage and handover

Target is continuous day/night coverage, but current state is PLANNED_NOT_OPERATIONAL. No staffing, agent identities, source monitors, alerting, runtime, shift coverage or 24/7 operation is verified.

Every future handover records outgoing/incoming lead and actual coverage window with timezone; staffed/unstaffed desks and uncovered intervals; open work orders, priority, status and next action; source health/freshness/terms exceptions; claims awaiting challenge and contradictions; incidents/quarantines/escalations; resource/cost state; incoming acknowledgement and timestamp.

If a shift is missed, record the coverage gap. Never fabricate a scan or imply a desk was active. Grok Desk/HyperGrok are planned and require independent runtime, source, review, recovery and publication gates.

## 8. Company-scoped publication and OCC

One publication has one recipient. If a finding is relevant to both companies, produce two separately reviewed reports with appropriate context and redaction. No shared private report body.

Company report minimum: recipient and decision context; as-of time; executive finding and confidence rationale; evidence links/source dates/claim grades; counter-evidence and alternatives; unknowns/limitations/freshness expiry; prohibited downstream uses; author/challenger/reviewer/revision; disposition and next review.

Main Hub/OCC receives only allowlisted aggregate metadata: work-order ID, recipient, desk, priority, status, due/age bands, aggregate source health, coverage gaps, incident severity, publication ID/version/status and approved evidence references. No raw customer records, private strategies, credentials, full report bodies or cross-company memory. OCC remains read-only.

## 9. Current operating status and readiness gates

Before claiming operational readiness, demonstrate named accountable leadership and backup; verified roster and shift coverage; source register with rights/freshness/owner; separate company workspaces and access boundaries; durable work queue/audit/recovery; independent challenge capacity; recipient-authenticated delivery and redaction; incident escalation and coverage-gap reporting; resource/cost controls; rehearsed handover/outage recovery; owner and company executive acceptance.

**Disposition:** ORGANIZATIONAL DESIGN PREPARED; NO STAFFING OR AGENT DEPLOYMENT VERIFIED; NO CONTINUOUS MONITORING; NO LIVE PUBLICATION; ADVISORY ONLY.

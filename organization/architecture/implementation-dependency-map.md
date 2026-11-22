# Canonical Implementation Dependency Map

**Status:** Architecture and implementation planning only. No implementation, installation, tests, account connections, deployment, paid services, runtime activation or external action is authorised by this document.

**Scope:** Shared workforce foundations and both company tenants, with the Trading & Technology multi-division, coordinated-launch and 24/7 multi-market operating model explicitly represented. This document is mirrored across the AI Revenue and Trading repositories; company-specific data and authority remain segregated.

## 1. Governing decisions and non-negotiable constraints

1. AI Revenue and Trading & Technology are independent companies with separate company identity, data, accounts, budgets, policies, audit trails, risk ownership and approval boundaries.
2. The planned Trading & Technology divisions are developed in parallel and intended to launch together. Crypto/PolyBot is one workstream, not a prerequisite sequence that postpones Forex, Indices, Gold/XAUUSD, Quant, Market Data, Portfolio/Capital Flow Intelligence, Research & Intelligence, Security & Recovery or other established divisions.
3. Coordinated launch is conditional: every required division must independently satisfy its readiness gates. If any required division is not ready, the organisation-wide Trading launch gate remains unmet; report the blocker rather than silently switching to a phased division launch.
4. Trading's target coverage is continuous at the organisational level. Daytime PolyBot and day operations coordinate with night-shift Grok Desk/HyperGrok as one operating system. Each specialist desk respects its own market calendar, session, data availability and approved scope; not every market is represented as open 24/7.
5. Gold/XAUUSD remains a dedicated specialist division. Its existing research, architecture and requirements are authoritative inputs to integration; do not flatten it into a generic PolyBot subtask or recreate completed work.
6. **AI Revenue revenue is not a prerequisite for Trading & Technology to launch.** Trading may launch independently when sufficient lawful starting capital is available and all Trading company/division readiness gates and owner approval are satisfied. The intended plan is parallel preparation and a coordinated launch where feasible. If lawful starting capital is unavailable, Trading goes on standby while AI Revenue pursues revenue as a possible capital source. Any AI Revenue-to-Trading support requires a separate lawful, documented, accounted-for and explicitly owner-approved arrangement that protects AI Revenue solvency and operating needs; no automatic transfers, shared treasury or commingling.
7. Existing CAD $0 incremental-spend rule remains. No paid subscriptions, APIs, hosting, credits, payment-backed trials, purchases, deposits, borrowing, leverage or other spend.
8. No installation, deployment, production connection, repository permission change, merge, CI/test run, customer contact, publishing, contract, financial transaction, wallet signing, broker/exchange order or other consequential external action without the relevant explicit approval.
9. Trading remains research and paper-trading only. Live execution, private keys, signing and exchange/broker execution credentials are not enabled by this architecture.
10. Main Hub/OCC is read-only oversight. Independent CRO risk veto and Security & Recovery controls remain separate and cannot be overridden by an agent or swarm.

## 2. Dependency graph — build order

The architecture has a strict logical dependency order, but workstreams within each layer can be prepared in parallel.

### Layer 0 — authority, scope and shared contracts

**Foundational; precedes every executable component.**

- Company and tenant identity model.
- Role and service identity registry.
- Data classification, company scope, recipient scope and permitted-action taxonomy.
- Parent-child task envelope and immutable scope inheritance.
- Policy decision contract and deny-by-default action classes.
- Approval records and owner-authority model.
- Canonical identifiers, timestamps, correlation IDs and audit-event vocabulary.

**Depends on:** Existing company charters, workforce roster, parent-child task envelope, security/recovery boundary standard and decision registers.

**Acceptance evidence:** reviewed schemas and examples; documented ownership; explicit cross-tenant denial cases; explicit action-class matrix; traceable decision/approval records. Conceptual examples are not implementation validation.

### Layer 1 — deterministic identity and policy enforcement

**First executable security foundation; model prompts are never the authority source.**

- Identity service issues and validates company, service, agent and delegated task identities.
- Policy decision point evaluates identity, role, company, scope, classification, action class, expiry, approval state and revocation epoch.
- Policy enforcement gateway mediates every tool, data, connector and external-action boundary.
- Tool allowlists and data access filters enforce least privilege.
- Approval service records owner approvals for separately gated consequential actions.
- Policy state unavailable, identity ambiguous, expired authority or unknown action => fail closed.

**Depends on:** Layer 0 contracts.

**Acceptance evidence before installation or synthetic testing:** threat model; reviewed identity lifecycle; signed/verified policy decision contract; least-privilege matrix; denial test catalogue; independent security review; recovery and rollback design. No credentials or real account connections in synthetic fixtures.

### Layer 2 — audit, event and revocation backbone

**Build alongside Layer 1; required before orchestration can be trusted.**

- Append-only or tamper-evident audit/event store with actor, tenant, task, policy decision, source, timestamp, action, outcome and correlation references.
- Revocation epoch and authority version service.
- Parent cancellation/expiry propagates to all descendants, queued jobs, delegated tokens, tool sessions and pending actions.
- Late results after cancellation/revocation are quarantined and cannot be committed as current work.
- Audit gaps, sequence anomalies or unavailable policy state trigger safe mode.

**Depends on:** Layer 0 identity and event contracts; Layer 1 policy model.

**Acceptance evidence:** event integrity design; retention/access policy; replay/duplicate handling design; revocation propagation matrix; bounded cancellation latency target; synthetic denial and late-result scenarios approved for later testing.

### Layer 3 — company tenants and workforce control plane

**Can be designed in parallel with Layers 1–2; runtime integration waits for their enforcement contracts.**

- Paperclip is the leading candidate for company org charts, roles, parent tasks, approvals, lifecycle and accountability.
- Separate AI Revenue and Trading company tenants, with separate identities, work queues, budgets, data stores and audit scopes.
- Shared services (R&I, Security & Recovery and Main Hub/OCC) receive explicit service identities and narrowly scoped recipient permissions; shared does not mean unrestricted cross-company access.
- Role templates and workforce rosters are versioned, with human owner as final authority.
- Company managers may delegate only within policy-issued parent authority.

**Depends on:** Layer 0; runtime integration depends on Layers 1–2.

**Acceptance evidence:** tenant-isolation design; role-to-permission mapping; cross-tenant negative cases; lifecycle/approval state model; proof that company administrators cannot silently expand global authority. Paperclip remains a candidate until version, adapter, runner and isolation review are completed on an approved host.

### Layer 4 — bounded orchestration and worker adapters

**Can be prepared independently after the parent-child envelope is stable; activation waits for deterministic policy and revocation.**

- Ruflo is the leading candidate for bounded decomposition, specialist swarms, handoffs and workflow orchestration inside an approved parent task.
- Claude Code, Codex, Qwen, Llama, Gemini and other compatible models/runtimes connect through separately reviewed adapters or MCP/API/local-runtime boundaries as appropriate.
- OpenHands remains a bounded engineering-agent candidate.
- Every child task inherits company, service, recipient, data, action, budget, expiry, reviewer-independence, correlation and revocation constraints.
- Effective authority is the intersection of parent authority, role authority and policy; a child cannot widen scope.
- Finite child count, concurrency, retries, time, output size and tool-call budgets.
- Autopilot, background workers, broad MCP, unrestricted hooks, federation and external actions remain disabled unless separately reviewed and approved.

**Depends on:** Layer 0; execution integration depends on Layers 1–3.

**Acceptance evidence:** adapter permission inventory; reproducible worker identity; bounded task examples; scope-escalation denial cases; cancellation/revocation tests later authorised; model/source provenance; output quarantine and review rules.

### Layer 5 — domain data, research and business registries

**Parallel domain workstreams; each uses the common provenance and policy envelope.**

Shared data plane:
- Source registry and source lifecycle.
- Evidence capture/provenance and immutable source references.
- Atomic claim records, confidence and challenge records.
- Recipient-scoped research publication and distribution receipts.
- Data-quality, freshness, schema, units, timezone, market-session and revision metadata.
- Company-scoped knowledge stores and sanitisation for any approved shared-service output.

Trading specialist registries:
- Crypto/Solana and PolyBot indicator/data semantics.
- Forex instruments, sessions, quote conventions, calendars and source qualification.
- Indices instruments, constituent/contract semantics, sessions and provider-specific data.
- Gold/XAUUSD specialist research, instrument/provider conventions, session calendar, volatility/liquidity characteristics and dedicated desk requirements.
- Quant/strategy hypotheses, assumptions, simulation methodology and falsification records.
- Market Data & Source Integrity source health, continuity and quality.
- Portfolio & Capital Flow Intelligence, including capital flows, fundraising, launches, VC/fund activity, whale movements, rotations, launchpads, treasury deployments and unlocks/vesting.
- PolyBot and other market-system contracts.
- Research & Intelligence, including Grok Desk/HyperGrok, independent challenge, source stewardship and knowledge governance.

AI Revenue registries:
- Service/product capabilities, delivery evidence, operating economics, buyer/problem validation, customer-safe materials and commercial risk.
- AI Creative Studio capability research and other revenue workstreams.

**Depends on:** Layer 0 data/recipient contracts; write paths depend on Layer 1–2 enforcement and audit.

**Acceptance evidence:** source qualification dossiers; data dictionaries; licensing/terms review; timestamp/session/units semantics; freshness thresholds; independent corroboration; claims traceable to evidence; correction/expiry handling. No live feeds or paid data/API access are implied.

### Layer 6 — Security & Recovery services

**Separate first-class service; parallel design, but operational dependencies are mandatory before activation.**

- Identity and access lifecycle, boundary audits and revocation coordination.
- Threat review, incident intake, severity and escalation.
- Backup, restore, disaster recovery and resilience.
- Privacy and sensitive-data handling.
- Trading Loss Recovery & Capital Reconciliation, with evidence-led classification; no guarantee that ordinary market/strategy losses are recoverable.
- Separation from R&I's independent research challenge and from OCC oversight.

**Depends on:** Layer 0–2 contracts; service implementation also depends on approved persistence/hosting and key-management design.

**Acceptance evidence:** threat model; incident playbooks; tested backup/restore evidence when tests are authorised; revocation evidence; access review; incident tabletop approval; recovery boundaries and no-secret-handling controls.

### Layer 7 — day/night market operations and 24/7 continuity

**Architecture can be designed now; cannot be declared operational until the full operational chain is proven.**

Day capability:
- PolyBot and day operations coordinate primary crypto/market monitoring, data-quality checks, strategy evaluation, paper-trading workflows and specialist desk handoffs.
- Specialist desks for Forex, Indices, Gold/XAUUSD, Quant, Market Data, Portfolio/Capital Flow and other approved markets maintain their own domain rules and session calendars.

Night capability:
- Grok Desk/HyperGrok perform market/event monitoring, research, opportunity/risk analysis, strategy challenge, paper-trading review and evidence-backed reporting.
- HyperGrok specialist roles include Desk Lead, Market Analyst, Research Analyst, Strategist, Risk Manager and Trade Reviewer. No Execution Trader role is introduced.

Continuity plane:
- Shared authoritative portfolio state and paper ledger; common risk limits and event/audit history.
- Market-specific calendars, holidays, session state and data-provider health.
- Acknowledged handover with named outgoing/incoming shift ownership, open tasks, positions/paper exposure, risk state, data freshness, incidents, unresolved claims and expiry.
- Alerts for stale feeds, missing bars, sequence gaps, service degradation, missed handovers and lost communications.
- Safe mode if data, risk controls, policy, audit or handover is unavailable.
- On-call/escalation, restart, backup and restore; no unattended recovery that can widen authority.

**Depends on:** Layers 1–6 plus persistent host, approved data access, monitoring and recovery.

**Acceptance evidence:** multi-shift synthetic rehearsal; missed-handover and stale-data scenarios; alert delivery evidence; restart/restore rehearsal; risk-veto demonstration; audit continuity; per-market coverage matrix; documented on-call ownership. A target schedule is not proof of 24/7 coverage.

### Layer 8 — Main Hub/OCC signed read-only interfaces

- OCC receives recipient-scoped, authenticated and integrity-protected status and reports.
- Signed envelopes include issuer identity, sequence, expiry, audience, source revision and digest, with anti-replay and quarantine rules.
- OCC cannot write company policy, grant permissions, approve spending, move funds, trade, publish or override company authorities.
- Cross-company reporting is sanitised and minimised; no unrestricted shared data plane.

**Depends on:** Layers 0–2, company tenant identities and recipient-scoped publication contracts; production interfaces also depend on persistence and security review.

**Acceptance evidence:** signature/key lifecycle review; audience isolation; replay/expiry/revision denial cases; source lineage; read-only enforcement; quarantine and recovery evidence. Existing OCC work remains design/prototype status unless separately verified.

### Layer 9 — coordinated launch gates

**All required Trading divisions launch together only after every gate is met.**

- Each division's own legal/regulatory and operational scope approved.
- Market data/source access qualified, licensed and monitored.
- Instrument semantics, calendars, data quality and freshness accepted.
- Strategy and quantitative evidence reviewed; no unsupported performance claims.
- Independent CRO risk approval and veto controls proven.
- Security, privacy, access, revocation, audit and incident readiness accepted.
- Persistent hosting, monitoring, alerting, backup/restore and on-call coverage proven.
- Day/night coverage and multi-shift handover rehearsed.
- Portfolio/capital accounting and any required starting capital lawfully available and separately approved.
- AI Revenue revenue is not a Trading launch gate. Trading's capital gate is satisfied by sufficient lawful starting capital from an independently approved source. AI Revenue revenue may be a future funding contingency only; any intercompany support requires separate lawful documentation, accounting and explicit owner approval.
- Explicit owner launch approval after evidence review.

If one required division fails its gate, the coordinated launch does not proceed. Maintain parallel development and report the precise blocker. Do not silently launch only the divisions that happen to be ready.

## 3. Parallel workstreams versus hard dependencies

| Workstream | Can proceed now in parallel? | Hard dependency before runtime |
|---|---|---|
| Company/tenant and role schemas | Yes | Identity and policy enforcement |
| Identity and policy contracts | Yes; foundational priority | Security review and approved implementation |
| Audit and revocation design | Yes, alongside identity | Durable event store and enforcement integration |
| Paperclip/Ruflo adapter research | Yes, no install | Host approval, least-privilege and policy integration |
| AI Revenue commercial readiness | Yes | Approved rehearsal, QA/economics, legal/tax/privacy/payment gates |
| Crypto/PolyBot semantics | Yes | Source contract and independent semantic review |
| Forex specialist division | Yes | Forex-specific data, calendar, instrument and regulatory acceptance |
| Indices specialist division | Yes | Index-specific data, calendar, instrument and regulatory acceptance |
| Gold/XAUUSD specialist division | Yes; preserve existing work | Gold-specific data/session/contract and risk acceptance |
| Quant/strategy research | Yes | Reproducible methodology, source quality and independent challenge |
| Market Data & Source Integrity | Yes | Provider qualification and freshness/continuity contracts |
| Portfolio & Capital Flow Intelligence | Yes | Evidence/source qualification and recipient boundaries |
| Research & Intelligence / HyperGrok | Yes | Approved sources, provenance, independent challenge and runtime controls |
| Security & Recovery | Yes | Identity, audit, revocation, backup and incident controls |
| OCC read-only interfaces | Yes, schema/design | Authenticated signed publisher and verified receiver controls |
| 24/7 shift operation | Design now | Persistent host, monitored sources, on-call, recovery and rehearsed handovers |

## 4. Company-specific versus shared-service boundaries

**AI Revenue tenant**
- Owns its company roles, tasks, customer/business data, commercial pipeline, delivery records, budget and audit trail.
- Must reach independently verified operational revenue before Trading launch.
- Does not automatically fund or expose data to Trading.

**Trading & Technology tenant**
- Owns its specialist market divisions, portfolio and paper ledger, strategy records, data entitlements, risk limits and audit trail.
- Each market division has its own qualification and readiness gate.
- Trading live execution remains disabled absent separate future legal, security, capital, risk and owner approvals.

**Shared Research & Intelligence**
- Provides common research methods, source stewardship, evidence/claim/publication contracts, Grok Desk/HyperGrok operating framework and cross-domain intelligence.
- Access is recipient-scoped. Company-sensitive findings remain in their originating tenant unless explicitly sanitised and approved.

**Shared Security & Recovery**
- Provides boundary, incident, revocation, resilience and recovery standards through separate service identity and least-privilege interfaces.
- Does not become a shared administrator with unrestricted access to both companies.

**Main Hub/OCC**
- Receives signed, read-only, recipient-scoped status and decision evidence.
- Cannot operate either company or override its authority.

## 5. Hosting and persistence dependency

The architecture is portable and can continue to be prepared without selecting a host. Runtime activation cannot.

- GitHub Codespaces is bounded development capacity, not a production always-on host.
- Zo Computer remains a future persistent-host candidate but is paid after its trial; no trial or subscription is authorised.
- Cloudroom free entitlement remains unresolved; do not treat it as a verified persistent host.
- Colab/Kaggle are ephemeral research notebooks, not persistent workforce infrastructure.
- E2B/Rig are metered; PequeRoku requires separate suitable self-hosted hardware.
- No current candidate has been verified as a zero-cost persistent always-on host for the full workforce, policy, database, audit, monitoring and day/night operating system.

Therefore:
- Continue schema, contracts, architecture, role design, source qualification research and dependency preparation.
- Do not install Paperclip/Ruflo or deploy databases/services until a suitable host and security design are explicitly approved.
- Do not rely on a phone, ephemeral notebook or idle-sleeping sandbox for 24/7 coverage.
- Any future hosting decision must include total cost, persistence, backups, monitoring, security, recovery, jurisdiction/data handling and exit plan.

## 6. Acceptance evidence ladder

No stage is implied by completion of the previous document or by a tool being available.

1. **Architecture reviewed:** contracts, ownership, threat model, data boundaries and dependency mapping reviewed.
2. **Implementation approved:** exact components, versions, licenses, host, costs, permissions and rollback plan approved by owner.
3. **Synthetic test approval:** isolated synthetic fixtures, test scope, expected denials and cleanup plan approved.
4. **Synthetic tests executed:** results, failures, logs and independent review recorded; no real credentials or external effects.
5. **Limited integration approval:** specific accounts, read-only scopes, data classes, retention and revocation plan approved.
6. **Shadow/paper operation approval:** bounded, monitored and reversible; no external financial execution.
7. **Division readiness accepted:** each division's evidence signed off by its accountable leader and independent risk/security reviewers.
8. **Trading launch approval:** every required Trading division passes its own gates, sufficient lawful starting capital is available, and the owner explicitly authorises launch. AI Revenue revenue is not a prerequisite. If capital is unavailable, Trading remains on standby; AI Revenue may continue its independent revenue work.
9. **Any live trading authority:** separate future decision and approvals; never inferred from paper readiness or organisation launch.

## 7. Immediate next preparation sequence

1. Reconcile the existing role/tenant, parent-child, policy gateway, audit/revocation, research evidence, Security & Recovery and OCC documents against this dependency map; record gaps rather than duplicate contracts.
2. Prepare a canonical interface register with one owner, version, producer, consumer, data classification, failure mode and acceptance evidence per interface.
3. Prepare a per-division readiness matrix for Crypto/PolyBot, Forex, Indices, Gold/XAUUSD, Quant, Market Data, Portfolio/Capital Flow and all established shared divisions. Preserve the Gold specialist material as source-of-truth.
4. Prepare a day/night coverage and market-calendar matrix, including handover data and safe-mode conditions.
5. Continue AI Revenue commercialization readiness and Trading division engineering preparation in parallel.
6. Keep hosting, installation, tests, connections and activation blocked until their separate approval gates are met.

## 8. Explicit non-claims

This document does not mean the workforce is staffed, deployed, connected, continuously monitoring, producing live signals, generating revenue, validated, or operating 24/7. It records a target architecture, dependencies and evidence required to earn those claims.

# Main Hub / OCC Build Plan

**Status:** Approved architectural direction; implementation plan only — not deployed  
**Priority:** First shared workstream  
**Applies to:** Trading & Technology Company and AI Revenue Company  
**Target:** Parallel development and independent evidence-based company launches; coordinated target window January 4–8, 2027; no company or shared-service launch dependency  
**Budget:** CAD $0 incremental by default

## 1. Purpose

Turn the Main Hub / Operations Control Centre (OCC) from a documented governance concept into a small, testable coordination and oversight system for two independent companies.

The Main Hub is a shared oversight layer. It is not a parent company, merged executive team, shared finance ledger, trading authority, or unrestricted agent controller.

## 2. Current verified baseline

The current architecture branches contain substantial reference material for:
- company isolation, agent identity and scoped task handoff;
- deterministic policy and approval boundaries;
- audit chains, durable approval records and outbox/dispatch safety;
- recovery authority, quarantine and evidence reconciliation;
- a two-company workforce registry and model-agnostic adapter contract;
- a production-readiness evidence register.

The current repository trees do **not** contain a demonstrated running Main Hub/OCC application. The control-plane Python files are reference/prototype components; the contracts and acceptance tests are not proof of production operation. No new Actions run, deployment or live service is implied by this plan.

## 3. Main Hub v0.1 — minimum useful build

Build a **read-only status and evidence control centre first**. Do not begin with autonomous command execution.

### Required components

1. **Company registry**
   - Two distinct company identifiers: Trading & Technology and AI Revenue.
   - Separate executives, agents, work queues, memory, budgets, ledgers, audit records and readiness decisions.
   - Shared-service interfaces explicitly listed and scoped.

2. **Decision and commitment register**
   - Stable decision ID, decision text, date, scope, owner approval state, affected company/workstream, source/evidence reference, current status and supersession link.
   - Preserve historical decisions; amendments create new entries rather than silently rewriting history.
   - Track strategy agreements and bot-intelligence work as first-class workstreams, not informal notes.

3. **Read-only company status snapshots**
   - Each company publishes a minimal summary through a defined adapter.
   - OCC receives status and evidence references only, not private customer records, trading records, credentials, raw memory or unrestricted task content.
   - Snapshot fields: company ID, source revision, timestamp, overall status, subsystem statuses, critical gate states, blockers, incident severity/count and evidence references.
   - Missing, stale, unauthenticated or inconsistent snapshots display as UNKNOWN / STALE / BLOCKED, never green.

4. **Readiness and evidence view**
   - Display each company’s critical gates separately.
   - Preserve PASS / FAIL / BLOCKED / NOT_RUN / WAIVED semantics.
   - Do not calculate an aggregate score that hides a failed critical gate.
   - OCC reports evidence; it cannot declare a company operational or waive a gate.

5. **Incident and recovery visibility**
   - Show company-reported incident summaries, quarantine state, last verified checkpoint and recovery status.
   - OCC may coordinate notifications and evidence collection, but cannot release quarantined systems or override company risk authority.

6. **Audit and observability**
   - Record who/what published each snapshot, source revision, timestamp, integrity reference and any rejected update.
   - Keep company audit streams separate; OCC stores only approved summary evidence and its own coordination audit.

## 4. Initial architecture

- **OCC core:** read-only aggregator, registry, decision log, evidence index and status presentation.
- **Research & Intelligence Division:** an organization-level division/shared service with its own leadership, workforce, queue, memory and scoped operating records. It serves both initial companies and future divisions without becoming a third company or acquiring their executive, finance, risk or data authority. It maintains source/provenance, freshness, confidence, historical research and handover records. Continuous day/night coverage, including the previously discussed Grok Desk and HyperGrok concepts, is a target architecture to be implemented and verified in stages—not a claim of current operation.
- **Company adapters:** one adapter per company; allowlisted fields only; authenticated source identity; schema/version validation; freshness checks.
- **Storage:** begin with a local/offline prototype and synthetic fixtures. Do not treat SQLite as production multi-node storage. Select durable production storage only after backup, restore, concurrency and isolation evidence.
- **Interface:** start with a simple local operator view or CLI/report if that is the fastest zero-cost testable path. A web dashboard is a later presentation layer, not a prerequisite for proving the data contract.
- **Workforce integration:** Paperclip remains the leading workforce-control candidate and Ruflo the bounded orchestration candidate. Neither receives OCC authority merely by integration.
- **Model access:** models may summarise approved evidence but cannot authenticate publishers, set status, grant permissions, approve actions or override deterministic policy.

## 5. Security and authority boundaries

- Default deny; least privilege; fail closed.
- No company-to-company raw data access by default.
- No credentials, API keys, wallet secrets, private keys, customer secrets or personal account tokens in OCC.
- No OCC endpoint for spending, purchases, publishing, client contact, account changes, deployments, wallet actions, broker orders or live trading.
- Trading risk controls and veto authority remain inside Trading & Technology and independent of OCC and model consensus.
- AI Revenue retains its own CEO, CFO, budgets, customer operations and commercial authority.
- Owner approval remains mandatory for consequential external actions and all standing restricted actions.
- A model, agent, Paperclip, Ruflo or OCC cannot approve its own permissions or change its own policy.

## 6. Build sequence and acceptance criteria

### M0 — Baseline inventory
- Map existing contracts, prototypes, registries and evidence gates.
- Identify duplicate, stale and conflicting documents.
- Confirm exact source revisions before implementation.
- Acceptance: traceable inventory; no operational claims.

### M1 — Canonical records and schemas
- Define company registry, decision register, workstream register and status-snapshot schema.
- Add synthetic examples for both companies.
- Acceptance: schema validation rejects missing identity, invalid status and unapproved fields. Freshness, replay protection and source-revision provenance require separate runtime checks; JSON Schema alone cannot establish them.

### M2 — Read-only OCC prototype
- Ingest synthetic company snapshots.
- Display company separation, gate states, blockers, stale data and evidence references.
- Acceptance: OCC cannot mutate company state or execute external actions; missing data never appears healthy.

### M3 — Company adapters
- Add separate read-only adapters for each company.
- Authenticate publisher identity and verify source revision, timestamp, scope and allowed fields.
- Acceptance: cross-company access attempts, forged publisher, replay, stale data, schema drift and oversized/private payloads are rejected.

### M4 — Resilience and audit
- Test process restart, interrupted writes, duplicate/replayed snapshots, clock skew, partial outage, backup and restore.
- Acceptance: no silent loss or false-green status; all failures are visible and recoverable.

### M5 — Controlled workforce integration
- Connect read-only status and approved task summaries to workforce tooling only after isolation and permission tests.
- Keep write actions and unattended execution disabled.
- Acceptance: company-specific agent identities and permissions remain isolated; owner approvals cannot be bypassed.

### M6 — Operational rehearsal
- Run company outage, OCC outage, stale snapshot, compromised publisher, incident escalation and recovery exercises.
- Acceptance: each company can continue independently if OCC is unavailable; no shared component can bypass its controls.

## 7. Workstreams the Main Hub must preserve

AI Revenue's revenue-first commercial preparation is maintained in [Revenue-First, Zero-Upfront Commercialization Plan](revenue-first-commercialization-plan.md), with the reusable [workflow audit template](workflow-audit-template.md) and [synthetic demonstration](sample-synthetic-workflow-audit.md). These remain company-local business artifacts; OCC receives only approved summary evidence and does not perform customer-facing actions.


- Main Hub/OCC and two-company governance. The company registry remains exactly two operating companies; the Research & Intelligence Division is a distinct organization-level division/shared service, not a third company.
- Research & Intelligence Division: continuous day/night market, strategy, technology, AI, business, competitive, risk and data intelligence; research archives and source/provenance registry; opportunity discovery; evidence grading; specialist research agents; day/night handovers; scoped intelligence delivery to Trading & Technology, AI Revenue and future divisions. Preserve existing research and data rather than restarting it. Public/approved sources only; company-private records remain separately controlled.
- Trading & Technology: PolyBot, REA bot/capability reverse engineering, strategy discovery, independent strategy implementation, backtesting, paper validation, market data/provenance, capital-flow intelligence, Crypto, Forex, indices, Gold, risk, security and recovery.
- AI Revenue: AI-operated executive and departmental workforce, first commercial revenue stream, customer acquisition/delivery, finance, AI Creative Studio and reusable products/services.
- Shared workforce infrastructure: Paperclip, Ruflo, model adapters, memory, evaluation, observability and bounded engineering agents.
- Existing skill/tool and capability registries; do not re-add tools without a demonstrated gap.
- Deferred projects remain deferred unless explicitly resumed.
- Canonical organizational map: `organization/architecture/organization-and-division-charter.md` / `docs/architecture/organization-and-division-charter.md`. It records the full AI Revenue departments, Trading & Technology specialist workstreams, Main Hub/OCC, Research & Intelligence, shared-infrastructure boundaries and independent parallel launch model.
- Research & Intelligence operating charter: `organization/architecture/research-intelligence-division-charter.md` / `docs/architecture/research-intelligence-division-charter.md`; defines leadership, specialist desks, knowledge governance, day/night handovers, evidence standards and scoped delivery.
- Each company maintains its own detailed operating blueprint in its own repository and architecture branch; these remain company-scoped and are linked from the corresponding organization charter.
- Parallel execution and independent launch programme: `organization/architecture/parallel-build-launch-programme.md` / `docs/architecture/parallel-build-launch-programme.md`; defines four simultaneous lanes, company-specific gates, optional shared infrastructure and non-dependency rules.

Strategy discovery outputs must distinguish public claims, hypotheses, reproduced mechanics, backtest results and independently validated results. No strategy is labelled profitable from marketing claims or synthetic data.

## 8. Launch and operating rules

- AI Revenue and Trading & Technology are independent, standalone companies developed in parallel. Each company must pass its own evidence-based launch gates; neither requires the other's revenue, launch or operational readiness. January 4–8, 2027 is the coordinated target window, not a hold point.
- Neither company is a prerequisite, supplier, funding source, customer, or operational dependency for the other's launch. Neither must generate revenue, receive customer payment, or reach operational readiness before the other can launch.
- AI Revenue is a complete AI company with its own executive leadership, departments, agent workforce/swarms, products and services, customer operations, finance, security and independent launch decision.
- Trading & Technology has its own executive leadership, specialist workforce, trading/technology systems, data, finance, security and independent risk authority and launch decision.
- Shared infrastructure is limited to approved cooperation and competitive advantage: reusable infrastructure, model/runtime adapters, orchestration technology, scoped research/intelligence and defined interfaces. It does not create shared company authority, executives, finances, private memory, customer/trading data, permissions or operational dependencies.
- Each company must remain able to operate if the other company or Main Hub/OCC is unavailable. Main Hub/OCC coordinates and reports; it does not control either company or make one company's launch conditional on the other.
- Trading & Technology must pass its own data, security, risk, paper-mode, exit, recovery, incident and rehearsal gates. Live trading is a separate readiness and owner-approval decision; it is not implied by company launch.
- Extend the target only where evidence shows it is necessary for safety, integrity or readiness.
- No paid subscriptions, APIs, credits, hosting, trials with billing risk, purchases or other spending without explicit owner approval.
- No Actions runs, merges, deployments, public releases, account/permission changes or consequential external actions without separate explicit approval.

## 9. Implementation progress (2026-11-20)

- **M0 baseline inventory:** initial repository-tree and architecture-document inventory completed. The inventory confirmed that the OCC application itself is not present as a demonstrated running service. Existing control-plane Python modules remain reference/prototype material until tested at an exact revision.
- **M1 canonical records:** JSON Schema and synthetic company snapshots, registry/workstream examples, decision-log starter and a complete root-envelope fixture containing both company snapshots are committed under `main-hub/` in both architecture branches. The schema constrains the company registry and status-snapshot collection to exactly two entries, with one record for each company. The root envelope now carries both company snapshots instead of only an AI Revenue snapshot.
- **Validation limitation:** JSON syntax parsing passed for the schema and four fixture files. Full JSON Schema validation has **not** been run; no validator package was installed and no GitHub Actions workflow was triggered. JSON Schema can validate structure and declared constraints, but it cannot by itself prove publisher authenticity, replay resistance, real-time freshness or source-revision provenance. Those require separate runtime controls, which are not implemented.
- **M2 read-only prototype:** an offline Python-standard-library report generator, strict nested-field allowlists, company-identity checks, conservative freshness handling and a 29-test authored suite have been committed under `organization/architecture/main-hub/prototype/` in the AI Revenue architecture branch. This is a temporary implementation staging location only; it does not give AI Revenue authority over OCC or company records. The prototype reads synthetic fixtures only and has no network, database, server, credentials or external-action capability. Tests are authored but have **not** been executed; this is reference code, not a running service.
- **M2 hardening:** validation now checks nested gate, blocker, incident and evidence structures, rejects unexpected nested fields and malformed enum types, and marks stale synthetic snapshots as stale while retaining their untrusted label.
- **Research & Intelligence Division:** formally included as a core organization-level division/shared service in this plan. Its architecture, leadership/workforce, continuous day/night operating model, knowledge governance and delivery interfaces must be carried into canonical organization records and later readiness gates. It is not operational yet.
- **M2 parser bounds (2026-11-21):** added explicit fixture byte, JSON depth, node, array, object and string/key limits plus four regression tests. The latest expanded suite remains unexecuted; formal Draft 2020-12 validation remains pending.
- **M2 exact-source validator (2026-11-21):** authored `validate_m2_schema.py` in the AI Revenue prototype staging area. It pins the Git blob identities of the schema and five synthetic fixture files, checks the Draft 2020-12 meta-schema, validates the complete envelope with date-time format assertion, and checks company/record identity uniqueness. The script has not been executed; no schema-validation pass is claimed.
- **Parallel company blueprints (2026-11-21):** created company-scoped operating blueprints for AI Revenue and Trading & Technology in their respective repositories. These detail each company's executive responsibilities, departments/workstreams, agent workforce boundaries, operating lifecycle and independent launch gates.
- **Parallel execution programme (2026-11-21):** created mirrored four-lane plan for AI Revenue, Trading & Technology, Main Hub/OCC and Research & Intelligence. It explicitly makes shared infrastructure and shared intelligence non-blocking optional enhancements, with independent company launch decisions.
- **Next:** when explicitly authorized, execute the exact-pinned schema validator and the current prototype suite; meanwhile continue company-specific workforce/department plans, Research Division registries and handovers, and OCC read-only presentation design without creating launch dependencies.

## 9. Definition of done for Main Hub v0.1

Main Hub v0.1 is complete only when:
- both company identities and their boundaries are represented correctly;
- decision/workstream records are durable and traceable;
- read-only snapshots from both companies validate and display correctly;
- stale, missing, forged, replayed and unauthorized data fail closed;
- critical readiness gates and evidence references are visible without false-green aggregation;
- OCC cannot change company state or execute external actions;
- both companies remain able to operate independently if OCC is unavailable;
- tests are run against an exact recorded revision and retained as evidence.

**Current disposition:** M0 COMPLETE / M1 DRAFTED / M2 REFERENCE PROTOTYPE COMMITTED BUT UNTESTED / NOT OPERATIONAL.

## 12. Authoritative parallel-launch correction (2026-11-21)

This section supersedes any earlier sentence in this document that makes AI Revenue revenue, AI Revenue launch, Trading & Technology launch, Main Hub/OCC activation, or Research & Intelligence activation a prerequisite for another operating company's launch.

- AI Revenue and Trading & Technology are built in parallel and have separate readiness evidence, executive decisions and launch gates.
- Neither operating company is a prerequisite for the other's launch, revenue, staffing, funding, infrastructure or operational continuity.
- AI Revenue does not need to generate revenue before Trading & Technology can launch. Trading & Technology does not need to launch before AI Revenue can launch.
- Main Hub/OCC and Research & Intelligence are organization-level shared services and are not launch prerequisites for either company.
- The January 4–8, 2027 window is a coordination target, not a hold point. A company that independently satisfies its own launch gates may launch when authorized, even if another lane is delayed.
- Trading & Technology company launch remains distinct from live-trading authorization. Research/paper operation is the default; live execution requires its own evidence-based gate and separate explicit owner approval.
- Shared infrastructure is optional, scoped and replaceable. Each company must continue safely if the other company or any shared service is unavailable.
- All standing no-spend, no-deployment, no-installation, no-publishing, no-financial-action and explicit-approval restrictions remain in force.

If any earlier section, table, milestone or copied summary conflicts with this correction, this correction governs. Historical text is retained for traceability, not as active policy.

## 13. Workforce, Research and OCC specifications added (2026-11-21)

The following detailed specifications are part of this build programme and remain design-only until separately implemented, reviewed and authorized:
- AI Revenue department role catalogue: `organization/architecture/workforce/department-agent-role-catalogue.md`.
- Trading & Technology specialist role catalogue: `docs/architecture/workforce/trading-specialist-agent-role-catalogue.md`.
- Research & Intelligence operating system: `organization/architecture/research-intelligence-operating-system.md` / `docs/architecture/research-intelligence-operating-system.md` (mirrored).
- Shared infrastructure tenancy and failover: `organization/architecture/shared-infrastructure-tenancy-and-failover.md` / `docs/architecture/shared-infrastructure-tenancy-and-failover.md` (mirrored).
- Read-only OCC operator console specification: `organization/architecture/main-hub/occ-readonly-operator-console-spec.md` / `docs/architecture/main-hub/occ-readonly-operator-console-spec.md` (mirrored).

These references do not authorize installations, deployments, data sharing, continuous unattended operation, external actions or live trading. The two operating companies retain independent launch gates and separate authority.

## 14. Task, queue and research record contracts added (2026-11-21)

- AI Revenue task schema: `organization/architecture/workforce/schemas/agent-task.schema.json`.
- AI Revenue queue/approval workflow: `organization/architecture/workforce/queue-and-approval-workflows.md`.
- Trading & Technology task schema: `docs/architecture/workforce/schemas/agent-task.schema.json`.
- Trading queue and independent CRO workflow: `docs/architecture/workforce/queue-and-risk-workflows.md`.
- Shared Research record schema (mirrored in both repositories): `organization/architecture/research/schemas/research-records.schema.json` / `docs/architecture/research/schemas/research-records.schema.json`.

These are draft contracts. Schema validation, sample-record validation, queue implementation, durable storage, tenant-isolation testing and operational rehearsal remain pending. No test execution or runtime installation is implied.

## 15. Workforce execution, Research operations and queue observability (2026-11-21)

The next architecture layer has been documented; all items below remain design-only, not deployed:
- AI Revenue identity lifecycle, role-to-queue capability matrix, separation of duties, durable task state, lease fencing, idempotency, retry/dead-letter, company-local policy and exact owner-approval binding: `organization/architecture/workforce/workforce-execution-and-identity.md`.
- Research & Intelligence workforce roles, specialist desk ownership, source stewardship, day/night handovers and recipient-scoped publication: `organization/architecture/research/research-workforce-and-publication.md`.
- Read-only OCC workforce/queue observability contract, including tenant-specific publisher channels, strict allowlists, freshness, replay handling and quarantine: `organization/architecture/main-hub/occ-workforce-observability-contract.md`.

These specifications do not create identities or credentials, install Paperclip/Ruflo, start continuous research, connect queues, expose task payloads or enable external actions. Company-local policy remains authoritative; OCC remains read-only. The Trading & Technology company has its own corresponding workforce specification in its own repository.

## 16. Fast-track and continuous improvement programme (2026-11-21)

This build plan is governed by the organization-wide fast-track system at `organization/architecture/fast-track-continuous-improvement-operating-system.md` and the cross-company Technology Intelligence/REA framework at `organization/architecture/research/technology-intelligence-and-rea-framework.md`.

The operating priorities are dependability, validation, capital preservation, sustainable profitability and expansion. Work proceeds in parallel across AI Revenue, Trading & Technology, Main Hub/OCC and Research & Intelligence. Crypto/PolyBot remains the first Trading capability priority; it does not delay or gate AI Revenue's independent launch. Progress is measured by independently verified working capabilities, not document or agent counts.

REA is a cross-organization research capability for lawful evaluation of apps, businesses, bots, agents, APIs, workflows and tools. It remains uninstalled and unintegrated pending supported Windows/Mac/Linux runtime and explicit authorization. The preserved portfolio and no-spend/approval restrictions remain binding.

The canonical portfolio index is `organization/architecture/intelligence/capability-opportunity-registry.md`. It preserves existing named workstreams, records recipient scope and explicit status, defines a weighted evidence-led prioritization method, and requires source-level reconciliation before adoption. It is a planning ledger, not a live feed or approval authority.

The next policy-enforcement consolidation is recorded in `organization/security/policy-gateway-integration-and-gap-closure-plan.md`. It maps existing identity, deterministic policy, durable approval, audit, recovery and dispatch contracts into one staged company-local enforcement path, documents known gaps and preserves all test/deployment approval gates. No production enforcement is claimed.

The targeted registry/control-plane baseline inventory is recorded at `organization/architecture/intelligence/registry-and-control-plane-baseline-inventory.md`. It records fetched source revisions, distinguishes existing detailed registries from the new portfolio index, and lists the remaining source-level reconciliation and production-control gaps.

The Public APIs catalogue has been evaluated as a permanent discovery/reference input for Research & Intelligence. Its recipient-scoped assessment and API candidate shortlist are recorded in `organization/architecture/research/public-apis-directory-evaluation.md`. It is not an API service, a provider licence, or authorization to connect any listed endpoint.


## Research-source updates — 2026-11-21

- Public API provider work orders and existing-source overlap review: `research/provider-api-workorders-and-comparison.md` (AI Revenue: `organization/architecture/research/provider-api-workorders-and-comparison.md`; Trading: `docs/architecture/research/provider-api-workorders-and-comparison.md`).
- MoonPay PayBox and historical USDC launch-faucet assessment: `research/moonpay-paybox-and-airdrop-assessment.md` (AI Revenue: `organization/architecture/research/moonpay-paybox-and-airdrop-assessment.md`; Trading: `docs/architecture/research/moonpay-paybox-and-airdrop-assessment.md`).
- PayBox is research-only and is not approved as a company wallet or trading gateway: current published terms prohibit use on behalf of a business entity and identify the contracting provider as unregulated BVI Launchpad Limited.
- The PayBox USDC launch faucet is historical; current official availability and Canadian eligibility remain unverified. Airdrop research is optional and cannot fund or gate either company's independent launch.
- No PayBox account, connector, wallet, X authorization, API call, claim, funding, transaction, or installation occurred.


## 13. Owner's latest launch-priority and capital-contingency decision (2026-11-21)

This section supersedes the earlier independent-launch wording in this build plan where it conflicts with the owner's latest sequencing decision.

- **Default:** build AI Revenue and Trading & Technology simultaneously. Continue both companies' independent work queues, executive authority, finance, policies, records and readiness gates. Pursue Trading capital in parallel; do not pause Trading preparation while capital is being secured.
- **Parallel launch path:** if Trading capital is available and Trading independently passes its company-launch gates, both companies may launch in parallel in the coordinated target window, after their own approvals. A ready company is not held back solely by delay in the other.
- **Capital-shortfall fallback:** if Trading capital is unavailable at launch review, AI Revenue takes first launch priority if it passes its own readiness gate and the owner authorizes launch. Trading remains STANDBY / NOT LAUNCHED for funded/live operations; continue only safe, authorized no-cost research, development and paper preparation.
- **Reactivation:** reassess Trading when a legitimate capital source is available and its own readiness gates pass. AI Revenue revenue may be considered as a possible future source only through a separately approved, legally/accountingly sound arrangement. There is no automatic intercompany transfer, loan, shared treasury, guarantee or funding obligation.
- **Capital integrity:** do not count projected, unclaimed, airdropped or hypothetical rewards as available capital. Do not substitute borrowed funds, paid memberships, leverage, deposits or speculative rewards for capital readiness.
- **Trading live execution:** remains a separate gate after company launch and requires its own evidence-based readiness and explicit owner approval.
- **No status inflation:** report actual capital availability, source, restrictions, company readiness and launch status separately. If capital is unavailable, Trading is standby—not launched or live.
- This sequencing does not merge the companies or make one company's private records, executive authority, finance or risk controls subordinate to the other. Main Hub/OCC and Research & Intelligence remain non-operational shared services unless separately authorized and verified.

The four-lane build continues simultaneously across AI Revenue, Trading & Technology, Main Hub/OCC and Research & Intelligence. The capital contingency changes launch order only when required; it does not pause parallel preparation.

## Initial Research & Intelligence work portfolio (2026-11-21)

The initial high-priority, recipient-scoped research portfolio and Grok Desk/HyperGrok operating blueprint are recorded in `organization/architecture/research/initial-high-priority-research-portfolio-and-grok-desk-blueprint.md`. This work order separates AI Revenue, Trading & Technology and the core Research & Intelligence shared service; maps dependencies and blockers; and defines aggregate-only OCC reporting. It does not establish live desk coverage, automated source ingestion, authenticated publication, operational readiness or permission for external actions. Company launch gates remain independent.


## Organization-level Security & Recovery Division (2026-11-21)

Security & Recovery is a first-class organization-level division alongside Crypto/Trading, Treasury/Finance, Technology/Infrastructure, Research/Intelligence and Business/Commercial. Its charter and proposed specialist units are recorded in the AI Revenue repository at `organization/architecture/security-recovery/security-and-recovery-division-charter.md` and mirrored in the Trading repository at `docs/architecture/security-recovery/security-and-recovery-division-charter.md`.

The incident register and recovery assurance standard are also mirrored in both repositories. The register is intentionally empty. It defines evidence-backed incident handling, Risk owner → Executive → affected division/system owner escalation for critical/high incidents, SHA-256 backup-integrity checks, restore-after-corruption drills, rollback/restart validation and owner-approved closure.

The AI Executive Advisory Desk remains independent above divisions and may challenge, warn, request pauses and recommend safe mode/recovery, but cannot trade, move funds, raise limits, override safeguards or independently execute containment, rollback, liquidation, restart or recovery.

Both companies retain embedded security responsibilities and independent records, credentials, policies, executives and recovery paths. OCC receives only approved aggregate metadata. This is documentation only: no incident monitoring, containment, notifications, backup jobs, restore drills, rollback, restart, deployment or operational recovery has occurred.


## Organization-level Security & Recovery Division (2026-11-21)

Security & Recovery is a first-class organization-level division alongside Crypto/Trading, Treasury/Finance, Technology/Infrastructure, Research/Intelligence and Business/Commercial. Its charter and proposed specialist units are recorded in the AI Revenue repository at organization/architecture/security-recovery/security-and-recovery-division-charter.md and mirrored in the Trading repository at docs/architecture/security-recovery/security-and-recovery-division-charter.md.

The incident register and recovery assurance standard are also mirrored in both repositories. The register is intentionally empty. It defines evidence-backed incident handling, Risk owner → Executive → affected division/system owner escalation for critical/high incidents, SHA-256 backup-integrity checks, restore-after-corruption drills, rollback/restart validation and owner-approved closure.

The AI Executive Advisory Desk remains independent above divisions and may challenge, warn, request pauses and recommend safe mode/recovery, but cannot trade, move funds, raise limits, override safeguards or independently execute containment, rollback, liquidation, restart or recovery.

Both companies retain embedded security responsibilities and independent records, credentials, policies, executives and recovery paths. OCC receives only approved aggregate metadata. This is documentation only: no incident monitoring, containment, notifications, backup jobs, restore drills, rollback, restart, deployment or operational recovery has occurred.


The Security & Recovery assurance register is maintained separately in each company scope and mirrored as a blank template at organization/architecture/security-recovery/security-control-and-recovery-readiness-register.md and docs/architecture/security-recovery/security-control-and-recovery-readiness-register.md. OCC may receive only allowlisted aggregate control/recovery status; it must not expose detailed control evidence, credentials or forensic records.

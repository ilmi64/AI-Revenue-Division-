# Main Hub / OCC Build Plan

**Status:** Approved architectural direction; implementation plan only — not deployed  
**Priority:** First shared workstream  
**Applies to:** Trading & Technology Company and AI Revenue Company  
**Target:** January 2027 simultaneous activation, subject to independent readiness gates  
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

- AI Revenue and Trading & Technology are independent, standalone companies intended to build and launch in parallel in January 2027, each when its own launch-readiness gates are met.
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
- **Next:** execute the latest committed standard-library tests only when explicitly requested, then perform full Draft 2020-12 schema validation using an already-available offline validator. Only after those checks should the next iteration add a local operator presentation.

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

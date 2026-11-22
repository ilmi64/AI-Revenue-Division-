# PG-7 — Independent Security Review and Operational Rehearsal Plan

**Status:** Architecture and review protocol only; no independent review, tests, deployment or operational rehearsal has occurred.  
**Scope:** Company-local policy gateway and workforce control plane.  
**Authority:** Each company retains its own executive, security, risk and owner-approval boundaries.  
**Execution posture:** Documentation only until separately authorized; CAD $0 incremental by default.

## 1. Purpose and exit standard

PG-7 is the final design/review gate before any proposal to deploy a company policy gateway or connect it to live tools. It does not itself authorize implementation, production use, customer activity, payments, wallet/broker access or trading.

The exit standard is not "the documents look complete." It is a package of independently reviewed, exact-revision evidence showing that:
- the intended control path is complete and enforceable at every action boundary;
- no unmediated path can perform a prohibited action;
- identity, task, policy, approval, cost, dispatch, receiver, audit, revocation and recovery controls compose correctly;
- each company remains isolated from the other;
- fail-closed behaviour and recovery are demonstrated under realistic failure conditions;
- unresolved findings are either closed with evidence or explicitly accepted by the proper company authority within policy;
- owner approval is obtained for the exact next stage, separately from the review outcome.

A review can conclude BLOCKED or NOT READY. No target date or launch pressure changes that result.

## 2. Independence and reviewer qualifications

The review must be performed by people who did not author or implement the control being reviewed, with relevant competence in:
- application and platform security;
- authorization systems and distributed transaction semantics;
- cryptographic identity, key custody, rotation and revocation;
- database consistency, idempotency, event delivery and recovery;
- cloud/runtime/MCP/tool integration and network egress;
- privacy, tenant isolation, logging and incident response;
- the company's applicable product, financial and operational risk.

At least one reviewer must be independent of the implementation team and must be able to report findings directly to the relevant company security executive and owner. A model-based review can supplement but cannot replace qualified independent review.

The AI Revenue review and Trading & Technology review are separate engagements with separate evidence, findings, sign-off and authority. A reviewer may reuse a common technical checklist, but must assess each company's actual policy overlay and data boundary independently.

## 3. Review inputs and immutable scope

Before review begins, freeze and record:
1. Repository, branch, exact commit SHA and file/blob manifest.
2. Architecture, threat model, operation taxonomy, task schema, policy profile and approval schema versions.
3. Runtime and deployment topology, including every agent, scheduler, tool broker, MCP server, connector, API, database, queue, worker, network route and receiver.
4. Data classification, tenant boundary, secret/key custody model and retention rules.
5. Identity issuer, owner authority, trusted time, revocation and emergency-stop trust roots.
6. Outbox, sender, receiver, idempotency, fencing, audit and recovery contracts.
7. Company-specific prohibited operations, budgets, risk limits and approval classes.
8. Known gaps, accepted risks, dependencies and unimplemented controls.

Any material change to code, policy, schema, topology, key, identity issuer or permission after the review invalidates the affected evidence and requires targeted re-review. Findings must reference exact artifacts and versions; screenshots or narrative assertions alone are insufficient where machine-verifiable evidence is available.

## 4. Review domains and minimum questions

### A. Identity and authority
- Can an agent, model, administrator, scheduler or shared service create or elevate its own identity?
- Are issuer, subject, audience, company, role, session, runtime and expiry cryptographically bound?
- Are identity lifecycle, revocation, rotation and compromise handling complete?
- Can a valid identity be replayed in another company, task, environment or runtime?
- Is owner authority independently authenticated and separated from agent authority?

### B. Task and delegation
- Is every task assigned by a trusted company-local scheduler?
- Are parent/child delegation, task reassignment, cancellation, expiry and scope reduction handled?
- Can a sub-agent inherit broader tools/data/operations than the parent task?
- Are task state transitions durable, fenced and auditable?
- Can an agent fabricate completion or evidence?

### C. Deterministic policy and operation coverage
- Does every external side-effect path pass through the same mandatory policy boundary?
- Are operation/resource identifiers exact and allowlisted, with unknown values default-deny?
- Are wildcard, shell, arbitrary URL, filesystem, browser, MCP and direct API routes controlled?
- Can cached permits survive a policy change, revocation, emergency stop or recovery epoch?
- Are hard denies independent of owner approval?

### D. Approval and transaction integrity
- Is approval bound to exact company, task, actor, operation, resource, amount, currency, recipient, policy version, nonce, expiry and audience as applicable?
- Can approvals be altered, replayed, reused, transferred or consumed concurrently?
- Is approval consumption atomic with action reservation and audit append?
- Are retries and ambiguous outcomes safe?
- Can an owner approve a broader action than the one actually reviewed?

### E. Cost and resource controls
- Are inference, API, hosting, storage, egress, marketplace and third-party charges identified and metered?
- Can a provider incur charges outside the gateway's budget controls?
- Are quotas and circuit breakers enforced before resource consumption?
- Are budget exhaustion and metering outages fail-closed?
- Is the CAD $0 default effective across every AI Revenue workload, including indirect model/tool calls?

### F. Data, privacy and isolation
- Are customer, company, trading, wallet, strategy, credential and private memory records isolated?
- Can logs, traces, prompts, backups, exports or error reports leak data across companies?
- Are Research & Intelligence publications recipient-scoped and minimized?
- Does Main Hub/OCC receive only approved read-only summaries?
- Can a shared orchestration or model provider expose cross-tenant context?

### G. Dispatch, receiver and external effects
- Is the action intent immutable and uniquely identified?
- Does the receiver enforce idempotency and epoch fencing rather than trusting the sender?
- What happens when a timeout occurs after the external system may have accepted the request?
- Is outcome_unknown quarantined for reconciliation rather than automatically resent?
- Can a receiver accept a stale, revoked or cross-company action?

### H. Audit, monitoring and recovery
- Are audit events append-only, ordered, integrity-protected and independently checkpointed?
- Are clock drift, time rollback, sequence gaps, duplicate events and missing evidence detected?
- Can recovery restore a consistent state without resurrecting consumed approvals or stale permissions?
- Are quarantine, revocation and emergency-stop states durable across restart/failover?
- Are recovery authority and ordinary operator authority separated?

## 5. Company-specific mandatory overlays

### AI Revenue
- CAD $0 incremental spend remains the default; paid inference, APIs, hosting, storage, subscriptions, marketplace charges and other billable services deny unless the exact spend and budget are separately owner-approved.
- Customer contact, proposal submission, contract acceptance, publication, listing creation, payment requests and customer-data export remain external actions with separate approval.
- No agent may use a customer manifest, private inventory file or sales dataset outside the authorized customer/project scope.
- Product safety, recall, authenticity, privacy and marketplace policy checks must be explicit before a resale-related listing or customer recommendation.
- No purchase of liquidation stock is permitted by this architecture; inventory acquisition requires a separate business case and explicit owner approval.

### Trading & Technology
- Research and paper simulation remain the default operating modes.
- Live order placement, wallet signing, transfers, withdrawals, broker/exchange orders, leverage, risk-limit changes and strategy activation remain hard-denied in the current policy baseline.
- Owner approval cannot override hard-deny or independent risk-veto controls.
- Public market-data research must preserve source, timestamp, licence/terms and provenance; stale or contradictory data must not silently become actionable.
- Halal/Shafi'i issue flags are research annotations, not religious rulings or permission to execute.

## 6. Controlled rehearsal programme

Rehearsals must use synthetic data and isolated non-production infrastructure unless a later, separately approved plan explicitly authorizes otherwise. Do not connect wallets, brokers, exchanges, customer systems, payment processors or production APIs as part of a tabletop exercise.

Required scenarios:
1. Compromised or revoked agent identity attempts a tool call.
2. Task is reassigned, cancelled or narrowed while an agent holds a prior permit.
3. Owner approval is replayed, altered or concurrently consumed.
4. Policy service, trusted clock, revocation feed or audit store becomes unavailable.
5. Budget meter or provider cost signal fails while an agent attempts a billable operation.
6. Agent attempts direct network, shell, filesystem, browser or connector bypass.
7. Cross-company data access is attempted through logs, memory, shared model context, backups and Research publication.
8. Sender times out after dispatch and receiver outcome is ambiguous.
9. Receiver receives a duplicate action or stale recovery epoch.
10. Emergency stop is activated during an in-flight task and then the system restarts.
11. Backup restore occurs after approval consumption, revocation and audit checkpoint.
12. Shared orchestration, OCC or Research Division becomes unavailable; each company must continue in a bounded local fallback.
13. A product/manifest workflow encounters a recall, prohibited item, uncertain authenticity or incomplete condition record (AI Revenue).
14. A market-data outage, stale quote, abnormal spread or risk-limit breach occurs during paper simulation (Trading).

For each scenario record: objective, exact build/configuration, preconditions, inject, expected denial/degradation, observed result, evidence, incident timeline, recovery steps, residual risk, reviewer and sign-off. A tabletop discussion is not a technical test; label evidence accurately.

## 7. Findings severity and disposition

Use a common severity scale:
- **Critical:** unauthorized financial/external action, cross-company compromise, policy bypass, key/owner authority compromise, or inability to stop/revoke a dangerous action. Blocks all deployment.
- **High:** material authorization, data isolation, receiver idempotency, audit integrity or recovery weakness. Blocks affected production scope.
- **Moderate:** bounded weakness with compensating controls; requires owner-visible remediation plan and expiry.
- **Low:** limited impact or documentation/operability issue; tracked to closure.
- **Observation:** improvement recommendation without a demonstrated vulnerability.

Every finding must include affected versions, preconditions, impact, reproducibility/evidence, affected company, remediation owner, due condition, retest evidence and disposition. No finding may be closed solely because a model says it is fixed. Critical and High findings require independent retest. Risk acceptance cannot waive law, hard-deny rules, owner approval or the Trading risk veto.

## 8. Stage gates after PG-7

| Gate | Required evidence | Prohibited until passed |
|---|---|---|
| PG7-A — Design review | Exact artifact manifest, threat model, operation coverage and independent review report | Runtime wiring |
| PG7-B — Isolated implementation review | Code/config review, complete action-path inventory, static analysis and signed build provenance | External production connections |
| PG7-C — Synthetic conformance | Authorized test plan, negative/positive cases, concurrency and replay evidence | Customer, payment, wallet, broker or exchange actions |
| PG7-D — Resilience rehearsal | Revocation, clock, outage, restore, quarantine and ambiguous-outcome drills | Production dispatch |
| PG7-E — Company acceptance | Separate executive, CISO, risk (Trading) and owner decisions; unresolved risk register | Production activation |
| PG7-F — Narrow staged activation | Separately approved exact operation/resource scope, budget, rollback, monitoring and kill switch | Any scope expansion |
| PG7-G — Post-activation assurance | Monitoring, incident review, key rotation, access recertification and periodic independent reassessment | Unreviewed expansion or unattended autopilot |

Passing one company does not pass the other. Passing a technical gate does not authorize spending, publishing, customer contact, payments, live trading or any external action unless the relevant separate approval is granted.

## 9. Evidence register requirements

For every gate retain:
- company ID and environment;
- repository/commit/configuration/policy/schema digests;
- reviewer identity and independence declaration;
- test/rehearsal plan version and authorization record;
- raw result artifacts, logs and integrity digests;
- expected vs observed outcomes;
- failures, exceptions and unresolved risks;
- remediation and independent retest;
- executive, risk and owner decision references;
- expiry/revalidation trigger.

The OCC may display only allowlisted, company-published summaries and evidence references. It must not ingest raw credentials, private customer records, unrestricted task payloads or cross-company audit content.

## 10. Current status and non-claims

This plan is authored architecture, not a completed review. No independent security assessment, penetration test, code audit, conformance test, tabletop, disaster-recovery drill, key ceremony, deployment or production activation has occurred under PG-7. No control is certified, no vulnerability-free claim is made, and no exactly-once external execution guarantee is implied.

The existing 29-test M2 suite and PG conformance cases remain unexecuted. The user has not authorized test execution. No GitHub Actions, package installation, deployment, production connection, paid service, external customer action, wallet/broker/exchange connection or live trading is authorized.

## 11. Completion recommendation

Before any future implementation:
1. Freeze and reconcile the exact company-local policy/identity/approval/dispatch contracts.
2. Resolve the approval-schema mismatch and select one canonical company-local transaction/audit authority.
3. Complete operation-to-enforcement coverage and prove no bypass path exists.
4. Implement cryptographic trust, trusted time, revocation, receiver idempotency and durable recovery only after explicit authorization.
5. Obtain independent design review before connecting any runtime.
6. Obtain explicit authorization for a narrowly scoped synthetic test programme; never assume documentation work authorizes test execution.
7. Require separate company and owner acceptance before any staged external activation.

**Disposition:** PG-7 plan authored; every review, test, rehearsal and production gate remains NOT_RUN / NOT_AUTHORIZED.

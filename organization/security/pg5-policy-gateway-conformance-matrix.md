# PG-5 — Deterministic Policy Gateway Conformance Matrix

**Status:** Test specification and synthetic-vector design only; not executed.  
**Applies independently:** AI Revenue Company and Trading & Technology Company.  
**Source stages:** PG-1 operation taxonomies, PG-2 approval/transaction design, PG-3 trusted identity/owner authority, PG-4 enforcement/bypass map.  
**Execution rule:** No tests, CI, GitHub Actions, installs, network calls, database changes or runtime integrations without separate explicit user authorization.

## 1. Purpose

Define a common, auditable conformance suite for the company-local deterministic policy gateways. The suite is intended to prove that each company enforces its own identity, task, policy, approval, cost, data, dispatch, audit and recovery boundaries—and that failure, ambiguity or bypass attempts deny safely.

This matrix is a test design. A listed case is not evidence that the case has been implemented, run or passed.

## 2. Conformance principles

1. Two independent test profiles: run AI Revenue and Trading fixtures separately. Never reuse company identities, approval keys, task stores, audit streams or private fixtures across tenants.
2. Default deny: unknown operation, resource, policy version, identity claim, issuer, audience, data class or state is denied.
3. Hard denies precede approvals: owner approval cannot override a company hard deny, Trading live-execution prohibition, or protected control-plane boundary.
4. Exact scope: company, principal, session, task, operation, resource, recipient, amount/currency, policy version, nonce and expiry must match exactly where applicable.
5. Time and revocation are authoritative: model-supplied clocks, status claims or revocation assertions are never trusted.
6. Single-use is durable: approval and action identifiers cannot be consumed twice, including across concurrent workers, restart and failover.
7. No ambiguous resend: timeout after a possible external dispatch is outcome-unknown/quarantined until verified receiver evidence arrives.
8. Audit is part of authorization: inability to durably append required evidence denies consequential operations.
9. No cross-company authority: shared software or infrastructure does not create shared identity, memory, policy, approval or execution authority.
10. Evidence is revision-bound: every result records exact source commit, schema/policy version, fixture digest, test harness version and execution environment.

## 3. Test fixture contract

Synthetic fixtures should model only non-secret, non-production data:

- Company profile and company-specific operation taxonomy.
- Identity assertion: issuer, subject/agent ID, role, company, session, runtime, audience, issue/expiry, key ID, policy scope and revocation epoch.
- Task assignment: task ID, company, assigned principal, queue, operation/resource allowlist, data classes, status, expiry, task version, parent scope and resource budget.
- Policy snapshot: immutable version/digest, allowlist, hard-deny set, cost budget, emergency-stop state and policy freshness.
- Approval envelope: owner authority, company, principal/session, task, exact operation/resource/recipient, amount/currency where applicable, policy version, nonce, issue/expiry and one-use state.
- Cost quote/meter: provider, model/tool, units, price basis, currency, uncertainty and usage cap.
- Data reference: tenant, classification, source, timestamp, freshness, revision and permitted fields.
- Dispatch intent: canonical operation, immutable payload digest, destination, action ID, idempotency key, approval ID, recovery epoch and audit correlation.
- Receiver evidence: receiver identity, action digest, destination, outcome, timestamp, nonce, idempotency key and signature-verification result.
- Recovery state: quarantine status, incident ID, checkpoint, recovery epoch, revocation freshness and independent release decision.

No fixture may contain real secrets, credentials, customer data, wallet details or production endpoints.

## 4. Core conformance matrix

| ID | Domain | Scenario / mutation | Expected result |
|---|---|---|---|
| PG5-001 | Baseline | Valid company-local read-only task, identity, data scope, current policy and audit path | Conditional allow only for the exact read-only operation and resource |
| PG5-002 | Identity | Missing identity assertion | DENY |
| PG5-003 | Identity | Wrong company, issuer, audience, subject, role, session or runtime | DENY |
| PG5-004 | Identity | Expired, not-yet-valid, malformed or unsupported identity assertion | DENY |
| PG5-005 | Identity | Revoked identity or stale revocation epoch | DENY |
| PG5-006 | Identity | Signature invalid, unknown key ID or trust registry stale/unavailable | DENY |
| PG5-007 | Task | Missing task, wrong assignee, wrong company, expired task or inactive status | DENY |
| PG5-008 | Task | Task cancelled, reassigned or scope/version changed after permit issuance | DENY at final recheck |
| PG5-009 | Task | Child agent attempts authority wider than parent task | DENY |
| PG5-010 | Policy | Unknown operation ID, resource, data class or policy version | DENY |
| PG5-011 | Policy | Wildcard, prefix expansion or unregistered alias used to widen an allowlist | DENY |
| PG5-012 | Policy | Stale, rolled-back, unsigned or contradictory policy snapshot | DENY |
| PG5-013 | Policy | Emergency stop active, stale or unavailable | DENY |
| PG5-014 | Approval | Approval missing where required | DENY |
| PG5-015 | Approval | Approval is for a different company, principal, session, task or policy version | DENY |
| PG5-016 | Approval | Operation, resource, recipient, amount or currency differs from approved scope | DENY |
| PG5-017 | Approval | Approval expired, revoked, malformed or signed by non-owner authority | DENY |
| PG5-018 | Approval | Approval nonce/ID replayed or consumed concurrently by two workers | At most one atomic consume/reserve; all duplicates DENY |
| PG5-019 | Approval | Agent, executive agent or Research/OCC identity attempts to mint owner approval | DENY and security event |
| PG5-020 | Cost | Paid model/API/compute/hosting/subscription action under AI Revenue CAD $0 policy | DENY before billable dispatch |
| PG5-021 | Cost | Cost unknown, unmetered, currency ambiguous or provider quote stale | DENY under CAD $0; no paid fallback |
| PG5-022 | Cost | Usage cap reached or retry would exceed budget | DENY/STOP; no uncontrolled retry |
| PG5-023 | Data | Cross-company read/write, memory lookup, log, backup or publisher access | DENY and security event |
| PG5-024 | Data | Unclassified, stale, contradictory or provenance-missing source used for a consequential decision | DENY or quarantine per data policy |
| PG5-025 | Runtime | Direct connector/database/API call bypasses broker | Block at runtime/egress; record security event |
| PG5-026 | Runtime | Arbitrary URL, raw socket, shell, filesystem path or package install requested | DENY unless separately allowlisted and authorized |
| PG5-027 | Runtime | Swarm delegation attempts to launder a prohibited operation | DENY at final worker/action boundary |
| PG5-028 | Dispatch | Approval consumption, immutable intent, outbox reservation and audit append are not atomic | Transaction rollback; no sender invocation |
| PG5-029 | Dispatch | Duplicate action/idempotency key with changed payload digest | DENY and quarantine |
| PG5-030 | Dispatch | Sender timeout after possible remote effect | outcome_unknown; quarantine; never automatic resend |
| PG5-031 | Receiver | Receiver identity, destination, action digest, nonce or signature mismatch | Reject evidence; remain quarantined |
| PG5-032 | Receiver | Duplicate receiver callback/evidence | Idempotent evidence receipt; no duplicate state transition |
| PG5-033 | Audit | Audit store unavailable, append fails or checkpoint is stale | DENY consequential operation |
| PG5-034 | Audit | Audit event omits principal, task, policy version, decision reason or correlation ID | Reject event/deny action |
| PG5-035 | Recovery | Quarantine occurs before dispatch reservation | DENY |
| PG5-036 | Recovery | Quarantine races with dispatch reservation | Linearizable outcome: quarantine wins and denies, or committed intent is marked ambiguous and reconciled; never duplicate |
| PG5-037 | Recovery | Old recovery epoch attempts dispatch after release | DENY |
| PG5-038 | Recovery | Recovery assessor, owner release or dispatch authority is not independent | DENY release |
| PG5-039 | Resilience | Clock, revocation, policy, audit, task store or approval store unavailable | DENY consequential operation |
| PG5-040 | Resilience | Shared orchestrator/model provider/Main Hub unavailable | Company remains isolated; only independently permitted local/read-only fallback may continue |
| PG5-041 | Isolation | Company A token, task, approval, key, cache or publisher used in Company B | DENY and security event |
| PG5-042 | Input | Duplicate JSON keys, non-finite numbers, unsafe integer, oversized/deep payload or ambiguous canonicalization | Reject before policy evaluation |
| PG5-043 | Logging | Secret, credential or disallowed private data appears in audit/log/publication | Reject/redact; incident handling per policy |
| PG5-044 | Truth | Caller-supplied success label without signed receiver evidence | Remain unknown; no success transition |

## 5. Company-specific overlays

### AI Revenue profile

- AR.* operation IDs must resolve to the AI Revenue taxonomy and exact task capability.
- CAD $0 incremental spend is a hard policy input, not a warning. Paid inference, API calls, compute, storage, hosting, subscriptions and paid tools deny before dispatch.
- Customer contact, publication, contracts, proposals/quotes that create commitments, purchases, payments, deployment, permission changes and financial actions remain approval-class controlled.
- Owner approval cannot authorize an operation absent from the current taxonomy or policy allowlist.
- Client data, prospect research, invoices and company-private memory cannot cross into Trading or shared Research stores without an approved scoped publication.

### Trading & Technology profile

- TT.* operations resolve only to the Trading taxonomy and exact task capability.
- Research/backtest/paper modes remain distinct; a paper task cannot be upgraded by an agent or model into live execution.
- Live orders, wallet signing, exchange/broker access, deposits, transfers, withdrawals, and risk-limit/HALT/STOP modifications remain hard-denied. A valid owner approval must still fail these cases.
- Independent CRO/risk veto, market-data provenance and strategy evidence-stage requirements remain separate checks.
- Halal/Shafi'i flags are review metadata and cannot be auto-cleared by model confidence or policy evaluation.

## 6. Test execution protocol (future, separately authorized)

When and only when the owner explicitly authorizes a specific test run:

1. Confirm exact repository, branch, commit and file hashes.
2. Confirm offline mode, synthetic fixtures, no secrets, no network, no production DB and no external side effects.
3. Review the test command and expected resource use before execution.
4. Run one bounded suite; do not invoke GitHub Actions unless separately authorized.
5. Preserve stdout/stderr, exit code, environment/runtime version, fixture digests and exact source revision.
6. Distinguish authored, collected, executed, passed, failed, skipped and not-applicable cases.
7. Independently review failures and false-positive risks.
8. Do not convert a test pass into production readiness or permission to deploy.
9. Obtain separate approval before any integration, migration, key generation, network connection or deployment.

No tests have been run as part of this document. No test case is marked PASS.

## 7. Evidence record schema (conceptual)

Every executed result should capture:
- run ID and timestamp from trusted test environment;
- company profile and tenant identifier;
- repository, branch, commit SHA and source-file digests;
- policy, taxonomy and schema versions/digests;
- harness version and dependency inventory;
- test case ID, fixture digest and mutation;
- expected decision and actual decision;
- reason codes and enforcement point;
- audit event/checkpoint references;
- stdout/stderr and exit code;
- reviewer, disposition and unresolved limitations.

Evidence records must be append-only and company-local. A synthetic test result cannot be published as a live operational status.

## 8. Release gates

PG-5 is complete only when:
- Every matrix row has an implemented deterministic assertion and fixture.
- Positive cases prove only explicitly allowed, bounded behaviour.
- Negative cases prove denial at the final enforcement boundary, not merely an upstream UI check.
- Concurrency/race, restart, replay, revocation, clock skew, outage, restore and receiver ambiguity cases are exercised.
- Company isolation tests run independently for both companies.
- Independent security review accepts the test design and results.
- The authoritative production-readiness evidence register is updated with exact revision-bound evidence.

Even a complete PG-5 suite does not authorize production. PG-6 durable-store/receiver proof and PG-7 independent review/rehearsal remain separate gates.

## 9. Current disposition

- PG-5 conformance matrix authored.
- Synthetic fixture schema and executable test harness are not yet implemented as a complete PG-5 suite.
- Existing M2 OCC fixtures/tests are a separate workstream and are not evidence that this policy-gateway matrix passed.
- No tests, GitHub Actions, installations, database changes, keys, network connections, deployments or live actions were performed.
- All PG-5 cases remain NOT_RUN; production enforcement remains NOT_IMPLEMENTED / NOT_VERIFIED.

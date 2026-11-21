# Deterministic Policy Gateway — Integration & Gap-Closure Plan

**Status:** Architecture consolidation and implementation sequence; no deployment or enforcement claimed.  
**Applies to:** AI Revenue Company and Trading & Technology Company independently.  
**Canonical baseline:** Existing company-scoped policy, identity, approval, audit, control-store, recovery and dispatch contracts.  
**Operating rule:** Default deny; fail closed; CAD $0 incremental spend; no tests, installs, deployments, Actions or external connections without separate authorization.

## 1. Decision: consolidate existing controls; do not create a second policy engine

The repositories already contain substantial, overlapping reference material. The correct next step is to integrate and reconcile the existing contracts—not to introduce a parallel policy architecture.

Existing baseline to preserve:
- `security/policy-gateway-production-contract.md`: deterministic decision boundary, mandatory checks, fail-closed semantics, final recheck and production requirements.
- `security/deterministic-policy-enforcement-interface.json`: request/decision contracts, enforcement points, zero-spend default, company isolation, approvals, revocation and emergency-stop requirements.
- `security/policy_gateway_reference.py`, `reference_policy_engine.py` and associated acceptance/test-vector files: offline reference implementations only.
- `security/identity-lifecycle-production-requirements.md` and `identity_lifecycle_reference.py`: separate identity issuer, signed claims, company-specific trust roots, revocation and key lifecycle requirements.
- `security/durable-approval-audit-contract.md`, `owner-approval-repository-schema-contract.md`, `owner-approval-postgres-adapter-contract.md` and associated schema/reference files: approval scope, durable consumption and audit transaction design.
- `security/trusted-control-plane-facade-reference-contract.md`: trusted dependency binding and company/task scope resolution; known mismatch between façade's full approval scope and the current SQLite approval schema must be resolved before wiring.
- `security/linearizable-control-store-contract.md`, `transactional-dispatch-recovery-contract.md` and `outbox-dispatch-safety-contract.md`: authorization linearization, quarantine epochs, ambiguity handling, transactional intent/audit and receiver idempotency.
- `security/recovery-authority-and-quarantine-contract.md`, `recovery-authority-to-dispatch-boundary-enforcement-contract.md` and evidence reconciliation contracts: independent recovery authority, quarantine and evidence-based release.
- `security/production-readiness-evidence-register.md`: authoritative evidence gates; documents and test definitions are not proof of execution.

AI Revenue uses the `organization/security/` paths; Trading & Technology uses the corresponding `docs/security/` paths and retains its own risk authority and hard-deny set. These company-specific copies must not be merged into a shared authority or shared database.

## 2. Target authorization path

A consequential operation must pass through this ordered chain. A missing, stale, contradictory, unauthenticated or unavailable dependency denies the operation.

1. **Trusted identity:** company-specific issuer verifies immutable agent, role, runtime, session, audience, expiry, status and revocation. Model-supplied identity claims are untrusted.
2. **Trusted task assignment:** scheduler confirms the task is active, assigned to this principal, within scope and not expired/cancelled.
3. **Policy evaluation:** deterministic company-local policy checks operation, resource, data class, scope, budget/cost ceiling, policy version, emergency stop and company boundary.
4. **Hard-deny and separation-of-duty checks:** protected control-plane operations and prohibited actions are denied before considering approvals. Trading hard denies cannot be overridden by owner approval.
5. **Owner approval:** where allowed and required, verify a separately authenticated owner approval bound to exact company, principal/session, task, operation, resource, recipient, amount/currency, policy version, nonce and short expiry.
6. **Durable one-use consumption:** atomically consume approval, record immutable action intent, idempotency key and audit event. A validity check alone is not consumption.
7. **Final enforcement recheck:** scheduler/runtime/tool/data/cost/external-action gateway revalidates grant, revocation, policy version, emergency-stop state and scope immediately before the protected operation.
8. **Transactional dispatch boundary:** outbox intent, approval consumption, dispatch state and audit must share a durable transaction. The external sender runs only after commit.
9. **Receiver-side protection:** receiver enforces stable idempotency, immutable action digest, recipient/account binding, amount/currency, company identity and recovery epoch; signed fresh outcome evidence is required for reconciliation.
10. **Audit and recovery:** allow and deny decisions, approval lifecycle, action lifecycle, quarantine, recovery and evidence reconciliation are attributable and tamper-evident. Audit failure blocks consequential operations.

The policy gateway returns a decision; it does not execute actions, mint owner approvals, issue identities, control funds or set company risk appetite.

## 3. Company-local policy profiles

### AI Revenue

- Own policy namespace, issuer, approval authority, task scheduler, budget, audit stream and recovery authority.
- CAD $0 spend by default. Billable inference, compute, APIs, hosting, subscriptions and paid services deny before dispatch unless the owner changes the budget policy and approves the exact spend.
- Publication, customer contact, contract, purchase, account/permission change, deployment and financial actions require their specific approval class.
- Agent/manager/model consensus is not owner approval.
- Customer and company-private data remain in the AI Revenue tenant.

### Trading & Technology

- Own policy namespace, issuer, approval authority, scheduler, budget, audit stream, independent CRO/risk authority and recovery authority.
- Research and paper simulation are the default operating modes.
- Live orders, wallet signing, funds transfers, withdrawals, broker/exchange orders and HALT/STOP/risk-limit modifications remain hard-denied by the policy gateway and control-store boundary. Owner approval cannot override these hard denies.
- Risk authority retains independent veto and cannot be replaced by a model, Research & Intelligence, OCC or shared orchestration.
- Market-data provenance failure, stale data, risk-service outage, identity failure, policy uncertainty or audit failure deny consequential operations.
- Shafi'i/halal issue flags remain a separate review dimension; no policy engine or model issues religious rulings.

## 4. Known design gaps to close before any integration

1. **Cryptographic trust is still a design requirement.** Existing HMAC and injected verifier objects are synthetic reference patterns; production needs reviewed asymmetric signatures, separated company keys, protected key custody, rotation, revocation and issuer/audience pinning.
2. **Approval schema mismatch.** The trusted façade requires complete scope fields that the current SQLite approval schema does not persist. Design a versioned migration and atomic repository transaction before connecting the façade.
3. **Owner endpoint authority.** Approval issuance must be callable only by a separately authenticated owner-authority identity; agents must not reach an approval-minting endpoint.
4. **Durable distributed consumption.** SQLite demonstrates local serialization only. A production store needs unique IDs/nonces, appropriate isolation/locking, failover, backup/PITR and tested restore.
5. **Enforcement coverage.** Prove there is no bypass around scheduler, runtime/tool, data, cost, and external-action/outbox gateways. Network and process boundaries must enforce the same policy.
6. **Emergency-stop and revocation freshness.** Define bounded propagation objectives and deny on unavailable, stale or contradictory state. Revoke outstanding grants and cancel queued/running work safely.
7. **Clock trust.** Define authenticated time, skew/uncertainty handling and expiry semantics; agents cannot supply trusted time.
8. **Receiver-side idempotency and epoch fencing.** Local dispatch state cannot guarantee exactly-once remote effects. No automatic resend after an ambiguous dispatch.
9. **Audit integrity.** Hash chains alone do not prevent privileged rewrite. Add separately protected signing/checkpoint authority and independently stored immutable/WORM exports.
10. **Recovery separation.** Recovery assessor, owner release approval and dispatch authority must be independent. Recheck epoch, revocations, checkpoint and incident state under the authoritative transaction.
11. **Cost and resource controls.** Every model, tool, compute and external action must be metered and denied at the cost boundary when over budget or unknown.
12. **Independent security review and adversarial evidence.** Threat model, race/fault injection, bypass tests, company isolation, key compromise, replay, revocation, outage, restore and recovery exercises remain outstanding.

## 5. Implementation sequence — small, gated slices

| Stage | Deliverable | Acceptance evidence | Gate |
|---|---|---|---|
| PG-0 | Reconcile existing contracts, schemas, code and acceptance vectors | Path/SHA inventory; conflict and gap register; no duplicate policy engine | Documentation-only |
| PG-1 | Canonical company-specific operation taxonomy and policy profiles | Explicit allowlists, hard denies, cost-zero defaults, protected-control-plane list | Owner review before policy changes |
| PG-2 | Full-scope approval schema and durable repository design | Field-by-field compatibility matrix; unique nonce/approval constraints; atomic audit/consumption design | No migration or DB execution yet |
| PG-3 | Trusted identity and approval authority design | Asymmetric key separation, issuer/audience, rotation/revocation, owner-only endpoint model | No keys or credentials created |
| PG-4 | Company-local policy gateway integration design | Scheduler, runtime, data, cost and outbox enforcement map; bypass threat model | No network/runtime connection |
| PG-5 | Synthetic offline conformance vectors | Positive and negative cases, fail-closed outage/replay/expiry/scope/cost tests | Test execution requires explicit user authorization |
| PG-6 | Durable store and receiver contracts | Concurrency, idempotency, epoch fencing, audit and restore evidence | No production database or receiver |
| PG-7 | Independent review and rehearsal | Security review, incident/recovery drills, owner acceptance and evidence register closure | Deployment remains separately gated |

Parallel work is allowed for PG-1 through PG-4 where documents are independent. Schema migration, runtime wiring and test execution are serialized behind design review and explicit authorization.

## 6. Required conformance cases

At minimum, later authorized testing must prove:
- wrong company, role, session, task, audience or runtime identity denies;
- expired, revoked, replayed or malformed identity/approval denies;
- task reassignment, cancellation or scope change invalidates prior grant;
- unknown operation/resource, wildcard permission or stale policy denies;
- CAD $0 cost policy denies paid inference, compute, API, hosting and subscription actions;
- approval bound to a different amount, currency, recipient, resource, task or company denies;
- duplicate nonce, approval ID, action ID or idempotency key cannot create duplicate dispatch;
- policy, audit, clock, revocation, emergency-stop or repository outage fails closed;
- quarantine-before-dispatch denies; dispatch-before-quarantine becomes outcome_unknown and is never automatically resent;
- old recovery epochs cannot dispatch after release;
- Trading hard-deny actions remain denied even with a valid owner approval;
- cross-company storage, memory, tool, log, backup and publisher access denies;
- direct tool/network path bypass is blocked and recorded.

Authored vectors and prototype tests are not execution evidence. The user has not authorized test execution; no test result is claimed here.

## 7. Operating and approval boundaries

- No installation, package changes, paid API use, subscriptions, purchases, credentials, key generation, deployment, network integration, GitHub Actions run, merge, production database, customer contact, publishing, wallet/broker/exchange connection or live trading is authorized by this plan.
- Existing code and contracts remain reference/prototype material until exact-revision validation, independent review and authorized deployment.
- No model, agent, Paperclip, Ruflo, OCC or Research & Intelligence can approve its own access, change policy, create owner approval or override company risk.
- AI Revenue and Trading & Technology retain separate control planes, executives, finances, private memory, approval authorities, audit and recovery.
- Main Hub/OCC receives only read-only allowlisted summaries; it cannot authorize or execute.
- Research & Intelligence may recommend and publish scoped findings; it cannot approve company operations.
- Each company must continue safely if the other company or shared infrastructure is unavailable.

**Current disposition:** substantial design/reference foundation exists; policy gateway is not production-enforced, identity and approval cryptography are not implemented, current approval schema needs reconciliation, durable multi-node controls and receiver enforcement are absent, and all production-readiness gates remain open.

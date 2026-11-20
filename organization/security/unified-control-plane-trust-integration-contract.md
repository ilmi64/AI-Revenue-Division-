# Unified control-plane trust integration contract

Status: required integration architecture; current SQLite reference is not a production authorization service.

## Finding

The unified linearizable control-store reference provides a useful single-database transaction/state-machine demonstration, but several public methods accept authority-bearing inputs from their caller. The reference must not be exposed directly to agent runtimes, orchestrators, workers, tools or user-facing clients.

Observed reference limitations:
- `issue_approval` inserts approval rows from caller-supplied fields; it does not authenticate an owner signature or restrict issuance to a dedicated approval issuer.
- `enqueue` accepts caller-supplied company, stream, approval ID, destination-bearing intent and timestamps; it does not authenticate a scheduler or validate a signed task envelope.
- `authorize_and_start` accepts caller-supplied company, agent, task, operation, resource, policy version and timestamp; it does not itself verify a signed principal, current task assignment, trusted clock, current policy decision or current revocation state.
- `release_stream` accepts verifier objects as method arguments. Production callers must not be able to substitute trust roots or verifier implementations.
- The reference's database connection is directly available on the object. Production agents must never receive direct database access or credentials.
- Hard-deny checks are present in the reference, but do not replace authenticated identity, fresh policy, approval provenance or final-boundary enforcement.

These are known prototype limitations. The reference remains offline-only and must never be connected to real accounts, external senders, payments, wallets, brokers or exchanges.

## Required production architecture: narrow trusted control-plane service

Expose a service façade, not the SQLite/database object. Its trust roots, verifier implementations, clock, policy client, company mapping, revocation source and database credentials are injected only at trusted service startup from protected configuration. Requesting agents cannot supply or replace them.

### 1. Principal and task resolution
- Accept an authenticated transport/session context and signed identity assertion.
- Verify issuer, signature, audience, company, agent, role, runtime/session, issued-at/expiry, revocation and identity epoch.
- Resolve task assignment and immutable task envelope from the trusted scheduler/task store; never trust caller-provided company/agent/task fields as authority.
- Use a trusted clock service. Caller timestamps are correlation metadata only and cannot decide expiry, freshness or ordering.

### 2. Approval issuance
- Provide a separate owner-approval endpoint accessible only to the owner approval authority.
- Verify owner signature and exact scope before inserting approval data.
- Bind company, stream, principal, session, task, operation, resource/recipient, immutable intent digest where available, amount, currency, policy version, expiry, audience, nonce and single-use semantics.
- Do not expose the raw `issue_approval` method to company agents or general service clients.
- Approval issuance, revocation and consumption must produce auditable events with trusted time.

### 3. Trusted enqueue
- Only the trusted scheduler may enqueue.
- Resolve the signed task envelope and principal from trusted stores.
- Derive company, stream, approval reference, destination, amount/currency, operation, resource and enqueue recovery epoch from authoritative records.
- Canonicalize and persist an immutable intent digest. Agents may submit a proposal but cannot select or rewrite authoritative identity, company, stream, receiver, approval or epoch fields.
- Duplicate idempotency key with changed intent is a hard conflict.

### 4. Final dispatch authorization
- The dispatcher submits action ID and authenticated worker identity, not free-form authority claims.
- Resolve action, intent digest, task and principal from trusted stores.
- Obtain a fresh deterministic policy decision from the policy authority; bind decision to exact action digest, company/stream, recipient, amount/currency, task, policy version, recovery epoch and expiry.
- Recheck emergency stop, revocation, stream status/epoch, approval scope and hard-deny set in the same transaction boundary as approval consumption, dispatch_started transition and audit append.
- The policy service cannot override Trading hard denies. Owner approval cannot override them either.
- The authorization transaction's commit is the dispatch linearization point. Sender invocation occurs only after commit, with stable receiver idempotency key.
- If any trust dependency is unavailable, stale, ambiguous or inconsistent, fail closed.

### 5. Recovery release
- Owner and assessor verifier implementations, issuer registries and trust roots are bound at trusted service startup.
- No request may pass verifier objects, trust roots or callbacks.
- Verify signed owner approval and independent signed recovery assessment against exact company, stream, incident, checkpoint digest, audience, freshness and one-time nonce.
- Recheck quarantine state, epoch, unknown actions, revocations, audit/checkpoint status and emergency stop under the authoritative transaction before consuming approval and activating.
- A release increments the recovery epoch. It never revives old tasks, leases, approvals or dispatch permits.

### 6. Receiver evidence
- Sender-result labels such as accepted/rejected are not authoritative proof.
- Only a bound receiver-evidence verifier can transition remote outcomes.
- Bind signed evidence to issuer, audience, company, action ID, immutable intent digest, receiver account, idempotency key, operation, amount/currency, recovery epoch, outcome, timestamp and nonce.
- Receipt, replay consumption, state transition and audit append are atomic.
- Unknown, stale, replayed, mismatched or unverifiable results remain unknown/quarantined and are never auto-retried without trusted reconciliation.

### 7. Isolation and enforcement
- Separate service identities, databases/schemas, keys, policy namespaces, audit streams and recovery authorities for each company.
- OCC receives health summaries only unless the owner approves a scoped, time-limited interface.
- Runtime agents, Paperclip, Ruflo and model runtimes have no direct SQL/database credentials and cannot access trust roots.
- Enforce at scheduler, runtime/tool gateway, policy gateway, data gateway, cost gateway, dispatch/outbox worker and recovery boundary. Network segmentation must prevent bypass.
- The company ID is derived from authenticated identity and authoritative assignment, not an arbitrary caller field.
- Trading live orders, wallet signing, funds transfers, broker/exchange orders, withdrawals and risk-control modification remain hard-denied.

## Integration invariants

1. No component may strengthen its own authority by supplying an identity, approval, verifier, clock, policy decision or company identifier.
2. All authority-bearing records are traceable to a trusted issuer and exact scope.
3. One authoritative company-stream transaction domain serializes quarantine, release and dispatch authorization.
4. Every decision is bound to the same immutable action-intent digest and recovery epoch.
5. Owner approval is necessary where required but never sufficient to bypass policy or hard denies.
6. No success state is inferred from an unverified sender response.
7. Fail-closed behaviour is consistent across every boundary; no fallback path bypasses a failed dependency.
8. Cross-company access is denied unless a separate owner-approved scoped interface explicitly authorizes it.
9. Production service APIs do not expose raw database methods or caller-selectable verifier dependencies.
10. A passing offline prototype test is not evidence of cryptographic, distributed, deployment or operational readiness.

## Implementation sequence and release gates

A. Define authenticated request/response schemas and trusted service interfaces.
B. Implement identity/task resolution, trusted clock and revocation.
C. Implement owner-only approval issuance and durable single-use consumption.
D. Implement trusted scheduler enqueue and immutable intent digest.
E. Implement final dispatch policy recheck and same-transaction recovery/approval/audit authorization.
F. Bind recovery verifiers at startup and remove request-level verifier injection.
G. Integrate signed receiver evidence and atomic reconciliation.
H. Add company isolation, least-privilege DB roles, network bypass prevention and independent audit/checkpoint controls.
I. Run offline unit, integration, concurrency, fault-injection and restore tests; then independent security review and non-production receiver rehearsal.

No production deployment, live trading, external dispatch, account connection, paid service, merge or workflow run is authorized by this contract.

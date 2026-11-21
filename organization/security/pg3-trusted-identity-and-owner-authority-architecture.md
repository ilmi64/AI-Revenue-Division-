# PG-3 — Trusted Identity, Owner Authority, Time and Revocation Architecture

**Status:** Architecture design only; no keys, credentials, services, accounts or network connections created.  
**Applies independently:** AI Revenue and Trading & Technology.  
**Purpose:** Define the trust authorities and signed evidence needed before any company-local policy gateway can safely rely on identities, approvals, time, revocation or receiver outcomes.

## 1. Core decision: separate authorities, separate keys, separate companies

A model, agent, orchestrator, task payload or repository row is never a root of trust. The following are distinct trust authorities:

1. **Company identity issuer** — creates and revokes short-lived agent/service identities.
2. **Owner approval authority** — authenticates the human owner and signs exact, single-use approvals; not callable by agents.
3. **Policy authority** — evaluates current company policy and returns a short-lived, request-bound decision; it cannot issue identities or owner approvals.
4. **Trusted scheduler/task authority** — assigns immutable tasks and resolves current assignment/scope from its own authoritative store.
5. **Trusted time service** — supplies authenticated time/health to verifiers and control transactions.
6. **Revocation/emergency-stop authority** — publishes monotonic versions/epochs and invalidates outstanding credentials and permits.
7. **Dispatch authority** — performs final checks and atomically reserves/consumes an approved action; no model or agent has database access.
8. **Receiver evidence authority** — verifies signed remote outcome evidence; a caller-provided success/failure label is not evidence.
9. **Audit checkpoint authority** — signs audit checkpoints and anchors them outside the mutable operational database.

These roles must be administered separately with least privilege and independent audit. One service or signing key must not silently perform multiple trust roles for convenience.

## 2. Company trust domains

AI Revenue and Trading & Technology each require independent:

- issuer identifier and audience namespace;
- identity signing key set and trust registry;
- owner approval signer registry and keys;
- policy namespace and policy-signing key;
- task scheduler identity and authoritative task store;
- revocation and emergency-stop state;
- replay/nonce and one-time consumption store;
- audit stream and checkpoint signing key;
- receiver trust configuration and service credentials;
- database, service identities, secrets and recovery authority.

No identity, owner approval, nonce, permit, trust-root, signing key, private task record or company audit stream is portable across the company boundary. Shared infrastructure may host isolated services only if independent security review proves tenant separation, key separation, access enforcement and outage independence. A dedicated company service/database is preferred.

## 3. Signed identity assertion

### Required claims

A company identity assertion must bind:

- issuer (`iss`) and key identifier (`kid`);
- audience (`aud`) for one exact service boundary;
- immutable `agent_id`, `company_id`, `role_id`, runtime/model identity and capability profile;
- session ID, credential ID and identity epoch;
- issued-at, not-before and expiry using trusted time;
- lifecycle status and policy version;
- task correlation where available, without treating a task ID as proof of assignment.

The trusted scheduler independently resolves the task and confirms company, principal assignment, stream, allowed canonical operations/resources, task status and expiry. A child task cannot widen parent company, tool, data, cost, recipient or expiry scope.

### Verification

- Verify signature against a pinned issuer/key registry and explicit algorithm allowlist.
- Enforce exact issuer, audience, company and key status.
- Check not-before/issued-at/expiry, bounded clock uncertainty, credential status and identity epoch.
- Check current revocation state and task assignment.
- Reject unknown claims only according to a versioned schema; reject missing mandatory claims.
- Never accept agent-supplied company, agent, role, runtime, session, task assignment, policy version or `now` as authoritative.

## 4. Owner approval object and owner-only endpoint

### Exact approval binding

A signed approval must bind:

- approval ID, company, stream and audience;
- authenticated owner ID and signer key ID;
- principal agent, session and task;
- canonical operation ID and exact resource;
- recipient/destination account where relevant;
- immutable intent/payload digest where relevant;
- amount in integer minor units and ISO currency where relevant;
- policy version and applicable risk-review reference;
- issued-at, expiry, unique nonce and explicit single-use flag;
- canonical scope digest and signed-payload digest.

No floating-point money. Amount and currency must be paired. A material change to operation, resource, recipient, content digest, amount/currency, company, task, policy version or expiry requires a new approval.

### Owner endpoint boundary

- The approval API is exposed only to an authenticated owner-authority service identity and a separately verified owner session.
- Agents, model runtimes, Paperclip, Ruflo, task workers and shared orchestrators cannot call the approval-minting endpoint or write approval records.
- A valid signed document is not enough if the caller is unauthorized to submit it.
- The verifier checks owner registry membership, signer key status, signature, issuer/audience, canonical payload, scope, expiry and single-use.
- Repository persistence occurs only after successful verification; the repository is not a signature verifier.
- The approval receipt binds approval ID, company, scope digest, expiry and durable audit event ID.

### Company-specific restrictions

- **AI Revenue:** current CAD $0 policy continues to hard-deny positive or unknown-cost operations. The approval architecture does not itself change the budget. External publication, customer contact, purchase, payment, contract or production actions remain separately gated.
- **Trading & Technology:** live orders, wallet signing, deposits, transfers, withdrawals, broker/exchange orders and risk-control changes are hard-denied before approval lookup. No owner signature overrides the independent risk hard-deny set.

## 5. Cryptographic profile and key lifecycle

- Use a reviewed asymmetric signature profile (Ed25519 or a carefully configured P-256 profile are candidates), maintained cryptographic libraries and explicit algorithm allowlists.
- Do not use a shared HMAC secret as a production signing authority. Existing HMAC and injected verifier objects remain test/reference patterns only.
- Keep private keys in a managed KMS/HSM or equivalent isolated signing service; do not create, export or store private keys in source code, prompts, agent memory, task payloads, ordinary environment dumps or logs.
- Use separate key sets for each company and each authority: identity, owner approval, policy decision, audit checkpoint and receiver evidence.
- Pin key IDs, issuer, audience and allowed algorithms in verifier trust configuration.
- Define key activation, overlap, rotation, revocation, compromise response, backup and recovery before implementation.
- Define canonical serialization and domain separation. RFC 8785 JSON Canonicalization is a candidate, with explicit rejection of duplicate keys, non-finite numbers, unsafe integers, ambiguous numeric forms and unrecognized schema versions.
- Sign a versioned envelope that includes purpose/type so a token for one authority cannot be replayed as another.

No key generation or KMS/HSM setup is authorized by this document.

## 6. Trusted time and expiry

- Verifiers and transaction services obtain time from a trusted clock dependency, never from request fields, model output or agent tools.
- Define a bounded maximum clock uncertainty and permitted skew per service; if health is unknown, time moves backwards, or uncertainty exceeds the bound, fail closed.
- Record trusted observation time and relevant source timestamps separately.
- Enforce issued-at, not-before, expiry and maximum token lifetime. Expiry is checked at issuance, approval persistence, final dispatch authorization and receiver evidence acceptance.
- Use monotonic process time for measuring local elapsed intervals, but not as a substitute for authenticated wall-clock time across machines.
- Expired, future-dated, stale or contradictory evidence is rejected or quarantined.

## 7. Revocation, emergency stop and epochs

- Every identity, signing key, owner approval, policy version and dispatch permit has a revocation/status source.
- Revocation state is versioned monotonically and has a defined freshness SLO. A verifier cannot rely on an indefinitely cached status.
- A revocation outage or stale snapshot denies consequential operations.
- Revocation invalidates outstanding grants and permits at all enforcement points; queued tasks are cancelled or quarantined and running work receives bounded cancellation.
- Emergency stop is independently controlled by owner/security; Trading additionally retains its independent risk authority and HALT/STOP control.
- Quarantine and recovery use monotonically increasing epochs. An action authorized under an older epoch cannot be newly dispatched after recovery release.
- Revocation and epoch state are rechecked inside the same authoritative transaction that consumes approval and reserves dispatch.

## 8. Policy permit and final dispatch

A policy allow is a short-lived decision, not an external action. It must bind one request digest, company, principal/session, task, operation, resource, policy version, scope digest, expiry and single-use nonce. The maximum validity is bounded (the existing interface proposes 30 seconds) and must be revalidated at the final enforcement boundary.

The dispatch authority resolves action intent from trusted storage, not from model-supplied payloads. It applies hard denies, task assignment, policy, cost, revocation, emergency-stop and recovery-epoch checks; then atomically consumes the approval, reserves the action/outbox, and appends audit. No direct sender or database path is exposed to the model runtime.

## 9. Receiver-result evidence

A receiver response must be authenticated and bind issuer, audience, company, action ID, immutable intent digest, receiver account, idempotency key, operation, recipient, amount/currency, recovery epoch, outcome, trusted timestamp and unique evidence ID/nonce.

The verifier rejects mismatched, stale, future-dated, replayed or invalidly signed results. Evidence receipt, replay consumption, action state transition and audit append commit atomically. A timeout, unverified response or ambiguous outcome remains `outcome_unknown`; never convert a caller-provided label into success and never automatically resend a non-idempotent action.

## 10. Audit checkpoint authority

The operational database's hash chain is tamper-evident, not immutable against a privileged administrator. A separate checkpoint signer must periodically sign stream ID, sequence, head hash, schema/canonicalization version and timestamp. Store checkpoints in independently administered immutable/WORM storage or an equivalent external anchor. Keep checkpoint keys separate from identity, owner approval and policy keys. Restore and reconciliation must verify both local chain and external anchor.

## 11. Failure behaviour and monitoring

Fail closed on issuer, verifier, task scheduler, owner registry, clock, revocation, policy, risk service, replay store, database, audit or receiver-verification uncertainty. Monitor and retain evidence for forged claims, cross-company attempts, invalid audience, key rotation/revocation, replay, stale clock, task reassignment, approval mismatch, policy rollback, direct database access, ambiguous receiver outcomes and privileged trust configuration changes.

## 12. Acceptance evidence and non-authorization

Before any future production use, require independent cryptographic review, key-custody review, threat model, service/database privilege review, company-isolation adversarial tests, replay/concurrency/fault tests, clock rollback and revocation-outage tests, owner-endpoint authorization tests, receiver-evidence verification, checkpoint restore and recovery rehearsal, and owner acceptance.

The companion acceptance-test specification remains unexecuted. This document does not authorize tests, key generation, account connections, network access, migrations, paid services, deployments, external financial actions or live trading.

**Disposition:** PG-3 trust-authority architecture documented for review. Current reference verifiers, HMAC patterns, caller-supplied timestamps and receiver-result labels are not production trust controls.

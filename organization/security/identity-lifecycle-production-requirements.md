# Identity, approval and authorization lifecycle — production requirements

**Status:** Design requirements only. The adjacent Python module is a synthetic HMAC reference, not a production identity provider.

## Trust boundaries

- A trusted control-plane identity issuer creates agent identities. Agents, models, prompts, task descriptions and orchestration platforms cannot issue or elevate identities.
- The owner approval authority is separate from the identity issuer and from every agent runtime.
- Each company has a distinct issuer namespace, signing authority, key set, revocation state and audit stream. A Trading identity is never accepted as an AI Revenue identity, or vice versa.
- Paperclip, Ruflo and model runtimes are requesters/consumers, not roots of trust.
- A policy decision is not permission to execute by itself. Every scheduler, tool, data, cost and external-action gateway must independently verify the authorization grant and enforce its scope.

## Required identity claims

Production identity credentials must bind: immutable agent ID; company ID; role; runtime/model identity; capability profile; issuer and key ID; audience; issued-at, not-before and expiry; session ID; task correlation; credential ID; lifecycle status; and policy version. Credentials must be short-lived and audience-bound. Agent-supplied claims are never authoritative.

## Cryptographic design

- Use a reviewed asymmetric signature standard and maintained implementation (for example Ed25519 or an appropriately configured P-256 profile), with algorithm allowlists and key IDs pinned by verifier policy.
- Keep private signing keys in a managed KMS/HSM or equivalent isolated signer. No private keys in repositories, prompts, agent memory, environment dumps, task payloads or ordinary application logs.
- Separate keys for identity issuance, owner approvals, audit signing and any service-to-service authentication. Separate company keys at minimum.
- Define canonical serialization, domain separation, key rotation, overlap windows, emergency key revocation, backup and recovery before deployment.
- The HMAC helper in the reference module is intentionally a test fixture pattern only. A shared HMAC secret distributed to multiple verifiers would allow any holder to mint credentials and is not an acceptable production authority design.

## Owner approval requirements

An approval must be a separate signed object bound to exactly one company, task, action/operation, resource, recipient where relevant, amount/currency where relevant, expiry, nonce, policy version and approver identity. High-impact financial, publication, account-permission and deployment actions require explicit owner approval. Approval cannot be inferred from an agent's claim, a model's confidence, a manager-agent's instruction or consensus among agents.

## Replay, revocation and atomic consumption

- Authorization grants and approvals must carry unique identifiers/nonces and short expiries.
- Every enforcement point must perform an atomic, durable, shared replay check before the protected side effect. A process-local set is insufficient across restarts or multiple workers.
- Approval consumption and action-intent recording must be transactionally coordinated or use a safe idempotency/outbox design. A verification function that only says "valid" must not be mistaken for consumption.
- Revocation must propagate to all enforcement points within a defined service-level objective; stale or unavailable revocation state fails closed for consequential actions.
- Emergency stop and task cancellation must invalidate outstanding grants, not merely prevent new task creation.

## Audit and incident requirements

Record issuer, key ID, credential ID, approver, exact scope digest, policy version, decision, denial reason, replay/consumption result, gateway, timestamp and correlation IDs in append-only tamper-evident storage. Never log private keys or reusable bearer credentials. Test key compromise, revocation propagation, clock skew, issuer outage, audit sink outage, replay races, duplicate delivery and recovery.

## Deployment gate

No production use until independent security review, threat modelling, key custody design, cryptographic profile review, durable atomic replay/consumption, revocation and emergency-stop integration, company-isolation testing, gateway enforcement, audit/recovery drills and owner acceptance are complete. Until then: synthetic data, offline tests, no secrets, no network and no real actions.

# Durable owner-approval repository schema contract

Status: proposed PostgreSQL DDL; not applied, migrated, executed or security-reviewed.

The schema provides a full-scope durable record for the trusted façade's approval repository adapter. It covers company/stream, owner, principal, session, task, operation, resource, recipient, optional immutable intent digest, amount in integer minor units, currency, policy version, audience, nonce, single-use semantics, signer key reference, signed-payload/signature digests, the original signed envelope, expiry, revocation, one-time consumption and a per-company/stream audit chain.

## Required repository behaviour
- Accept only claims already verified by the trusted owner-approval authority. The repository is not a signature verifier.
- Enforce unique approval ID and company/nonce.
- Persist approval issuance and its audit event in one transaction.
- Consume an approval once, bound to one action ID, using row locking and unique constraints.
- Persist consumption and audit event in one transaction.
- Revoke and append its audit event atomically.
- Distinguish genuine duplicate consumption from unrelated integrity/audit failures; all ambiguous storage failures fail closed.
- Return a receipt containing approval ID, company ID, scope digest, expiry and audit event ID.

## Important integration boundary
Approval consumption must ultimately share the authoritative transaction domain with dispatch authorization, recovery-stream epoch checks, action state transition and audit append. This standalone schema illustrates the repository contract but does not, by itself, establish that cross-table transaction or policy boundary. The eventual production schema must be integrated into the unified company control store, with a fixed lock order and concurrency review.

## Non-goals and blockers
- No database was created or altered.
- No owner signature or identity cryptography is implemented here.
- No trusted clock, key custody, revocation service, policy engine or receiver is implemented.
- Hash-linked audit events are tamper-evident, not tamper-proof. Independent signed checkpoints and WORM storage remain required.
- No live trading, payment, wallet or external dispatch capability is enabled.

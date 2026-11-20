# Trusted control-plane façade reference contract

Status: offline prototype source and tests added; not executed, deployed or production-ready.

## Scope implemented in this reference
- A company-scoped façade binds identity verifier, scheduler, owner-approval verifier, trusted clock, trusted owner registry and approval repository at construction.
- Request methods cannot supply verifier callbacks, trusted owner IDs, clock values, company identity or repository adapters.
- Identity resolution checks verified issuer output, expected company/audience, expiry, identity epoch, and trusted scheduler assignment/company/task scope.
- Owner approval issuance checks verifier output, trusted owner registry, exact company/audience, single-use semantics, expiry, nonce, task/principal/resource/policy scope, and amount/currency pairing.
- Durable approval persistence is delegated to a trusted repository adapter. The façade validates the repository receipt and scope digest before returning it.
- The API returns immutable dataclasses, not database handles.

## Explicit limitations
- The verifier and repository adapters are trusted dependencies supplied at process startup. This prototype does not implement asymmetric cryptography, owner authentication, a production scheduler, revocation transport, trusted clock service, database isolation or key custody.
- The owner-approval method must be exposed only through an owner-authorized service identity. A valid signature is not permission for an agent to call the owner endpoint.
- The repository adapter must atomically persist the full approval scope and audit event, enforce unique approval IDs/nonces, and provide durable single-use consumption. The existing SQLite control-store approval schema does not yet store every field required by this façade; do not wire this façade to that schema until a compatible migration and transaction design are reviewed.
- The façade does not implement action enqueue, final policy evaluation, dispatch authorization, sender invocation, receiver evidence, recovery release or production networking.
- No model or agent may access verifier keys, trust roots, repository credentials or the underlying database.
- All adapters must fail closed. Tests use synthetic in-memory fixtures only.

## Required validation before extending
1. Run the documented offline unit tests locally and preserve output.
2. Add independent cryptographic verifier tests using asymmetric signatures and negative fixtures.
3. Add scheduler/revocation/clock outage and rollback tests.
4. Add a durable repository with full-scope approval schema, atomic audit and unique nonce constraints.
5. Review owner-only endpoint authentication and company isolation.
6. Do not connect to real accounts, payment systems, wallets, brokers, exchanges or external senders.

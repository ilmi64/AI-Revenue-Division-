# Linearizable Control Store — Static Review and Validation Gate

Status: static review only; the committed test suite has not been executed. This document does not certify runtime correctness, production readiness, or operational readiness.

## Verified source facts

- The two company branches contain byte-identical copies of the linearizable control-store reference, test file, and acceptance scenarios at the reviewed checkpoint.
- The test file defines 27 test methods.
- The reference uses one SQLite database and `BEGIN IMMEDIATE` transactions to serialize local state changes for a single-host prototype.
- Dispatch authorization commits approval consumption, action state `dispatch_started`, and an audit event together.
- Quarantine increments the recovery epoch and writes its audit/control-outbox records in the same transaction.
- Release rechecks quarantine state and epoch after the verifier calls, then consumes the release approval/nonce and activates the stream in one transaction.
- The sender is not implemented; the reference does not make an external network or financial call.

## Static-review limitations and mandatory production boundaries

1. **Caller claims are not authentication.** The `authorize_and_start` method receives agent, task, operation, resource, and policy-version values as arguments. It does not itself authenticate an agent identity or prove that these values came from a trusted issuer. A production caller must obtain identity and assignment from trusted control-plane services and enforce the deterministic policy gateway immediately before authorization.
2. **Trading hard-deny policy is not implemented inside this reference method.** Production policy must unconditionally deny live orders, wallet signing, funds transfers, broker/exchange orders, withdrawals, and Trading risk-control modifications. Add explicit negative acceptance tests at the production policy-gateway boundary. Never treat an approval row or a model-generated request as sufficient authority.
3. **Verifier fixtures are synthetic.** Test verifier objects return claims from fixtures. They do not implement asymmetric signature verification, trusted issuer/key registries, key rotation/revocation, or secure key custody. Production requires independently administered cryptographic verifiers and protected signing keys.
4. **SQLite is a local prototype, not the production control plane.** The current concurrency test is thread-based. It does not establish multi-process, multi-host, failover, replication, or production isolation guarantees. Production database selection and topology require separate verification and concurrency/failure testing.
5. **Audit hashes are tamper-evident, not tamper-proof.** A privileged database writer could rewrite the entire local chain. Production requires signed checkpoints and independently administered immutable/WORM retention, with restore-time verification.
6. **Receiver fencing is external.** The local epoch can reject stale queued work before dispatch authorization, but it cannot recall a request already committed for dispatch. A production receiver must enforce stable idempotency and the current company/stream recovery epoch, or the residual stale-arrival race must be explicitly accepted and controlled.
7. **Sender outcomes are not independently authenticated here.** Production must bind signed receiver evidence to the exact company, action, recipient/account, idempotency key, audience, outcome, freshness window, and replay nonce. Ambiguous outcomes remain quarantined until reconciled; never auto-resend.
8. **Owner approval issuance is outside this prototype's trust boundary.** The production approval issuer must verify owner authorization and exact action scope before inserting an approval. Approval consumption must remain atomic with the dispatch authorization record.
9. **Recovery assessment is a trusted external attestation.** The production recovery authority must independently verify database integrity, audit/checkpoint continuity, current revocations, emergency-stop state, and reconciliation of every unknown/in-flight action. A Boolean claim supplied by a worker is not evidence.
10. **Durability and restore are not yet proven.** Production needs backup/PITR, independent checkpoint storage, tested restore drills, monitoring, and fail-closed startup/restore enforcement across every dispatch-capable boundary.

## Validation sequence

1. Run the exact committed Python test file in an isolated, no-cost environment, separately against each repository checkout. Do not use GitHub Actions or paid/credit-consuming compute without explicit owner approval.
2. Preserve full output, interpreter version, source/test commit SHAs, and test counts. A test result is valid only for the exact fetched commit and environment.
3. Add and execute multi-process concurrency tests for dispatch-vs-quarantine, release-vs-dispatch, approval replay, and process crash/restart.
4. Add explicit negative tests for all Trading hard-deny operations at the deterministic policy gateway.
5. Verify a production database's transaction isolation, locking, durability, failover, and restore behavior before replacing the SQLite prototype.
6. Implement independently signed audit checkpoints, WORM retention, receiver-side idempotency/epoch fencing, and signed receiver-evidence verification.
7. Conduct independent security review and recovery/incident rehearsals before any operational claim.

## Current decision

**Not production-ready; not deployed; not connected to a sender; no live trading or external financial action is enabled by this reference.** Keep the PR draft. Do not merge, deploy, run CI, install services, or spend credits as part of this validation gate.

# Atomic receiver-evidence reconciliation contract

Status: proposed offline reference; not production-enforced.

## Trusted verification boundary
The reconciliation store must be constructed with the actual
`ReceiverEvidenceVerifier` instance created by trusted application wiring.
It rejects caller-supplied `verified=True` dictionaries and duck-typed verifier
objects. The store loads the action's company, receiver account and stable
idempotency key, then asks its bound verifier to validate issuer, signature,
freshness, audience and exact action/destination scope.

For this integrated path, the verifier must not have a separate replay store.
Its dedicated atomic-verification method validates the signature and scope
without consuming replay state. The reconciliation database owns the durable
replay receipt. A caller must not pass a separate replay store to this verifier.

## Atomic commit
After verification, the store starts a write transaction and reloads the action.
It compares the immutable action identity with the pre-verification snapshot,
then atomically:
- inserts unique receipt keys for (issuer, nonce) and (issuer, evidence ID);
- transitions `outcome_unknown` to reconciled-applied,
  reconciled-not-applied, or quarantined;
- appends the per-company audit event; and
- commits all three or none.

The unique constraints are the durable replay-consumption point. An exact retry
after commit returns the same result without another audit event. A reused nonce
or evidence ID with different content/scope is rejected. A crash or audit/database
failure before commit leaves no receipt and no action transition, so the exact
still-valid evidence can be reverified and retried.

## Failure handling
Invalid signature, stale evidence, wrong scope, missing trusted verifier,
database outage, lock timeout and audit failure all deny reconciliation. The
action remains on hold. Operational database failures must not be mislabeled as
replay conflicts. Freshness and signature verification are repeated on retry.

## Reference limitations and production blockers
This is a single-host SQLite prototype, not a distributed production ledger.
Trusted verifier construction, asymmetric signature validation, issuer/key
registry, trusted time, shared transactional database, immutable action intent,
multi-node race/failover, backup/PITR, independent signed checkpoints, WORM
storage, least-privilege database roles, monitoring and owner-approved recovery
remain production requirements. No network sender, broker, wallet or financial
side effect is implemented.
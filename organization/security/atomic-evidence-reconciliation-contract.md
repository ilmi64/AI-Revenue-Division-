# Atomic receiver-evidence reconciliation contract

Status: proposed offline reference; not production-enforced.

## Failure being closed
The standalone durable replay verifier previously claimed a nonce before the
reconciliation transaction. A crash after that claim but before the action
state/audit commit could make a valid receiver response unusable on retry.
The replay-store insert and action reconciliation were separate transactions.

## Required production sequence
1. A trusted control-plane verifier authenticates the receiver signature,
   issuer, freshness, audience, company, action, receiver account and stable
   idempotency key. It uses trusted keys, registry and clock; workers cannot
   configure any of these.
2. The verifier returns a normalized claim and canonical payload digest. The
   reconciliation service recomputes the digest from the exact evidence bytes
   and rejects any claim/evidence substitution.
3. In ONE durable database transaction, the reconciliation service:
   - locks/reloads the immutable action and checks company/destination/key;
   - inserts a unique receipt keyed by (issuer, nonce) and (issuer, evidence ID);
   - transitions outcome_unknown to its terminal reconciliation state;
   - appends the per-company audit event;
   - commits all three or none.
4. A retry after commit with the exact same issuer, nonce, evidence ID, digest,
   action and outcome returns the recorded result without adding a second audit
   event. A reused nonce or evidence ID with different content/scope is rejected.
5. A crash or audit/database failure before commit leaves no receipt and no
   state transition, so the exact still-valid signed evidence can be safely
   reprocessed. Freshness is checked again by the trusted verifier.

## Reference implementation
The SQLite prototype demonstrates atomic receipt + action state + hash-chain
audit, exact duplicate-result handling, digest re-binding protection, rollback
on audit failure, unique replay constraints and a two-connection race.
It is a separate integration reference, not yet wired into the existing
transactional dispatch store or production gateway. For this integrated path,
do not configure the verifier with its separate replay_store; the final
reconciliation transaction owns durable replay consumption.

## Operational failure handling
Database unavailable, lock timeout, audit failure, malformed evidence or
signature verification failure all deny reconciliation and preserve the
outcome_unknown hold. Distinguish operational store failures from a true
unique-key replay in telemetry; never silently treat an outage as a replay.
A retry must re-run trusted signature/freshness/scope verification.

## Production blockers
SQLite is single-host reference code, not a distributed production ledger.
Production requires a shared transactional database, database-level immutable
action intent and scope enforcement, asymmetric signature verification and
key rotation, trusted time, durable backups/PITR, multi-node race/failover tests,
independent signed audit checkpoints and WORM storage, least-privilege roles,
monitoring and owner-approved recovery. No sender, broker, wallet or financial
side effect is implemented here.

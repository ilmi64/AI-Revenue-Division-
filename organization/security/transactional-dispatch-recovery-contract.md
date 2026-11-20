# Transactional dispatch and recovery contract

Status: proposed offline reference; not production-enforced.

## Atomic boundary
The SQLite reference places action intent, one-time approval consumption,
dispatch_started state, and the matching audit event in one BEGIN IMMEDIATE
transaction. That commit is the authorization linearization point. Revocation
committing first blocks dispatch; dispatch_started committing first means later
revocation cannot prove the external effect was prevented.

## External side-effect boundary
The sender runs only after the transaction commits. A crash after that commit,
including before the sender call, is indistinguishable from a crash after remote
acceptance. Recovery MUST mark/retain outcome_unknown and MUST NOT automatically
send again. The remote receiver must enforce the stable idempotency key for the
full reconciliation window. Exactly-once delivery is not claimed.

## Reconciliation
The reference accepts raw evidence plus an injected verifier dependency; it does
not accept a caller-supplied authenticated boolean. The verifier MUST be
constructed, configured and injected only by trusted control-plane
infrastructure. It MUST NOT be selected, replaced, configured or invoked with
agent-controlled trust roots, issuer registries, receiver accounts, clocks,
replay stores or verification keys. Agents and workers may submit evidence
bytes, but cannot supply the verifier or its trust configuration.

The verifier must authenticate the receiver signature and bind the evidence to
the exact company, action ID, idempotency key, receiver account and recovery
audience.
The action's receiver account must be persisted in immutable action intent;
missing or mutable destination identity fails closed. The reconciliation adapter
accepts a verifier object exposing a trusted `verify` method, not an arbitrary
agent-provided callback. It must enforce issuer allowlists, freshness, nonce/evidence replay
protection and a stable evidence ID. Verification occurs outside the SQLite
write transaction; after verification, the reference reloads the action under
BEGIN IMMEDIATE and rechecks its company, ID and idempotency key before changing
state. Production must preserve this binding and recheck atomically.

Applied becomes reconciled_applied; authoritative not-applied becomes
reconciled_not_applied; inconclusive becomes quarantined. None reuses the old
approval. A new action requires a new intent and fresh owner approval.

## Backup and restore
Use SQLite's online backup API (or an equivalent consistent snapshot), never
copy a live database file blindly. After restore, check PRAGMA integrity_check,
verify every company audit chain against independently protected signed
checkpoints, reconcile action states against receiver evidence, revalidate
revocations and emergency-stop state, then keep external dispatch disabled
until an owner-approved recovery gate passes.

## Production blockers
This reference has no owner-signature verification, remote receiver, network
sender, distributed database, KMS/HSM, WORM store, independent checkpoint
signer, trusted evidence verifier, operational monitoring, or production
restore drill. SQLite locking is single-host/local. Audit hash chains alone do
not prevent privileged rewrite. A production adapter needs transactional
outbox + approval + audit in one durable DB, asymmetric identities, independent
policy gateway, immutable checkpoints, receiver idempotency, tested PITR and
multi-node race tests. Trading live orders, wallet signing, transfers,
withdrawals and risk-control modification remain hard-denied.

# Decision record: linearizable recovery and dispatch authorization

**Status:** proposed architecture decision; not implemented, deployed or production-validated.  
**Scope:** separate instance for AI Revenue and separate instance for Trading & Technology.  
**Decision owner:** company owner; this record documents the recommended technical design.  
**Related:** recovery authority to dispatch-boundary enforcement contract; transactional dispatch/recovery reference; durable approval ledger; outbox dispatch contract.

## 1. Decision

Each company must have one authoritative transactional control store (or one demonstrably linearizable transactional service) containing, within that company's security boundary:

- recovery stream state and monotonically increasing recovery epoch;
- owner approvals and one-time approval consumption;
- immutable action intents and idempotency keys;
- dispatch/outbox state;
- per-company audit append position and event;
- quarantine-control outbox events.

Quarantine and dispatch authorization must lock/update the same recovery-stream authority record in the same transaction domain. A separate recovery SQLite database and separate dispatch SQLite database do **not** provide this guarantee, even if both are locally durable.

The preferred production target is a strongly consistent relational database with transactional row locking, unique constraints, durable commits and tested backup/restore. A PostgreSQL implementation is a candidate, not yet selected or installed. The exact isolation level and lock behaviour must be verified against the chosen database and topology.

## 2. Required records and invariants

Minimum logical records:
- `company_stream(company_id, stream_id, status, recovery_epoch, incident_id, checkpoint_digest, updated_at)`
- `owner_approval(approval_id, company_id, exact_scope, expires_at, revoked_at, issuer_key_id, signature_digest)`
- `approval_consumption(approval_id UNIQUE, action_id UNIQUE, nonce UNIQUE, consumed_at)`
- `action_intent(action_id, company_id, stream_id, recovery_epoch, immutable_intent_digest, idempotency_key UNIQUE, state, approval_id, created_at)`
- `audit_event(company_id, stream_id, sequence, event_id UNIQUE, event_type, payload_digest, previous_hash, event_hash)`
- `control_outbox(event_id UNIQUE, company_id, stream_id, recovery_epoch, event_type, payload_digest, delivery_state)`

Every table and query is company-scoped. Composite foreign keys or equivalent constraints must prevent references across companies. Secrets and raw credentials never enter these records. The action intent is write-once; corrections create a superseding intent and new ID rather than mutating an authorized action.

## 3. Dispatch authorization transaction

The authorization transaction must:
1. Begin a transaction with documented serialization/locking semantics.
2. Lock the exact `company_stream` row (or perform a conditional update that serializes against quarantine).
3. Verify trusted principal, task assignment, company, stream, current epoch, task expiry, policy version, emergency stop, current revocation state and action scope.
4. Require stream status = `active`; reject missing, disabled, quarantined, stale or contradictory state.
5. Lock and validate the exact owner approval, including one-time nonce and exact action/resource/recipient/amount/time scope.
6. Insert the unique approval-consumption record.
7. Insert or transition the immutable action intent to `dispatch_started`, binding its digest, epoch and idempotency key.
8. Append the audit event in the same transaction.
9. Commit. Any failure rolls back all state changes.

The successful commit is the **authorization linearization point**. No sender is called before it. The dispatcher then invokes the receiver outside the database transaction using the stable idempotency key and the committed recovery epoch.

## 4. Quarantine transaction

Quarantine must:
1. Begin a transaction and lock the same `company_stream` row used by dispatch authorization.
2. Validate trusted incident authority and exact company/stream scope.
3. Increment `recovery_epoch`, set status to `quarantined` (or `dispatch_disabled` for initial registration), record incident/checkpoint binding.
4. Append the audit event and insert a durable quarantine event into `control_outbox` in that same transaction.
5. Commit.

The shared row lock/conditional transition gives dispatch authorization and quarantine a serial order:
- If quarantine commits first, a later dispatch transaction sees disabled state/new epoch and must deny.
- If dispatch authorization commits first, that action was authorized before quarantine. It may be in flight or may already have reached the receiver. Quarantine must stop subsequent actions and classify the action as potentially in flight until reconciled.

This does **not** recall an external side effect already accepted by a receiver.

## 5. The unavoidable network boundary

A database transaction cannot atomically include an arbitrary remote HTTP request, broker, exchange, wallet or payment receiver. Do not claim exactly-once delivery.

For high-consequence receivers, the receiver must enforce:
- stable idempotency key;
- authenticated company/action/recipient binding;
- monotonically increasing recovery epoch or a receiver-side revocation/fencing check;
- rejection of stale epochs and duplicate idempotency keys;
- authenticated signed outcome evidence for reconciliation.

If the receiver cannot validate fencing, a local gateway can reduce the race window but cannot mathematically guarantee that an already-authorized request will not arrive after quarantine commits. The system must disclose this residual risk and quarantine/reconcile any ambiguous in-flight action. Trading live execution remains disabled regardless.

## 6. Lock ordering and concurrency

Use one global lock order in every transaction to prevent deadlocks:
1. company stream row;
2. action intent row (if present);
3. approval row;
4. approval-consumption uniqueness;
5. audit stream head;
6. control-outbox row.

All code paths must follow the same order. Use unique constraints as the final replay defence. Retry only database transactions that are proven not to have committed; never automatically retry a remote sender call after an ambiguous outcome.

The implementation must test concurrent dispatch-vs-quarantine, duplicate approval consumption, duplicate action IDs, out-of-order control events, deadlock/serialization retry, process crash at each commit boundary, database failover and restore.

## 7. Recovery release transaction

Release is a separate privileged transaction. It must lock the same stream row and require:
- latest trusted signed checkpoint verified against the restored audit stream;
- database integrity and complete audit verification;
- every in-flight/unknown action reconciled;
- current key/revocation and emergency-stop state;
- trusted, fresh, exact-scope recovery assessment;
- independent owner-signed, one-time approval for this incident, checkpoint, company, stream and release action.

Consume the owner approval, append the release audit event, increment recovery epoch, and set stream active atomically. If any check or write fails, remain quarantined. Old leases and old action intents are never revived; fresh work requires new task leases and new action IDs/approvals.

## 8. Isolation and availability

Use separate company databases/instances and separate signing/verification authorities unless a later, independently reviewed design proves equivalent tenant isolation. A shared database cluster may host separate databases, but cluster-level administrators and backups remain a common trust dependency that must be documented.

When the control store, policy gateway, audit writer, recovery authority, trusted clock, key status or revocation source is unavailable, consequential work fails closed. No stale cache, local flag, model output, OCC summary, Paperclip state or Ruflo state may override the authoritative record.

## 9. Why not distributed two-phase commit

Do not introduce distributed two-phase commit across recovery DB, approval DB, audit DB, queue and external receiver as the first design. It increases operational failure modes and does not solve atomicity with arbitrary external systems. Keep the critical local authorization state in one transactional boundary; use a transactional outbox for asynchronous control-event delivery and authenticated idempotent receivers for remote effects.

## 10. Migration from current prototypes

The existing SQLite prototypes remain useful offline reference models, but are not production architecture:
- SQLite recovery authority and dispatch store currently use separate connections/databases and do not share an atomic transaction.
- They do not provide multi-node linearizability or independently administered immutable audit checkpoints.
- Injected verifier objects are interfaces, not production cryptographic key management.
- The prototypes must not be connected to real accounts or external senders.

Next implementation work must first build a combined synthetic reference store and deterministic concurrency tests. Only after those pass should a database-specific migration plan be considered. No database, runtime, broker, wallet, model provider or external service is authorised by this decision record.

## 11. Approval boundary

This decision authorises architecture documentation and offline synthetic design only. It does not authorise installation, deployment, paid use, GitHub Actions, merge, account access, external dispatch, publication, spending or live trading.

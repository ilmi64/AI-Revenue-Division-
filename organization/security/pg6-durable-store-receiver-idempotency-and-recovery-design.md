# PG-6 — Durable Store, Receiver Idempotency and Recovery Proof Design

**Status:** Architecture consolidation only; no schema migration, database, receiver, sender, cryptographic key, test or deployment.  
**Applies independently:** AI Revenue Company and Trading & Technology Company.  
**Inputs:** Existing linearizable control-store, transactional dispatch/recovery, outbox safety, recovery-to-dispatch enforcement and PG-2/PG-3/PG-4/PG-5 designs.  
**Rule:** One company-local durable transaction authority; fail closed; never automatically resend an ambiguous external action.

## 1. Objective and source reconciliation

PG-6 closes the design gap between a local approval decision and an external side effect. Existing reference contracts already establish the critical invariants:

- Quarantine and dispatch authorization serialize through the same company/stream control state.
- Approval consumption, immutable action intent, dispatch reservation and canonical audit append commit together.
- The external sender runs only after the authoritative transaction commits.
- A crash or timeout after dispatch reservation is ambiguous; local state cannot establish whether the receiver acted.
- Remote idempotency, immutable action binding, receiver identity and recovery-epoch fencing are required.
- Recovery release requires independent assessment, owner approval, checkpoint/revocation/emergency-stop verification and a new epoch.
- SQLite references demonstrate local serialization only; they do not prove multi-node correctness or production security.

This document consolidates those requirements into one target design. It does not introduce a second policy engine, approval repository or audit authority.

## 2. Canonical company-local transaction boundary

Each company must operate its own strongly consistent control-store transaction domain containing the minimum records needed to make an authorization decision linearizable:

1. Company/stream recovery state, quarantine flag and monotonically increasing recovery epoch.
2. Trusted task version/status/assignment reference, or a verifiable immutable reference to the authoritative scheduler state.
3. Exact-scope approval record and one-use consumption state.
4. Immutable action intent and unique action identifier.
5. Stable idempotency key and canonical payload digest.
6. Dispatch lifecycle state and bounded attempt/lease metadata.
7. Canonical company-local audit append position and event reference.
8. Transactional outbox event for the post-commit dispatcher.

The company must not split approval consumption, action reservation, recovery state and canonical audit append across independently committing databases. If the architecture later uses separate services, it must preserve a proven equivalent linearizable transaction protocol; an event bus alone is not sufficient.

The transaction store is not the policy authority, owner identity issuer or remote receiver. It persists the result of trusted checks and enforces the atomic state transition.

## 3. Required data invariants

### 3.1 Immutable action intent

Once reserved, the intent is write-once and binds:
- company ID and stream ID;
- action ID and canonical operation ID;
- principal, session and task ID;
- exact destination/receiver identity and account;
- resource and payload digest;
- recipient and amount/currency where applicable;
- approval ID and scope digest;
- policy version and taxonomy version;
- recovery epoch;
- stable idempotency key;
- creation time and audit correlation ID.

Database permissions and constraints must prevent later edits. A privileged correction creates a new audited record and cannot rewrite the original action intent.

### 3.2 Uniqueness and idempotency

Enforce unique company-scoped constraints for:
- action ID;
- idempotency key;
- approval ID consumption;
- approval nonce hash;
- receiver evidence ID;
- receiver idempotency receipt;
- recovery event ID and monotonic epoch.

A repeated idempotency key with a different action digest is a security incident and must be rejected. Idempotency retention at the receiver must exceed the maximum retry/reconciliation horizon.

### 3.3 Money and quantities

Represent money as integer minor units paired with an explicit normalized currency. Reject floating-point money, missing currency, negative or unsafe integer values, unsupported precision and ambiguous rounding. Quantity and unit fields require explicit semantics.

### 3.4 Tenant isolation

Company ID is resolved from authenticated service identity and trusted records, not accepted as authority from the agent payload. Separate databases or strongly isolated tenants, roles, keys, audit streams, backup scopes and recovery authorities are required. A shared cluster is not a shared authority.

## 4. Dispatch state machine

The following states are distinct and must not be collapsed into a generic success/failure label:

| State | Meaning | Permitted next action |
|---|---|---|
| pending | Immutable intent accepted but not yet reserved for dispatch | Recheck all gates |
| denied | A required gate failed before dispatch reservation | Terminal; new task/approval required |
| cancelled | Task cancelled or policy denied before dispatch reservation | Terminal; no sender call |
| dispatch_reserved | Approval consumed, intent/outbox and audit committed atomically | One authorized sender may claim |
| dispatch_started | Sender crossed the local dispatch boundary | Await authoritative receiver evidence |
| outcome_unknown | Timeout/crash/ambiguous acknowledgement; remote effect may have occurred | Quarantine and reconcile only |
| receiver_applied | Verified receiver evidence confirms exact action applied | Reconciled terminal result |
| receiver_not_applied | Verified receiver evidence proves exact action was not applied | New action requires fresh approval |
| quarantined | Integrity, identity, policy, receiver or recovery uncertainty | Independent recovery process only |
| failed_terminal | Verified terminal failure with no remaining safe retry | Close with evidence; new action needs new intent |

A local sender return code, UI label, model summary or timeout is not authoritative receiver evidence.

## 5. Ordering and race protocol

All transitions that can authorize a side effect must serialize against quarantine, revocation, task cancellation and recovery release.

### Quarantine wins

If quarantine commits first:
- stream state changes to quarantined/dispatch-disabled;
- recovery epoch increments;
- old leases and permits become stale;
- dispatch reservation fails;
- sender is not invoked.

### Dispatch reservation wins

If dispatch reservation commits first:
- exact approval consumption, immutable intent/outbox reservation and audit event are committed;
- quarantine cannot prove that the external effect was prevented;
- stop further dispatches;
- mark any uncertain in-flight action outcome_unknown;
- reconcile with authoritative receiver evidence;
- never blindly resend.

### Recovery release

Release is a distinct owner-gated transaction:
1. Independent assessor verifies store integrity, audit/checkpoint, revocation, key status, emergency stop and all ambiguous actions.
2. Separate owner authority signs a one-time exact-scope release approval.
3. Trusted verifier validates both assessment and approval outside the write transaction.
4. Under the authoritative transaction, recheck incident, checkpoint, approvals, nonce, revocation, emergency stop and current epoch.
5. Consume the release approval/nonce, append audit, increment epoch and set the stream active atomically.
6. Old tasks, leases and outbox records remain stale; new work requires fresh task assignment and fresh authorization.

A company executive, model, agent, OCC, Research & Intelligence, scheduler or orchestrator cannot release quarantine.

## 6. Receiver-side contract

The receiver is the only party that can authoritatively deduplicate the remote effect. A production receiver or its trusted idempotency service must:

- authenticate the company-specific sender identity;
- validate the exact operation, destination/account, payload digest and recovery epoch;
- persist the idempotency key and immutable action digest atomically with the side effect or with a receiver-side transactional protocol;
- return the same authoritative receipt for duplicate identical requests;
- reject a duplicate key with a different digest;
- reject expired, stale-epoch, wrong-company, wrong-recipient or replayed requests;
- expose an authenticated reconciliation query for an action ID/idempotency key;
- issue signed, fresh outcome evidence bound to company, receiver identity, action ID, digest, idempotency key, destination, epoch, nonce and timestamp;
- retain deduplication state and evidence for at least the full sender retry/reconciliation window.

If the remote receiver cannot provide durable idempotency or an authoritative reconciliation interface, the sender must treat uncertain outcomes as non-retryable and require manual reconciliation. Do not claim exactly-once remote execution.

For financial/trading receivers, this architecture does not grant permission to connect, sign, trade, transfer or withdraw. Trading's current live-execution and wallet/broker/exchange hard denies remain absolute.

## 7. Sender and outbox requirements

- The sender consumes only committed outbox records from its own company tenant.
- Sender identity is a narrowly scoped service identity, not an agent credential.
- Before the first network side effect, recheck the current task, identity, policy, approval-consumption record, emergency stop, revocation, budget and recovery epoch.
- A lease is a concurrency aid, not proof that the prior worker did not act. Lease expiry alone never authorizes redelivery.
- Attempts are bounded and observable; no infinite retries or fallback to another paid provider/endpoint.
- Any network ambiguity moves to outcome_unknown and blocks automatic redelivery.
- Sender cannot change action intent, destination, amount, payload digest, idempotency key or recovery epoch.
- A receiver response is accepted only through the trusted verifier; a caller-supplied authenticated Boolean is not accepted.
- No sender, endpoint, wallet, exchange, broker, payment processor or customer system is connected by this design.

## 8. Audit, checkpoint, backup and restore

Canonical audit events include approval issue/revoke/consume, task binding, policy decision, dispatch reservation, sender claim, send attempt, unknown outcome, receiver evidence, quarantine, recovery assessment, owner release, epoch change and final reconciliation.

Each event records company/stream, actor/service identity, task/action, operation, policy/taxonomy version, approval/intent digest, idempotency key reference, old/new epoch, event sequence, trusted timestamp, decision/reason and evidence references. Secrets and unnecessary customer data are excluded.

A hash chain alone is insufficient against privileged rewrite. Production requires independently administered signing/checkpoint authority and immutable/WORM exports, with key rotation and verification.

Backup/restore requirements:
- consistent transactional snapshots using database-supported backup/PITR mechanisms;
- restore into a non-dispatching state;
- integrity and schema migration checks;
- full audit-chain and independent checkpoint verification;
- reconciliation of all dispatch_started/outcome_unknown actions against receiver evidence;
- refresh of identity/key/revocation/emergency-stop/policy state;
- verification that old epochs and leases cannot resume;
- separate owner-approved release before any consequential operation.

A backup restore is not an automatic recovery release.

## 9. Failure matrix

| Failure | Required disposition |
|---|---|
| Primary database unavailable or uncertain commit | Deny new consequential work; reconcile commit state |
| Replica lag or split brain | No dispatch from stale/non-authoritative replica |
| Audit append/checkpoint unavailable | Deny consequential work |
| Clock uncertainty | Deny expiry-sensitive operations |
| Key/revocation registry unavailable or stale | Deny |
| Policy or scheduler unavailable | Deny |
| Outbox duplicate delivery | Idempotent local claim; receiver key prevents duplicate effect |
| Sender crash before/after remote acceptance | outcome_unknown unless authoritative evidence proves outcome |
| Receiver unavailable | Quarantine/reconcile; no blind retry |
| Duplicate callback | Idempotent evidence receipt |
| Conflicting receiver receipts | Security incident and quarantine |
| Recovery epoch mismatch | Deny |
| Shared orchestration/OCC outage | Company-local control store remains authoritative; no shared fail-open |
| Restore/checkpoint mismatch | Keep dispatch disabled; incident review |

## 10. Future proof programme

PG-6 implementation evidence must include:
- selected database/consistency model and transaction isolation rationale;
- schema and constraints reviewed against PG-2 canonical approval scope;
- proof that quarantine, approval consumption, action/outbox reservation and audit append share one linearizable boundary;
- concurrent race tests for dispatch/quarantine/revocation/cancellation/recovery;
- crash injection before commit, after commit, before send, after receiver acceptance and before local receipt commit;
- duplicate/reordered outbox and receiver callbacks;
- receiver idempotency and epoch-fencing proof;
- replay, stale key, clock skew, partition, failover, backup/restore and recovery-release tests;
- independent security review and exact-revision evidence register updates.

These tests are not authorized or executed. SQLite prototype behaviour is not production proof.

## 11. Company overlays

### AI Revenue

- CAD $0 spend policy remains enforced at the cost boundary.
- Any future approved external action must bind exact content, destination/customer, amount/currency and operation; no broad reusable approval.
- Customer communications, publishing, purchases, contracts, payments and deployment remain separately gated.
- Customer data and sales records remain in the AI Revenue tenant.

### Trading & Technology

- Research/backtest/paper are separate modes; no transition to live execution by approval, recovery or model instruction.
- Live orders, wallet signing, deposits, transfers, withdrawals, broker/exchange orders and risk-control changes remain hard-denied.
- Independent CRO/risk veto remains in force.
- Market-data and strategy evidence provenance are separate from dispatch correctness.
- Shafi'i/halal issue flags remain separate review metadata; no automated religious ruling.

## 12. Current disposition

PG-6 design is consolidated from existing reference contracts. No canonical production database has been selected or deployed; no cryptographic keys, trusted receiver, sender, network connection, idempotency service, WORM store, signed checkpoint service or monitoring has been implemented. No tests or recovery drills have been run. Production readiness remains NOT_IMPLEMENTED / NOT_VERIFIED.

No spending, installs, migrations, GitHub Actions, deployments, account connections, external actions or live trading are authorized by this document.

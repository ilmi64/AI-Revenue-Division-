# Recovery authority to dispatch-boundary enforcement contract

**Status:** proposed integration contract; not implemented or production-enforced.  
**Applies to:** both independent companies; each company has a distinct recovery authority, stream and policy namespace.  
**Purpose:** make quarantine an enforced deny state at every consequential execution boundary, rather than a status recorded only in a recovery database.

## 1. Security invariant

A stream is dispatchable only when the authoritative recovery registry reports all of the following for the exact company and stream: state = `active`; current recovery generation/epoch; no unresolved quarantine; current trusted checkpoint is verified; no emergency stop; policy and revocation state are fresh; and the requested action independently passes the deterministic policy gateway.

Any missing, stale, contradictory, unauthenticated or unavailable recovery state means **deny and fail closed**. A cached `active` result is not sufficient for consequential actions. OCC summaries, model output, Paperclip task status, Ruflo workflow state and agent claims are never recovery authority.

## 2. Mandatory enforcement points

The same authoritative gate must be applied at all of these boundaries, not just one:
1. Scheduler: do not lease or dispatch new work for a quarantined stream.
2. Agent runtime: reject task start, resume, child-task creation and delegated work.
3. Tool/data gateway: deny protected reads and all writes/actions when the stream is held; apply company and resource scope independently.
4. Cost gateway: deny paid inference, compute or other billable calls while the stream is held or budget state is unavailable.
5. Outbox dispatcher: check immediately before the final authorization transaction and again before any retry/reconciliation transition that could permit a side effect.
6. External-action gateway: reject before credentials/signing/network dispatch. Trading live-order, wallet-sign, transfer, withdrawal and risk-control mutation hard-denies remain absolute and are not made available by recovery release.
7. Queue, retry and dead-letter workers: quarantine blocks retries, replay, redrive and child jobs.
8. Startup and restore: all workers start in a non-dispatching state until the authoritative registry, checkpoint and policy state have been verified.

No direct runtime-to-tool, model-to-provider, worker-to-network or alternate adapter path may bypass these gates.

## 3. Authoritative state and fencing

- Recovery state is keyed by immutable `company_id` + `stream_id`; never trust either value from an unverified task payload.
- The recovery authority issues a monotonically increasing `recovery_epoch` when a stream is quarantined or released. Every task lease, dispatch intent and outbox record carries the epoch under which it was created.
- Quarantine increments the epoch and atomically marks the stream disabled. All earlier leases, task grants and dispatch authorizations are stale.
- Every boundary compares the task/action epoch to the current authoritative epoch. A mismatch is denied and audited.
- Workers must not be able to choose, increment, restore or override the epoch.
- A worker that loses contact with the recovery authority, policy gateway, audit sink or revocation source must stop consequential work. No fail-open cache or stale local replica.
- Read-only diagnostic access may be exposed through a separately scoped path; it must not allow protected data disclosure or side effects outside approved incident scope.

## 4. Quarantine propagation protocol

1. The recovery authority commits the quarantine event, new epoch and `dispatch_disabled` state to its authoritative transactional store.
2. A durable, authenticated control event is emitted using an outbox in the same transaction. Delivery is at-least-once; consumers are idempotent.
3. Scheduler, runtimes, gateways, queues and outbox workers consume the event, invalidate leases/caches, pause affected work and acknowledge the exact company/stream/epoch.
4. The dispatcher independently reads authoritative state before each consequential action; event delivery is not the sole enforcement mechanism.
5. Missing acknowledgement, consumer outage, event gap or epoch disagreement keeps the stream disabled and raises an incident.
6. A quarantine event must not be undone by a normal task update, restart, retry, database restore or model request.

## 5. Release protocol

Release is possible only through the existing independent recovery authority after:
- database integrity and complete audit-chain verification;
- verification against the latest independently signed checkpoint in external immutable storage;
- revocation/key status and emergency-stop refresh;
- reconciliation of every `dispatch_started`, `outcome_unknown` and otherwise ambiguous action;
- validation that no stale worker, lease, credential or task can resume under the old epoch;
- trusted recovery assessor's signed, fresh, exact-scope assessment; and
- separate owner-signed, one-time, exact-scope release approval.

The release transaction atomically consumes the owner approval and nonce, records the signed assessment digest and checkpoint binding, increments the recovery epoch, changes state to active, and appends the audit event. If any part fails, the transaction rolls back and dispatch remains disabled. A company executive, OCC, model, orchestrator, scheduler or runtime cannot release quarantine.

After release, workers must obtain fresh leases and fresh policy decisions under the new epoch. Old queued tasks and outbox intents are not automatically revived. They require explicit safe re-creation or reconciliation under new action IDs and approvals.

## 6. Race and failure semantics

- Quarantine must serialize against dispatch authorization through a shared transactional control boundary or equivalent linearizable mechanism.
- If quarantine commits before dispatch authorization, dispatch is denied.
- If dispatch authorization commits first, the action may already be in flight; quarantine cannot recall an external side effect. Mark it as potentially in flight, stop subsequent actions, and reconcile with receiver evidence.
- A worker must not hold a long-lived authorization token that survives a quarantine epoch change. Prefer a single-use, short-lived token bound to company, stream, epoch, task, action, resource, policy version and idempotency key.
- A network partition between the recovery authority and an execution boundary means no new consequential action. Do not infer safety from an event bus message alone.
- Duplicate, delayed and out-of-order control events are expected; consumers enforce monotonic epochs and idempotency.
- Recovery database corruption, checkpoint mismatch, missing event history or audit failure means quarantine, not automatic repair-and-resume.

## 7. Required audit evidence

Record, in the correct company stream: actor/service identity, company, stream, task/action, old and new epoch, decision, policy version, checkpoint digest, quarantine/release incident ID, approval/assessment IDs, event ID, timestamp, enforcement point, consumer acknowledgement and side-effect counter where applicable. Never put secrets or raw credentials in audit payloads.

The audit sink must be independently protected. A hash chain alone does not prevent a privileged writer from rewriting the entire chain; use signed checkpoints and separately administered immutable/WORM storage.

## 8. Acceptance tests — not yet executed

| ID | Scenario | Required result |
|---|---|---|
| RDE-01 | Quarantine while task is queued | Scheduler refuses lease; no runtime start |
| RDE-02 | Quarantine while task is running | Runtime cancels/halts permitted work; no new consequential calls |
| RDE-03 | Old lease presented after epoch increment | Deny and audit stale epoch |
| RDE-04 | Cached active state during authority outage | Fail closed |
| RDE-05 | Tool gateway receives active task but quarantined stream | Deny before protected read/write |
| RDE-06 | Outbox action queued before quarantine, authorization after quarantine | No sender invocation |
| RDE-07 | Dispatch authorization commits before quarantine | Mark potentially in flight; reconcile, never blind retry |
| RDE-08 | Duplicate/out-of-order quarantine event | Idempotent; highest epoch remains authoritative |
| RDE-09 | One consumer misses quarantine event | Authoritative preflight still denies; incident raised |
| RDE-10 | Queue redrive/dead-letter retry while quarantined | Deny; no duplicate side effect |
| RDE-11 | Paid model/compute request during quarantine | Cost gateway denies before provider call |
| RDE-12 | OCC/model/runtime attempts release | Deny; no state mutation |
| RDE-13 | Invalid, stale, revoked or wrong-scope owner approval | Release denied; approval not consumed |
| RDE-14 | Checkpoint/audit/revocation/emergency-stop unavailable | Release denied; stream remains disabled |
| RDE-15 | Valid recovery release | New epoch; fresh leases only; old intents remain held |
| RDE-16 | Restart/restore after quarantine | Starts disabled until full verification |
| RDE-17 | Cross-company stream/epoch substitution | Deny and security incident |
| RDE-18 | Concurrent quarantine and dispatch authorization | Linearizable ordering; no action authorized after committed quarantine |
| RDE-19 | Worker bypasses scheduler and calls tool directly | Gateway denies and alerts |
| RDE-20 | Trading live-order/wallet/transfer/withdrawal request after release | Absolute hard-deny remains in force |

Pass requires proof at the actual deployed scheduler, runtime, tool/data gateway, cost gateway, queue, outbox and external-action gateway, with side-effect counters and audit evidence. Unit tests or an event-bus acknowledgement alone are insufficient.

## 9. Production blockers

This contract does not implement the recovery registry, event transport, fencing, gateway hooks, distributed transaction/consensus, cryptographic identities, key custody, immutable checkpoint store, monitoring or incident automation. The existing SQLite references are offline single-host prototypes. Before production, choose and test a linearizable state/transaction design, define outage semantics, prove every execution path is mediated, conduct concurrency and partition tests, and independently review the implementation.

**Approval boundary:** architecture and scoped documentation only. No installation, deployment, workflow execution, paid usage, external account access, financial action or live trading is authorised.

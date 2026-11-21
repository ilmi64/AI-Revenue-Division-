# Outbox dispatch safety contract

Status: offline reference only. No external sender, account, broker, wallet or customer endpoint is connected.

## Dispatch lifecycle
- Queue immutable action intent with unique action_id and idempotency_key. Reuse of a key with different intent is rejected.
- Claim a pending item transactionally and assign a short lease. A claim increments a bounded attempt counter.
- A lease expiry alone MUST NOT cause automatic redelivery: the previous worker may have performed the side effect before crashing.
- Immediately before dispatch, revalidate principal/session, task state, company scope, current policy version, approval validity/consumption, resource limits, emergency stop and cancellation.
- Sender must support idempotency at the remote boundary. Local idempotency alone cannot prevent duplicate external effects.
- Persist the confirmed result idempotently. Repeated completion with the same result is harmless; conflicting completion is an incident.
- Timeout, process crash after send, or uncertain acknowledgement transitions to outcome_unknown. Do not retry until an independent reconciliation proves no effect or the remote idempotency contract proves safe replay.
- Retry only after evidence is recorded, with bounded attempts and backoff policy. Exhaustion moves to failed/quarantined, never infinite retry.
- Policy denial or cancellation before dispatch moves to cancelled. A claimed action is not dispatched if fresh policy fails.

## Required production controls
- Durable database transaction and lease compare-and-swap; worker identity authenticated and least-privileged.
- Remote idempotency key supported and retained by receiver for at least the full retry/reconciliation horizon.
- Separate policy gateway recheck immediately before side effect; fail closed on policy, approval, revocation, audit or emergency-stop unavailability.
- Append-only event trail for claim, denial, send intent, acknowledgement, unknown outcome, reconciliation and completion.
- Reconciliation adapter is read-only until separately approved; it must query authoritative remote state and record evidence reference.
- Alert on stale leases, outcome_unknown age, retry exhaustion, conflicting completion and duplicate remote receipts.
- Crash/fault-injection tests at every boundary: before claim commit, after claim, before send, after remote acceptance, before local completion commit, during reconciliation and during restart.
- No exactly-once guarantee is claimed across independent systems unless the receiver provides idempotency or a transactional protocol. The safe default for ambiguous side effects is stop and reconcile.

## Scope and safety
SQLite reference and tests use synthetic payloads and callback test doubles only. No network or financial execution occurs. Live trading, wallet signing, funds transfer, publication, customer messaging and purchases remain denied absent separate approval and production readiness review.

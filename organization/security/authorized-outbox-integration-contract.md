# Authorized outbox integration contract

Status: offline composition reference only. No live adapters, network sender, production identity issuer or deployment.

## Correct sequence
1. A trusted control plane creates an immutable task and principal context. Model-supplied claims are never authoritative.
2. An action intent is enqueued with stable action ID and idempotency key. Enqueue does not consume an owner approval.
3. A worker claims the action using the transactional outbox.
4. At the final dispatch boundary, a trusted resolver reloads principal and task from authoritative stores. The action payload is cross-checked against that context.
5. The deterministic gateway rechecks identity, task scope, current policy, emergency stop and Trading hard-deny rules.
6. If required, the gateway consumes the exact owner approval atomically once at this boundary. Approval binds company, agent/session, task, operation, resource, amount/limits, policy version, expiry and nonce in production.
7. Only an allow decision reaches the sender. Sender must enforce the same idempotency key at the remote boundary.
8. Audit decision and result. A timeout or crash with ambiguous external effect becomes outcome_unknown; reconcile with authoritative evidence before any retry.

## Critical invariants
- Never consume one-time approval during preflight and then consume it again at dispatch.
- Never dispatch using stale cached authorization. Final policy and emergency-stop reads are mandatory.
- Never trust principal/task identity fields supplied by the action payload; resolve from trusted stores and compare.
- Audit dependency failure denies. If audit is mandatory and unavailable, no sender call.
- No automatic retry of expired leases or ambiguous effects. Receiver-side idempotency or a documented transactional protocol is required.
- Trading live order, wallet signing, funds transfer, withdrawals, broker orders and HALT/STOP modification remain prohibited regardless of task allowlist.
- The sender must not be model-controlled and must not expose a bypass route.

## Known limitations
This reference composes existing offline interfaces but does not make them production-safe. The current gateway callback interface consumes approval during authorize; therefore call it exactly once, at final dispatch, for an approval-bearing request. A production implementation should split pure authorization evaluation from atomic approval consumption or provide a single atomic authorize-and-consume operation.
The current outbox uses a local SQLite store and test sender. The audit callback is a test interface. No distributed atomicity, signed permit, remote idempotency, crash recovery across systems or production cryptography is implemented.

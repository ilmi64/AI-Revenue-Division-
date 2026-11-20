# Unified linearizable recovery and dispatch control-store contract

Status: offline synthetic reference only; not production or deployed.

## Unified transaction domain
One company-scoped store holds stream recovery state and monotonically increasing
epoch, exact-scope approvals and consumption, canonical action intent and stable
idempotency key, dispatch state, audit append position, and transactional control
outbox events. The reference uses SQLite to demonstrate local serialization only.

## Required ordering
Quarantine and dispatch authorization must lock/update the same authoritative
company/stream state row in one strongly consistent transaction domain.

- If quarantine commits first, dispatch observes a non-active stream and denies.
- If dispatch authorization commits first, exact approval consumption, transition
  to dispatch_started and audit append commit together. Quarantine cannot recall
  an action already authorized or in flight.
- Quarantine increments the recovery epoch. Owner-gated release increments it
  again. Actions enqueued under an older epoch cannot dispatch after release.
- A crash after dispatch_started commit is ambiguous. Never auto-resend from
  local state alone. Timeout or exception becomes outcome_unknown.
- New work after release requires a new intent and fresh exact-scope approval.

## Recovery release
Release requires a trusted assessor and a separate owner-signed one-time approval.
Assessment must confirm database integrity, audit chain, checkpoint match, current
revocations, emergency-stop clear and reconciliation of unknown actions. Verify
documents outside the write transaction, then recheck incident, checkpoint and
epoch under the lock before commit.

The reference persists release approval IDs and nonces in a unique-key
consumption table in the same transaction as the release transition, preventing
local replay. Verifier objects are synthetic test doubles; cryptographic signature
verification is not implemented. Production must verify owner signatures through
a trusted asymmetric authority before atomic approval/nonce consumption and release.

## External side effects
No local database can atomically commit arbitrary remote HTTP, exchange, broker,
wallet or payment effects. Exactly-once delivery is not claimed. Production
receivers must enforce stable idempotency, immutable action digest, company and
recipient binding, operation/amount binding, recovery-epoch fencing, and signed
fresh outcome evidence. Without receiver-side epoch validation, a request
authorized before quarantine may arrive remotely after quarantine.

## Production blockers
- SQLite is a single-host reference, not production multi-node storage.
- No asymmetric signatures, KMS/HSM, trusted issuer or real cryptographic verifier.
- No independently administered WORM audit store or signed checkpoint signer.
- No receiver idempotency/epoch-fencing adapter or network sender.
- No production monitoring, backup/restore drill or independent security review.
- Synthetic tests do not establish production consistency or security.

## Safety
Trading live orders, wallet signing, transfers, withdrawals and risk-control
changes remain denied by the separate policy gateway. This reference does not
authorize or execute them. No GitHub Actions/CI is authorized by this contract.

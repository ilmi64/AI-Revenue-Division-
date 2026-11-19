# Recovery, reconciliation and backup-restore contract

Status: offline reference only. No production backup, remote receiver query, or recovery automation.

## Unknown external outcomes
- A timeout, worker crash after send, or lost acknowledgement is outcome_unknown, never an automatic retry.
- Reconciliation requires authenticated, fresh, authoritative receiver evidence bound to the original action ID and idempotency key.
- confirmed_applied closes the action as applied; do not send again.
- confirmed_not_applied closes the old intent. A new action intent must be created with a fresh final policy check and fresh owner approval when required. Never reset the old consumed approval or replay its action.
- inconclusive, stale, mismatched, unauthenticated or unavailable evidence remains quarantined and requires human/operator review.
- Receiver evidence should be signed or obtained over authenticated mutually authenticated channels and retained by digest plus protected evidence location.

## Crash recovery
- Worker lease expiry does not prove no external effect. Expired leased actions are quarantined/unknown, not automatically requeued.
- Recovery scans are read-only until reconciliation evidence is available.
- Any database integrity failure, missing audit link, duplicate action key or unknown schema version halts dispatch and raises an incident.
- Recovery must preserve approval consumption and never recreate approvals from model context.

## Backup and restore
- Backups must be encrypted, access-controlled, immutable where supported and stored separately from the primary database.
- Record backup ID, timestamp, database/schema version, company scope, audit-chain heads, approval consumption manifest and cryptographic digest.
- Restore into an isolated environment first. Verify schema, row counts, per-company audit chains, unique approval/nonce/action constraints, consumed-approval manifest and outbox state.
- Compare restored audit heads to independently protected checkpoints. A self-consistent local hash chain alone cannot prove no privileged rewrite.
- Restore tests must include point-in-time recovery, partial backup, corruption, key unavailability, stale checkpoint and cross-company leakage.
- Never resume dispatch automatically after restore. Require explicit recovery sign-off and revalidation of policy version, emergency stop, revocations and unknown actions.

## Production gate
Independent receiver reconciliation, protected evidence, durable event/outbox transactions, recovery runbooks, restore drills, least-privilege access and owner approval are required before any external action. Trading execution remains separately prohibited until its own risk and live-readiness gates pass.

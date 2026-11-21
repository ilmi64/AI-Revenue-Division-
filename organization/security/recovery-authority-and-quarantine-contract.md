# Independent recovery authority, quarantine and release contract

Status: proposed SQLite reference only; not production-enforced.

## Authority separation
The recovery authority is separate from company runtime/workforce and the OCC.
It can disable dispatch and record recovery state. It cannot create business
actions, alter Trading risk limits, move funds, sign transactions or resume a
worker by itself. A model, agent, Paperclip task, Ruflo plan or ordinary company
operator cannot release a quarantine.

## Quarantine
Any integrity failure, missing/stale/conflicting checkpoint, audit mismatch,
restore uncertainty, replay ambiguity, revoked key or unresolved external action
places the affected company/stream in quarantine. Quarantine disables dispatch.
It is idempotent for the same incident/checkpoint and is audited. A new incident
replaces the previous quarantine context and requires a new approval.

## Release requires two independent proofs
1. A trusted recovery assessor signs a fresh, scoped assessment bound to company,
   stream, incident and checkpoint digest. It must affirm database integrity,
   full audit-chain validity, exact checkpoint match, current revocations,
   emergency-stop clear state and reconciliation of unknown actions.
2. The owner supplies a cryptographically verified, one-time approval bound to
   the exact company, stream, incident, checkpoint digest, release action and
   recovery-authority audience. It expires and has a unique nonce.
3. The authority rechecks quarantine identity after signature verification, then
   consumes the approval and nonce, transitions the stream to active and appends
   the audit event in one transaction. A retry of the exact successful release
   is idempotent; a consumed approval cannot release a later incident.
4. Missing, stale, invalid, conflicting or out-of-scope evidence keeps the stream
   quarantined. There is no automatic release or timeout-based reopening.

## Reference limitations
The SQLite ledger is local and its hash chain is tamper-evident, not tamper-proof.
Test signers are synthetic. Production needs asymmetric signatures with KMS/HSM,
independent owner identity verification, separately administered recovery
assessor, immutable/WORM audit storage and signed external checkpoints,
shared transactional database, independent monitoring, backup/PITR and restore
drills, multi-node race testing, revocation/key rotation, incident runbooks and
explicit owner release. The caller must wire the actual trusted verifier
implementations; this prototype does not supply cryptographic signing.
No external dispatch, wallet, broker, payment or trading action is implemented.

## Initial activation
A newly registered stream begins in `dispatch_disabled`. It cannot be activated
directly. It must first have a concrete checkpoint and incident/release scope
recorded through quarantine, then pass the same signed assessment and owner
release gate. This intentionally prevents a default-on path.

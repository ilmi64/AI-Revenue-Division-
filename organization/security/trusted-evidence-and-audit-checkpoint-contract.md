# Trusted receiver evidence and audit checkpoint contract

Status: proposed security boundary; not production-enforced.

## Receiver evidence
- The recovery gateway accepts structured evidence, never a worker-supplied
  authenticated boolean or model-generated assertion.
- Evidence binds issuer, audience, company, action ID, receiver account,
  idempotency key, outcome, observation time, unique nonce and evidence ID.
- A trusted host adapter verifies the issuer's asymmetric signature against
  an independently administered issuer registry. Private signing keys remain
  with the receiver; verifier public keys are pinned/rotated through controlled
  key management.
- Evidence is rejected on signature failure, issuer mismatch, scope mismatch,
  stale/future timestamp, invalid outcome or replay.
- Signature covers canonical payload excluding the signature field.
- The verifier returns a normalized verified claim and payload digest. Only
  that output may be passed to the reconciliation transaction.
- The verifier's current in-memory nonce cache is demonstration-only. A separate
  SQLite replay-store prototype now demonstrates durable nonce and evidence-ID
  uniqueness across restarts and independent connections. It is not wired into
  the verifier by default. Production needs a shared transactional multi-node
  store, retention policy, backup/restore, failover testing and atomic claim after
  signature and scope verification.
- Receiver evidence must be independently retrieved or authenticated; an AI
  worker must not control the verifier callback, trusted issuer registry,
  receiver account binding, clock or replay store.

## Audit checkpoints
- Per-company audit chains remain separate.
- A checkpoint contains company ID, stream ID, sequence, event hash,
  checkpoint time, schema/policy version and signer key ID.
- An independent checkpoint authority signs the canonical checkpoint.
- The signature and checkpoint are stored outside the primary database in
  independently administered immutable/WORM storage.
- Restore verifies SQLite/database integrity, every event link, the latest
  trusted signed checkpoint, and that the restored stream reaches the
  checkpoint's exact sequence and hash. Missing, stale, rolled-back or
  conflicting checkpoints quarantine the company stream.
- A hash chain without a separately protected signed checkpoint cannot prove
  that a privileged actor did not rewrite the entire chain.

## Recovery hold
After restore or evidence-verification failure, dispatch remains disabled.
The owner receives an incident summary and must approve recovery only after
independent reconciliation, revocation refresh, emergency-stop refresh,
key status checks and audit verification.

## Production blockers
The reference uses an injected verifier and in-memory replay set. It does not
implement asymmetric cryptography, key management, durable replay storage,
receiver APIs, WORM storage, checkpoint signing, trusted clocks or production
monitoring. Never treat the reference tests as proof of production security.

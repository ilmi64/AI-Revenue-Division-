# OCC Hash-Linked Audit Event Contract

## Purpose

Provide deterministic, append-by-copy event construction and integrity checking
for OCC feed-conflict, quarantine, recovery-review and release-claim history.
Events can be passed between components as structured records. This module does
not write them to durable storage.

## Event model

Supported event types:

- FEED_CONFLICT_DETECTED
- QUARANTINE_ENTERED
- RECOVERY_REVIEW_REQUIRED
- RELEASE_CLAIM_RECORDED

Each event carries a contiguous sequence number, prior event SHA-256 digest,
event type, caller-supplied epoch timestamp, canonical instrument identity,
caller-supplied details, explicit false trust/authorization flags and its own
SHA-256 digest. JSON serialization is deterministic (sorted keys, compact
separators, UTF-8, non-finite numbers rejected).

Appending returns a new list and does not mutate the supplied prior list.
Verification checks sequence continuity, predecessor links, instrument identity,
false authorization flags and each event digest.

## Security limitations

This is a hash-linked integrity aid, not a trusted or tamper-proof audit ledger.
A party able to rewrite the entire sequence can recompute every hash. There is
no signature, trusted timestamp, external anchor, authenticated writer,
persistent append-only storage, access control, or independent evidence
verification. All event details and identities remain caller-supplied claims.
The verifier reports chain_authenticated=false, tamper_resistant=false and
persistent_audit_verified=false. A trusted host must provide authenticated
identity, protected durable storage, external anchoring and separation of
duties before relying on this history for release decisions.

All market-data trust, paper-use and execution flags remain false. No feed
polling, network access, notification, broker, exchange, wallet, persistence or
execution is performed.

## Validation status

Tests are authored but not executed. GitHub Actions remain on quota hold.

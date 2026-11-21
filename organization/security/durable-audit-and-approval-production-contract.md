# Durable audit and one-time authorization: production contract

Status: proposed design and local reference simulations only; not enforced or deployed.

## Audit event requirements
- Canonical UTF-8 JSON, sorted keys, compact separators, SHA-256 pinned by schema version; reject ambiguous floats and secret-bearing fields.
- Each event has globally unique event_id, monotonic per-stream sequence, timestamp, company_id, actor_id, event_type, classified payload, previous_hash and hash. Genesis previous hash is 64 zeroes.
- Verify sequence continuity, unique IDs, previous-hash links and event hashes on ingestion, export and recovery. Missing, reordered, duplicated or malformed events quarantine the stream and fail closed.
- Record decisions and outcomes, not credentials, bearer tokens, private keys, seed phrases, passwords, raw authorization headers or reusable approval material. Apply allowlisted payload schemas and redaction before persistence.
- Separate company streams and storage ACLs. OCC receives only approved summaries and integrity status, never unrestricted private event payloads.
- Hash chaining detects edits relative to a trusted checkpoint; it does NOT stop an attacker with write access from rewriting the entire chain.

## Production integrity controls
- Durable transactional append store with unique constraints on (stream_id, sequence) and event_id; serializable/compare-and-swap sequence allocation.
- Sign periodic chain checkpoints with asymmetric keys held by KMS/HSM; independent auditor verifies signatures. Anchor checkpoint digests outside the writer's administrative domain.
- WORM/immutable retention or equivalent object-lock controls, separate writer/auditor identities, least-privilege ACLs, encryption at rest/in transit, key rotation, retention/legal-hold policy, backup and restore drills.
- Alert and quarantine on signature failure, chain gap, duplicate, clock anomaly, unauthorized access or retention-policy drift.

## One-time owner approval consumption
- Approval is a signed, short-lived, single-action capability bound to owner, company, agent/session, task, exact operation, exact resource, amount/limits where relevant, expiry, policy version, audience and cryptographically random nonce/approval_id.
- Verify signature, issuer, audience, company, identity, session, exact scope, expiry, revocation, cancellation and current policy at the enforcement gateway immediately before action.
- Consume approval_id and nonce atomically in a durable transaction with unique constraints. A successful consumption must be committed before the external side effect is attempted.
- Coordinate action execution with a transactional outbox/idempotency key. Retries must return the same recorded outcome and must never repeat a non-idempotent side effect. Reconcile uncertain outcomes before retrying.
- Revocation and cancellation must propagate to all gateways; outages, stale policy, uncertain consumption, unavailable audit store or clock uncertainty fail closed.
- Never treat a model statement, chat history, consensus, or possession of an approval description as approval.

## Local demo limitations
The accompanying Python modules use in-memory lists/sets and a process-local lock. They are deterministic teaching/test fixtures only. They do not provide durable storage, cross-process or distributed atomicity, cryptographic owner signatures, authenticated identity, secure clock, external side-effect coordination, immutable retention or production key custody. Unit tests cannot establish those properties. Production requires database-specific transaction/unique-constraint tests, concurrency/fault injection, recovery drills, independent security review and deployment approval.

## Release gate
Do not connect these references to Paperclip, Ruflo, model runtimes, wallets, brokers, exchanges, customer systems or external-action gateways until separately approved, threat-modelled, implemented, independently tested and reviewed. Live trading and funds movement remain disabled absent separate authorization.

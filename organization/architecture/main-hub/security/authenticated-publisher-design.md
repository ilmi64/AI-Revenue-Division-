# Authenticated company publisher design v0.1

**Status:** Architecture proposal only. Not implemented, not security-certified, and not authorization to connect either company to the OCC.

## 1. Purpose and security boundary

Define how each independently governed company can publish a small, read-only operational snapshot to the Main Hub / OCC without allowing the OCC to become a company control plane.

The publisher is owned and operated by its company. The OCC is a consumer and display layer. A valid signature proves that a registered publisher key signed specific bytes; it does not prove that the reported business state is true, that evidence is sufficient, or that a readiness gate should pass.

The OCC must never infer permission to execute actions, move funds, change risk limits, deploy software, or alter company records from a received snapshot.

## 2. Trust domains and key separation

- AI Revenue and Trading & Technology each maintain a separate publisher identity, key registry, signing process, revocation process, and data store.
- Do not share private signing keys, key-management credentials, sequence counters, or company source records between companies.
- Each publisher key is scoped to exactly one company ID, one publisher ID, permitted schema versions, and a limited set of snapshot types.
- The OCC holds only the public verification keys and their approved metadata. It must never receive private keys, seed phrases, API credentials, or signing secrets.
- Initial public-key trust must be provisioned through an owner-approved, out-of-band process. A key cannot make itself trusted by appearing in a snapshot.
- Key creation, replacement, revocation, scope changes, and trust-root changes require an auditable owner-approved process. Model-generated recommendations cannot authorize these changes.

## 3. Proposed signed message

Use a detached Ed25519 signature over a precisely defined canonical byte representation. Before implementation, select and pin a standards-compliant canonicalization implementation (prefer RFC 8785 JSON Canonicalization Scheme) and publish cross-language test vectors. Reject duplicate JSON object keys, invalid UTF-8, non-finite numbers, integers outside the interoperable safe range, unsupported encodings, and ambiguous representations. Prefer integer-only protocol fields and prohibit floating-point values in signed claims.

The signed payload should contain only allowlisted OCC summary fields:

- `protocol_version`
- `schema_version`
- `company_id`
- `publisher_id`
- `key_id`
- `snapshot_id`
- `sequence` (monotonically increasing per publisher key)
- `issued_at` and `expires_at` (UTC RFC 3339 timestamps)
- `audience` (the intended OCC environment/instance)
- `source_revision` (the exact company-side revision or immutable source identifier)
- `payload_digest` (digest of the canonical snapshot payload)
- `snapshot` (the constrained summary record)

The signature input must bind the protocol/domain string, audience, company identity, publisher identity, key ID, sequence, timestamps, source revision, and payload digest. This prevents a valid message being repurposed for another company, environment, publisher, or protocol. The signature is detached from the canonical signed bytes; the precise byte layout and digest algorithm must be frozen in a versioned protocol specification before code is written.

Do not include credentials, private customer data, raw account records, wallet addresses, private strategy logic, private agent memory, or unrestricted logs in the snapshot.

## 4. Verification order

The receiving adapter should fail closed and perform checks in this order:

1. Enforce transport/body size limits, content type, UTF-8, duplicate-key rejection, and strict parsing.
2. Validate the outer envelope's exact field allowlist and protocol version.
3. Resolve the key ID from the OCC's pre-provisioned trust registry; reject unknown, expired, revoked, or out-of-scope keys.
4. Confirm company ID, publisher ID, audience, schema version, and snapshot type match the key's registered scope and the configured OCC instance.
5. Reconstruct the exact canonical signed bytes and verify the Ed25519 signature.
6. Recompute the canonical snapshot digest and compare it with the signed digest.
7. Validate the snapshot against the pinned JSON Schema Draft 2020-12 validator, including format assertion for timestamps, and apply semantic checks not expressible in the schema.
8. Validate timestamp bounds, expiry, permitted clock skew, and maximum snapshot age.
9. Atomically enforce replay and ordering controls.
10. Store the accepted message in an append-only receipt/audit record, then expose a sanitized summary to the read-only OCC view.

No data is displayed as authenticated before every applicable check succeeds. Authentication status and operational/readiness status remain separate fields.

## 5. Replay, ordering, freshness, and quarantine

- Maintain a durable, atomic uniqueness constraint on `(company_id, publisher_id, key_id, sequence)` and on `(company_id, snapshot_id)`.
- Reject duplicate or lower sequence numbers. Do not rely on wall-clock timestamps alone to prevent replay.
- Sequence allocation must be durable at the publisher and survive restart without reuse. Key rotation starts a new key-scoped sequence namespace; the trust registry records the accepted transition.
- Require `issued_at` not to be materially in the future, `expires_at` to be after `issued_at`, and message age to be within a configured maximum. The initial policy should be conservative and configurable per snapshot class; do not silently extend expiry.
- If the publisher clock is unreliable, mark the feed untrusted/stale and require remediation rather than weakening checks.
- Invalid signature, unknown/revoked key, wrong company/audience, schema failure, replay, sequence rollback, digest mismatch, or expiry sends the message to quarantine with a reason code.
- Quarantine must not replace or erase the last accepted snapshot. The OCC should show the last accepted data with its age and a prominent stale/unavailable state.
- Quarantine records contain only bounded diagnostic metadata and a digest/reference; never copy secrets or unrestricted payloads into logs.

## 6. Key lifecycle

Key states: `PENDING`, `ACTIVE`, `ROTATING`, `REVOKED`, `EXPIRED`.

- Provision: generate keys within an approved company-controlled key boundary; publish the public key, key ID, company/publisher scope, validity interval, and approval evidence through the out-of-band trust process.
- Activate: OCC accepts a key only after trust-registry approval and a controlled verification test.
- Rotate: approve and register the next public key before a defined overlap window; each message identifies exactly one key. Do not accept arbitrary fallback keys.
- Revoke: revoke immediately for suspected compromise; reject all newly received messages signed by that key after the effective revocation point. Preserve prior receipts for audit, but mark their trust status as requiring review if compromise may predate revocation.
- Recover: require a separately controlled recovery procedure and owner approval. A model or the compromised publisher must not be able to restore its own trust.
- Keep private-key operations inside the company's approved secret/key-management boundary. Do not put private keys in Git, fixtures, model context, OCC storage, or ordinary application logs.

## 7. Semantic and evidence checks

A valid signature is necessary but not sufficient. The adapter must also verify:

- The publisher is authorized to report the stated company and snapshot class.
- Gate IDs, blocker IDs, evidence IDs, and snapshot IDs are unique in their defined scope.
- Every gate evidence reference resolves to an evidence ID in the same company snapshot.
- Evidence references are immutable identifiers or content-addressed references; a reference string alone is not proof that evidence exists or was independently checked.
- Critical readiness gates remain unresolved unless their exact state is `PASS` and the referenced evidence has passed the appropriate independent verification process.
- `WAIVED` never becomes `PASS`; waiver authority and rationale must be recorded separately.
- Reported health, authenticated publisher status, evidence-verification status, and readiness assessment are distinct dimensions.

The OCC should display the publisher's reported status as a claim, separately from the OCC's own trust and freshness assessment.

## 8. Storage, availability, and recovery

- Use a durable receipt ledger with transactional uniqueness enforcement; do not use the current offline prototype or a single-process in-memory map as the production replay defence.
- Keep company-specific accepted snapshots partitioned by company identity and access policy.
- Preserve receipt metadata: message digest, publisher/key IDs, sequence, timestamps, audience, verification result, schema version, source revision, and quarantine/acceptance reason.
- Make ingestion idempotent. A retry of the same message must not create a second accepted event or advance the displayed state.
- If the receipt store is unavailable, reject/defer ingestion; do not bypass replay checks or fall back to unauthenticated display.
- Backups, restoration, key-registry recovery, and replay-ledger consistency need a tested recovery procedure before production use.

## 9. Required test programme before any adapter is trusted

Create deterministic test vectors shared across publisher and receiver implementations. At minimum test:

- valid signature and valid payload;
- modified payload, digest, signature, company ID, publisher ID, audience, key ID, schema version, and source revision;
- unknown, expired, revoked, out-of-scope, and rotated keys;
- duplicate JSON keys, invalid UTF-8, oversized input, malformed envelope, unsupported protocol version;
- duplicate snapshot ID, duplicate sequence, lower sequence, concurrent duplicate delivery, and retry after receiver restart;
- future-issued, expired, malformed, timezone-naive, and excessive-age timestamps;
- schema violations, unknown gate evidence IDs, duplicate record IDs, and invalid evidence references;
- quarantine preserves the last accepted snapshot and never upgrades a status;
- company A's key cannot publish for company B;
- OCC outage and replay-ledger recovery fail closed.

A test pass demonstrates only the tested implementation and threat cases. It is not a security certification.

## 10. Rollout gates

**Gate A — protocol freeze:** canonicalization, signature input, digest, timestamp policy, schema versioning, and test vectors reviewed and pinned.

**Gate B — independent publisher prototype:** each company implements its own publisher and test keys in isolated non-production environments. No live company records are exported.

**Gate C — receiver verification:** OCC verifies signatures, scope, schema, freshness, sequence, replay, and quarantine using synthetic test vectors only.

**Gate D — security and recovery review:** key custody, rotation/revocation, durable replay storage, audit integrity, access control, backup/restore, and incident response independently reviewed.

**Gate E — owner authorization:** only after prior gates pass may the owner separately approve a limited read-only connection for one company. Approval for one company does not authorize the other.

No gate in this document is currently passed. No publisher, key, adapter, or live connection is currently claimed to exist.

## 11. Explicit non-goals

This protocol does not authorize the OCC to issue commands, approve company actions, manage budgets, access private company records, change trading risk, trigger agent tasks, or make live-trading decisions. Those require separate company-owned interfaces, deterministic policy enforcement, and explicit owner approval where applicable.

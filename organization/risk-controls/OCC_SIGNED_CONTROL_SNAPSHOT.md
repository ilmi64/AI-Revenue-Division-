# OCC Signed Control Snapshot — Producer Contract

**Status:** Versioned producer contract for the PolyBot paper interlock. No running publisher or transport is included.

## Contract alignment

The snapshot object is defined by `organization/risk-controls/occ-control-snapshot.schema.json` and must match the PolyBot `build_occ_veto_proposals` contract exactly. Unknown fields are rejected. The signature is carried separately from the snapshot so the signed bytes are unambiguous.

## Producer requirements

- Emit only `schema_version: 1` and `source_system: OCC`.
- Assign a unique, bounded `snapshot_id` to every snapshot.
- Use finite UTC epoch timestamps. `generated_at_epoch` must be earlier than `expires_at_epoch`; TTL must be short and bounded (the current PolyBot receiver default is 300 seconds).
- Keep `generated_at_epoch` strictly increasing across accepted snapshots. Persist the producer's last generated timestamp and snapshot ID across restarts; a clock rollback must stop publication and raise an incident rather than emit an older snapshot.
- Include the exact approved `policy_sha256` and current `portfolio_version`; do not guess, default or silently advance either value.
- Use `CLEAR` only when all OCC stop conditions are affirmatively clear. Use `HALT` for any applicable stop condition, with at least one allowlisted condition and evidence reference.
- Never encode an order, size, leverage, routing, wallet, signing or execution instruction in the snapshot.

## Authentication envelope

The PolyBot receiver expects a lowercase 64-character HMAC-SHA256 signature over the canonical snapshot bytes:

1. Serialize the snapshot as UTF-8 JSON with keys sorted lexicographically.
2. Use compact separators `(',', ':')`, `ensure_ascii=False` and `allow_nan=False`.
3. Calculate HMAC-SHA256 with a secret of at least 32 bytes.
4. Send the snapshot and lowercase hexadecimal MAC over an authenticated, encrypted transport.

The secret must be provisioned out of band, never committed to Git, never placed in the snapshot, and never sent alongside the message. HMAC is shared-secret authentication: it does not distinguish individual holders of the same key. Key rotation, revocation, sender identity binding and secret-manager integration require a separate security design.

## Delivery and acknowledgement

A producer must not assume a snapshot was applied merely because it was generated or transmitted. The receiver acknowledgement must identify the snapshot ID and result. Delivery failure, missing acknowledgement, authentication failure, replay rejection or receiver unavailability must be recorded as an OCC incident and keep the trading interlock unavailable. Retry logic must not mutate a previously signed snapshot; create a new, later snapshot ID and timestamp when state changes or a retry policy requires a fresh message.

## Semantics

- A validated `HALT` becomes a SYSTEM/HALT veto in PolyBot and blocks new exposure.
- A validated `CLEAR` only confirms the current OCC snapshot; it never clears an already active PolyBot veto.
- Only the existing explicit operator-clearance workflow may clear a veto, with acknowledgement and recorded rationale.
- Invalid or missing OCC state is never interpreted as CLEAR.

## Validation and limitations

This file is a producer-side contract, not an executable publisher. No HMAC secret, key store, message queue, network transport, acknowledgement service, live feed or production connection is included. The PolyBot receiver is currently specified as single-process/single-writer and its tests have not been run. Before runtime use, both repositories need schema conformance tests, sender/receiver interoperability tests, clock rollback tests, crash/restart tests, independent security review and owner approval. Live trading remains disabled.

## Implemented producer library

`occ_snapshot_publisher.py` now provides:
- `SnapshotSequenceStore.issue(...)` for validated CLEAR/HALT snapshots with a persistent monotonic timestamp guard;
- `sign_snapshot(...)` for canonical HMAC-SHA256 signing;
- `write_envelope_atomic(...)` for atomic local/shared-filesystem publication with restrictive file permissions.

The emitted envelope is exactly `{snapshot, signature_hex}`. The publisher library is not a daemon and does not decide whether OCC is CLEAR. The caller must derive status from the approved OCC risk state, pass the current policy digest and portfolio version, and publish only after those inputs are verified. The shared inbox must be protected by filesystem permissions. No cross-machine network transport is included.

`policy_file_sha256(path)` calculates the exact digest from the approved policy file bytes. PolyBot must be configured with the same digest; a policy change requires a deliberate digest update and a fresh snapshot.
A test-only cross-repository HMAC vector is stored at `fixtures/occ-control-envelope.test.json` and duplicated in PolyBot's `tests/fixtures/`. Both repositories' unit tests verify the same canonical signature. Its public test secret must never be reused for any deployment.

## Conservative Main Hub publisher

`occ_fail_closed_publisher.py` adds a manual, HALT-only publishing entry point for the current governance baseline. It reads the authoritative policy file, calculates its exact digest, issues a 60-second signed HALT snapshot with `required_owner_approval_missing`, and atomically writes the envelope to the configured trusted local inbox.

This publisher deliberately has no CLEAR path. Even changing the policy status field to an apparently approved value cannot make this function emit CLEAR. A future clearance publisher must be a separately reviewed implementation backed by an approved OCC state aggregator, complete readiness evidence, explicit owner approval, and tested restart/incident gates.

Example invocation (only on a prepared host with both repositories and protected filesystem paths):

```bash
export OCC_HMAC_SECRET_HEX='<fresh locally provisioned secret hex>'
python organization/risk-controls/occ_fail_closed_publisher.py \
  --policy organization/risk-controls/risk-control-policy.json \
  --sequence-db /secure/occ/sequence.sqlite3 \
  --inbox /secure/shared/occ-control-envelope.json \
  --portfolio-version 0  # replace with the current durable PolyBot paper portfolio version
```

The command is manual and is not started by this repository. The portfolio version must be read from the current durable PolyBot paper state; a mismatch is rejected by PolyBot. Never commit the secret or place it in chat. The publisher is not a daemon and does not start trading.
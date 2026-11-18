# OCC Persistent Snapshot History

**Status:** Offline local journal prototype. Research-only. Not a running service.

## Purpose

Store successive unified OCC research-intelligence snapshots in a local JSONL
history. Each entry contains the snapshot, its canonical SHA-256 digest, a
sequence number, the previous entry hash and a hash of the complete journal
entry. This makes later edits, missing rows and broken ordering detectable
relative to the recorded chain.

## Append

Run from `organization/market-divisions`:

```bash
python -m specialist_research.snapshot_history append \
  --history /path/to/private/occ-snapshots.jsonl \
  --snapshot /path/to/unified-intelligence.json \
  --appended-at-utc 2026-11-17T18:00:00Z
```

The input must be a unified OCC research-only snapshot with explicit stop state,
UTC generation time and hard-false trade/live authority fields. The journal
assigns a deterministic snapshot ID from the canonical snapshot content.
Identical snapshots are not appended twice.

## Verify

```bash
python -m specialist_research.snapshot_history verify \
  --history /path/to/private/occ-snapshots.jsonl
```

Verification checks JSONL integrity, row sequence, previous-hash linkage,
snapshot digest, deterministic snapshot identity, record hash, authority
markers, UTC timestamps and stop continuity.

## Stop persistence

If any verified prior snapshot records `global_stop_active=true`, a later
snapshot with `global_stop_active=false` is rejected. This prototype has no
stop-clearance workflow. It cannot authorize a stop to be cleared; an
independent, separately governed clearance process must be designed and
approved before that capability exists.

## Safety and limitations

- Standard-library local file processing only; no network, API, broker, wallet,
  signing, orders, publishing or deployment.
- Single-writer operation is required. Concurrent writers are not coordinated.
- File permissions, encryption, backups, access control and trusted storage
  remain the operator's responsibility.
- SHA-256 hash chaining is an integrity aid, not a digital signature, identity
  proof, tamper-proof storage or defence against an attacker who can rewrite
  the entire journal.
- The journal does not independently verify source evidence or position
  reconciliation; it records the snapshot as supplied.
- A valid journal does not imply live readiness or trading permission.
- The regression tests are authored but have not been executed in a local
  supported Python environment. The existing organisation workflow does not
  discover this specialist-research test directory.

# OCC Incident and Control-Event History

**Status:** Offline local prototype. Research-only. Not a live incident service.

## Purpose

Record a chronological event stream for incidents, specialist stop raises and
challenges, corrective actions, recovery evidence, day/night handovers and
stop-clearance requests. The ledger is separate from snapshot history: snapshots
record state; this ledger records the events that explain changes and review.

## Supported event types

- `incident_opened`, `incident_closed`
- `stop_raised`, `stop_challenged`
- `corrective_action_proposed`, `corrective_action_verified`
- `recovery_evidence_added`
- `handover_recorded`
- `stop_clearance_requested`

Stop-related events require evidence references. A clearance request is only
recorded as `pending` or `rejected`. There is deliberately no event that
clears the global stop. A challenge, corrective action, incident closure or
recovery-evidence record cannot clear a stop.

## Append and verify

Run from `organization/market-divisions`:

```sh
python -m specialist_research.incident_event_ledger append \
  --ledger /path/to/private/occ-events.jsonl \
  --event /path/to/event.json

python -m specialist_research.incident_event_ledger verify \
  --ledger /path/to/private/occ-events.jsonl
```

The event envelope uses sequence numbers, previous-entry SHA-256 links,
canonical event digests and complete-entry hashes. The JSON Schema is
`incident-event-ledger.schema.json`.

## Safety and limitations

- Local standard-library processing only; no network, broker, wallet, orders,
  signing, publishing, deployment or background service.
- Single-writer only; concurrent appenders are not coordinated.
- Hash chaining is an integrity aid, not a digital signature, identity proof,
  trusted timestamp, access-control mechanism or tamper-proof storage.
- The actor identifier is supplied metadata, not authenticated identity.
- Event records are not independently verified evidence; reviewers must inspect
  the referenced evidence through a separate controlled process.
- Stop state is monotonic in this prototype. Any future stop-clearance process
  requires a separately specified, independently approved control and must not
  be inferred from a corrective-action or incident-closure event.
- Regression tests are authored but have not been executed.

# OCC Day/Night Handover Reconciliation

**Status:** Offline, read-only audit prototype. Research-only.

## Purpose

Audit explicit `handover_recorded` events in the incident/control-event
journal. The audit checks shift acknowledgements, position reconciliation,
dependency health, evidence references, unresolved critical items, duplicate
handover identities/transitions and continuity between consecutive handovers.

## Handover event contract

The event's `details` object must include:

- `handover_id`, `outgoing_shift_id`, `incoming_shift_id`
- `snapshot_id` and `portfolio_version`
- `outgoing_acknowledged=true`, `incoming_acknowledged=true`
- `positions_reconciled=true`
- `dependency_health` (must be `healthy` for acceptance)
- `active_veto_ids` (explicit list; active vetoes are carried forward and
  reported, never cleared by handover)
- `unresolved_critical_items` (must be explicitly empty for acceptance)

The event itself must have evidence references, an actor identifier and UTC
occurred/recorded timestamps, as required by the incident event ledger.

## Run

From `organization/market-divisions`:

```sh
python -m specialist_research.handover_reconciliation \
  --event-ledger /path/to/private/occ-events.jsonl \
  --output /path/to/private/occ-handover-audit.json
```

Exit codes: `0` means the recorded handovers passed the checks; `1` means
the audit is blocked; `2` means an input or parsing/validation error occurred.

## Interpretation and safeguards

- The underlying event ledger must pass hash-chain verification first.
- A missing handover event cannot be inferred from an expected shift schedule;
  this tool has no schedule source. It reports gaps between recorded shift
  transitions as warnings, not proof that an event was omitted.
- Duplicate handover IDs or repeated shift transitions are errors.
- Active vetoes are preserved and reported as of the handover event's
  `occurred_at_utc`. Every identified `stop_raised` event that occurred at or
  before that timestamp must be present in the handover's `active_veto_ids`;
  a later stop does not retroactively invalidate an earlier handover. Missing
  carry-forward blocks acceptance. A handover does not clear a stop.
- Open incidents remain visible in the report.
- Missing acknowledgements, unreconciled positions, unhealthy dependencies,
  missing evidence, or unresolved critical items block acceptance.
- No event is written, no source ledger is changed, and no stop is cleared.
- Hash chains do not authenticate evidence, identity or trusted time.
- This is not continuous monitoring and does not reconcile live broker,
  exchange, wallet, order or position state.
- Output always has `trade_authority=false` and `live_readiness=false`.
- Regression tests are authored but not executed.

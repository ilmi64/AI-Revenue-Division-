# OCC Audit and Reconciliation

**Status:** Offline, read-only reconciliation prototype. Research-only.

## Purpose

Compare the independently hash-verified OCC snapshot journal with the
independently hash-verified incident/control-event journal. The audit reports
missing history, invalid hash chains, disagreement over the latched global-stop
state, and mismatched stop identifiers.

## Run

From `organization/market-divisions`:

```sh
python -m specialist_research.audit_reconciliation \
  --snapshot-history /path/to/private/occ-snapshots.jsonl \
  --event-ledger /path/to/private/occ-events.jsonl \
  --output /path/to/private/occ-audit-report.json
```

Exit codes:
- `0`: histories passed integrity and cross-ledger checks.
- `1`: audit found inconsistency or missing snapshot state.
- `2`: input or parsing/validation error.

## Reconciliation rules

1. Both journals must independently pass their hash-chain and record validation.
2. At least one snapshot must exist; an empty snapshot history cannot be called
   consistent.
3. The latest snapshot global-stop boolean must match the event ledger's
   monotonic stop state.
4. If a snapshot stop has a `stop_id`, a matching `stop_raised` event must
   exist with `details.stop_id`.
5. If a `stop_raised` event has a `stop_id`, the latest active snapshot must
   contain that stop ID.
6. Events or snapshot stops lacking IDs are reported as warnings because exact
   correlation is impossible. Warnings do not authenticate the evidence.

The prototype intentionally treats every `stop_raised` event as latched. It
does not model an approved stop-clearance workflow, and it must not infer one
from incident closure, challenges, corrective actions or recovery evidence.

## Limitations

- Read-only and offline; no writes to either source ledger.
- No database, service, scheduler, alerting or continuous monitoring.
- No source-evidence authentication, signer identity, trusted timestamp or
  cryptographic signature.
- Hash chaining is not tamper-proof if an attacker can rewrite the whole chain.
- Does not reconcile portfolio positions, orders, P&L, broker balances or
  actual execution state.
- Does not prove the content of a snapshot is truthful; it checks consistency
  of the supplied records.
- Research-only output; `trade_authority=false` and
  `live_readiness=false` unconditionally.
- Regression tests are authored but not executed.

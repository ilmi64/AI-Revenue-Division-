# OCC Read-Only Incident Intake Contract

## Purpose

Provide a common reporting shape for incidents surfaced by independently operated divisions. OCC may consolidate and prioritize supplied snapshots; it does not gain authority to alter a source system merely by receiving an incident.

## Normalized record

Required fields:

| Field | Meaning |
|---|---|
| `source_system` | Stable identifier for the originating system |
| `source_incident_id` | Stable ID within that source system |
| `division` | Owning division, e.g. Crypto, Forex, Indices, Gold |
| `severity` | Source severity or explicitly documented adapter policy |
| `status` | `OPEN`, `ACKNOWLEDGED`, or `RESOLVED` |
| `reason_code` | Machine-readable cause |
| `summary` | Short, non-sensitive explanation |
| `observed_at_epoch` | First observation time |
| `updated_at_epoch` | Latest source update time |

Optional `instrument` identifies the exact instrument/contract. Do not collapse unlike instruments: SOL/CAD, BTC/USD, an FX pair, an index contract, and XAUUSD require distinct source identities and their own market/contract controls.

## Reporting semantics

- OPEN and ACKNOWLEDGED are active. RESOLVED is retained for audit context but excluded from active counts.
- Staleness is a reporting flag based on the incident's observed age and a configurable threshold. It is not proof that a source is still failing and does not resolve anything.
- Duplicate `(source_system, source_incident_id)` pairs in one snapshot are rejected.
- Timestamps in the future or internally inconsistent timestamps are rejected.
- Reports are deterministic for the same input and reporting time.

## Solana paper-exit adapter

`occ/solana_exit_adapter.py` implements a callable, read-only adapter against the two query methods exposed by the Solana CoordinationStore contract:

- `unresolved_exit_market_data_incidents()`
- `unresolved_position_exits()`

It does not import the Solana repository, open its database, instantiate a store, poll a runtime, or mutate source state. A caller must explicitly supply a compatible source object and a reporting timestamp.

Stable source identities are namespaced separately for market-data incidents and position-exit operations. Market-data records preserve their reason code and first/last-seen timestamps. Position-exit records preserve operation identity, creation time and source workflow status. OCC status remains OPEN because the source query contract does not provide authenticated OCC acknowledgement. No source record is acknowledged or resolved.

**Severity policy:** both unresolved market-data incidents and unresolved position exits are mapped to CRITICAL because either means paper-exit safety or reconciliation is uncertain. This is an explicit conservative adapter policy, not a severity field supplied by the source. Review this policy before broadening the adapter to other incident classes.

## Current implementation limits

The adapter is a pure callable transformation and report builder. It is not connected to an OCC runtime, scheduler, dashboard, database, notification transport, credentials, account integration, or execution capability. Other divisions require their own reviewed adapters and source-of-truth checks.

## Approval and safety boundary

This contract does not authorize source-system writes, operator acknowledgement, incident resolution, account lockout, trading, order routing, wallet access, or live operations. Those actions remain outside OCC's read-only reporting role and require separate reviewed controls and owner approval.

Tests are authored, not executed; GitHub Actions remain on quota hold.

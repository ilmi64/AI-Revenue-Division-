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
| `severity` | Source-assigned `INFO`, `WARNING`, or `CRITICAL` |
| `status` | Source status: `OPEN`, `ACKNOWLEDGED`, or `RESOLVED` |
| `reason_code` | Machine-readable cause |
| `summary` | Short, non-sensitive explanation |
| `observed_at_epoch` | First observation time |
| `updated_at_epoch` | Latest source update time |

Optional `instrument` identifies the exact instrument/contract. Do not collapse unlike instruments: SOL/CAD, BTC/USD, an FX pair, an index contract, and XAUUSD require distinct source identities and their own market/contract controls.

## Reporting semantics

- Source severity is preserved; the aggregator does not silently upgrade or downgrade it.
- OPEN and ACKNOWLEDGED are active. RESOLVED is retained for audit context but excluded from active counts.
- Staleness is a reporting flag based on the incident's observed age and a configurable threshold. It is not proof that a source is still failing and does not resolve anything.
- Duplicate `(source_system, source_incident_id)` pairs in one snapshot are rejected.
- Timestamps in the future or internally inconsistent timestamps are rejected.
- Reports are deterministic for the same input and reporting time.

## Current implementation

`occ/incident_intake.py` is a pure in-memory validator and report builder. It accepts snapshots supplied by a caller. It has no network client, database, scheduler, notification transport, credentials, account integration, or execution capability.

The Solana paper-exit escalation bridge in the separate `Solana-memecoins` repository is a candidate source adapter, not a connected runtime. It must be reviewed and mapped explicitly before use. Other divisions require their own adapters and source-of-truth checks.

## Approval and safety boundary

This contract does not authorize source-system writes, operator acknowledgement, incident resolution, account lockout, trading, order routing, wallet access, or live operations. Those actions remain outside OCC's read-only reporting role and require separate reviewed controls and owner approval.

No tests are claimed as executed in this change; GitHub Actions remain on hold.

# OCC Division Health Reporting Contract

## Purpose

The division health report is a read-only aggregation primitive for snapshots supplied by a caller. It is intended to give the Main Hub a consistent way to summarize component health across Crypto, Forex, indices, Gold, research, infrastructure and supporting divisions.

It is not a polling service, monitoring daemon, readiness certification, deployment gate, or trading authority.

## Snapshot fields

Each input mapping requires:

- `division`: owning division name.
- `component`: component or service within that division.
- `source_system`: caller-declared source identifier.
- `health_status`: `HEALTHY`, `DEGRADED`, `FAILED`, or `UNKNOWN`.
- `observed_at_epoch`: finite, non-negative observation time, not in the future.

Optional fields:

- `evidence_level`: `UNVERIFIED` (default), `ADAPTER_VALIDATED`, or `SOURCE_VERIFIED`.
- `summary`: descriptive text.
- `source_reference`: non-empty reference to supporting evidence.

The source identifier and evidence level are caller-supplied labels. The validator does not authenticate an adapter, endpoint, transport, signature, source record or evidence artifact. A value of `SOURCE_VERIFIED` is not proof of verification by this module.

## Aggregation rules

- Duplicate `(division, component, source_system)` identities in one snapshot batch are rejected.
- Future, invalid, boolean, non-finite and negative timestamps are rejected.
- Observations at or beyond the stale threshold are marked stale and their effective health becomes `UNKNOWN`.
- Missing entries from the caller's `expected_divisions` list are reported and counted as `UNKNOWN`.
- Aggregate severity ordering is `HEALTHY < UNKNOWN < DEGRADED < FAILED`; a failed component cannot be hidden by healthy components.
- Empty input yields `UNKNOWN`, never `HEALTHY`.

## Health is not readiness

Every report sets `readiness_assessed=false` and `operational_ready=false`. A healthy heartbeat or component snapshot cannot establish:

- authenticated and independent market data;
- strategy validity or out-of-sample performance;
- risk, legal, regulatory or halal approval;
- broker/exchange account permissions or funding;
- resilience, incident response or operational staffing;
- paper-to-live equivalence or permission to execute.

A separate, independently reviewed readiness process must evaluate those controls for each market and instrument. Gold/XAUUSD requires its own contract, quote unit, custody, possession, settlement, financing and margin review. Forex and indices likewise require their own venue, quote, contract and financing specifications.

## Explicit non-capabilities

This module does not poll divisions, persist snapshots, create incidents, acknowledge or resolve incidents, notify operators, schedule work, connect to a broker/exchange, access credentials, or submit orders. It does not change any source state.

## Verification status

The module and unit tests are proposed code. Tests have been authored but not executed. No GitHub Actions run is authorized while the quota hold remains.

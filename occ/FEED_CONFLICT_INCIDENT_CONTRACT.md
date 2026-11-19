# OCC Feed-Conflict Incident Projection Contract

## Purpose

Convert an explicit `CONFLICT_DETECTED` result from the OCC independent-feed
agreement diagnostic into a normalized, OPEN OCC incident snapshot. Other
agreement statuses produce no incident.

## Projection rules

- Requires the diagnostic's trust and authorization flags to remain explicitly
  false.
- Requires at least two accepted observations with unique source IDs.
- Requires a finite diagnostic spread strictly greater than the configured
  non-negative threshold.
- Emits severity CRITICAL, status OPEN, division OCC and reason code
  MARKET_DATA_SOURCE_CONFLICT.
- Uses the exact instrument symbol for incident context and sorts source IDs
  for deterministic incident identity.
- Includes spread/threshold as diagnostic metadata only; it does not select a
  correct feed or price.

## Authority boundary

This is an in-memory projection only. It does not import or invoke an incident
store, persist records, acknowledge or resolve incidents, send notifications,
contact operators, halt external systems, or invoke trading/execution. The
result's `read_only_projection`, `source_mutation_performed`,
`notification_sent` and `execution_eligible` fields make that boundary
explicit.

A downstream incident intake may validate the returned mapping, but this
module does not wire itself into a runtime or claim delivery/receipt.

## Test and operational status

Tests are authored but not executed. GitHub Actions remain on quota hold.

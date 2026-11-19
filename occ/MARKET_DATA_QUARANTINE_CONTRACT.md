# OCC Market-Data Quarantine and Recovery Review Contract

## Purpose

Provide a pure deterministic state transition for instrument-scoped market-data
quarantine. It consumes the independent-feed agreement diagnostic and an
optional prior state snapshot. It does not persist the state or control a
runtime.

## States and transitions

- NOT_QUARANTINED: no conflict is present in the supplied diagnostic and no
  prior quarantine is active.
- QUARANTINED: a validated CONFLICT_DETECTED report is received, or a prior
  quarantine remains without sufficient recovery evidence.
- RECOVERY_REVIEW_REQUIRED: a quarantined instrument later has
  AGREEMENT_WITHIN_THRESHOLD_UNVERIFIED with at least two unique source IDs,
  or an operator release claim is recorded.

A later agreement never clears quarantine. Insufficient sources, rejected
inputs or unverified group labels preserve quarantine. Repeated conflicts
preserve the original quarantine timestamp and increment a conflict counter.

## Manual review boundary

An APPROVE_RELEASE claim may be recorded with reviewer ID, evidence reference
and review timestamp. These remain caller-supplied claims, not authenticated
identity or evidence. The state remains RECOVERY_REVIEW_REQUIRED;
release_authorized remains false. A trusted host must separately authenticate
reviewer authority, verify independent fresh sources and evidence, enforce
separation of duties, and durably audit an approved release before any future
implementation can clear quarantine. That host mechanism is not implemented.

## Fail-closed guarantees

All outputs keep market_data_trusted, paper_use_authorized and
execution_eligible false. No automatic recovery, persistence, notification,
external system mutation, feed polling, credentials, broker, exchange, wallet
or execution is performed. Prior state is caller-supplied and unauthenticated;
this function is not a tamper-resistant ledger.

## Test and operational status

Tests are authored but not executed. GitHub Actions remain on quota hold.

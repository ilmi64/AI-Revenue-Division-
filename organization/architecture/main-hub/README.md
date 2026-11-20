# Main Hub / OCC v0.1 records

**Status:** Draft schema, synthetic fixtures and an offline read-only reference prototype. Not operational.

This directory defines the first data contract and local prototype for the read-only OCC.

## Ownership and staging
The prototype currently resides in the AI Revenue architecture branch only as a temporary shared-workstream staging location because no dedicated Main Hub repository has been established. This placement does not make OCC an AI Revenue-controlled authority. Company decision rights, data ownership and risk controls remain independent. Do not use this prototype for live company decisions.

## Files
- `schema/records.schema.json`: JSON Schema draft 2020-12 envelope and reusable definitions.
- `fixtures/ai-revenue.snapshot.example.json` and `fixtures/trading-technology.snapshot.example.json`: synthetic snapshot fragments, each corresponding to `$defs.snapshot`.
- `fixtures/registry-and-workstreams.example.json`: synthetic registry/workstream fragment corresponding to `$defs.company` and `$defs.workstream`.
- `fixtures/decisions.example.json`: empty decision-log fragment corresponding to `$defs.decision`.
- `prototype/`: Python-standard-library offline report generator and tests. This is a reference prototype, not a deployed OCC service.

The fixture fragments are intentionally not complete root-envelope documents. The root schema requires the complete envelope with registry, decisions, workstreams and one snapshot; the fragments are separated to keep each synthetic record easy to inspect.

## Safety properties
- Both company IDs are fixed and distinct.
- Prototype input uses a strict allowlist; unexpected fields and company identity mismatches are rejected.
- Credentials, raw company records, customer data, wallet details, private keys and unrestricted agent memory are not part of the contract.
- Synthetic examples use `UNKNOWN` and `NOT_RUN`; they must never be presented as live status.
- `WAIVED` is recorded but never counts as a critical gate pass.
- The prototype has no authenticated publisher adapter. All sources remain untrusted; non-synthetic but unauthenticated data also remains `UNKNOWN`.
- Stale data is displayed as `STALE`; missing or malformed inputs fail closed.

## Validation
The prototype and its tests use only Python's standard library. Ten tests have been authored but **not yet executed** against the committed revision. Full JSON Schema draft 2020-12 validation has also **not yet been executed**. Do not install packages or trigger GitHub Actions under the current approval restrictions. Record validator name/version and exact commit when validation is later performed in an already-available offline environment.

## Current status
**M1 contract drafted; M2 offline reference prototype committed; test execution and full schema validation pending; authenticated adapters absent; not operational.**

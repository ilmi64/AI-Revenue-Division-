# Main Hub / OCC v0.1 records

**Status:** Schema and synthetic fixtures only. No application, authenticated adapter, or production service is implemented.

This directory defines the first canonical data contract for the read-only OCC prototype.

## Files
- `schema/records.schema.json`: JSON Schema draft 2020-12 definitions for company registry entries, decisions, workstreams, status snapshots, gates, blockers and evidence references.
- `fixtures/ai-revenue.snapshot.example.json`: synthetic AI Revenue status snapshot.
- `fixtures/trading-technology.snapshot.example.json`: synthetic Trading & Technology status snapshot.
- `fixtures/registry-and-workstreams.example.json`: synthetic company and workstream examples, including REA/strategy intelligence.
- `fixtures/decisions.example.json`: empty decision-log starter; add only traceable decisions with explicit approval state and source evidence.

## Safety properties
- Both company IDs are fixed and distinct.
- Snapshot fields are allowlisted; unknown fields are rejected by schema validation.
- Credentials, raw company records, customer data, wallet details, private keys and unrestricted agent memory are not part of the contract.
- Synthetic examples use `UNKNOWN` and `NOT_RUN`; they must never be presented as live status.
- `WAIVED` is recorded as a gate state but does not make a critical gate pass. OCC cannot waive company gates.
- A schema-valid snapshot is not authenticated or trusted by itself. Publisher authentication, replay protection, freshness and source-revision checks belong to the adapter layer and remain unimplemented.

## Validation
Use a JSON Schema draft 2020-12 validator in an offline development environment. No package installation or GitHub Actions run is authorized by this document. Record validator name/version and exact commit when tests are later run.

## Current status
**M1 contract drafted; schema validation not yet executed; fixtures are synthetic; not operational.**

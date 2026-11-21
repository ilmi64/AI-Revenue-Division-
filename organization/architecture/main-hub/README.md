# Main Hub / OCC v0.1 records

**Status:** Draft schema, synthetic fixtures, an offline read-only reference prototype, and a proposed authenticated-publisher design. Not operational.

This directory defines the first data contract and local prototype for the read-only OCC.

## Ownership and staging

The prototype implementation currently resides in the AI Revenue architecture branch only as a temporary shared-workstream staging location because no dedicated Main Hub repository has been established. This placement does not make OCC an AI Revenue-controlled authority. Company decision rights, data ownership and risk controls remain independent. Do not use this prototype for live company decisions.

## Files

- `schema/records.schema.json`: JSON Schema draft 2020-12 envelope and reusable definitions.
- `fixtures/ai-revenue.snapshot.example.json` and `fixtures/trading-technology.snapshot.example.json`: synthetic snapshot fragments, each corresponding to `$defs.snapshot`.
- `fixtures/registry-and-workstreams.example.json`: synthetic registry/workstream fragment corresponding to `$defs.company` and `$defs.workstream`.
- `fixtures/decisions.example.json`: empty decision-log fragment corresponding to `$defs.decision`.
- `fixtures/main-hub-envelope.example.json`: complete synthetic root-envelope document matching the top-level schema shape.
- `prototype/`: Python-standard-library offline report generator and tests. This is a reference prototype, not a deployed OCC service.
- `security/authenticated-publisher-design.md`: proposed trust, signature, replay, freshness, key-lifecycle, quarantine, and rollout requirements. Design only; no publisher or adapter is implemented.
- `verification/m2-verification-matrix.md`: explicit M2 schema, semantic, parser, security-protocol and recovery test matrix. Test plan only; execution states are tracked separately.

The individual fixture fragments are intentionally not complete root-envelope documents. The root schema requires the complete envelope with registry, decisions, workstreams and one snapshot per company; the fragments are separated to keep each synthetic record easy to inspect.

## Safety properties

- Both company IDs are fixed and distinct.
- Prototype input uses a strict allowlist; unexpected fields and company identity mismatches are rejected.
- Credentials, raw company records, customer data, wallet details, private keys and unrestricted agent memory are not part of the contract.
- Synthetic examples use `UNKNOWN` and `NOT_RUN`; they must never be presented as live status.
- `WAIVED` is recorded but never counts as a critical gate pass.
- The prototype has no authenticated publisher adapter. All sources remain untrusted; non-synthetic but unauthenticated data also remains `UNKNOWN`.
- Stale data is displayed as `STALE`; missing or malformed inputs fail closed.
- A valid future publisher signature will authenticate the publisher/message only; it will not establish truth, evidence sufficiency, readiness, or authority to act.

## Validation

The prototype and its tests use only Python's standard library. **Twenty-five tests are authored; execution against the latest strict-JSON-hardened revision is pending.** A prior 14-test revision passed locally, but that result predates the current expanded suite. Full JSON Schema Draft 2020-12 validation has not yet been executed by a standards-compliant validator. A custom structural check previously passed selected schema assertions and negative cases; it is not a standards-compliant validator.

The root schema constrains the company registry and status snapshots to exactly two entries, one for each company. Do not install packages or trigger GitHub Actions under the current approval restrictions. Record validator name/version and exact commit when formal validation is later performed in an already-available offline environment.

## Current status

**M1 contract drafted; M2 offline reference prototype committed; 23-test execution and formal schema validation pending; authenticated-publisher design drafted but not implemented; adapters absent; not operational.**

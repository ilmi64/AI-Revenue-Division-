# OCC read-only prototype v0.1

**Classification:** Offline reference prototype; synthetic data only; not operational.

## Run locally

From this directory:

```sh
python occ_readonly.py
python -m unittest -v
python validate_m2_schema.py
```

The default fixture directory is the sibling `../fixtures` directory. The program reads two JSON snapshots and prints a JSON report to stdout. An optional `--output` path writes a report file locally.

## Safety limits

- Python standard library only; no package installation required.
- This is an offline fixture demonstrator, not a hardened parser for hostile network input. It applies explicit caps: 1 MiB per fixture, nesting depth 32, 20,000 JSON nodes, 1,000 items per array, 256 members per object and 8,192 characters per string/key. These are prototype safety bounds, not a substitute for a hardened network-facing parser.
- No network calls, web server, database, credentials, external actions, or company adapter.
- Strict field allowlist; rejects identity mismatch, unexpected fields, duplicate JSON object keys, non-standard JSON constants, invalid reference clocks, and invalid freshness limits.
- Rejects duplicate gate, blocker, and evidence IDs; gate evidence references must resolve to evidence IDs in the same company snapshot.
- Malformed or missing fixture files fail closed with a concise contextual error.
- Synthetic source revisions are explicitly untrusted.
- All unauthenticated sources remain `UNKNOWN`; stale sources display `STALE`.
- A critical gate is considered unresolved unless its state is exactly `PASS`; `WAIVED` is not a pass.
- This prototype does not authenticate publishers, verify signatures, prevent replay, prove source-revision provenance, or validate the full JSON Schema. It is not a readiness authority.
- `validate_m2_schema.py` is a separate offline validation utility. It pins exact GitHub blob identities for the schema and synthetic fixtures, invokes the Draft 2020-12 validator with date-time format checking, and checks company/record identity uniqueness. It requires the already-available `jsonschema` package; do not install anything if it is unavailable. The validator script has been authored but has **not** been executed.

## Current verification record (2026-11-21)

- Latest prototype code commit: `415946922ecf6fd1e4573cfeb0ce18d38dcc2441` (blob `9a39b3d5f1e6a3708bee4271b6be52c1a72b64e5`).
- Latest test-suite commit: `5a91e4210b3ed7d8e2fcc4a8d5f7f41a27f036a8` (blob `e7c38a0365d604a04ac6d23f2cb7441fe3f6097f`; 29 authored tests; execution pending).
- A custom, offline structural check was applied to the exact committed schema and fixtures. The complete envelope, both company snapshots, registry companies, workstreams, and decisions produced no errors under the checker's implemented schema assertions.
- Negative checks rejected a missing company snapshot, a duplicated company identity, and an unexpected field.
- This is a custom structural check, **not** a standards-compliant Draft 2020-12 validator. Formal schema validation remains open. The latest resource-bound code and four regression tests are authored but have not yet been executed.
- The exact prior committed source, test and fixture contents were reproduced locally and the 14-test suite passed (2026-11-20). That run predates the current integrity hardening and the expanded 29-test suite; rerun the latest exact revision before treating the expanded suite as verified.

## Next required work

1. Re-run the expanded standard-library test suite against the exact updated commit and record the result.
2. Execute `python validate_m2_schema.py` against the exact pinned schema/fixture blobs, using the already available `jsonschema` package and date-time format assertion. The script is authored; execution and evidence recording remain pending.
3. Design authenticated, company-owned publishers and freshness/replay protections before accepting any non-synthetic data.
4. Keep company data stores and decision authority separate.

### Unified company visibility (offline)

Run the aggregate viewer with independently assigned synthetic inputs:

```sh
python occ_company_visibility.py \
  --ai-revenue-snapshot ../fixtures/ai-revenue.snapshot.example.json \
  --trading-snapshot ../fixtures/trading-technology.snapshot.example.json
```

The optional `--aevora-operations` path accepts the redacted output of
Aevora AI's `revenue_workflow_demo --mode anchored --view occ`. That
aggregate contains no publication timestamp or publisher authentication, so
its counters are labeled `UNVERIFIED_UNTIMED`.

The viewer displays allowlisted subsystem states and aggregate counts by
company. Missing data stays unknown. A rejected, stale, or quarantined company
snapshot contributes no counts, and each other input is evaluated independently.
Synthetic and unauthenticated inputs never establish operational readiness. The
viewer writes only to stdout and does not expose evidence references, raw
identifiers, descriptions, approvals, or action controls.

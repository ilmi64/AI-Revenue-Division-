# OCC read-only prototype v0.1

**Classification:** Offline reference prototype; synthetic data only; not operational.

## Run locally

From this directory:

```sh
python occ_readonly.py
python -m unittest -v
```

The default fixture directory is the sibling `../fixtures` directory. The program reads two JSON snapshots and prints a JSON report to stdout. An optional `--output` path writes a report file locally.

## Safety limits

- Python standard library only; no package installation required.
- No network calls, web server, database, credentials, external actions, or company adapter.
- Strict field allowlist; rejects identity mismatch, unexpected fields, duplicate JSON object keys, non-standard JSON constants, invalid reference clocks, and invalid freshness limits.
- Rejects duplicate gate, blocker, and evidence IDs; gate evidence references must resolve to evidence IDs in the same company snapshot.
- Malformed or missing fixture files fail closed with a concise contextual error.
- Synthetic source revisions are explicitly untrusted.
- All unauthenticated sources remain `UNKNOWN`; stale sources display `STALE`.
- A critical gate is considered unresolved unless its state is exactly `PASS`; `WAIVED` is not a pass.
- This prototype does not authenticate publishers, verify signatures, prevent replay, prove source-revision provenance, or validate the full JSON Schema. It is not a readiness authority.

## Current verification record (2026-11-20)

- Prototype code commit: `f844c158c3171f80ebfcf2a3d3dae093f8363592`.
- Test-suite commit: updated in the current branch revision (25 authored tests; latest expanded execution pending).
- A custom, offline structural check was applied to the exact committed schema and fixtures. The complete envelope, both company snapshots, registry companies, workstreams, and decisions produced no errors under the checker's implemented schema assertions.
- Negative checks rejected a missing company snapshot, a duplicated company identity, and an unexpected field.
- This is a custom structural check, **not** a standards-compliant Draft 2020-12 validator. Formal schema validation remains open.
- The exact prior committed source, test and fixture contents were reproduced locally and the 14-test suite passed (2026-11-20). That run predates the current integrity hardening and the expanded 23-test suite; rerun the latest exact revision before treating the expanded suite as verified.

## Next required work

1. Re-run the expanded standard-library test suite against the exact updated commit and record the result.
2. Add full draft 2020-12 schema validation using an already available validator (do not install packages under the current no-spend/no-install rule).
3. Design authenticated, company-owned publishers and freshness/replay protections before accepting any non-synthetic data.
4. Keep company data stores and decision authority separate.

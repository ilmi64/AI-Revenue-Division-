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
- Strict field allowlist; rejects identity mismatch, unexpected fields, invalid reference clocks, and invalid freshness limits.
- Synthetic source revisions are explicitly untrusted.
- All unauthenticated sources remain `UNKNOWN`; stale sources display `STALE`.
- A critical gate is considered unresolved unless its state is exactly `PASS`; `WAIVED` is not a pass.
- This prototype does not authenticate publishers, verify signatures, prevent replay, prove source-revision provenance, or validate the full JSON Schema. It is not a readiness authority.

## Next required work

1. Execute the 14 authored standard-library tests in an authorized local environment and record the exact revision.
2. Add full draft 2020-12 schema validation using an already available validator (do not install packages under the current no-spend/no-install rule).
3. Design authenticated, company-owned publishers and freshness/replay protections before accepting any non-synthetic data.
4. Keep company data stores and decision authority separate.

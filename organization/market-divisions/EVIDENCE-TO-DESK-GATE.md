# OCC Evidence-to-Desk Gate

Offline, deterministic research gate for Capital Flow Intelligence and specialist market observations.

## Run

From this directory:

```bash
python evidence_to_desk_gate.py \
  --events normalized-events.jsonl \
  --ledger review-ledger.jsonl \
  --source-registry capital-flow-source-registry.json \
  --observations market-observations.jsonl \
  --now-utc 2026-11-17T12:00:00Z \
  --output gate-report.json
```

All inputs are local snapshots supplied by the operator. The `--now-utc` reference is explicit to make runs reproducible. The default market quote age limit is 120 seconds and maximum source/receive clock skew is 5 seconds; set these to a documented market-specific policy before using the gate for any operational decision.

## Gate behavior

- Verifies the capital-flow review ledger hash chain before processing any event. A failed chain blocks the entire run.
- Requires each event to have a ledger review, a recent UTC review timestamp, eligible review state, source/evidence references and separate confidence dimensions.
- Checks each event source against the supplied source registry. Access must be verified, cost free/not-applicable, terms reviewed permitted, and operational status approved manual/adapter. The current candidate registry intentionally fails these gates.
- Rejects duplicate event IDs in a batch.
- Checks market timestamps, clock skew, quote age, finite positive bid/ask, crossed quotes, licence status, session and market-specific mappings. It also requires a supplied market source registry, exact instrument/source candidate mapping, approved status, approved terms and Canadian eligibility; the current candidate registry intentionally fails closed.
- Gold checks require explicit basis, quote unit, session, quote age/staleness, financing and settlement metadata. Indicative bullion spot remains visibly distinct from broker-executable XAUUSD.
- Emits a JSON report with eligibility, errors and warnings. It never generates a trade stance or instruction.

## Status interpretation

- `BLOCKED`: review ledger integrity failed; no records are processed.
- `PARTIAL_OR_BLOCKED`: at least one record failed one or more checks.
- `PASS_RESEARCH_GATES`: supplied records passed this configured research-evidence gate only. This is not live readiness, provider approval, product/halal approval, a trading signal, or execution permission.

## Limits

This is not a full JSON Schema validator and does not verify external URLs, signatures, source authenticity, wallet attribution, chain finality, data licensing beyond supplied registry assertions, independent-provider status, exchange calendars, broker contract specifications, or Shariah compliance. Hash chaining detects accidental/unsophisticated edits but is not authentication or tamper-proof storage. Single-writer ledger use remains required. No network, API, credential, wallet, broker, scheduling, background service or execution capability is included.

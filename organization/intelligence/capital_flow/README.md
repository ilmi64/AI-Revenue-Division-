# Offline Capital Flow Normalizer

A standard-library-only JSON Lines (JSONL) normalizer for the OCC Capital Flow & Opportunity Intelligence workstream.

## Scope and safety

- Offline only: reads a local file and writes a local file; no network, APIs, provider SDKs, wallet access, or credentials.
- Research data only: never creates buy/sell/long/short instructions or execution-ready states.
- Preserves unknown values as `null`; it does not turn missing timestamps, valuations, directions, or wallet attribution into zero or guesses.
- Deduplicates only when chain, transaction hash, and event type all match. Conflicting values are retained as explicit conflict flags.
- Self-transfers, exchange hot-wallet reshuffles, bridge hops, wrapped-token mint/burn, internal treasury moves, stale observations, and weak attribution are warnings—not proof of intent.
- Does not establish beneficial ownership or infer accumulation/distribution intent.

## Input

One JSON object per line. Minimum fields:

```json
{
  "event_type": "large_wallet_transfer",
  "chain": "ethereum",
  "transaction_hash": "0x<64 hex characters>",
  "observed_at": "2026-11-17T10:00:00Z",
  "ingested_at": "2026-11-17T10:01:00Z",
  "source_ids": ["public-explorer"],
  "evidence_refs": ["https://example.invalid/tx/..."]
}
```

Supported timestamps are epoch seconds or ISO-8601 strings with an explicit timezone. Naive timestamps are rejected. The complete event taxonomy and field semantics are defined in the adjacent `capital-flow-event.schema.json`.

Optional `transfer_classification` values include `self_transfer`, `exchange_hot_wallet_reshuffle`, `bridge_hop`, `wrapped_token_mint_burn`, and `internal_treasury_move`. They are copied only into quality flags.

## Run

From this directory:

```sh
python capital_flow_normalizer.py input.jsonl --output normalized.jsonl
python capital_flow_normalizer.py input.jsonl --output normalized.jsonl --now-epoch 1794910000
python -m unittest -v
```

The fixed `--now-epoch` makes stale-data checks reproducible. If omitted, the tool does not mark observations stale. Exit code is non-zero when one or more input lines are rejected; valid lines are still written.

## Deduplication policy

Records with the same `chain + transaction_hash + event_type` are merged. Source and evidence references are unioned. Disagreements in value, direction, or entity attribution are preserved in `conflicts` and `quality_flags`; the first record remains the base record and must be reviewed. Events without both chain and transaction hash are never deduplicated automatically.

## Test coverage

Tests cover identifier normalization, unknown-value preservation, timezone rejection, self-transfer warnings, exchange/bridge/wrapped-token classifications, stale observations, duplicate merging, duplicate conflicts, and malformed JSONL lines. Tests are supplied but have not been run in the hosted repository environment.

# Capital Flow → Crypto Desk Evidence Handoff

**Status:** Draft contract, research-only. No automated dispatch, live feed, or trading authority is enabled.

## Purpose

Give the Crypto Specialist Desk a controlled, traceable view of Capital Flow Intelligence events without turning observations into signals. The handoff carries reviewed event facts, confidence dimensions, provenance, conflicts and limitations. The canonical event record and append-only review ledger remain the source of truth.

## Flow

1. Capital Flow normalizes an observation into the canonical event schema.
2. A reviewer records a decision in the append-only review ledger. Only `watch`, `research`, `unverified` or `corroborated` events may be included; rejected and expired events are excluded.
3. The handoff builder resolves each event against the canonical event and verifies the review hash chain before producing a packet.
4. Crypto Desk checks token/contract identity, venue/chain, liquidity, source freshness, attribution, event finality and independent corroboration.
5. The desk may cite the packet as evidence in its own specialist assessment. It must not inherit an event's confidence as strategy confidence.
6. Grok Desk and HyperGrok may challenge interpretation, but cannot promote the packet to an executable instruction or clear a stop.

## Required safeguards

- Preserve the canonical `event_id`, source IDs, evidence references, observation time, confidence dimensions, conflicts and quality flags.
- Keep source reliability, attribution confidence, event confidence and materiality separate.
- Treat `unverified` and `watch` as leads, not facts; even `corroborated` does not imply predictive value.
- Do not infer buy/sell pressure from a transfer without verified entity attribution, transaction context, direction reference and finality.
- Flag exchange wallet reshuffles, self-transfers, bridge hops, wrapped-token mint/burn, internal treasury moves, stale observations and possible label errors.
- Re-resolve the canonical event and review ledger at consumption time; never trust a copied handoff packet alone.
- Deduplicate by canonical event ID; preserve conflicting updates and corrections rather than silently overwriting.
- If evidence is missing, ledger verification fails, the event is expired/rejected, or timestamps are invalid, reject the record.
- Handoff failure or missing data means no capital-flow evidence is available; it does not mean zero activity.

## Desk output boundary

The handoff can support research questions such as:
- Which ecosystems have newly disclosed funding or grant activity?
- Are verified treasury movements consistent with internal operations or external deployment?
- Are token unlocks, liquidity changes or exchange flows approaching a known event window?
- Does a claimed whale accumulation event survive attribution and independent-source checks?

It cannot provide a trade stance, entry, exit, target, sizing, leverage, order, or permission to execute. The Crypto Desk must independently produce its own assessment under `specialist-assessment.schema.json`.

## Validation and release gates

- Validate against `capital-flow-desk-handoff.schema.json`.
- Resolve all event IDs and verify their canonical event schema and review-ledger hash chain.
- Verify timestamp ordering, review freshness, asset/chain/contract mapping and evidence reachability.
- Add deterministic negative tests for rejected/expired events, tampered ledger, missing provenance, stale review and duplicate IDs before any automated adapter is considered.
- No provider connection, API usage, wallet access, external dispatch or scheduled monitoring is included.

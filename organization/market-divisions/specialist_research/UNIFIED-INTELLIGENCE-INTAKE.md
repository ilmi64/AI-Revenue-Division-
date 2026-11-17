# OCC Unified Research Intelligence Intake

**Status:** Offline snapshot builder and contract; not a running service. Research-only.

## Purpose

The unified intake is the organisation-level aggregation boundary for four independent specialist desks:

- Crypto
- Forex
- Equity Indices
- Gold / XAUUSD (kept as a distinct first-class desk)

It also carries the optional Capital Flow Intelligence -> Crypto research handoff, an evidence provenance index, OCC stop propagation, portfolio-version consistency and explicit day/night handover validation.

## Processing path

1. Read local JSONL market observations and a local market-source registry.
2. Call the specialist replay engine, which reruns the canonical OCC evidence-to-desk gate from those raw inputs. A caller-supplied gate report is not accepted.
3. Run the market-specific desk assessors. Multiple instruments per specialist desk are supported; duplicate instrument IDs and inconsistent portfolio versions are blocked.
4. Attach optional Capital Flow context only through the separate adapter, which verifies its event/review/source inputs and exact token identity. Capital Flow does not replace the market evidence gate.
5. Build an evidence index mapping each evidence reference to desk, instrument and evidence type.
6. Aggregate all desk HALTs and stop challenges into a global stop. A prior global stop remains active; CLEAR is not authority to erase it.
7. Validate day/night handover separately. Missing acknowledgements, missing reconciliation, unhealthy dependencies, unresolved critical items or version mismatch leave handover blocked.

## Handover contract

A handover JSON record must contain:
- `outgoing_shift_id`, `incoming_shift_id`, `handover_at_utc`, `snapshot_id`;
- `portfolio_version`, `active_veto_ids`, `unresolved_critical_items`;
- `dependency_health` equal to `healthy`;
- `outgoing_acknowledged`, `incoming_acknowledged`, `positions_reconciled` explicitly true.

Both shifts must be distinct. The handover timestamp cannot be in the future. `unresolved_critical_items` must be an explicit empty array. Any active veto remains visible and propagates to the global stop. Absence of a handover record never implies acceptance.

## Coverage and statuses

The snapshot reports instrument counts for Crypto, Forex, Indices and Gold. Missing coverage is always visible. By default, partial coverage is `unverified`; use `--require-full-coverage` when the specific replay requires all four desks. A specialist halt, invalid packet, failed evidence gate, required coverage gap, active stop or previous stop results in `halt`.

A research or unverified status is not a trading signal, readiness declaration or execution approval.

## CLI

Run from `organization/market-divisions`:

```bash
python -m specialist_research.unified_intake \
  --observations fixtures/specialist-market-observations.synthetic.jsonl \
  --market-source-registry synthetic-market-source-registry.json \
  --now-utc 2026-11-17T12:00:00Z \
  --portfolio-version 7 \
  --output /tmp/occ-unified-intelligence.json
```

Optional inputs:
- `--capital-flow-events`, `--capital-flow-reviews`, `--capital-flow-source-registry` (all three together);
- `--handover path/to/handover.json`;
- `--previous-global-stop` to carry forward a previously active global stop;
- `--occ-stop-state HALT` to inject an explicit stop observation;
- `--require-full-coverage`;
- `--max-market-age-seconds` and `--max-clock-skew-seconds`.

The output contract is `unified-intake.schema.json`.

## Security and limitations

- Standard-library local processing only; no network, provider APIs, broker/wallet connections, signing, orders, publication or deployment.
- Source-registry approval is a local assertion, not independent proof of source authenticity, licensing or legal rights.
- Evidence references are indexed, not authenticated by this component.
- SHA-256 digests are reproducibility aids, not signatures or proof of identity.
- No autonomous daemon, live monitoring, background scheduling, position reconciliation service or shift notification exists here. Position reconciliation is an explicit handover assertion and must be independently performed by the responsible operators.
- This component cannot clear a stop or grant trade authority.
- Synthetic fixtures are for structural testing only.

## Regression coverage

See `test_unified_intake.py` and the multi-instrument coordination test in `test_engines.py`. Tests are authored but must be run in a supported local Python environment before the PR can be considered validated.

# Specialist research engines (offline)

This package adds deterministic, standard-library-only research engines for the
Crypto, Forex, Equity Indices and dedicated Gold/XAUUSD desks.

## Entry points

Import `assess_crypto`, `assess_forex`, `assess_indices`, and
`assess_gold` from `specialist_research.engines`. Each accepts an already
collected observation, a fixed UTC evaluation time ending in `Z`, and optional
evidence references. The `coordinate` function performs an OCC read-only
aggregation over desk packets.

Example:

```python
from specialist_research.engines import assess_gold, coordinate

packet = assess_gold(observation, "2026-11-17T12:00:00Z")
occ_view = coordinate([packet], "2026-11-17T12:00:00Z")
```

## Desk-specific checks

- **Crypto:** exact BASE/QUOTE pair identity, quote-currency consistency,
  verified token/market identity, chain/contract context and perpetual funding
  and settlement context.
- **Forex:** explicit quote-currency-per-base-unit convention, currency
  orientation, central-bank and macro evidence slots, session and financing
  context.
- **Indices:** cash-index identity/currency, futures contract/expiry and CFD
  broker-symbol/contract-unit separation, with constituent and roll provenance.
- **Gold:** independent XAUUSD spot, COMEX futures and CFD basis identity;
  session/calendar provenance; quote age and explicit stale flag; futures
  expiry; spot/futures leg provenance and time alignment; macro evidence slots;
  financing, settlement and instrument-specific Shariah review flags.

## Safety and interpretation

These modules do not fetch data, validate a provider's legal licence, replace
the upstream evidence-to-desk gate, or prove that a source is truthful. They
must consume the result of the common evidence gate and preserve its errors.
A clean packet means only that the fields checked by this local engine passed.
Synthetic, delayed, indicative or historical inputs remain research-only.

Statuses are limited to `research`, `unverified` and `halt`. A missing or
contradictory identity produces `halt`; incomplete evidence produces
`unverified`. No directional stance, price target, position size, leverage,
order, signal or execution permission is generated. OCC coordination can
propagate a stop challenge or halt on inconsistent portfolio versions/times;
it cannot clear a desk stop or grant authority.

No network, API, wallet, broker, order, signing, publishing, deployment, or
background scheduling functionality exists here. The package is not a running
service or live trading system.

## Local tests

From `organization/market-divisions`:

```sh
python -m unittest specialist_research.test_engines -v
```

Tests use invented fixture metadata only. They have been authored but must not
be described as passing until executed in a suitable local environment.


## OCC-gated multi-desk replay

The `replay.py` harness joins the output JSON from the existing
`evidence_to_desk_gate.py` pipeline to the four desk assessors. It will not
run a desk packet unless the gate report has the expected research-only
authority marker, overall `PASS_RESEARCH_GATES` status, and exactly one
eligible gate result for that instrument. Failed/missing/ambiguous gate rows
become explicit desk halts. Gate warnings are carried into the desk packet.

Example (run from `organization/market-divisions`):

```sh
python -m specialist_research.replay \
  --observations fixtures/specialist-market-observations.synthetic.jsonl \
  --gate-report /tmp/occ-synthetic-gate-report.json \
  --now-utc 2026-11-17T12:00:00Z \
  --output /tmp/occ-multi-desk-replay.json
```

The replay expects the gate report's market-observation records to be keyed by
the same `instrument_id` values as the observation JSONL. It does not consume
capital-flow events implicitly. Capital-flow evidence remains opt-in. When all three local inputs are supplied,
the replay re-runs the Capital Flow -> Crypto adapter for each Crypto observation.
The adapter verifies the canonical event records, the complete review-ledger
hash chain, latest review decision, source access/cost/terms status, event
freshness/revalidation, evidence references and independent confidence fields.
It attaches an event only when base asset, chain ID and contract address match
exactly. Ticker-only matches are prohibited. A challenge, rejection, expiry,
or invalid ledger/source record cannot be attached.

Example (run from `organization/market-divisions`):

```sh
python -m specialist_research.replay \\
  --observations fixtures/specialist-market-observations.synthetic.jsonl \\
  --gate-report /tmp/occ-synthetic-gate-report.json \\
  --capital-flow-events /path/to/canonical-events.jsonl \\
  --capital-flow-reviews /path/to/review-ledger.jsonl \\
  --capital-flow-source-registry /path/to/source-registry.json \\
  --now-utc 2026-11-17T12:00:00Z \\
  --output /tmp/occ-multi-desk-replay.json
```

All three Capital Flow inputs are required together. If omitted, the replay
reports `not_consumed`. If supplied but no event passes, it reports
`provided_no_eligible_match`. A failed adapter is marked blocked on the
Crypto packet and cannot add an event. Capital Flow evidence never replaces
the independent market evidence gate or market observation. The handoff is
research context only and does not produce a directional signal, sizing,
leverage, order, or execution permission.

The harness detects duplicate instrument IDs, mismatched OCC portfolio
versions/timestamps, invalid authority markers and unsupported instruments.
A desk halt is propagated to OCC; no coordinator function can clear it. This
is a local deterministic replay tool, not a live supervisor or readiness test.

Additional replay tests:

```sh
python -m unittest specialist_research.test_replay specialist_research.test_capital_flow_handoff -v
```

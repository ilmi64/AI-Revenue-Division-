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

These modules do not fetch data, independently establish a provider's legal
licence, or prove that a source is truthful. In the replay path, the canonical
OCC evidence-to-desk gate is rerun internally from the raw local observations
and source registry immediately before desk assessment. A clean packet means
only that the fields checked by the local gate and engine passed. Synthetic,
delayed, indicative or historical inputs remain research-only.

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

The replay harness no longer accepts a precomputed gate-report file. It calls
`evidence_to_desk_gate.run_pipeline()` internally immediately before desk
assessment, using the raw local market-observation JSONL, the market-source
registry JSON, one fixed UTC evaluation time and explicit market-age/clock-skew
limits. This removes the old trust boundary where a caller could fabricate
`PASS_RESEARCH_GATES` and an authority string in a supplied JSON report.

The market-source registry must map each observation's exact
`instrument_id` to its `source_id` candidate and show approved manual/read-only
status, approved terms and Canada review. These are local operator assertions,
not independent proof of source authenticity or legal rights. Unapproved or
missing mappings fail closed.

Example (run from `organization/market-divisions`):

```sh
python -m specialist_research.replay \
  --observations fixtures/specialist-market-observations.synthetic.jsonl \
  --market-source-registry synthetic-market-source-registry.json \
  --now-utc 2026-11-17T12:00:00Z \
  --max-market-age-seconds 120 \
  --max-clock-skew-seconds 5 \
  --output /tmp/occ-multi-desk-replay.json
```

The output records canonical SHA-256 digests for the observation set,
market-source registry and exact evidence-gate implementation file. When
Capital Flow inputs are supplied, it also records separate digests for the
event set, review ledger and Capital Flow source registry. The fixed evaluation
time and freshness thresholds are recorded alongside them. These digests
support reproducibility and later comparison; they are not signatures, source
authentication, or proof that registry assertions are true. The gate
implementation is re-run from raw inputs; no external gate report is trusted.

Capital-flow evidence remains opt-in. When all three local inputs are supplied,
the replay independently runs the Capital Flow -> Crypto adapter for each
Crypto observation. The adapter verifies canonical event records, the complete
review-ledger hash chain, latest review decision, source access/cost/terms
status, event freshness/revalidation, evidence references and independent
confidence fields. It attaches an event only when base asset, chain ID and
contract address match exactly. Ticker-only matches are prohibited.

Example with the optional Capital Flow inputs:

```sh
python -m specialist_research.replay \
  --observations fixtures/specialist-market-observations.synthetic.jsonl \
  --market-source-registry /path/to/market-source-registry.json \
  --capital-flow-events /path/to/canonical-events.jsonl \
  --capital-flow-reviews /path/to/review-ledger.jsonl \
  --capital-flow-source-registry /path/to/capital-flow-source-registry.json \
  --now-utc 2026-11-17T12:00:00Z \
  --output /tmp/occ-multi-desk-replay.json
```

All three Capital Flow inputs are required together. If omitted, the replay
reports `not_consumed`. If supplied but no event passes, it reports
`provided_no_eligible_match`. A failed adapter is marked blocked on the
Crypto packet and cannot add an event. Capital Flow evidence never replaces
the independently rerun market evidence gate or market observation. The
handoff is research context only and does not produce a directional signal,
sizing, leverage, order, or execution permission.

The harness detects duplicate instrument IDs, mismatched OCC portfolio
versions/timestamps, invalid authority markers and unsupported instruments.
A desk halt is propagated to OCC; no coordinator function can clear it. This
is a local deterministic replay tool, not a live supervisor or readiness test.

Additional replay tests:

```sh
python -m unittest specialist_research.test_engines specialist_research.test_replay specialist_research.test_capital_flow_handoff -v
```


## Unified OCC research-intelligence intake

The organisation-level offline aggregator is documented in
[`UNIFIED-INTELLIGENCE-INTAKE.md`](UNIFIED-INTELLIGENCE-INTAKE.md), implemented
in [`unified_intake.py`](unified_intake.py), and constrained by
[`unified-intake.schema.json`](unified-intake.schema.json). It combines all
four desks, evidence provenance, optional Capital Flow context, stop
propagation, portfolio version checks and explicit day/night handover. Multiple
instruments per desk are supported. See `test_unified_intake.py` for authored
regression cases; tests have not yet been run.


## Persistent OCC snapshot history

The local append-only snapshot journal is documented in
[`SNAPSHOT-HISTORY.md`](SNAPSHOT-HISTORY.md) and implemented in
[`snapshot_history.py`](snapshot_history.py). It records each unified OCC
snapshot with a deterministic snapshot ID, snapshot digest, sequence number,
previous-entry hash and record hash. Verification checks the chain and
snapshot authority fields. Once a prior entry records a global stop, this
prototype rejects a later snapshot that attempts to clear it. There is no
stop-clearance workflow.

Example commands (from `organization/market-divisions`):

```sh
python -m specialist_research.snapshot_history append \
  --history /path/to/private/occ-snapshots.jsonl \
  --snapshot /path/to/unified-intelligence.json \
  --appended-at-utc 2026-11-17T18:00:00Z

python -m specialist_research.snapshot_history verify \
  --history /path/to/private/occ-snapshots.jsonl
```

The journal is single-writer and local-only. Hash chaining is not a digital
signature, tamper-proof storage, source authentication, or a substitute for
protected backups and access controls. Regression cases are in
`test_snapshot_history.py`; they have not been executed.


## Persistent incident and control-event history

The separate append-only event ledger is implemented in
[`incident_event_ledger.py`](incident_event_ledger.py), described in
[`INCIDENT-EVENT-HISTORY.md`](INCIDENT-EVENT-HISTORY.md), and constrained by
[`incident-event-ledger.schema.json`](incident-event-ledger.schema.json).
It records incidents, specialist stop raises/challenges, corrective actions,
recovery evidence, handovers and stop-clearance requests. A clearance request
can only be recorded as pending or rejected; no event in this prototype clears
a stop. Incident closure is tracked separately from global-stop state.

Regression tests are in `test_incident_event_ledger.py`; they are authored,
not executed. Like snapshot history, this is a local single-writer prototype,
not a continuously running OCC service.

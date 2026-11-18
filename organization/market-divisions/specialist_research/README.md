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
review-ledger hash chain, latest review decision, source access/cost/terms and
Canada-review status, allowlisted access mode, event freshness/revalidation,
evidence references and independent confidence fields. It attaches an event
only when base asset, chain ID and contract address match exactly. Ticker-only
matches are prohibited.

The Capital Flow source contract is defined by
[`capital-flow-source-registry.schema.json`](capital-flow-source-registry.schema.json);
start from `capital-flow-source-registry.template.json`. The template contains
no pre-approved providers. Each source must independently pass access, zero-cost,
terms, Canada-review and operational gates. Registry values remain operator
assertions, not proof of authenticity or legal rights.

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


## OCC audit and reconciliation

The read-only cross-ledger audit is implemented in
[`audit_reconciliation.py`](audit_reconciliation.py) and documented in
[`AUDIT-RECONCILIATION.md`](AUDIT-RECONCILIATION.md). It independently
verifies snapshot and incident-event histories, compares their global-stop
state, and correlates stop IDs where available. It fails closed if no snapshot
exists or either history fails integrity validation. It cannot clear a stop
or grant execution authority.

Regression cases are in `test_audit_reconciliation.py`; they are authored,
not executed. This remains an offline audit utility, not a running monitor.


## Day/night handover audit

The read-only handover continuity audit is implemented in
[`handover_reconciliation.py`](handover_reconciliation.py), with its contract
in [`HANDOVER-RECONCILIATION.md`](HANDOVER-RECONCILIATION.md). It verifies the
underlying event ledger first, then checks explicit outgoing/incoming
acknowledgements, position reconciliation, dependency health, evidence,
unresolved critical items, duplicate handover IDs/transitions and recorded
shift-chain continuity. Every stop ID raised at or before a handover's
`occurred_at_utc` must be carried forward in that handover; later stops do not
retroactively invalidate earlier handovers, and active vetoes remain latched.
No handover is inferred when no explicit handover event exists.

The event JSON Schema now defines the required handover details. Regression
cases are in `test_handover_reconciliation.py`; tests are authored, not
executed. The audit is offline and does not connect to live positions or a
shift scheduler.


## Unified OCC control-health integration

The read-only adapter in [`control_health.py`](control_health.py) composes
snapshot-history integrity, incident-event integrity, cross-ledger stop
reconciliation and day/night handover acceptance into the unified OCC snapshot.
It adds the required `control_health` object defined in
[`unified-intake.schema.json`](unified-intake.schema.json).

The adapter reads both local JSONL journals and never writes to either one.
Missing/corrupt history, cross-ledger disagreement or a missing/blocked
handover produces `HALT_AUDIT` and promotes the snapshot research status to
`halt`. A continuity warning produces `WARN_AUDIT`; only fully consistent
ledgers and an explicitly accepted handover produce `PASS_AUDIT`. Audit
holds do not invent a `stop_raised` event or alter the specialist/global-stop
fields. Existing stop IDs are surfaced and remain unchanged.

Example (from `organization/market-divisions`):

```python
from pathlib import Path
from specialist_research.control_health import build_control_health

integrated = build_control_health(
    unified_snapshot,
    Path("/path/to/private/occ-snapshots.jsonl"),
    Path("/path/to/private/occ-events.jsonl"),
)
```

Regression cases are in `test_control_health.py`; they are authored and have
not yet been executed. This is an offline integration adapter, not a live
monitor, position reconciler, trusted-signature system or execution control.


## Main unified-intake connection

The unified snapshot builder now accepts the optional paired CLI inputs
`--control-health-snapshot-history` and `--control-health-event-ledger`.
Supply both to attach a fresh read-only audit result to the generated snapshot.
Without both, the builder emits `control_health.status=NOT_PROVIDED`; it never
pretends an audit passed.

The adapter requires the snapshot being built to exactly match the latest
persisted snapshot-history payload. This deliberately prevents attaching a
green audit to a different or stale snapshot. Operational sequence:

1. Build the unified snapshot without the audit flags and persist that exact
   JSON snapshot using the existing `snapshot_history append` command.
2. Ensure the event ledger contains an explicit, accepted handover record
   referencing that persisted snapshot ID.
3. Re-run the same intake inputs and timestamp with both audit flags. The
   adapter attaches the integrity, consistency and handover audit to the
   output. Any changed input, timestamp, or snapshot payload fails closed.

Example final build flags:

```sh
--control-health-snapshot-history /path/to/private/occ-snapshots.jsonl \
--control-health-event-ledger /path/to/private/occ-events.jsonl
```

This is an explicit operator-run, offline sequence. The intake does not append
history or events automatically, and it does not create a scheduler or daemon.


## Canonical Capital Flow review ledger

The append-only review journal is implemented in
`capital_flow_review_ledger.py`, with its record contract in
`capital-flow-review-ledger.schema.json`. It uses the exact entry-hash
construction and field names consumed by `capital_flow_handoff.py`.

Create one review JSON object containing `reviewed_at` (UTC ending in Z),
`event_id`, `action`, `reviewer_id`, `reason`, `review_status`,
non-empty `evidence_refs`, `supersedes_entry_hash` and the fixed
research-only `authority` marker. For the first review of an event,
`supersedes_entry_hash` must be null; every later review must reference the
latest prior entry hash for that event. This prevents silent replacement of
prior review decisions.

Example commands (from `organization/market-divisions`):

```sh
python -m specialist_research.capital_flow_review_ledger append \
  --ledger /path/to/private/capital-flow-reviews.jsonl \
  --review /path/to/review.json

python -m specialist_research.capital_flow_review_ledger verify \
  --ledger /path/to/private/capital-flow-reviews.jsonl
```

The adapter independently verifies the resulting hash chain before using
reviews. The journal is offline and single-writer; it has no identity
authentication, trusted timestamp, locking, network access or stop/trade
authority. A hash chain is not a digital signature or tamper-proof storage.
Tests are authored but have not been executed.


### Synthetic end-to-end Capital Flow acceptance tests

`test_capital_flow_end_to_end.py` exercises the review-writer output through
the independent Crypto handoff adapter using synthetic fixtures only. It
covers successful research-context attachment, a later challenge blocking an
otherwise accepted event, Canada source-review failure, exact contract
mismatch, tampered review-ledger rejection and missing-review rejection.

Run it independently from `organization/market-divisions`:

```sh
python -m unittest specialist_research.test_capital_flow_end_to_end -v
```

It is also included automatically by the OCC regression runner's
`test_*.py` discovery. These tests are authored, not yet executed.


### Review lifecycle and challenge resolution

The review writer and independent Crypto handoff verifier now replay the
per-event decision lifecycle. The first decision must be `review`. A
`challenge`, `reject` or `expire` blocks the event. A challenged event may
return to research only through `correct` or `reopen`, and the resolving
record must cite at least one evidence reference not present in the prior
decision. A rejected or expired event cannot be reopened. A correction also
requires new evidence even when no blocking action preceded it.

The Crypto adapter independently repeats these lifecycle checks rather than
trusting the writer. This is still evidence-reference validation, not a
cryptographic proof that the referenced evidence is authentic or independent.


### Unified Capital Flow audit

The unified OCC snapshot now includes a `capital_flow_audit` section with
per-Crypto-instrument accepted event IDs, rejected-event reasons, review-ledger
integrity metadata, aggregate accepted/rejected counts and explicit authority
flags. A malformed handoff boundary is recorded as a packet validation error
and therefore fails the unified snapshot closed. A validly shaped but blocked
handoff remains visible as blocked research context; it is not silently
relabelled as an eligible event.

This audit is distinct from the independent market-data evidence gate. It does
not promote Capital Flow evidence into a price observation, signal, stop-clearance
decision or execution permission.


## Capital Flow classification and materiality

`capital_flow_taxonomy.py` adds deterministic descriptive categories for whale
movements, exchange flows, treasury activity, supply unlocks, fundraising,
launch activity, institutional capital, ecosystem funding, cross-chain flows
and protocol fundamentals. Unknown event types remain explicitly unclassified.
A bounded 0–5 materiality annotation is mapped to low/moderate/high/critical
tiers; it is not a directional score or a trade trigger.

Source reliability, attribution confidence, event confidence and materiality
remain separate dimensions. The taxonomy reports source counts and any
corroboration count as claims, but always marks source independence as
unverified: multiple source IDs do not establish independent ownership,
collection or provenance. The unified OCC audit carries the classifications
alongside accepted event IDs so the Crypto desk can inspect the context without
converting it into a market observation or execution instruction.


## Capital Flow evidence provenance

`capital_flow_provenance.py` annotates each accepted research event with
per-reference publisher identity, canonical source identity, source family,
publisher-claimed publication timestamp and a declared independence group.
Missing, malformed, duplicate, unmapped or future-dated metadata is reported
as incomplete. It does not silently upgrade the event's evidence confidence.

A metadata-complete result is still explicitly unverified. Publisher names,
canonical source IDs, timestamps and independence groups are supplied claims;
the adapter does not authenticate the referenced content, verify ownership,
or establish that two publishers are operationally independent. The unified
OCC audit carries this provenance assessment beside event classification.


## Capital Flow research queue priority

`capital_flow_priority.py` ranks only the order in which a human/research
workflow should inspect events. High priority requires high materiality,
minimum source reliability, attribution and event-confidence thresholds, plus
complete provenance metadata. Missing provenance prevents elevated priority;
known self-transfers, exchange hot-wallet reshuffles, bridge hops, wrapped-token
mint/burns and internal treasury movements are excluded from the priority queue.

Priority labels are not directional signals, market observations, risk limits,
position sizing or execution instructions. Metadata completeness is not
evidence authenticity, and declared source independence remains unverified.


## Dedicated Gold/XAUUSD specialist research contract

`gold_specialist.py` adds an independent, optional structured research layer
for Gold. When a Gold observation supplies structured session metadata or
macro evidence, `assess_gold` attaches this layer to the Gold desk packet.
The contract separates eight context families: real yields, USD, central-bank
demand, ETF flows, futures positioning, physical demand, geopolitical context
and rates/policy. Each evidence item carries a factor/type, reference, source,
UTC observation timestamp, value/unit and declared source status.

The layer also validates XAUUSD USD quote basis, bid/ask and spread
reconciliation, quote freshness, session/calendar fields, futures expiry and
roll status, CFD broker symbol/contract unit, financing, settlement and
instrument-specific Shariah review status. Macro evidence older than seven
days or future-dated is flagged for review. Missing macro factors are warnings;
identity, quote, basis and contract defects halt the Gold packet.

The macro factors are coverage/context only. The module deliberately produces
no directional score or forecast. Source IDs and declared groups do not prove
independent ownership or collection paths. Evidence is caller-supplied and not
independently authenticated. Indicative bullion, broker-executable XAUUSD,
COMEX futures and broker CFDs remain distinct instrument bases.

New offline tests are in `test_gold_specialist.py`; engine integration is also
covered in `test_engines.py`. These tests are authored, not yet executed.

The output contract is specified in
[`gold-specialist-research.schema.json`](gold-specialist-research.schema.json).


## Cross-desk OCC propagation and Main Hub integration

The unified intake treats a specialist HALT or stop challenge from Crypto, Forex,
indices or Gold as a global OCC stop. Explicit OCC stops, prior global-stop
state and active handover veto IDs are accumulated; a CLEAR/INACTIVE/NONE
observation cannot remove a prior stop. The intake does not perform stop
clearance. Handover records must explicitly acknowledge both shifts, reconcile
positions, report healthy dependencies, carry active veto IDs and contain no
unresolved critical items. It must also declare positive instrument coverage
for Crypto, Forex, indices and Gold, plus a separate
`positions_reconciled_by_desk=true` confirmation for every desk. A single
aggregate positions-reconciled flag is not sufficient. Missing handover
evidence is never interpreted as acceptance.

Structured Gold specialist results are summarized under
`gold_specialist_audit` in the unified snapshot, including per-instrument
macro-factor coverage, status, warnings/errors and the research-only authority
boundary. The Main Hub dashboard exposes that audit alongside OCC control
health, without promoting it into live readiness or execution permission.

Replay evidence digests now include a named SHA-256 map for the replay,
canonical evidence gate, specialist engine, Gold specialist and Capital Flow
handoff/taxonomy/provenance/priority implementations. These hashes identify
the code used for reproducibility; they do not authenticate external source
content, establish trusted time, or make local records tamper-proof.

Regression coverage has been extended for HALT propagation from Forex, indices
and Gold, Gold context survival through unified intake, Gold audit visibility
in the Main Hub, and specialist implementation fingerprints. Tests remain
authored until the local regression runner is executed in an approved
environment.


## Independent stop-clearance evidence assessment

`stop_clearance_review.py` is a read-only assessor for the stop-clearance
lifecycle. A request must identify a known latched stop and incident, link
existing `recovery_evidence_added` and `corrective_action_verified` event IDs
for that same stop/incident, and identify its requestor. Review events must
come from people other than the requestor and include two distinct reviewer
identities: one `independent_risk` and one `occ`. Each review records an
eligible or rejected decision with evidence references and a reason.

Even when both reviewers mark the request eligible, the result is only
`eligible_for_separate_occ_decision`. The stop remains active; no event or
module in this workflow clears or downgrades it. Reviewer identity, role,
evidence authenticity and trusted time are not independently authenticated.
The control-health report includes this assessment under
`control_health.stop_clearance_review`, while the global stop remains latched.

The associated regression suite is
`test_stop_clearance_review.py`; tests are authored and have not yet been
executed in this environment.


## Portfolio-wide OCC risk aggregation

`portfolio_risk.py` provides a read-only aggregation layer across Crypto,
Forex, indices and Gold. Each desk must explicitly supply
`context.portfolio_risk.positions` records with a unique position ID,
instrument identity, asset class, long/short side, notional and currency,
already-valued amount and valuation currency, exposure group, source timestamp
and evidence references. Missing desk or position context is UNKNOWN, never
assumed to be zero exposure.

The intake accepts an optional versioned OCC risk configuration
(`--portfolio-risk-config`; contract: `portfolio-risk-config.schema.json`) and optional timestamped correlation evidence
(`--correlation-evidence`, JSONL; each pair requires a source ID, sample count,
lookback window, methodology, timestamp and evidence references). Limits support portfolio, individual desk and named exposure-group scopes, and are evaluated only against exposure
already expressed in the configured valuation currency. Desk/group totals are partitioned by currency. The module does not
invent FX conversions, leverage, contract multipliers, prices, margin, or
positions. Currency buckets are kept separate. Invalid inputs and configured
limit breaches halt the portfolio; any specialist HALT or stop challenge
escalates to the portfolio-wide HALT. Missing correlation evidence remains
UNKNOWN and is never treated as independence.

Correlation pairs are preserved as caller-supplied, unauthenticated evidence. Where both instruments have signed exposure in one shared valuation currency, a pairwise covariance-style exposure proxy is reported. Pairwise proxies are not additive and are not portfolio VaR, a validated covariance model, forecast or execution signal. Risk limits must be explicitly supplied and owned by OCC;
there are no fabricated default thresholds. The Main Hub surfaces UNKNOWN as
a warning and HALT as a stop-level audit result. The complete report always
retains the research-only authority boundary.

Regression coverage is in `test_portfolio_risk.py` and the Main Hub dashboard
tests. These tests are authored, not yet executed.


## Instrument-specific portfolio exposure and stress testing

The unified OCC portfolio risk adapter validates position metadata against an
explicit instrument-type contract before an aggregate can be assessed:
Crypto spot/perpetual, Forex spot/CFD, index futures/CFDs, and Gold spot,
futures/CFDs have distinct valuation-basis requirements. Derivative records
must supply contract multipliers where applicable; leveraged products must
supply leverage and margin fields where required. Units, optional delta,
valuation currency and evidence references are checked. This is metadata
validation only: the adapter does not reprice contracts, infer broker
specifications, calculate margin requirements, or derive a position from a
ticker.

Every assessed portfolio requires explicit versioned OCC risk limits and at
least one named stress scenario. Scenarios supply shock percentages by asset
class, with optional instrument-specific overrides. Outputs show P&L and
loss by valuation currency, leaving uncovered positions explicitly
incomplete. The simple linear shock model is a first-order research proxy;
it does not model options convexity, basis, liquidity, gap risk, funding,
liquidation or margin calls. Missing shock coverage or normalization metadata
keeps the portfolio UNKNOWN; known limit breaches and specialist stops HALT.
No default limits or stress assumptions are supplied.

Example risk configuration shape:

```json
{
  "schema_version": "1.0.0",
  "limits": [
    {"scope": "portfolio", "metric": "gross_exposure",
     "valuation_currency": "USD", "max_value": 100000}
  ],
  "stress_scenarios": [
    {"scenario_id": "risk_off",
     "shocks_by_asset_class": {
       "crypto": -0.20, "forex": 0.03,
       "indices": -0.12, "gold": 0.08
     }}
  ]
}
```

All thresholds and shocks are illustrative configuration examples, not
approved limits or forecasts. The module remains offline and research-only.


## Derivative margin, liquidation-distance and liquidity overlays

Derivative positions (Crypto perpetuals, Forex/Index/Gold CFDs and futures)
must carry explicit initial margin, maintenance margin, available margin,
liquidation-distance percentage, executable depth notional, financing/funding
cost and funding horizon. Invalid or missing fields keep the derivative
overlay UNKNOWN. Available margin below the supplied initial-margin amount
and executable depth below position notional generate risk warnings; they do
not fabricate a liquidation price or slippage estimate.

These fields are caller-supplied and must be sourced from the relevant venue,
broker or contract specification. The current adapter validates the supplied
metadata only. It does not implement broker-specific maintenance-margin
tiers, liquidation engines, mark-price rules, partial liquidation, order-book
impact, slippage, funding accrual, expiry settlement, contract rolls or gap
execution. Those remain explicit model gaps and prevent any claim of live
risk coverage.


## Venue-parameterised derivative path simulation

`venue_risk_simulation.py` adds an offline path simulator for explicitly
specified Crypto perpetual, Forex CFD, index future/CFD and Gold future/CFD
contracts. It replays caller-supplied UTC mark-price steps, applies the supplied
maintenance-margin tier schedule, calculates price P&L and funding transfers,
and estimates liquidation fees and market impact using explicit depth and
impact parameters. If the venue specification explicitly supports partial
liquidation, it tests a quantity reduction against the configured maintenance
buffer; otherwise a trigger is modelled as full liquidation.

The required venue specification includes contract multiplier, initial-margin
rate, mark-price rule, maintenance tiers, liquidation fee, impact coefficients,
buffer ratio and partial-liquidation support. Each path step supplies mark,
depth, funding rate and funding interval. Initial margin is checked against
the supplied initial-margin rate. Missing/invalid rules, incomplete tier
coverage, invalid timestamps or invalid path values block the simulation.
There are no default venue profiles or broker assumptions.

Example interface:

```python
from specialist_research.venue_risk_simulation import simulate_derivative_path

result = simulate_derivative_path(venue_spec, position, mark_path)
```

This is a deterministic model harness, not a broker-exact liquidation engine.
The impact calculation is a configurable heuristic, not an order-book replay.
It does not model intrabar sequencing, queue priority, insurance funds, ADL,
bankruptcy pricing, cross-collateral, venue-specific liquidation sequencing,
or guarantee gap fills. Caller-supplied venue rules and market data are not
authenticated. Gold, FX, indices and Crypto still require separate reviewed
venue/contract profiles; one profile must not be copied across instruments.

Synthetic regression cases are in `test_venue_risk_simulation.py`. They cover
missing model inputs, ordinary price-path P&L, long liquidation, partial
liquidation, short-side funding, timestamp ordering, gap visibility and the
research-only authority boundary. Tests are authored and have not yet been
executed in this environment.


## Explicit contract lifecycle and carry replay

`contract_lifecycle.py` separates product lifecycle events from generic
liquidation mechanics. It validates a venue/instrument profile and replays
caller-supplied funding, financing, roll and expiry-settlement events in strict
timestamp order. The profile contract is documented in
`contract-lifecycle-profile.schema.json`.

Profiles distinguish Crypto perpetuals, Forex CFDs, index CFDs, Gold CFDs,
index futures and Gold futures. Dated futures require an explicit contract
code, UTC expiry, settlement method and roll method. Crypto perpetuals require
a funding-rate convention. CFDs require an explicit annualized, daily or no
financing convention. The module never supplies a default calendar, triple
swap rule, funding sign, settlement formula or broker close-out convention.

Carry events may provide a signed cashflow directly, or a rate/notional/basis
tuple whose sign is interpreted literally as cashflow to the position.
Roll events must identify the current and next contract, both reference prices,
and an explicit cash adjustment. Expiry settlement must occur on or after the
profile expiry and must provide the matching contract, settlement method,
settlement price and realized cashflow. Settlement closes the simulated
quantity; no cash/physical delivery calculation is inferred.

Example interface:

```python
from specialist_research.contract_lifecycle import replay_contract_lifecycle

result = replay_contract_lifecycle(contract_profile, position, lifecycle_events)
```

This is a research ledger replay, not a venue calendar or accounting engine.
Event values and currency are caller-supplied and unauthenticated. The module
does not infer triple-swap calendars, financing accrual, tax, fees, delivery
logistics, margin release or settlement cashflows. It is not connected to the
derivative path simulator automatically; a future integration must reconcile
both outputs without double-counting carry or settlement cashflows.

Synthetic regression coverage is in `test_contract_lifecycle.py`, including
profile validation, contract roll continuity, expiry settlement, invalid event
ordering, financing conventions and the research-only authority boundary.
Tests are authored and have not yet been executed.


## Unified derivative simulation orchestration

`simulation_orchestrator.py` coordinates the venue path simulator and the
contract lifecycle replay under one fail-closed interface. It checks that the
venue and contract profiles agree on instrument type and quote currency, and
that the position identity matches the contract profile. The price path owns
mark-to-market P&L, maintenance margin, liquidation fees and estimated impact.
The lifecycle ledger exclusively owns funding/financing, rolls and expiry
settlement.

To prevent carry from being counted twice, every price-path funding rate must
be exactly zero. Funding and financing cashflows are supplied only through
lifecycle events. Dated contracts cannot run through expiry without an explicit
settlement event. The path may not continue after settlement. Lifecycle
cashflows and venue equity are reported separately; the orchestrator does not
add settlement cashflows to path equity because a supplied settlement amount
may already include realized price P&L. It does not perform implicit FX
conversion or merge unlike currencies.

The unified input contract is
`simulation-orchestrator-input.schema.json`. The interface is:

```python
from specialist_research.simulation_orchestrator import simulate_unified_derivative

result = simulate_unified_derivative(
    venue_spec, contract_profile, position, price_path, lifecycle_events
)
```

A passing reconciliation means only that the two model outputs are internally
consistent under the supplied inputs. It does not validate venue accuracy,
authenticate evidence, establish correct accounting, or grant operational
readiness. No broker or exchange connection, order routing, stop clearance or
trade authority is present. Regression coverage is in
`test_simulation_orchestrator.py`; tests are authored and have not yet been
executed.


## Versioned venue and instrument profile registry

`venue_profile_registry.py` provides a pure, offline registry validator and
effective-date resolver for separately versioned venue/instrument profiles.
It supports Crypto perpetuals, Forex CFDs, index futures/CFDs and Gold
futures/CFDs. Each record binds a venue simulation specification to a matching
contract lifecycle profile, with an explicit revision, validity interval,
profile state, verification state, review state and evidence provenance.

The registry contract is `venue-profile-registry.schema.json`; the empty
fail-closed starting point is `venue-profile-registry.template.json`.
Evidence provenance requires a source identifier, source reference, source
type, capture timestamp and SHA-256 digest. The digest is only a consistency
fingerprint for supplied evidence; the registry does not retrieve, authenticate
or independently verify the underlying source.

Only an effective profile with state `approved`, accepted review metadata and
at least `source_checked` verification can be resolved for research replay.
Unverified, pending, rejected, suspended, expired and not-yet-effective
profiles are blocked. The `append_profile_revision` helper returns a new
in-memory registry value, closes the previous revision's effective interval,
and checks revision sequencing. It does not write files or persist registry
changes.

`simulate_registered_derivative` in `simulation_orchestrator.py` resolves
the registry before calling the two simulation engines. This is a research
eligibility gate only: reviewer identity and profile metadata are caller
supplied and unauthenticated. No profile, including an approved one, can grant
operational readiness, trade authority or live readiness. Actual venue terms,
contract multipliers, margin tiers, financing conventions, settlement rules
and Shariah considerations require independent instrument-specific review.

Regression coverage is in `test_venue_profile_registry.py`; orchestrator
integration coverage also checks that unverified profiles are blocked. Tests
are authored and have not yet been executed.


## Venue intelligence and evidence acquisition

`venue_intelligence.py` is the offline intake and assessment layer for
venue-specific contract documentation. It defines separate required-fact
checklists for Crypto perpetuals, Forex CFDs, index futures/CFDs and Gold
futures/CFDs. Researchers supply source records and extracted facts; the
module does not browse, scrape, download, contact venues, or use API keys.

The evidence contract is `venue-intelligence-evidence.schema.json`. Each
source record identifies publisher, source class, source reference,
publication/capture timestamps and a SHA-256 content fingerprint. Each fact
must reference a known source and include its observation timestamp. The
assessor reports missing coverage, malformed provenance, conflicting values
and future-dated observations. A per-fact `max_age_days` can be supplied when
an explicit freshness policy is known. No universal freshness threshold is
invented; without one the result is `NOT_ASSESSED_NO_TTL`.

A complete bundle returns
`EVIDENCE_COVERAGE_COMPLETE_UNVERIFIED`, not approval. Conflicting evidence,
stale evidence under an explicit TTL, missing critical fields or invalid
provenance block draft preparation. `prepare_profile_draft` creates only a
candidate marked `under_review`, `unverified` and `pending`; it does not
construct a trusted venue profile or call the registry append function.
Human review and separate evidence verification remain mandatory.

`build_research_intake_report` aggregates per-venue/instrument evidence
coverage without ranking trading opportunities. All outputs remain
research-only. Source hashes do not authenticate source content, publisher
identity, URLs, collection timestamps or independence. The current source
candidate list is not a claim that any exchange or broker has been researched
or connected.

Regression coverage is in `test_venue_intelligence.py`; tests are authored
and have not yet been executed.


## Candidate venue research catalogue

`venue_research_catalogue.json` seeds the venue intelligence workstream with
official public-documentation candidates across all four divisions. The first
candidate set includes Kraken MTF and Coinbase International Exchange for
Crypto perpetual documentation; OANDA (Canada) Corporation for Forex, index
and Gold CFD documentation; and CME Group/COMEX for Gold and equity-index
futures specifications.

The seed catalogue records source URLs and the specific documentation topics
located during initial research, plus unresolved contract, margin, funding,
settlement and legal-entity questions. It deliberately does not copy dynamic
margin/leverage figures into static profile fields. Source content hashes are
null and full-document capture is false because the source bytes have not been
captured and hashed into the evidence-intake format. Therefore these entries
are documentation leads, not verified profiles.

Canada/Ontario access is unverified for every candidate product. CME futures
access depends on an eligible Canadian FCM and account approval; a public
exchange contract specification does not establish broker access. The OANDA
references are Canada-specific, but the user's account entity, exact product
availability and current contract terms still require confirmation. Kraken
MTF and Coinbase International Exchange eligibility must be checked separately
for Canadian residents and exact legal entities.

`venue_catalogue.py` validates catalogue structure and reports whether
documentation has merely been located or actually captured. It does not
authenticate publishers, retrieve source documents, verify eligibility, or
create/approve registry profiles. The catalogue schema is
`venue-research-catalogue.schema.json`; synthetic regression coverage is in
`test_venue_catalogue.py`.

Initial official-source research references:
- Kraken MTF linear contract specifications:
  https://support.mtf.kraken.com/hc/en-us/articles/25499987607837-Linear-Contract-Specifications
- Coinbase International Exchange perpetual specifications:
  https://help.coinbase.com/en/global-exchange/perpetual-futures-basics/perpetual-futures-product-specifications
- OANDA Canada margin rates:
  https://www.oanda.com/ca-en/legal/margin-rates/
- OANDA Canada financing methodology:
  https://help.oanda.com/ca/en/faqs/financing-costs-ca.htm
- OANDA Canada financing costs:
  https://www.oanda.com/ca-en/trading/financing-costs/
- CME Group Gold futures specifications:
  https://www.cmegroup.com/markets/metals/precious/gold-futures.contractSpecs.html
- CME Group equity-index futures information:
  https://www.cmegroup.com/markets/equities/sp-500-and-nasdaq-100-futures.html
- COMEX Gold futures rulebook:
  https://www.cmegroup.com/content/dam/cmegroup/market-regulation/rule-filings/2024/8/24-283_1.pdf

These references are starting points only. Product terms and margins change;
the exact current contract, exchange notices, broker/FCM terms and account
jurisdiction must be checked before a profile can be prepared or approved.


## Venue document revision tracking and profile freshness

`venue_document_revisions.py` adds an offline revision comparison layer for
official venue and contract documents. A researcher supplies a captured
document's text, canonical HTTPS URI, publisher/source class, capture time,
extraction method and structured facts. `capture_document_revision`
computes a SHA-256 fingerprint over the supplied text and creates a revision
record. The record retains the captured text so the digest can be rechecked
before comparisons; this is an explicit caller-supplied capture, not an
automated fetch or a claim that a provider's complete document was obtained.

`compare_document_revisions` compares consecutive revisions for the same
document and reports added, removed, changed, unchanged and internally
conflicted extracted facts. Critical terms include contract multiplier,
quote/settlement currency, initial/maintenance margin, mark-price rules,
funding/financing, expiry, settlement, liquidation, closeout, tick and roll
terms. A changed document requires human review even if the extracted facts
appear unchanged. Missing facts are not interpreted as zero or as proof that
a term was removed unless the prior/current extraction explicitly establishes
that comparison.

`assess_profile_revision_impact` checks the explicit
`source_revision_ids` mapping on a profile against the latest captured
revision per document. A mismatch, missing latest capture or newly untracked
source produces `STALE_REVIEW_REQUIRED`. A reviewer must compare the
revisions and separately decide whether the profile requires a new draft or
approval. No profile values are updated, no registry revision is appended,
and no previously approved profile is silently kept current.

The record contract is `venue-document-revisions.schema.json`; synthetic
coverage is in `test_venue_document_revisions.py`. These are deterministic
offline functions only: no polling, browser automation, network fetch,
background monitoring or venue API calls are implemented. Captured text,
extracted facts, publication dates and reviewer metadata remain
unauthenticated. SHA-256 detects a mismatch against the supplied bytes but
does not establish publisher identity, source authenticity or trusted time.
This distinction follows NIST guidance that a bare hash does not provide
source authentication; digital signatures or authenticated mechanisms are
needed for that stronger property:
https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-175Br1.pdf

All outputs remain research-only with `trade_authority=false` and
`live_readiness=false`. Gold futures (GC/MGC) and Gold CFDs/XAUUSD remain
separate instrument-specific document/profile tracks; a revision in one must
not be copied into the other.


### Stale-source gate for registered derivative replay

The registry now accepts optional `document_id` and `revision_id` links on
each profile provenance record. When a caller supplies
`latest_document_revisions` to `resolve_profile` or
`simulate_registered_derivative`, the resolver compares those captures with
the exact revisions recorded by the profile. A changed revision, an untracked
new document, a missing latest capture, or missing revision links blocks
research eligibility with a stale-source status. The registered replay
therefore cannot use a profile that fails a supplied freshness audit.

If `latest_document_revisions` is omitted, the registry explicitly reports
`document_freshness.status=NOT_PROVIDED`; the legacy research-resolution path
remains available but carries no document-freshness assurance. For new
evidence-controlled replay, callers should supply the complete latest capture
set and populate both provenance links. This is still not an unattended
monitor: the latest document captures must be supplied by a researcher.


## Official venue-document excerpt capture set

`venue_document_capture_manifest.json` now inventories nine official-page
search excerpts linked to all seven candidate venues. The sources cover
Kraken MTF linear crypto derivatives, Coinbase International Exchange
perpetuals, OANDA Canada's margin schedule, financing policy and index-CFD
methodology, CME/COMEX Gold futures, and CME equity-index futures.

This is deliberately labelled
`PARTIAL_OFFICIAL_EXCERPT_CAPTURE_NOT_FULL_DOCUMENTS`. The stored text is
only the excerpt reviewed during public documentation research, not the
complete web page, downloadable rulebook or client agreement. The capture
timestamp is date-only normalized to UTC midnight; it is not a trusted
publisher timestamp. SHA-256 fingerprints the stored excerpt bytes only.
The original URLs and research references are retained for source traceability.

The first-pass fact extraction records, among other items:

- Kraken MTF: USD margin/settlement, hourly perpetual funding, mark-price
  description and broad tier ranges. Instrument/size-specific tier tables,
  liquidation fees and collateral rules remain missing.
- Coinbase International Exchange: BTC/ETH USDC-settled perpetual examples,
  multiplier, settlement cadence, increments and default initial-margin
  examples. Maintenance margin, liquidation, funding formula and Canadian
  eligibility remain missing.
- OANDA Canada: instrument-specific Canadian margin/leverage examples;
  FX/metals tom-next financing plus admin fee; 5pm ET overnight financing
  cutoff and index CFD futures/cash reference methodology. Exact live
  instrument rates, contract units, closeout and triple-day handling remain
  outstanding.
- CME/COMEX Gold: GC 100 troy ounces and MGC 10 troy ounces. Exact expiry,
  tick, delivery/notice, settlement and current FCM margin remain outstanding.
- CME equity indices: ES USD 50 and MES USD 5 per S&P 500 point, with
  0.25-point tick examples. Exact contract month, final settlement and FCM
  requirements remain outstanding.

The companion `venue_document_capture.py` validates the manifest and
produces a research-only capture report. Its regression tests verify all
nine excerpt digests, seven-candidate coverage, explicit partial-capture
status and fail-closed handling of tampered hashes or false full-document
claims. The JSON contract is
`venue-document-capture-manifest.schema.json`.

No candidate has become profile-eligible. The Ontario account/product
eligibility checks remain open. In particular, CME access still depends on
an eligible Canadian FCM and account, and international crypto-derivative
documentation does not establish that a Canadian/Ontario resident can use
those products. Gold futures GC/MGC and XAUUSD Gold CFDs remain separate;
the OANDA financing description is a conventional financing mechanism and
is not a Shariah approval.


The source review was subsequently deepened by opening the official Kraken,
Coinbase and CME Gold pages. The Kraken excerpt now records the page's
explicit mark-price formula, hourly funding range and multiplier, its
statement that maintenance margin is half initial margin, and its USD
settlement timing. Coinbase BTC/ETH examples were checked against the opened
product specification. CME GC/MGC contract sizes and the stated date of the
page's indicative margin estimates were checked against the opened Gold
product page. The manifest distinguishes `official_web_open_excerpt` from
`official_web_search_excerpt` so the retrieval method is not overstated.


The OANDA Canada financing and index-CFD help pages were also opened. The
financing page specifies the 5pm ET overnight cutoff, distinct FX/gold versus
index financing bases, a 2.5% index admin-fee component, and typical
Wednesday (FX/metals) versus Friday (indices) triple-day financing, subject
to settlement calendars and holidays. The index-CFD FAQ describes the
futures-plus-cash/spot reference, dividend/corporate-action adjustments,
non-expiry, dynamic spreads, and identifies OANDA Canada Corporation ULC as
CIRO-regulated with accounts available to people with a Canadian bank
account. These statements do not establish an individual account's product
permissions. OANDA's conventional financing charges/credits are recorded
for technical modelling only; they are not treated as Shariah approval.


The Gold futures track now also includes the opened COMEX Rulebook Chapter 113
excerpt. It records the 100-troy-ounce contract unit, physical delivery
requirements, minimum 995 fineness, USD 0.10 per-ounce tick, the third-last
business-day trading cutoff and the delivery window. This makes the delivery
risk explicit: a GC futures profile must carry first-notice/last-trade and
broker cutoff controls rather than treating the instrument as a cash-settled
XAUUSD CFD. The rulebook excerpt does not replace the FCM's own delivery
instructions or account-specific controls.


### OCC venue revision review queue

`build_revision_review_queue` in `venue_document_revisions.py` combines document comparison reports and profile-source freshness reports into a deterministic human-review queue. Changes to critical contract terms (including multiplier, margin, mark price, funding/financing, liquidation, expiry, settlement, roll and tick terms) are ordered ahead of standard document changes. Stale or untracked profile sources also produce review items.

The queue is a prioritization aid, not a risk score, source-authentication mechanism or approval workflow. Invalid comparison/profile-impact input fails closed. An empty queue means only that the supplied reports contain no outstanding items; it does not establish that documents are complete or current. No profile is modified, approved or made eligible for replay. All outputs retain `trade_authority=false` and `live_readiness=false`.

The revision-record schema now accepts either `extraction_method` (manual/synthetic capture) or `retrieval_method` (research manifest capture), while requiring at least one provenance field. Regression coverage includes critical-first ordering, stale-source queueing, invalid-input blocking and the no-authority boundary. Tests are authored and have not yet been executed.


### Explicit-policy document capture freshness

`assess_document_freshness` evaluates the age of a captured revision against an explicit per-document `max_age_days` policy and a caller-supplied UTC evaluation time. It reports stale captures for review, distinguishes documents with no TTL as `NOT_ASSESSED_NO_TTL`, and rejects future-dated captures, duplicate policies and invalid/non-finite thresholds. No universal freshness window is assumed.

This measures age since the local capture only; it does not prove when the publisher last changed the document or whether the capture is complete. Stale results can be routed into `build_revision_review_queue` as critical review items. Freshness checks do not approve evidence, update venue profiles or grant simulation/trading eligibility. Regression coverage has been added but has not been executed.


### Canadian venue eligibility and Gold delivery controls

The current venue catalogue records two explicit Canadian crypto-derivatives gates: Kraken's published Canada restrictions say residents cannot trade derivatives or use margin; Coinbase International Exchange is institutional-only in selected jurisdictions, and Canadian institutional eligibility is not established. These are not treated as eligible Canadian venue candidates. The catalogue validator prevents these statuses from being silently downgraded to generic "unverified" or upgraded to "approved".

OANDA Canada's published margin schedule lists Gold at 4.5:1. This is a dated public schedule reference, not an account-specific guarantee or a static simulator constant. The live spread/margin display can change, and exact contract unit, closeout terms and account treatment remain to be captured. Conventional CFD financing is not a Shariah approval.

`gold_delivery_controls.py` adds a fail-closed GC/MGC physical-delivery gate. It requires the exact contract month, exchange calendar revision, FCM policy revision, First Position/First Notice/last-trade/delivery dates, and explicit FCM long/short/new-position cutoff dates and UTC times. It validates GC against COMEX Chapter 113 and MGC against Chapter 120. The module also enforces the MGC rule that delivery quantities are multiples of ten contracts except on the last intent day, with Chapter 120's ACE-based delivery structure documented separately. It does not calculate exchange dates, infer FCM deadlines, roll or liquidate positions, or submit delivery instructions. Missing or inconsistent calendar/policy inputs halt the assessment. The test fixtures are synthetic and do not represent a real contract calendar or broker policy.


### OANDA Canada Gold CFD: hours, gaps, closeout and instrument identity

The official-page excerpt manifest has been extended from nine to thirteen captures. Four new OANDA Canada excerpts record:

- XAU/USD is a Gold CFD quoted against USD and measured in troy ounces; it does not convey physical ownership of bullion. The page does not establish a universal account-independent contract multiplier.
- The published XAU/USD metal-CFD hours are Sunday-Friday 18:05-16:59 New York time. Hours may change for daylight saving time and holidays. The displayed MT4 lot size is 100, which is platform-specific and must not be generalized to every account/platform.
- OANDA warns that spreads can widen around market close, prices can gap on reopening, and stops may execute at a worse prevailing price. Positions cannot be opened or closed while markets are closed.
- Under-margined accounts can be subject to automatic closeout of all tradable open positions at current rates. The customer agreement gives OANDA discretion to close positions without providing time to respond when it considers immediate action necessary.
- OANDA's general Canada FAQ says CFDs and precious metals are automatically enabled on accounts, but this does not verify an individual customer's account status or the applicable instrument terms.

The new excerpts are stored as oanda_xauusd_instrument_page, oanda_canada_trading_hours_and_gap_risk, oanda_canada_margin_closeout, and oanda_canada_cfd_account_eligibility. The capture manifest still explicitly contains partial excerpts only: no complete client agreement, page bytes, authenticated publisher proof or trusted publisher timestamp has been captured.

These facts imply additional Gold risk-model requirements: session-aware close/reopen windows; spread-widening and gap stress scenarios; stop execution slippage/gap assumptions; and a broker-level forced-closeout scenario that can close multiple positions at current rates. The existing venue simulator's generic liquidation heuristic is not an OANDA margin-closeout implementation. Do not equate the two or treat a stop as guaranteed protection. Account-specific contract size, margin threshold, closeout sequence and financing remain unresolved.

The XAU/USD CFD remains distinct from GC/MGC futures. It is a price-difference contract and does not provide the same delivery/ownership rights as physical bullion. Conventional CFD financing is still not a Shariah approval. No venue profile was created or approved, and no account connection or live trading permission was obtained.

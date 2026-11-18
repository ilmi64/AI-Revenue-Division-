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
(`--portfolio-risk-config`) and optional timestamped correlation evidence
(`--correlation-evidence`, JSONL). Limits are evaluated only against exposure
already expressed in the configured valuation currency. The module does not
invent FX conversions, leverage, contract multipliers, prices, margin, or
positions. Currency buckets are kept separate. Invalid inputs and configured
limit breaches halt the portfolio; any specialist HALT or stop challenge
escalates to the portfolio-wide HALT. Missing correlation evidence remains
UNKNOWN and is never treated as independence.

Correlation pairs are preserved as caller-supplied, unauthenticated evidence;
they are not a validated covariance model, portfolio VaR, forecast or
execution signal. Risk limits must be explicitly supplied and owned by OCC;
there are no fabricated default thresholds. The Main Hub surfaces UNKNOWN as
a warning and HALT as a stop-level audit result. The complete report always
retains the research-only authority boundary.

Regression coverage is in `test_portfolio_risk.py` and the Main Hub dashboard
tests. These tests are authored, not yet executed.

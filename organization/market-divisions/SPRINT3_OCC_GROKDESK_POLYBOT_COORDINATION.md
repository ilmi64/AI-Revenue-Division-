# Sprint 3 — OCC, Grok Desk / HyperGrok and PolyBot Coordination

**Status:** Target architecture and handoff contract. Not runtime-connected. Research/paper-only.

## Operating topology

- **OCC / Main Hub:** organisation-level source of policy, task ownership, division status, approval gates, incident register, readiness evidence and cross-division coordination. OCC may raise a global stop; it cannot authorize trades.
- **Crypto Specialist Desk:** market-specific research and paper assessment for crypto. PolyBot remains the crypto research/paper execution simulator and position-management sandbox, subject to its deterministic risk controls.
- **Forex Specialist Desk:** independent FX research and paper assessment. No broker connection or execution authority is implied.
- **Indices Specialist Desk:** independent cash-index/futures/CFD research and paper assessment. Instrument type and contract mapping must be explicit.
- **Gold Specialist Desk:** dedicated XAUUSD/COMEX/gold-instrument research and paper assessment. It has its own mapping, data lineage, basis, roll, unit and financing checks.
- **Grok Desk:** day/night research and operational advisory function. It collects specialist outputs, challenges assumptions, tracks unresolved risks and prepares handover summaries.
- **HyperGrok:** higher-level synthesis and adversarial review. It can compare desk hypotheses, identify cross-market dependencies and recommend further tests; it cannot turn disagreement into an executable consensus or override the risk controller.

## Decision and data flow

1. Each specialist desk receives a source-labelled market observation and validates the market-specific mapping and data-quality gates. Gold additionally enforces explicit quote basis, age/staleness, session, settlement and financing metadata. The Crypto desk may consume Capital Flow Intelligence packets only through the evidence-only handoff contract, resolving each event against the canonical record and verified review ledger.
2. Each desk emits a versioned, non-executable assessment using specialist-assessment.schema.json.
3. Grok Desk reviews the assessments for freshness, evidence, contradictions, missing coverage and operational incidents.
4. HyperGrok performs a separate challenge pass. Its output is advisory metadata, never an authority token.
5. OCC records the task, accepted evidence, owner, portfolio version, active stop conditions and readiness state.
6. PolyBot consumes only approved paper inputs for crypto simulation. Other desks remain research/paper workstreams until their own adapters, simulations and tests exist.
7. Any validated global HALT is passed through the stop-only control path. Missing or invalid OCC state is treated as interlock unavailable and blocks new exposure. A CLEAR observation does not clear a previously active veto.
8. Existing-position protection, deterministic risk checks and reconciliation continue independently of advisor availability. Capital Flow evidence never creates an order or execution permission.

## Day/night handover

Each handover must include:
- outgoing and incoming role identifiers and UTC handover time;
- last accepted snapshot ID, source timestamps and portfolio version;
- current mode (research or paper) and desk coverage;
- active HALTs/veto IDs and their evidence references;
- unresolved positions, orders, fills or transaction reconciliation;
- source, licence, feed, storage and dependency health;
- open hypotheses, contradictory assessments and pending reviews;
- incident IDs, owner, containment and next review time;
- incoming acknowledgement and explicit acceptance of responsibility.

No acknowledgement, uncertain position/order state, stale evidence, failed persistence or unavailable critical dependency means the desk remains blocked. Do not infer that the next shift has accepted control.

## Independence and escalation

- Grok Desk and HyperGrok are not allowed to approve their own outputs or clear risk stops.
- Specialist desks cannot edit another desk's source evidence or portfolio version.
- OCC is the coordinator and audit record, not a broker, exchange or execution engine.
- Risk/Security retains stop-and-challenge authority only.
- Owner-reserved approvals remain outside the agent chain.
- If Crypto, Forex, Indices and Gold assessments conflict, record the conflict and escalate to OCC review; do not average the views or let a language model select a winner.

## Build gates

1. Confirm the source-of-truth and schema versions for OCC, PolyBot and each specialist desk.
2. Implement authenticated snapshot transport and replay protection before any cross-process control message is trusted. A SHA-256 digest alone is not sender authentication.
3. Wire the stop-only bridge to the existing deterministic controller and test HALT, CLEAR, missing snapshot, stale snapshot, tampering, restart and storage failure.
4. Add specialist market-data adapters only after source, licence, timezone, venue and instrument/contract mapping are verified.
5. Add replay and paper simulations with market-specific costs, sessions, gaps, rollovers and failure cases.
6. Run shift handover, outage, conflicting-signal and recovery rehearsals.
7. Keep all live execution disabled unless a separate explicit owner approval and independent readiness review are completed.

## Explicit non-capabilities

This architecture does not establish a running service, real-time data feed, authenticated inter-process connection, replay protection service, autonomous background operation, broker/wallet access, signing, order routing, trade sizing, leverage, live trading, deployment or production readiness.

## Capital Flow evidence path

The Capital Flow → Crypto handoff is research-only. It carries canonical event IDs, separate source/attribution/event confidence dimensions, evidence references, review state, conflicts and limitations. The Crypto desk must independently validate token/contract identity, event finality, attribution, liquidity and relevance. Rejected, expired, orphaned or ledger-invalid records are not consumed. See [handoff specification](CAPITAL-FLOW-CRYPTO-DESK-HANDOFF.md).

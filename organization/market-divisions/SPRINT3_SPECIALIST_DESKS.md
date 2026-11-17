# Sprint 3 — Specialist Market Desks

**Status:** Contract and operating model only. Research/paper scope; no execution authority.

## Organisation

OCC coordinates four independent specialist desks:

1. **Crypto** — 24/7 venues, token/contract identity, on-chain flows, liquidity, custody and smart-contract risks.
2. **Forex** — pair orientation, pip conventions, broker contract specifications, session/holiday state, macro releases and rollover/financing.
3. **Indices** — cash index versus futures versus CFD identity, multiplier/tick value, exchange calendar, overnight gaps, expiry and roll.
4. **Gold** — a dedicated first-class desk for XAUUSD, COMEX futures and gold exposure distinctions. It owns its own source lineage, ounce/contract conversions, spot/futures basis, session liquidity, USD/real-yield/event research, expiry/roll checks and settlement/financing risk. Gold is not subsumed into Forex.

## Common authority boundary

- Desks research, simulate, challenge and report. They do not create or authorize orders.
- OCC coordinates and records readiness; it cannot grant trade authority.
- The deterministic risk controller remains independent and can block new exposure.
- A HALT from any validated desk/OCC source is escalated globally. A desk cannot clear another desk's veto.
- Missing, stale, delayed, indicative, synthetic, unlicensed or ambiguously mapped data cannot satisfy live-readiness gates.
- Conflicting desk views are escalated, not averaged into a synthetic consensus.
- All decisions retain source timestamps, received timestamps, exact instrument mapping, portfolio version and evidence references.
- All times use UTC at system boundaries; local market sessions are explicit metadata, never inferred from a symbol alone.

## Day/night operation

Each desk has an outgoing and incoming handover record. The outgoing shift records accepted data snapshot, open hypotheses, active vetoes, unresolved incidents, dependency health and next review time. The incoming shift acknowledges the handover and reconciles positions/orders/fills before making a new paper assessment. A missed handover, uncertain state or failed persistence is a stop condition.

## Halal and product-structure review

Asset identity alone does not establish permissibility. Instrument-specific review must cover ownership/possession, spot versus derivative structure, leverage/margin, interest or swap/rollover charges, short selling, settlement, counterparty and broker terms. Unassessed means unassessed; no model may declare a product halal by default.

## Delivery sequence

1. Freeze the common input/output contract and central authority boundary.
2. Add source-specific adapters only after provenance, licence and instrument mapping are documented.
3. Add deterministic quality gates and per-market contract tests.
4. Build replay and paper evaluation with realistic spread, fees, slippage, session and rollover effects.
5. Add shared portfolio versioning, restart-safe state and explicit shift handover.
6. Run independent risk review and readiness assessment.
7. Keep live execution disabled unless a separate explicit owner approval and full operational review are completed.

## Not included

No live feeds, paid data, broker APIs, wallet connections, signing, order routing, trade sizing, leverage, execution, deployment, external account changes or spending. Synthetic fixtures may test code paths but cannot be represented as live market evidence.

## Capital Flow Intelligence integration

The Crypto desk may receive evidence-only event packets under [the Capital Flow → Crypto handoff](CAPITAL-FLOW-CRYPTO-DESK-HANDOFF.md), validated by `capital-flow-desk-handoff.schema.json`. Canonical event records and the verified review ledger remain authoritative; packets are not signals or trade instructions.

## Gold data-quality contract

Gold observations are subject to [the XAUUSD data-quality controls](GOLD-XAUUSD-DATA-QUALITY.md) and the Gold-specific conditions in `market-observation.schema.json`. Indicative bullion spot, broker XAUUSD, gold CFDs and COMEX futures remain distinct instrument bases.


## Common observation contract and synthetic validation fixtures

The common [market observation schema](market-observation.schema.json) now makes specialist identity explicit for Crypto spot/perpetuals, Forex quote orientation, cash indices, futures, CFDs and Gold. The offline [evidence-to-desk gate](EVIDENCE-TO-DESK-GATE.md) checks the local source registry, timestamp quality and instrument-specific fields. Four deterministic synthetic fixtures are documented in [Synthetic Specialist Desk Fixtures](SYNTHETIC-SPECIALIST-FIXTURES.md); they are test data only and cannot establish market readiness or authorize external sources.

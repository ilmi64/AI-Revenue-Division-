# Policy Gateway PG-1 to PG-7 — Evidence and Blocker Crosswalk

**Status:** Documentation crosswalk; no implementation validation, test execution, independent review, rehearsal or activation performed.

## Executive assessment
The organization has a substantial design foundation, but the Policy Gateway is not production-enforced. PG-1 through PG-7 describe intended controls and acceptance evidence; they do not prove that any runtime, connector, database, sender or receiver enforces them.

## Evidence crosswalk
| Stage | Design artifact / current evidence | Implementation evidence | Verification state | Main blocker before progression |
|---|---|---|---|---|
| PG-1 Operation taxonomy | Company-specific AR.* and TT.* operation taxonomies documented | No deployed company-local policy enforcement demonstrated | DESIGN ONLY | Owner review of taxonomies; exact allowlists and hard-deny semantics must be implemented deterministically |
| PG-2 Approval compatibility | Full-scope approval and transaction design documented | No schema migration or unified durable repository implemented | DESIGN ONLY | Resolve trusted-façade vs SQLite approval-scope mismatch; define one transactional approval/audit authority |
| PG-3 Identity and owner authority | Company-local issuer, owner authority, keys, revocation and trusted-time architecture documented | No production keys, issuer, owner endpoint or revocation service | DESIGN ONLY | Independent key custody, identity proof, owner-only approval issuance, rotation/revocation and trusted time |
| PG-4 Enforcement and bypass resistance | Scheduler/runtime/tool/data/cost/outbox/egress/receiver enforcement map documented | No complete enforcement coverage or bypass resistance demonstrated | DESIGN ONLY | Prove all execution paths are mediated; prevent direct connector, DB, shell, network and delegated-agent bypass |
| PG-5 Conformance matrix | 44 core synthetic conformance cases plus company overlays documented | Executable harness/fixtures incomplete; latest tests not run | SPECIFICATION ONLY / NOT_RUN | Complete deterministic fixtures and harness; obtain explicit test-execution approval; record pinned-revision results |
| PG-6 Durable store and recovery | Transaction, idempotency, epoch fencing, ambiguity and recovery design documented | No production store, sender, receiver, immutable audit or restore drill | DESIGN ONLY | Durable transactional consumption; receiver idempotency; no automatic resend on ambiguous outcome; independently tested recovery |
| PG-7 Independent review and rehearsal | Reviewer criteria, review scope, 14 tabletop scenarios and staged gates documented | No independent review, rehearsal or activation | PLAN ONLY | Qualified independent reviewer; exact revision; findings closed; controlled rehearsal; owner acceptance |

## Cross-cutting blockers
1. Cryptographic trust: production asymmetric signatures, separated company trust roots, key custody, rotation and revocation are not implemented.
2. Approval schema: current approval storage does not persist every scope field expected by the trusted façade.
3. Owner authority: no demonstrated separately authenticated owner-only approval issuance endpoint.
4. Durable one-use consumption: no proven multi-process/multi-node linearizable approval consumption and dispatch reservation.
5. Enforcement completeness: no proof that every tool, runtime, data, cost, egress and receiver path is mediated.
6. Revocation and emergency stop: propagation freshness and fail-closed behavior are not operationally demonstrated.
7. Trusted time: expiry and clock-skew controls are not implemented and independently tested.
8. Receiver idempotency: no receiver-side stable idempotency and recovery-epoch enforcement proven.
9. Audit integrity: no independently protected signing/checkpoint and immutable export demonstrated.
10. Recovery separation: assessor, owner release and dispatch authority separation is not rehearsed.
11. Resource controls: inference, tool, compute and external-action cost meters are not deployed.
12. Independent assurance: no independent adversarial review or operational rehearsal has occurred.

## Company-specific hard boundaries
### AI Revenue
- CAD $0 incremental spend remains default; unknown or billable inference, compute, API, hosting and subscription costs deny.
- Customer contact, publishing, contracts, purchases, account changes and production deployments remain approval-gated.
- Customer data remains in AI Revenue's tenant and approved storage.

### Trading & Technology
- Research and paper simulation only by default.
- Live orders, wallet signing, transfers, withdrawals, broker/exchange orders and risk-limit modifications remain hard-denied; owner approval cannot override.
- Independent CRO/risk veto remains mandatory. Market-data, identity, policy, risk-service or audit uncertainty fails closed.
- Halal/Shafi'i review is separate and does not become a model-issued ruling.

## Required evidence before any staged activation
- Exact-revision independent design/security review with findings and dispositions.
- Completed executable synthetic conformance suite, with authorized execution and retained logs.
- Negative tests for replay, expiry, scope mismatch, duplicate dispatch, outage, bypass and cross-company access.
- Durable store concurrency and crash-recovery evidence.
- Receiver idempotency and ambiguous-outcome reconciliation evidence.
- Revocation, emergency-stop, clock and audit-integrity evidence.
- Recovery tabletop and restore rehearsal, independently assessed.
- Company-specific owner acceptance and a separately approved, narrow activation scope.

## Reporting rule
Use these evidence states consistently: SPECIFIED, IMPLEMENTED, EXECUTED, PASSED, INDEPENDENTLY VERIFIED, REHEARSED, AUTHORIZED. Never promote a document or authored test to a higher state without its corresponding evidence.

**Current disposition:** PG-1 through PG-7 documentation is substantially prepared. The gateway is not implemented as a production control plane, no tests have been run under the current approval boundary, no independent review/rehearsal has occurred, and no activation is authorized.
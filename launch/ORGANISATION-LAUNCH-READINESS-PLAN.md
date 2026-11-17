# Organisation-wide Launch Readiness Plan

**Status:** Draft operating plan; not a launch authorization  
**Baseline:** 2026-11-16  
**Scope:** All active divisions except Animora, which is on hold  
**Launch model:** Coordinated organisation-wide launch with capability-specific gates

## 1. Objective

Prepare one governed organisation, not disconnected prototypes. All ten active divisions participate in the initial readiness programme. A division may enter in restricted read-only, research or paper mode while higher-risk capabilities remain disabled.

A document, dashboard, passing unit test, mergeable pull request or synthetic simulation is not by itself evidence of operational readiness.

## 2. Scope

Active divisions:
1. Executive Management and Organisation Control Centre (OCC)
2. AI Revenue
3. Technology and Infrastructure
4. Research and Intelligence
5. Finance and Treasury
6. Risk, Security and Recovery
7. Crypto and PolyBot
8. Trader Intelligence and Strategy Replication (TISRD)
9. Ecommerce
10. Business and Commercial

Animora is excluded from active implementation by owner instruction. Preserve existing work; do not edit its app, consume Lovable credits or advance studio/store production until resumed.

## 3. Launch tiers

### Tier A — Controlled internal/read-only launch
Potential scope: source intake, research, dashboards, internal task routing, evidence records, finance simulations, risk monitoring, offline tests, manual research and paper trading. Requires source permissions, security, provenance, monitoring, incident and rollback controls.

### Tier B — Limited commercial operation
A specific service or product may operate only after its own legal, tax, privacy, consumer, contract, fulfilment, funding and owner-approval gates pass. This does not authorize trading or other divisions' external actions.

### Tier C — Live financial operation
Separate higher gate. Requires verified Ontario eligibility and legal/product review, approved counterparties where applicable, approved accounts and permissions, tested read-only feeds, independently validated strategies, capital/risk limits, custody/signing controls, incident response and explicit owner authorization. This plan does not authorize live trading, wallet signing, deposits, withdrawals or financial transactions.

A Tier A launch must never be described as Tier B or Tier C readiness.

## 4. Organisation-wide exit criteria

All mandatory controls must pass before Tier A launch:
- Canonical division and owner-role registry; no duplicate or orphan divisions.
- OCC status, queue, dependency, evidence, approval and incident views reconcile to source records.
- Every task has a unique ID, scope, responsible role, dependency, acceptance evidence, risk class and approval gate.
- Every external data source has documented provenance, permitted use, rate limits, retention, freshness and failure behaviour.
- Credentials are stored outside source code and logs; least privilege; no secrets in prompts, tickets or artifacts.
- Risk controls are deterministic for hard stops and cannot be overridden by model output.
- Finance distinguishes forecast, receivable, invoice, payout pending, cash received and reconciled cash.
- Automated workflows have timeout, bounded retry, idempotency, duplicate handling, review path and operator stop.
- Incident severity, escalation, evidence preservation, recovery owner and restart authorization are rehearsed.
- Backups are restorable; changes versioned; release and rollback procedures tested.
- Human approval gates enforced for spending, external contact, publishing, contracts, account changes and financial actions.
- End-to-end rehearsal demonstrates cross-division handoffs and complete audit trail.
- Tests executed in a supported environment with results tied to exact commits.
- No unresolved critical/high security, legal, data-rights or financial-control blocker remains for selected scope.

## 5. Workstream approach

All divisions progress in parallel through four lanes:
- Foundation: scope, roles, schemas, source register, controls and runbooks.
- Build: implementation on isolated feature branches; no production deployment.
- Verification: offline tests, read-only integration, failure injection, security review and evidence capture.
- Rehearsal: integrated controlled scenario, handover, stop/recovery and executive sign-off.

A blocked division continues safe independent work and reports its blocker.

## 6. Readiness states

- PLANNED: scope or design not established.
- BUILDING: artifacts or partial implementation exist; incomplete or unverified.
- TESTING: bounded tests or rehearsal underway with evidence.
- READY_RESTRICTED: controls pass for a specifically named restricted mode.
- OPERATIONAL: approved scope is live, monitored, staffed and supported by ongoing evidence.
- BLOCKED: unresolved dependency or control prevents intended scope.
- ON_HOLD: owner-directed pause.

Every status cites evidence and timestamp. No status advances on narrative assertion alone.

## 7. Governance and approvals

Owner approval required before any purchase, subscription, paid API, paid credits, billing-risk trial, external outreach, application, proposal, customer commitment, contract, publishing, listing, advertising, account change, permission grant, wallet connection, deposit, withdrawal, transfer, signing, live trade, merge to protected/base branches or production deployment.

Executive and Risk functions may recommend, challenge and stop. They cannot authorize owner-reserved actions or override deterministic safeguards.

## 8. Current global constraints

- CAD 0 incremental spending ceiling until owner changes the rule after revenue.
- No paid services, API usage, trials with billing risk, upgrades or infrastructure purchases.
- GitHub Actions remain on hold; preserve the next 2,000 minutes for owner-prioritized tests/deployments.
- No merge or production deployment.
- No wallet signing, live trading, deposits or withdrawals.
- No Animora implementation while on hold.
- No TikTok work unless owner reopens that channel.
- Do not claim unattended background operation without a supported runtime, named owner, alert path and tested recovery.

## 9. Initial launch decision

The first launch candidate is Tier A: coordinated internal, read-only and paper operations across all ten active divisions. This is a target, not a declaration of readiness. Tier B and Tier C are separate approvals.

## 10. Required executive launch packet

Before Tier A go/no-go, assemble:
- Current division readiness matrix and linked evidence.
- Exact commit/branch identifiers and executed test results.
- Data-source and permission register.
- Security review and credential inventory (never secret values).
- Risk and incident register with accountable owners.
- Finance reconciliation and zero-spend confirmation.
- End-to-end rehearsal results, defects and remediation.
- Backup/restore and rollback evidence.
- Outstanding blockers and scope exclusions.
- Owner's explicit go/no-go decision and approved operating envelope.

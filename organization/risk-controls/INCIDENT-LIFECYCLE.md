# Organisation incident lifecycle

This is a draft operating procedure. It does not establish a staffed incident-response team or production monitoring.

## Lifecycle

1. **Detect** — record the time, affected division/system, observed symptom and detection source. Do not convert a suspicion into a fact.
2. **Triage** — assign SEV1–SEV4 based on impact, scope, active exposure and recoverability. Record facts separately from hypotheses.
3. **Contain** — stop the affected workflow, revoke or isolate only where the owner has authorised the specific action, and preserve relevant evidence. For trading/order uncertainty, halt new activity and reconcile before resumption.
4. **Investigate** — build a timestamped event timeline; record source, integrity, access restrictions and confidence for each evidence item.
5. **Recover** — use a known-good backup or rollback plan only after owner approval and independent review where the action is consequential.
6. **Validate** — verify system state, data integrity, access scope and downstream effects. A successful restart alone is not closure.
7. **Close and learn** — record root cause or unresolved uncertainty, impact, corrective actions, owners, due dates and evidence of completion.

## Severity guide

- **SEV1 — Critical:** active credential compromise, unauthorised financial/wallet action, uncontrolled live execution, material data breach, or organisation-wide critical outage.
- **SEV2 — High:** significant division outage, suspected unauthorised access, unresolved transaction/fill state, or material integrity failure with contained scope.
- **SEV3 — Moderate:** degraded service, failed scheduled workflow, isolated data-quality issue, or recoverable control breach without evidence of external impact.
- **SEV4 — Low:** minor defect, documentation gap or non-urgent improvement.

Severity is provisional and must be revisited when evidence changes.

## Minimum incident record

- Unique incident ID and UTC timestamps.
- Reporting and affected divisions; accountable owner and reviewer.
- Category, severity, status and affected assets/systems.
- Observed facts, hypotheses and confidence kept distinct.
- Evidence references, provenance, integrity notes and access restrictions.
- Containment and recovery decisions, approvals and timestamps.
- Dependencies, notifications considered, next review time and closure evidence.

## Mandatory safeguards

- Never place passwords, MFA codes, seed phrases, private keys or API secrets in tickets, prompts, reports or evidence bundles.
- Do not contact providers, customers, regulators, law enforcement or counterparties without explicit owner approval.
- Do not pay upfront recovery fees, promise recovery, or trade to recover losses.
- Risk & Compliance may impose a stop recommendation and escalate; it cannot authorise transactions or waive deterministic controls.
- When facts are uncertain, preserve uncertainty and keep the affected workflow halted.
- No automated incident action may spend money, sign, transfer, publish, change permissions or deploy.

## Readiness limitation

This procedure is not operational until named responders, contact paths, evidence storage, access controls, notification mechanisms, tested playbooks and a witnessed tabletop exercise exist.

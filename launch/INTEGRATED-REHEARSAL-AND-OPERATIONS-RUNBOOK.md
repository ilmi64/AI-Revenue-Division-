# Integrated Rehearsal and Operations Runbook

**Status:** Proposed rehearsal procedure; no rehearsal has yet been claimed  
**Target:** Tier A coordinated internal/read-only/paper launch

## 1. Objectives

Demonstrate that all ten active divisions exchange correctly scoped information through OCC, maintain evidence and approvals, detect unsafe conditions, stop safely, recover and produce one consolidated executive report. This does not test profitability or authorize live trading/external actions.

## 2. Required roles

Assign before rehearsal:
- Executive owner / launch decision-maker.
- OCC coordinator.
- Technology/runtime operator.
- Research/data steward.
- Finance controller.
- Independent Risk lead.
- Crypto/PolyBot research operator.
- TISRD research reviewer.
- AI Revenue pipeline owner.
- Ecommerce analyst.
- Business & Commercial reviewer.
- Incident commander and backup.

If one person holds multiple roles, record conflicts and require independent review for critical risk, finance and release decisions. Unassigned role templates do not count as staffed coverage.

## 3. Pre-flight

- Freeze exact feature-branch commits under test and record SHAs.
- Confirm GitHub Actions remain unused until owner releases hold.
- Confirm zero incremental spend and no paid endpoint/trial activation.
- Confirm no production credentials, private keys, seed phrases or wallet signing capability are present.
- Confirm test data is synthetic or lawfully acquired and labelled.
- Confirm source terms and permitted use for every external feed.
- Confirm deterministic hard stops and approval gates.
- Confirm environment isolated from production accounts and funds.
- Confirm backup/restoration procedure and evidence location.
- Confirm incident contacts, stop authority and restart authority.
- Confirm Animora excluded and untouched.

## 4. Rehearsal scenarios

### A — Normal multi-division intake
1. Research ingests a small approved set of source observations.
2. Source adapter preserves provenance, source timestamp, retrieval time and freshness.
3. Technology validates schema, idempotency and error handling.
4. Crypto, Forex/Gold/Indices research receives matching instrument semantics only.
5. TISRD receives permitted aggregate/public research inputs only.
6. OCC creates linked work items with dependencies and acceptance evidence.
7. AI Revenue and Business/Commercial update internal opportunity records without external contact.
8. Ecommerce calculates a sample contribution estimate using explicitly synthetic inputs.
9. Finance labels figures simulated/forecast and does not classify them as cash received.
10. Risk checks no prohibited action is enabled.
11. OCC produces a consolidated report with source references and decisions.

Expected: traceable records, no unapproved external action, distinct finance categories.

### B — Stale or conflicting market data
Inject stale observations and conflicting provider values. Verify stale records cannot silently enter a signal; disagreement triggers review; originals are retained; affected division and OCC receive the exception.

### C — Agent/model failure
Simulate model timeout, malformed response, unsupported source citation and provider quota exhaustion. Verify deterministic validation, bounded idempotent retries, explicit fallback records and human review for consequential/uncertain outputs. No permission escalation.

### D — Finance and approval boundary
Enter simulated invoice, payout pending, CAD cash receipt with proof, non-CAD receipt without conversion evidence and unapproved commitment. Verify only eligible reconciled CAD receipts count as cash; forecasts/receivables/payouts remain distinct; unapproved purchase/publishing/contact actions are blocked.

### E — Crypto paper-exit uncertainty
Simulate exit reservation, no-fill, timeout or persistence failure. Verify position remains pending; no profit stage is consumed; reset/clear cannot erase unresolved exit; restart halts or reconciles as specified; no wallet or exchange execution endpoint is reachable.

### F — Incident, recovery and restart
Inject synthetic data-integrity or credential-exposure incident. Trigger stop/quarantine; preserve evidence; assign commander; pause dependent work; restore from known-good backup in isolation; validate integrity; require independent Risk review and explicit owner restart approval.

### G — Day/night handover
Day desk prepares time-bounded report; Grok Desk receives source-linked facts, hypotheses, unresolved items and risks; HyperGrok/designated reviewer challenges quality and contradictions; OCC acknowledges or rejects handover. No context loss, duplicate task or implied trade authorization.

## 5. Stop conditions

Halt affected workflow and escalate if:
- Secret, private key, seed phrase or credential is exposed.
- Prohibited or unapproved external action is attempted.
- Source rights or jurisdictional permission are uncertain.
- Hard risk limit or deterministic safeguard fails.
- Data is stale, malformed or materially conflicting and cannot be isolated.
- Ledger or position state cannot be reconciled.
- Evidence is missing, altered or inaccessible.
- Backup cannot be restored or integrity is uncertain.
- Operator, incident owner or stop authority is unavailable.

No model may waive a stop condition.

## 6. Handover record

Every shift handover contains:
- Handover ID and UTC window.
- Sending and receiving role acknowledgements.
- Active divisions and systems in scope.
- Completed tasks and evidence references.
- Source status, freshness and outages.
- Verified facts, clearly labelled hypotheses.
- Open risks/incidents and severity.
- Pending approvals and prohibited actions.
- Next review time/trigger.
- Exact software/configuration version and known defects.

## 7. Evidence and scoring

Record each scenario PASS, FAIL, BLOCKED or NOT_RUN. PASS requires observable result and evidence reference. Synthetic fixtures must be labelled. Capture defect severity, owner role, remediation and retest.

Tier A requires all critical scenarios pass; no unresolved critical/high security, data-integrity or approval defect; no unauthorized action possible in tested scope; backup restoration and safe stop/restart demonstrated; all ten active divisions visible in consolidated report; owner, Risk and Technology sign off exact tested commit and operating envelope.

## 8. Post-rehearsal

OCC produces scope, exact commits, environment, scenarios, results, defects, residual risks, division status changes, exclusions and go/no-go recommendation. Only owner can authorize launch. Passing rehearsal is not permission for Tier B or Tier C activity.

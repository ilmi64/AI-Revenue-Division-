# Division Launch Acceptance Matrix

**Status:** Baseline assessment; readiness claims require linked evidence and re-verification  
**Scope:** Ten active divisions; Animora is ON_HOLD and excluded

| Division | Initial restricted launch scope | Evidence already present | Critical missing evidence / acceptance gate |
|---|---|---|---|
| Executive Management / OCC | Read-only consolidated status, queue, dependencies, approvals and reporting | OCC foundation PR #1; integration PR #6; 20-task queue; division registry; task packet generator; AI workforce dashboard integration | Review branch dependency chain; run validators offline; reconcile queue and all canonical division IDs; test malformed/missing data; test role/approval handoffs; owner roles unassigned; no operational control plane or staffed board |
| AI Revenue | Internal opportunity research and pipeline tracking; no external applications or promises | Read-only revenue intelligence PR #3; candidate opportunity research and ATS checks reported previously | Re-verify current PR head; refresh opportunities, Canada eligibility, payout/fees and terms; approval for applications/outreach; pipeline from lead to accepted work to invoice to reconciled cash |
| Technology / Infrastructure | Offline builds and isolated test runtime; no production autonomy | AI workforce registry PR #5; Qwen2.5 1.5B integration foundation; model/routing architecture | Qwen end-to-end unverified; Llama 3.2 1B not installed; runtime/host not established; secrets, least privilege, sandbox, network policy, logs, monitoring, backup and recovery untested |
| Research / Intelligence | Permitted read-only research and source qualification | Market-data registry: 5 instrument groups and 17 candidates; gold/FX/indices review; Hype manual intake specification | Terms and Canada/Ontario reviews pending; independent corroboration; freshness, outage and disagreement tests; lawful use and retention evidence; source owners unassigned |
| Finance / Treasury | Offline ledger and zero-spend reconciliation | Finance controls and 14 regression test cases; month-end close procedure; CAD proof-of-receipt logic | Tests not run; no bank connector or verified balances; no reconciled opening cash; no approved signatory; tax/liability and reserve figures unverified |
| Risk / Security / Recovery | Offline policy validation and tabletop rehearsal | Risk policy, eight cross-division risk entries, evidence register schema, incident lifecycle and validators | Tests not run; ratings provisional; ownership unassigned; evidence store not protected/tamper-evident; no alerting or staffed response; no recovery rehearsal; access controls/security review incomplete |
| Crypto / PolyBot | Read-only market intake, manual observation and paper simulation only | Binance public adapter PR #4; Pump.fun research and paper prototypes; day/night desk PR #37; staged-exit reconciliation PR #42; Hype manual research PR #40 | Real Pump.fun create/createV2 and CPI/inner-instruction coverage unverified; two independent RPCs not tested; no qualifying real out-of-sample data; fees/spread/impact/latency uncalibrated; no wallet signing/live orders |
| TISRD | Public, permitted, non-personal research and methodology review | TISRD design PR #39; Hype intake restricted to operator-entered aggregate asset observations | Verify rights per source; no unauthorized scraping/profiling/copying; methodology and survivorship-bias controls; out-of-sample evidence; Ontario eligibility; PR chain/tests need re-verification |
| Ecommerce | Offline product and unit-economics research only | Unit-economics calculator, README, sample CSV and six regression tests | Tests not run; real supplier/shipping quotes absent; marketplace fees, tax, refunds, returns, payouts and demand unverified; store strategy under review; no products, supplier commitments or publishing |
| Business & Commercial | Internal offer, pricing and partnership design | Cross-division dependencies and commercial concepts in programme | No approved offer catalogue, costed delivery capacity, legal terms, privacy/consumer review, contract templates, pipeline owner or validated demand; no external outreach or commitments |

## Cross-division acceptance rules

1. Each division names an accountable owner role and backup; role assignment does not imply an agent or person is staffed.
2. Each deliverable has an acceptance test and retained evidence.
3. Shared schemas and IDs are used for work, risks, incidents, sources and approvals.
4. Data quality and legal permissions are checked before downstream use.
5. A failure in one division is visible to dependent divisions and OCC.
6. No agent promotes its own output to verified evidence without independent checks where required.
7. Risk can place a hold; only the designated owner approves owner-reserved actions.
8. A division may be READY_RESTRICTED for a bounded scope while other capabilities remain blocked.

## Initial Tier A exclusions

- Live financial execution, wallet signing, custody, deposits, withdrawals or transfers.
- Paid APIs, paid model access, subscriptions, trials or purchases.
- Automated collection where source terms do not authorize it.
- Customer outreach, external applications, contracts, publishing, product listings or advertising.
- Animora app, studio, merchandise or store development while on hold.
- Workflows requiring a continuously running host or alert path not yet established.

## Evidence record template

For every acceptance item, record: acceptance ID, division, requirement, status, evidence URI, commit SHA, test command, environment, test timestamp UTC, result, reviewer, open defect IDs, scope limitations and next review date.

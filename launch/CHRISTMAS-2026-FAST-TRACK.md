# Christmas 2026 Readiness / New Year 2027 Launch Fast-Track

**Prepared:** 2026-11-16  
**Readiness target:** 2026-12-24  
**Coordinated activation target:** First eligible operating sessions after New Year 2027 (initial planning window: week of 2027-01-04)  
**Status:** Execution schedule and readiness gates; not a launch authorization  
**Scope:** Ten active divisions; Animora remains ON_HOLD

## 1. Two-stage outcome

**By December 24, 2026 — be ready to initiate.** All ten active divisions should have completed their applicable build, integration, security, testing and rehearsal work; exact launch scope, owners, blockers, operating procedures and approvals should be assembled into a final go/no-go packet. Christmas is the readiness deadline, not the live-market launch date.

**After New Year — coordinated controlled activation.** Aim to initiate approved division operations at the first eligible sessions after the New Year holiday, planning around the week of January 4, 2027. Actual activation dates must be checked against each relevant exchange, broker, venue, provider and jurisdiction calendar. Crypto markets may trade continuously while traditional exchanges and FX/metals providers follow separate holiday schedules. Do not assume all instruments reopen at the same time.

The intended first activation is a controlled, restricted programme: OCC coordination, internal reporting, authorized read-only research, finance/risk monitoring, and paper trading where its controls pass. Any division or capability that fails its gate remains blocked or excluded rather than delaying safe independent divisions.

This is not a promise that every commercial service or live financial capability will be ready. Tier B commercial operation and Tier C live financial execution remain separate approvals. A coordinated organisational launch does not itself authorize live trades, wallet signing, deposits, withdrawals, customer commitments, publishing, spending, merge or deployment.

## 2. Non-negotiable operating envelope

- Incremental spend: CAD 0 until the owner changes the rule after revenue.
- No paid APIs, subscriptions, trials with billing risk, upgrades or infrastructure purchases.
- GitHub Actions: HOLD until the owner explicitly releases it. Preserve the next 2,000 minutes.
- No merge, branch retarget, protected-branch change, deployment or production launch without explicit owner approval.
- No wallet signing, live order, deposit, withdrawal or transfer.
- No Animora implementation or Lovable credit use while Animora is ON_HOLD.
- All work remains on isolated feature branches or in offline/read-only preparation.
- A green CI result, mergeable PR, synthetic simulation or completed document is not an operational-readiness certificate.

## 3. Actions quota protection

A read-only workflow-file audit found scheduled triggers in both default-branch repositories:

- PolyBot `.github/workflows/paper-simulation.yml`: weekday schedule `0 14 * * 1-5`; it runs the full Python unit-test suite and synthetic paper simulation. Its PR workflow also runs on pull requests targeting `main`.
- AI Revenue `.github/workflows/research-radar.yml`: weekly schedule `23 13 * * 1`; the job runs tests, installs Ollama, downloads Qwen2.5 1.5B, generates a report and uploads an artifact.

The workflow files contain these schedules; the current enabled/disabled state and future run history were not verified. A local instruction not to trigger Actions does not itself pause scheduled workflows. The owner should confirm both workflows are disabled/paused in GitHub Actions while the 2,000-minute reserve is protected. Do not edit workflow files to pause them during this hold, because a push/PR event could itself trigger a run. No workflow was triggered by this audit.

## 4. Current OCC baseline and reconciliation gap

The latest read-only parse of the inherited OCC source records shows:

- 20 work-queue tasks; all 20 remain `proposed`.
- All 20 tasks remain `unassigned_pending_owner_confirmation`; none is recorded as started or completed.
- The inherited readiness register reports nine active divisions as `building` and Crypto as `testing`; it still reports Animora as `building`.
- The inherited queue still contains ANI-001 and ANI-002 as proposed tasks.

The owner's later instruction to place Animora ON_HOLD takes precedence operationally. The inherited readiness register and queue have not yet been reconciled to that instruction because the launch PR is deliberately kept on its current parent commit. Until a reviewed source-register update is integrated, OCC dashboard outputs may still display stale Animora and queue states. Do not treat those inherited values as current owner intent or as evidence of assigned work.

The immediate OCC priority is to reconcile owner-directed holds, active scope, role/backup assignments, queue state and dashboard interpretation before any launch rehearsal.

## 5. Countdown work plan

Dates are target windows, not evidence that work has happened. If a prerequisite or Actions release is delayed, keep the relevant gate blocked rather than compressing or skipping safety checks.

| Window | Priority work | Exit evidence |
|---|---|---|
| Nov 17-20 | Executive/OCC governance, role and backup roster proposal, task/evidence/dependency reconciliation, decision queue and division ownership gaps | One canonical register; every active division has accountable owner role, backup requirement, escalation route and acceptance evidence; owner-reserved decisions remain pending |
| Nov 20-24 | Repository and PR dependency audit across OCC and PolyBot; resolve duplicate/overlapping workforce scope; refresh exact base/head SHAs; prepare local test instructions | Reviewed dependency graph, file-overlap report, exact commit inventory, isolated integration sequence and no blind retargeting |
| Nov 24-30 | Offline validation and code review; finance and risk controls; source-rights/Ontario review; security and runtime gap closure; paper-state/restart review | Reproducible local checks where environment permits; defects logged with severity; source-use decisions; security and runtime acceptance checklist |
| Dec 1-5 | If and only if owner releases Actions: run the smallest high-value validation set first, exact-head and dependency ordered | Test results tied to exact SHAs; failures captured and triaged; Actions consumption recorded; stop before broad runs if critical failures appear |
| Dec 6-12 | Remediate test failures; verify read-only source adapters, data freshness, finance reconciliation, stop conditions, state integrity, backup/restore | Repeatable passing tests for selected scope; no unresolved critical/high blocker affecting intended activation |
| Dec 13-18 | Integrated cross-division rehearsal: normal handoff, stale/conflicting data, model/provider failure, finance boundary, paper exit uncertainty, incident/recovery, day/night handover | Timestamped rehearsal records, participant/owner roles, expected vs actual outcomes, defects and remediation evidence |
| Dec 19-22 | Final evidence review, access/secret review, zero-spend check, restore/rollback check, scope and exclusions freeze | Complete executive launch packet; every gate PASS or explicit BLOCKED; no silent waivers |
| Dec 23-24 | Readiness review and freeze; approve or reject proposed January activation scope | Owner's explicit readiness decision, approved operating envelope, named operators/backup and January activation checklist; otherwise remain in controlled preparation |
| Dec 26-31 | No rushed year-end market activation. Reconfirm venue calendars, source health, permissions, credentials, data quality and operational staffing; only conduct approved non-market preparation | Fresh dated pre-open checks and no unresolved critical/high blocker for each proposed capability |
| Jan 4-8, 2027 (planning window) | Initiate approved divisions at their first eligible operating sessions, in controlled stages; maintain stop authority and daily reconciliation | Per-division activation record, exact scope, market/session confirmation, live monitoring and rollback path; live financial actions remain separately gated |

## 6. GitHub Actions release-day sequence

Do not trigger workflows while the hold is active. Once the owner explicitly releases the hold, use this order and stop on critical failures:

1. **OCC foundation and data integrity:** validate division registry, work queue, readiness register, dashboard and task-dispatch validators at the exact proposed integration commits.
2. **AI workforce:** run model/role/handoff schema validators; Qwen runtime test only if its runner and model download fit the available quota. Llama remains optional and must not displace core tests.
3. **Finance and Risk:** execute finance-control, risk-register, evidence-register and incident-control tests.
4. **Market data:** validate source-registry schemas and adapter unit tests; no paid endpoints or credentialed provider tests.
5. **PolyBot critical state safety:** run PR #42 staged-exit reconciliation tests, portfolio ledger/restart tests, fail-closed configuration tests and the smallest relevant deterministic suite.
6. **PolyBot data/strategy integrity:** test Pump.fun create/createV2 decoding and CPI/inner-instruction fixtures, RPC failover, provenance, stale/conflicting data stops and out-of-sample evaluator controls.
7. **TISRD and Hype:** run only permitted manual-intake/schema tests; no unauthorized scraping, profiling or restricted-source ingestion.
8. **Full selected-scope regression:** only after the targeted suites pass and remaining quota is known. Never run broad workflows merely to make the dashboard green.

For each run record workflow URL, commit SHA, trigger, start/end, minutes consumed if available, pass/fail, skipped tests, artifacts and defects. A failed run is not to be rerun repeatedly without diagnosing the failure.

## 7. Repository integration controls

### OCC repository

Current intended chain:
- PR #1: OCC foundation.
- PR #6: workforce, Finance, market data and Risk integration, based on PR #1's branch.
- PR #7: launch-readiness package, based on PR #6's exact head.

PR #5 contains overlapping AI-workforce files and must be compared file-by-file with PR #6. Do not merge both blindly or assume the overlap is harmless. PRs #3 and #4 remain separate main-based workstreams and require their own compatibility review.

### PolyBot repository

Current reviewed chain and known drift:
- PR #36 head is the base branch for PR #37; the recorded base SHA currently matches.
- PR #42 is based on PR #37's exact recorded head and remains a separate paper-state safety improvement.
- PR #39 is based on the PR #37 branch but its recorded base SHA is older than the current PR #37 head; refresh and compare before any integration.
- PRs #40 and #41 are based on the TISRD branch but their recorded base SHA does not match PR #39's current head; reconcile the chain and inspect overlap before any integration.
- Earlier PolyBot PRs contain additional dependencies; do not infer a safe global merge order from PR numbers alone.

Every integration decision requires refreshed PR metadata, changed-file lists, exact base/head SHAs, diff review, dependency verification and owner approval. Mergeable metadata alone is insufficient.

## 8. Ten-division work allocation

| Division | Christmas readiness / January activation focus |
|---|---|
| Executive Management / OCC | Single control plane, canonical registers, owner decision queue, handoffs and executive launch packet |
| AI Revenue | Canada-eligible zero-upfront opportunities, truthful service offer, evidence and revenue-vs-cash tracking |
| Technology & Infrastructure | Reproducible local tests, safe runtime design, secrets/least privilege, backup, restore and rollback |
| Research & Intelligence | Source provenance, terms/rights, freshness, independent corroboration and failure states |
| Finance & Treasury | CAD ledger controls, commitments, receivables vs received/reconciled cash, close and no-spend evidence |
| Risk, Security & Recovery | Deterministic stops, incident roles, protected evidence, escalation, restore and restart rehearsal |
| Crypto & PolyBot | Read-only/paper-only validation, transaction decoding, independent RPC design, position/exit reconciliation and safe-mode behaviour; any live execution excluded absent separate approval |
| Trader Intelligence & Strategy Replication | Lawful source intake, reproducible research, benchmark fairness, out-of-sample evidence and separation from execution authority |
| Ecommerce | Research and unit economics only until supplier, platform, tax, shipping, returns, demand and payout evidence is validated; no listings or purchases |
| Business & Commercial | Costed offer catalogue, delivery capacity, privacy/contract requirements and approval-ready customer workflow; no outreach or commitments |

Animora is intentionally excluded from implementation and activation scope until the owner resumes it.

## 9. Tier A acceptance gate

A Tier A go/no-go packet must show all of the following for the exact selected scope:

- Canonical division, task, dependency, role, approval and evidence registers reconcile.
- Accountable owner/backup and incident escalation roles are explicitly assigned or the capability is excluded.
- All selected code is traceable to exact reviewed commits.
- Applicable tests have actually executed in a supported environment; no fabricated or inferred pass status.
- External data rights, jurisdiction, permitted use, freshness and failure handling are recorded.
- No secrets are present in source, logs, prompts or reports; least-privilege design is reviewed.
- Deterministic stops cannot be overridden by model or executive advisory output.
- Finance records distinguish forecast, receivable, invoice, payout pending, cash received and reconciled cash.
- Retry, idempotency, ambiguous outcomes and operator reconciliation behave safely.
- Backup/restore and rollback have been demonstrated.
- Cross-division rehearsal passes with audit evidence.
- No unresolved critical/high blocker affects the selected Tier A scope.
- Owner explicitly approves the exact operating envelope.

A division may be excluded from initial activation only if its dependencies are isolated and the exclusion is explicit. Crypto remains paper-only unless a separate future live-readiness process and explicit approval are completed.

## 10. Executive reporting cadence

At each active work session, report only:
- What changed, with branch/PR/file/commit references.
- What was actually tested and the exact evidence.
- Critical/high blockers opened, closed or unchanged.
- Actions hold and remaining quota status (without triggering workflows).
- Owner decisions genuinely required.
- Next highest-value work across the active divisions.

Do not describe work as running in the background between sessions unless a supported, verified runtime is actually operating.

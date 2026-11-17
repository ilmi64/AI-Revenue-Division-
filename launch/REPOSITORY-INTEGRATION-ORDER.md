# Repository Integration and Dependency Order

**Status:** Read-only snapshot taken 2026-11-16/17; re-check before any merge  
**Purpose:** Prevent parallel draft pull requests from being merged in an unsafe order.

## AI Revenue / OCC repository

Repository: ilmi64/AI-Revenue-Division-

| PR | Purpose | Current relationship | Required treatment |
|---|---|---|---|
| #1 | OCC foundation | Draft, open, unmerged; base main | Parent foundation. Review and validate before descendants. |
| #6 | OCC workforce, Finance, market data and Risk integration | Draft, open, unmerged; base org-control-centre-foundation (PR #1 head) | Child of #1. Review overlap with PR #5 and verify exact parent SHA. |
| #7 | Organisation launch readiness | Draft, open, unmerged; base feature/occ-ai-workforce-integration (PR #6 head) | Child of #6. Do not merge directly to main or independently of #6. |
| #5 | AI workforce foundation | Draft, open, unmerged; base main | Parallel foundation with overlapping AI workforce files integrated into #6. Compare file-level changes before deciding merge, retarget or close; avoid duplicate/conflicting integration. |
| #3 | Read-only revenue intelligence | Draft, open, unmerged; base main | Independent candidate; verify current head and tests before integration. |
| #4 | Binance public market-data adapter | Draft, open, unmerged; base main | Independent candidate; verify current head, provider semantics and tests before integration. |

Snapshot facts:
- PR #6 head at review: 961ffa0c7ffbd6ce5c90c69b9746e4f73850089a.
- PR #7 base SHA matches that PR #6 head.
- PR #7 head at review: c4e6bac29dc901b509cbaeef8b47a88655da97bf.
- PR #7 was reported mergeable after metadata refresh, but remains draft and unmerged.
- PR #1, #6 and #7 form an explicit parent/child sequence. PR #5 overlaps conceptually and must not be blindly merged as a separate duplicate.

## Solana / PolyBot repository

Repository: ilmi64/Solana-memecoins

| PR | Purpose | Current relationship | Required treatment |
|---|---|---|---|
| #37 | Day/night Grok Desk oversight | Draft, open, unmerged; base feature/j7tracker-fomo-social-signals | Parent desk branch; review base and real data dependencies. |
| #39 | TISRD design | Draft, open, unmerged; base feature/day-night-grokdesk-oversight | Intended child of #37, but reported base SHA did not match the latest #37 head in the snapshot. Reconcile before merge. |
| #40 | Hype manual research intake | Draft, open, unmerged; base feature/trader-intelligence-replication-division | Depends on TISRD foundation. Verify base branch SHA against PR #39 head before integration. |
| #41 | OpenBB / TradingAgents / Investor Skills design | Draft, open, unmerged; base feature/trader-intelligence-replication-division | Parallel TISRD child. Verify base branch SHA and avoid duplicate integration with #40. |
| #42 | Standalone staged-exit reconciliation | Draft, open, unmerged; base feature/day-night-grokdesk-oversight | Intended child of #37; reported base SHA matched #37 head at snapshot. Paper-only; single-process JSON store is not distributed or tamper-evident. |

Snapshot facts:
- PR #37 head at review: 24e21f2a86f9b6b965b44d3b647f37979ff21d9f.
- PR #39 head at review: a532c35c75059a761b8e5e7343373a46df8c856c; its reported base SHA was 8057dd77659de851b342795aef51b4beca0f741e.
- PR #40 and #41 reported base SHA fb6cc2745f75ea5c666f93f4a84c0dd109814de0, which did not match PR #39 head in the snapshot.
- PR #42 base SHA matched PR #37 head at review.
- Mergeable metadata is not proof of a correct dependency chain, test pass or production readiness.

## Safe integration procedure

1. Refresh every PR's base/head SHA and changed-file list immediately before review.
2. Fetch complete diffs and identify duplicate paths, schema drift, import assumptions and incompatible interfaces.
3. Validate dependency order and confirm the intended parent commit is actually the base SHA.
4. Run only the smallest essential offline test suites in a local/supported environment while Actions remain on hold.
5. Record test commands, environment, exact SHAs, output and reviewer.
6. Resolve conflicts on isolated branches; do not overwrite user work.
7. Keep PRs draft until review and acceptance evidence are complete.
8. Obtain explicit owner approval before merge, retargeting protected branches or deployment.

## Explicit no-go conditions

- Never merge a child before its required parent.
- Never assume mergeable=true means the PR is correct.
- Never merge overlapping PR #5/#6 workforce changes without a file-level reconciliation.
- Never merge TISRD children until their base SHA is reconciled to the intended parent.
- Never merge paper-trading logic into a live execution path without a separate risk and owner gate.
- No GitHub Actions use until the owner releases the hold.

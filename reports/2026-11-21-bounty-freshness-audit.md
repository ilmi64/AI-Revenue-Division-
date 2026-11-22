# Paid Coding Opportunity Freshness Audit — 2026-11-21

**Recipient:** AI_REVENUE / Research & Intelligence / Commercial Opportunity Acquisition  
**Status:** READ-ONLY VALIDATION; NO CLAIM-READY TASK FOUND  
**Budget:** CAD $0 incremental  
**Jurisdiction lens:** Ontario, Canada  
**Purpose:** Validate whether surfaced bounty listings represent current, actionable, funded opportunities rather than stale search snippets, closed issues or completed challenges.

## 1. Executive result

A second-pass freshness check rejected two attractive-looking listings as unsuitable for immediate execution:

1. **IssueHunt / Apache Superset #3821 — REJECTED.** IssueHunt's indexed listing showed "Funded" and $17, but the linked GitHub issue is CLOSED, locked and last updated in 2022. It is not an available task.
2. **Algora TSPerf $15,000 challenge — REJECTED.** The official challenge page now shows a winner section and past livestreams. The first-successful-solution condition means the headline prize must not be treated as open or available.

The scan therefore still has **zero verified claim-ready coding bounties**. This is a useful negative result: it prevents time being invested against stale or already-awarded listings.

## 2. Exact false-positive audit

| Candidate | Discovery evidence | Primary-source validation | Decision |
|---|---|---|---|
| IssueHunt: "Allow users to tag dashboards", apache/superset#3821 | IssueHunt issue index surfaced it as funded for $17 with one PR | GitHub API issue record: state CLOSED, locked=true, closed 2022-03-16, last updated 2022-03-16. The old issue body describes a broader folder/grouping request, not a fresh paid task. | REJECT — CLOSED / STALE |
| Algora TSPerf challenge | Search surfaced a $15,000 TypeScript VS Code plugin challenge | Official Algora challenge page says the prize goes to the first successful solution and displays a "Winner" section and livestreams. | REJECT — WINNER SECTION PRESENT; CURRENT AVAILABILITY NOT ESTABLISHED |

## 3. Sources and evidence

- IssueHunt listing: https://oss.issuehunt.io/issues
- Apache Superset issue #3821: https://github.com/apache/superset/issues/3821
- Algora TSPerf challenge: https://algora.io/challenges/tsperf
- Algora payout-country documentation: https://github.com/algora-io/algora/blob/main/priv/content/docs/payments.md
- BOSS earning documentation: https://www.boss.dev/doc/get-started
- GitHub Bug Bounty rules: https://bounty.github.com/rules

The IssueHunt page is dynamically indexed and was not retrievable for a complete live re-check during this audit. The primary GitHub issue record is decisive for #3821. The Algora page is an official source and its winner section is decisive enough to reject the challenge from the active queue unless Algora explicitly republishes/reopens it.

## 4. Revised task acceptance rule

No item enters the execution queue unless all checks pass on the same day as selection:

1. The exact issue/challenge page is open and not locked, closed, completed or marked awarded.
2. The sponsor and exact funded amount/currency are visible in the primary platform or repository record.
3. Funding is real, not a mock-payment balance or unverified bounty request.
4. The issue is not already claimed in a way that excludes another contributor; competing PRs/attempts are inspected.
5. Acceptance criteria, maintainer decision authority, repository activity and licence are clear.
6. AI assistance is permitted under the exact platform, repository and sponsor rules.
7. Ontario/Canada eligibility, payee identity, payment method, minimums, fees, tax/KYC and payout timing are verified.
8. Estimated effort and expected value are defensible; headline reward is not treated as expected income.
9. A scoped owner-approval packet exists before any claim, comment, implementation for an external sponsor or submission.

If any primary-source check fails or is unavailable, status is HOLD/REJECTED rather than inferred open.

## 5. Portfolio impact and next action

- BOSS remains the first platform-level watch candidate because official documentation explicitly lists Canada and describes an individual bank payout route. No exact current funded issue has yet passed the same-day gate.
- Algora remains a platform watchlist because Canada is supported for payouts, but platform coverage is not a funded task.
- IssueHunt remains watch-only; stale indexed listings are not evidence of open work.
- GitHub Bug Bounty remains a specialist lane with strict scope, human validation and no testing authorization.
- Meta remains HOLD until current official terms and portal scope can be reviewed.
- OpenBounty remains excluded while its MVP says mock payments only.

**Immediate acquisition method:** use primary platform feeds and GitHub issue state/PR/timeline evidence; reject stale search-index cards; maintain an exact-task queue with a same-day freshness timestamp. Continue in parallel with AI Revenue's own service/product delivery readiness rather than waiting for bounty income.

## 6. Control record

- No account was created or connected.
- No task was claimed or publicly commented on.
- No code was changed for an external project.
- No tests or scans were run against external systems.
- No customer, maintainer or programme was contacted.
- No spending, submission, contract or payment occurred.
- No bounty, receivable or revenue is claimed.

**Disposition:** READ-ONLY FRESHNESS AUDIT COMPLETE; NO CLAIM-READY TASK FOUND.

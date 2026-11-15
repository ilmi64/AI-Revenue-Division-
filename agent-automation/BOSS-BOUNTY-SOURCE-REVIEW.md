# BOSS Bounty Source Review

## Purpose
Discover public GitHub issues carrying official-looking BOSS bounty markers and preserve the original issue/comment links for manual review. This is not a BOSS API integration and does not establish that a bounty is active, payable, escrowed, or available to a Canadian contributor.

## Current research status
- Official BOSS documentation lists Canada among supported bounty-earner countries and describes individual accounts, identity/personal information, and an international bank account.
- Official pricing documentation describes a 5% + USD $0.60 earning fee and a possible 1% currency-conversion fee.
- Public GitHub issue discussions include reports of broken bounty links, invalid amounts, and a disabled integration. These reports are not proof of a platform-wide outage, but they are sufficient to require current manual confirmation before any work is started.
- A BOSS marker, badge, or bot summary is only a discovery signal. The collector never marks funding or payout as verified.

Official references:
- https://www.boss.dev/
- https://www.boss.dev/doc/
- https://www.boss.dev/doc/get-started
- https://www.boss.dev/doc/pricing
- https://github.com/marketplace/boss-bounty

## Collector behavior
- Uses only GitHub's public issue-search and issue-comment API endpoints.
- Searches for BOSS issue links and badge markers in open public issues.
- Reads a bounded number of public issue comments to detect BOSS bot summaries, prior claim/champion activity, and explicit warning language.
- Writes unverified leads to `division-inputs/github_bounties.json`.
- Writes source health and warning counts to `external-source-output/boss-source-report.json`.
- No BOSS private API, account login, scraping, browser automation, account credentials, payment details, or paywalled data.

## Mandatory owner review
Before treating any BOSS lead as worth engineering effort, manually verify:
1. The BOSS issue page opens and displays a current bounty.
2. The bounty is still active and the platform currently supports payout for Canadian residents.
3. The account setup, identity/tax requirements, and Canadian bank payout route are available to the owner.
4. The issue is genuinely open, scoped, unclaimed, and has no competing PR likely to close it.
5. The sponsor and maintainer are credible and acceptance criteria are specific.
6. Fees, currency conversion, dispute rules, and payout timing are acceptable.

## Safety
No claims, champion comments, issue comments, applications, code submissions, PRs to third-party repositories, sponsor contact, account creation, bank connection, or financial actions are performed. A warning signal forces `review_required`; it does not prove fraud or a platform-wide outage.

# Multi-Lane Revenue Source Registry

## Purpose
This registry connects the organisation's nine supported revenue lanes to a review-only directory of potential sources and existing discovery connectors. It gives Executive Management a clear view of lane coverage, unconnected platforms and research gaps.

## Current coverage
- **AI development and automation services:** Upwork, Contra and gend.me Web Developer (verify wallet cash-out; platform tokens are not cash).
- **Freelance technical services:** Upwork, Contra and gend.me Web Developer.
- **AI evaluation and data annotation:** YPAI, CrowdGen by Appen, Outlier and Alignerr. YPAI advertises Canada-specific contributor roles and rates, but selection, available tasks, accepted hours and actual payout remain unverified. CrowdGen project allocation and payout access vary by country and project.
- **Digital products:** Gumroad candidate source.
- **Grants and sponsorships:** Government of Canada Business Benefits Finder, NRC IRAP and GitHub Sponsors. GitHub Sponsors is a longer-term route requiring qualifying contribution history and payout onboarding; it is not a quick-task source.
- **Security testing:** HackerOne and Bugcrowd researcher programs.
- **Research tasks:** intentionally left as a research gap until a standalone source's Canadian access, genuine task supply and payout terms can be verified.
- **GitHub bounties:** existing public issue discovery plus BOSS and Algora candidates. BOSS markers and Algora listings are not proof of current funding or payment.
- **Remote employment:** existing public job feeds and employer ATS connectors.

## Newly reviewed candidates and limitations
- **YPAI:** Canada-specific freelance contributor openings were advertised for model evaluation, annotation and data collection. Published rates are not guaranteed earnings; the contributor must personally qualify and complete work. Verify the exact opening, selection, project supply, approval process, payout method, minimums, fees and timing.
- **CrowdGen by Appen:** AI data collection, annotation and evaluation. Project allocation, location eligibility, mobile verification and payment methods vary. Official payment information describes monthly processing, generally by the 14th of the following month; confirm the user's specific payout route.
- **gend.me:** Ontario-based developer-work candidate. Advertised CAD developer credits and AI Builder Tokens are conditional on customer approval. Tokens are not cash; wallet withdrawal terms remain unverified.
- **BOSS:** Canada is listed in official individual-earner documentation, but every bounty must be verified individually. A marker, badge, bot summary or public issue is not evidence of a live funded reward. Published fees must be checked again before accepting work.
- **Algora:** verify-first only. Current bounty availability, Canadian eligibility, sponsor funding, fees and payout route were not conclusively established.
- **GitHub Sponsors:** Canada is a supported receiving region, but eligibility, contribution-history, tax, banking and two-factor requirements apply. Sponsorship is uncertain and long-term.
- **BountyOS:** excluded. The reviewed current product is a creator/product-placement platform built around TikTok and Instagram, not a software bounty marketplace. TikTok remains excluded from the organisation's content plan unless the owner reopens that decision.

## Connection state
The registry is not an account integration. Platforms marked `not_connected` are research candidates only. Manual research entries are not connected accounts. Existing connectors are read-only. No credentials, cookies, platform accounts or payment accounts are used by the registry.

The validator writes:
- `executive-output/revenue-lane-coverage.json`
- `executive-output/revenue-lane-coverage.md`

The executive reporting agent consumes the JSON coverage artifact when it is available.

## Canada and zero-cost controls
- Canada listed by a platform does not mean every project accepts Ontario residents.
- Review identity checks, tax forms, payout method, minimum withdrawal, fees, task availability and dispute terms before any commitment.
- A free profile or zero monthly plan does not mean every application or transaction is free.
- No paid Connects, subscriptions, training, deposits, equipment or verification charges without separate approval.
- Grants are conditional project support and often require a qualifying organisation, eligible project costs and reporting. NRC IRAP's minimum criteria include an incorporated, for-profit Canadian business with up to 500 FTE developing an innovative technology-driven product or service.
- Security testing is permitted only against assets and test types explicitly authorized by a current program scope.
- Advertised rates, reward ceilings, listings, platform credits/tokens and source counts are not income.
- Record earned revenue separately from cash actually received. Never treat a discovery lead or accepted-but-unpaid task as cash.

## Approval gates
No automated applications, claims, client contact, security testing, submissions, public launches, purchases, invoices, payments, trading or other consequential external actions are enabled. Owner approval remains mandatory for each such action.

Run locally:
```bash
cd agent-automation
PYTHONPATH=. python -m unittest test_validate_revenue_lane_registry.py -v
cd ..
PYTHONPATH=agent-automation python agent-automation/validate_revenue_lane_registry.py
```

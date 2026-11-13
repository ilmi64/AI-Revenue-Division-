# Multi-Lane Revenue Source Registry

## Purpose
This registry connects the organisation's nine supported revenue lanes to a review-only directory of potential sources and existing discovery connectors. It gives Executive Management a clear view of lane coverage, unconnected platforms and research gaps.

## Current coverage
- **AI development and automation services:** Upwork and Contra candidate sources.
- **Freelance technical services:** Upwork and Contra candidate sources.
- **AI evaluation:** Outlier and Alignerr candidate sources.
- **Digital products:** Gumroad candidate source.
- **Grants and sponsorships:** Government of Canada Business Benefits Finder and NRC IRAP information.
- **Security testing:** HackerOne and Bugcrowd researcher programs.
- **Research tasks:** intentionally left as a research gap until a source's Canadian access, task supply and payout terms can be verified.
- **GitHub bounties:** existing public issue discovery connector; ordinary issues are not presumed paid.
- **Remote employment:** existing public job feeds and employer ATS connectors.

## Connection state
The registry is not an account integration. Platforms marked `not_connected` are research candidates only. Existing connectors are read-only. No credentials, cookies, platform accounts or payment accounts are used by the registry.

The validator writes:
- `executive-output/revenue-lane-coverage.json`
- `executive-output/revenue-lane-coverage.md`

The executive reporting agent consumes the JSON coverage artifact when it is available.

## Canada and zero-cost controls
- Canada listed by a platform does not mean every project accepts Ontario residents.
- Review identity checks, tax forms, payout method, minimum withdrawal, fees, task availability and dispute terms before any commitment.
- A free profile or zero monthly plan does not mean every application or transaction is free.
- Grants are conditional project support and often require a qualifying organisation, eligible project costs and reporting. NRC IRAP's minimum criteria include an incorporated, for-profit Canadian business with up to 500 FTE developing an innovative technology-driven product or service.
- Security testing is permitted only against assets and test types explicitly authorized by a current program scope.
- Advertised rates, reward ceilings, listings and source counts are not income.

## Approval gates
No automated applications, claims, client contact, security testing, submissions, public launches, purchases, invoices, payments, trading or other consequential external actions are enabled. Owner approval remains mandatory for each such action.

Run locally:
```bash
cd agent-automation
PYTHONPATH=. python -m unittest test_validate_revenue_lane_registry.py -v
cd ..
PYTHONPATH=agent-automation python agent-automation/validate_revenue_lane_registry.py
```

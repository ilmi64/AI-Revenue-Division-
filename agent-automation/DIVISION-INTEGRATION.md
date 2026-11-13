# Revenue Division Integration Contract

## Shared intake
The Revenue Intelligence pipeline now has a common HTTPS-only intake contract. Each division can provide a JSON feed at `division-inputs/<lane>.json`. Records must include `title`, `url`, `source_name`, and the matching `lane`.

Supported lanes:
- `ai_development`: AI agents, workflow automation and integration services
- `freelance_services`: software development, debugging, APIs, testing and documentation
- `ai_evaluation`: AI training, evaluation and data annotation
- `digital_products`: reusable software, templates and digital products
- `grants_sponsorships`: grants and open-source sponsorships
- `security_testing`: authorized security testing and responsible disclosure
- `research_tasks`: paid technical research and research tasks
- `github_bounties`: public GitHub issue/bounty discovery
- `remote_employment`: remote employment listings from public job feeds

## Current connection state
GitHub public issue search is the only live external discovery source in this pipeline. Other divisions are connected through a documented, testable feed interface; they are not yet connected to external platform accounts or APIs. An empty feed is not evidence that a lane has no opportunities.

## Downstream handling
The unified lead file is `opportunity-output/all-opportunities.json`. Development triage, structural risk review and finance due diligence consume this shared file. All entries remain unverified until a human checks the original terms and eligibility.

## Required controls
- HTTPS sources only; no credentials or secrets in feed files.
- No automated account login, scraping behind access controls, application, claim, contact, submission, publishing, invoicing, payment or trade.
- Verify platform terms, Canadian eligibility, fees, KYC, payout minimums and tax implications before acting.
- Do not treat advertised amounts or discovery counts as revenue.
- Keep each division's data provenance and source URL.

## Feed example
```json
[
  {
    "title": "Example automation contract",
    "url": "https://example.com/opportunity/123",
    "source_name": "Example platform",
    "lane": "ai_development",
    "summary": "Optional short source-derived description"
  }
]
```
This is a schema example only, not a real opportunity.

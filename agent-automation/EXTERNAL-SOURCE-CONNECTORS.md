# External Opportunity Source Connectors

## Live read-only connectors
The external source agent queries three public feeds without API keys, login, cookies or browser automation:
- Jobicy: `https://jobicy.com/api/v2/remote-jobs?count=100`
- Remote OK: `https://remoteok.com/api`
- Himalayas: `https://himalayas.app/jobs/api?limit=100`

It retains the original listing URL, source name, company, location text and a short excerpt. Jobicy's live API response requests clear credit and requires application links to point to the original URL. Remote OK's API response requires a followed link to the original listing and explicit mention of Remote OK. Himalayas listings are linked to the original application/listing page.

## Important limitations
- These are remote-employment feeds, not a complete freelance, bounty or AI-task marketplace.
- Location text is a hint only. A country restriction mentioning Canada or worldwide is not a guarantee of eligibility; full terms must be checked.
- No salary, bounty, currency, payment terms, Canadian eligibility, tax status or payout is treated as verified.
- The collector filters for technical, AI, automation, evaluation, research, security and contract-related language. Keyword matches are not suitability assessments.
- Listings can expire, be duplicated, be location-restricted or be inaccurate. Always follow the original source.
- Provider terms can change. Recheck terms before any public redistribution; this implementation is an internal research feed and does not publish a job board.

## Workflow
The collector writes lane-specific JSON files under `division-inputs/` and a source-health summary under `external-source-output/`. The existing division intake normalizes these alongside GitHub discovery, then downstream triage, risk, finance and executive agents run.

## Invocation
```bash
python agent-automation/external_opportunity_sources.py
```

No applications, claims, contacts, submissions, invoices, payments or account changes are performed.

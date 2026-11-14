# Employer ATS Job Board Connectors

This module adds read-only public job-board feeds for Greenhouse, Lever and Ashby. It uses Python's standard library and makes HTTPS GET requests only. No credentials, cookies, browser automation, private APIs, applications or account actions are used.

## Configuration

Copy `ats-boards.example.json` to `ats-boards.json` and replace the example values with employer board identifiers obtained from the employer's own careers page. Do not commit private information; this configuration contains only public board names. The runtime defaults to an empty board list when `ats-boards.json` is absent. No employers are preselected or represented as connected.

- Greenhouse: `https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true`
- Lever: `https://api.lever.co/v0/postings/{board}?mode=json`; set `region` to `eu` for EU-hosted boards, otherwise `global`.
- Ashby: `https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true`

The official Greenhouse documentation says public GET job-board data requires no authentication and distinguishes it from the authenticated application-submission endpoint. Lever documents published postings as public and its API supports global and EU instances. Ashby documents its public GET endpoint and published-job fields.

## Data and safeguards

The connector preserves the original job URL and application URL, employer, location, department, employment type, workplace type, publication date and source attribution when supplied. It filters for relevant technical/AI/automation/evaluation/research/security/contract language and maps results into the existing division lanes.

A Canada/worldwide location string is only an eligibility hint. No listing is treated as Canadian-eligible, paid, funded, available, or suitable without human verification. Compensation is not converted into revenue. Listings are deduplicated by original URL. Requests are sequential with a one-second pause between configured boards.

The connector writes lane JSON into `division-inputs/` and board health to `external-source-output/ats-source-report.json`. The shared intake carries the application URL and employer metadata downstream. No automatic applications, claims, contacts, submissions, invoices, payments, publication or trading occur.

## Run

```bash
PYTHONPATH=agent-automation python agent-automation/ats_job_board_sources.py
PYTHONPATH=agent-automation python -m unittest discover -s agent-automation -p 'test_ats_job_board_sources.py' -v
```

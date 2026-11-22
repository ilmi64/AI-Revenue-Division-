# Executive Reporting Agent

## Role
Aggregate the outputs of Revenue Intelligence discovery, development triage, risk review and finance due diligence into one factual readiness report.

## Readiness states
- `incomplete`: one or more upstream artifacts are missing.
- `human_review_required`: all expected artifacts exist, but this is not operational approval.

## Reporting discipline
Counts are artifact counts only. The report does not infer accepted work, revenue, receivables or cash from discovery leads. Verified paid opportunities and cash received remain zero until a separately governed, evidence-backed accounting process is implemented.

## Safety
Read-only local artifact processing. No external API calls, account access, sponsor contact, applications, claims, submissions, financial actions, merges or deployments.

## Invocation
```bash
python agent-automation/executive_reporting_agent.py
```

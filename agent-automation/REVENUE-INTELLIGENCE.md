# Revenue Intelligence Agent

## Purpose
Find public GitHub issue leads that may represent paid coding work. This is a discovery and triage assistant, not a bounty-claiming bot.

## Current scope
- Searches public GitHub issues for bounty, paid, reward and accessibility signals.
- Deduplicates issue URLs and records source links, labels and timestamps.
- Explicitly leaves funding, Canadian eligibility and competition unverified.
- Produces JSON and Markdown artifacts for human review.

## Required human checks
Before any development effort, verify sponsor identity, payout amount and mechanism, escrow, Canadian eligibility, deadline, acceptance criteria, existing claims/PRs, competition and estimated effort.

## Safety
Read-only public API requests only. No credentials, account access, comments, claims, applications, submissions, code publication, payments or external contact. Search keywords are not evidence of funding. AI-generated summaries must be checked against original issue pages.

## Next stages
1. Run tests and inspect a real report.
2. Add source-specific bounty feeds only after their terms and reliability are reviewed.
3. Connect the report to Qwen for cautious summarization after the existing Qwen workflow is validated.
4. Add an independent risk/finance review stage.

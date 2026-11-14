# Development Task Agent

## Role
Turn Revenue Intelligence discovery records into small, reviewable engineering triage briefs. This agent does not autonomously solve, claim, or submit bounty work.

## Inputs and outputs
- Input: `opportunity-output/github-opportunities.json`
- Outputs: `development-output/engineering-triage.json` and `engineering-triage.md`
- Prioritisation is a transparent keyword heuristic, not a model-generated estimate.

## Human verification
Read the full source issue and comments. Verify funding, sponsor, payout/escrow, Canadian eligibility, deadline, acceptance criteria, competition, technical scope and effort. The agent deliberately marks scope, effort and acceptance criteria as unverified.

## Safety boundary
No issue comments, claims, assignments, sponsor contact, applications, code publication, pull requests, payments or account actions. Do not treat a high triage score as evidence that an opportunity is funded or suitable.

## Invocation
```bash
python agent-automation/development_task_agent.py --input opportunity-output/github-opportunities.json
```

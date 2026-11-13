# Risk Review Agent

## Role
Apply deterministic structural safety checks to engineering triage briefs before a human considers an opportunity.

## Checks
- Source must be a GitHub URL.
- Scope, effort and acceptance criteria must remain explicitly unverified.
- The prohibited-action boundary must be present.
- Heuristic score must remain within its documented 0-5 range.

## Limits
This does not verify sponsor identity, whether a bounty is funded, Canadian eligibility, escrow, payout reliability, technical correctness or legal terms. A passed structure check is not an approval to work or submit.

## Invocation
```bash
python agent-automation/risk_review_agent.py --input development-output/engineering-triage.json
```

All records remain subject to human review. The agent cannot claim, comment, assign, contact, apply, submit, publish, merge, deploy or spend.

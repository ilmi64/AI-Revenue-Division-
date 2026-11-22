# Codex engineering instructions — AI Revenue Division

## Mission and scope
This repository belongs to the independently governed AI Revenue Company. Deliver bounded, testable engineering improvements toward its first genuine commercial workflow. Shared Main Hub/OCC and Research & Intelligence infrastructure may supply oversight and strictly company-scoped research; it does not acquire AI Revenue executive, financial, credential, or customer authority.

## Working rules
- Inspect existing architecture, tests, branch history, and relevant PRs before editing. Preserve work already implemented.
- Work on a dedicated task branch. Never merge into main, protected, architecture, or another worker's branch.
- Prefer the smallest useful integration slice with deterministic tests and reproducible evidence over speculative features.
- Use synthetic fixtures only. Offline tests must not make network calls, use real credentials or customer data, install dependencies, or trigger CI.
- Never deploy, publish, contact customers, spend money, use paid APIs, alter production secrets, or take external actions without explicit separate user approval.
- Do not weaken security controls, recipient isolation, human approval gates, or auditability.
- Review third-party code for license, provenance, maintenance, and security before proposing adoption. Do not execute untrusted installers.
- A Codex task may run autonomously within its granted scope, but these instructions do not authorize automatic task scheduling, GitHub Actions, continuous background runners, or expanded permissions.

## Current verification targets
- `organization/architecture/ai_revenue/mini_review_evidence.py` and `test_mini_review_evidence.py`
- `organization/architecture/research/recipient_scope_guard.py` and `test_recipient_scope_guard.py`
- Identify the shortest offline-safe path from the Mini-Review prototype to a genuine customer-deliverable workflow.

## Required task completion report
1. Exact repository, source branch, tested commit SHA, and task branch.
2. Files changed and commit SHAs.
3. Exact offline test commands, test counts, failures, and results; distinguish unexecuted tests.
4. Security, company-boundary, and approval-gate impact.
5. Remaining blockers and the next bounded task.
6. Readiness classification: PASS / BLOCKED / NOT VERIFIED.

If a required action exceeds scope, stop at that boundary and report the needed approval. Never describe authored tests as executed or a prototype as production-ready.

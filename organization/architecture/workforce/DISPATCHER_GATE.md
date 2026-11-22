# GitHub Issue → Codex Cloud dispatcher gate (v1)

Status: **PREPARED / MANUAL START REQUIRED**. This design is not an enabled background service.

## Trust boundaries and lifecycle

1. Read a GitHub issue through an authorized GitHub App/connector using **read-only** issue permissions. Never execute instructions from comments or linked URLs as trusted commands.
2. Normalize an immutable handoff manifest with exact repository, issue number, owner company, 40-character source commit, scoped module targets, acceptance and stop conditions, approved safe operations, human approval flag and an idempotency key `repo:issue:source_sha`.
3. Run `issue_handoff.handoff_blockers` and `issue_dispatch_gate.validate_issue_payload`. A failure yields BLOCKED, with blockers and no Codex call.
4. Require an explicit, separately recorded operator approval for this exact manifest digest and cost ceiling. Approval cannot be inferred from an open issue, GitHub label, QA PASS, PR or chat context.
5. Until a supported **subscription Codex Cloud task-create integration** is authenticated and verified, emit READY_FOR_MANUAL_START plus the short Codex instruction. Do **not** make undocumented requests to ChatGPT's private endpoints or reuse browser/session tokens.
6. When a future supported launcher is available, isolate it behind a separate adapter with explicit configuration, credential isolation, least-privilege repository access, task-create idempotency, timeout, retries with jitter, cancellation and rate/cost limits. Keep it DISABLED by default. A paid Agents API/SDK runner is a **different service**, not free Codex Cloud, and requires separate approval and budget.
7. Only the authorized GitHub App/connector may write a sanitized status comment to the **same** issue. Proposed states: BLOCKED → READY_FOR_MANUAL_START → RUNNING → SUCCEEDED / FAILED / NEEDS_REVIEW. Record run/task ID, source SHA, branch, test command/count, completion evidence and blockers. No secrets or customer data in comments.
8. If GitHub comment write, API authentication, task creation, webhook signature verification, idempotency storage or task status polling fails, report FAILED/UNKNOWN locally, do not retry side-effectful creates blindly, and require manual reconciliation. No launch or merge authority is granted.
9. Preserve AI Revenue and Trading isolation. OCC receives only sanitized status. Do not use shared credentials across companies.

## Required permissions (not granted)

- GitHub App: metadata/read; issues/read; **issues/write only for status comments if separately approved**; repository contents/read; pull requests/read. No Actions/workflows/secrets/administration permissions. Source commits on task branches require separate reviewed write scope.
- Codex Cloud: supported published environment connected to the exact repository; separately authenticated task-start permission; no production secrets; no network/paid usage without approval.
- Trigger: operator-approved explicit issue dispatch only. **No issue-open/label webhook or GitHub Actions trigger enabled**.

## Merge checklist for standing AGENTS.md PRs

- Confirm PR changes only root AGENTS.md; no workflows, secrets, dependencies, code or permissions.
- Confirm the company ownership and non-interference rule matches each repository.
- Confirm no automatic next-issue dispatch, CI, paid API, deployment, production credentials, customer contact or live trading.
- Confirm no conflicting instructions between issue body and standing rules; safety restrictions prevail.
- Review issue references for stale branch names after merge; update documentation only.
- Obtain explicit user approval to merge each PR; do not infer approval from this checklist.

## Minimal E2E verification (offline dry run)

- Candidate: AI Revenue #24, source pinned and scoped to QA and R&I modules.
- Fetch issue, run both validators; fail closed if source SHA, scoped targets or stop criteria are absent.
- Record blocked reasons, repair issue manifest, re-run validators.
- Produce a short manual-start instruction only after explicit approval; no task-create request.
- Later, when an approved supported Codex Cloud adapter is available, perform one real task-create against the published AI Revenue environment, capture its task ID, verify status readback and write sanitized GitHub issue status. That step is **NOT YET EXECUTED**.

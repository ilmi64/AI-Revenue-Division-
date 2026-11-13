# Implementation Roadmap

## Phase 0 — Foundation
- [x] Create a separate implementation branch.
- [x] Define division-wide agent roles and reporting lines.
- [x] Define budget, security and approval gates.
- [ ] Review and merge the draft PR only after owner approval.

## Phase 1 — First local AI pilot
- [x] Add a read-only public release Research Radar collector.
- [x] Add unit tests for report rendering and missing-release handling.
- [x] Add a local Ollama client for AI-assisted research summaries.
- [x] Select Qwen2.5 1.5B as a small Apache-2.0 model candidate.
- [x] Add a weekly/manual GitHub Actions workflow using an ephemeral public runner.
- [x] Keep permissions read-only; no secrets, account connections, or external write actions.
- [ ] Merge only after owner review.
- [ ] Run the first workflow and inspect the artifact, duration, resource use, and AI output quality.
- [ ] Fix any install, model-pull, runtime, or test failures before considering the pilot operational.

## Phase 2 — Existing services and platform feasibility
- [x] Inspect the existing Printify Store Analyst: on-demand trigger, AI COO analyst, five read-only Printify tools, healthy Printify connection, no incomplete executions. Preserve it unchanged.
- [ ] Inventory all Make scenarios, connections, schedules and execution health.
- [ ] Review GitHub Actions usage and repository settings.
- [ ] Evaluate Activepieces Community Edition for persistent multi-step workflows.
- [ ] Evaluate Dify Community Edition for knowledge retrieval and agent applications.
- [ ] Confirm current license terms and exact intended business use.
- [ ] Identify an always-on host with adequate CPU, RAM, storage and backups, at CAD $0.
- [ ] Identify any additional model/runtime costs; do not assume a free trial is cost-free.
- [ ] Complete security review before connecting any real account.

## Phase 3 — Controlled expansion
- [ ] Validate the first AI pilot's accuracy, prompt-injection resistance, repeatability and failure handling.
- [ ] Add source citations, run logs, rate limits and a manual stop switch.
- [ ] Create division-specific agents one at a time, beginning with read-only research, risk and reporting.
- [ ] Keep external write actions disabled unless separately approved.
- [ ] Obtain owner review before connecting another division.

## Phase 4 — Organisation-wide readiness
- [ ] Verify every agent's permissions, owner, dependencies, failure behavior and reporting route.
- [ ] Run an organisation-wide readiness review before any operational launch.
- [ ] Keep all consequential actions behind explicit owner approval.

## Current blockers
1. The AI workflow is committed only to the feature branch; it has not yet run in GitHub Actions.
2. Model quality and CPU execution time are unverified until the first run.
3. The temporary runner is not a persistent automation server; Activepieces/Dify need a separately approved always-on host.
4. The existing Make Printify Store Analyst must remain unchanged.

## Definition of done
The division is not considered operational merely because its code or design exists. It must pass a real workflow run, produce a reviewed artifact, demonstrate acceptable accuracy and failure handling, and remain within CAD $0 incremental cost.

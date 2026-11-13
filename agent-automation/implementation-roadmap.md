# Implementation Roadmap

## Phase 0 — Foundation (started)
- [x] Create a separate implementation branch.
- [x] Define division-wide agent roles and reporting lines.
- [x] Define budget, security and approval gates.
- [ ] Review this architecture and merge only after owner approval.

## Phase 1 — Use existing services first
- [ ] Inventory existing Make scenarios, connections, schedules and execution health.
- [ ] Keep the existing Printify Store Analyst intact; document its inputs, outputs, permissions and current AI module behavior.
- [ ] Review the existing GitHub Actions workflow and free-minute usage.
- [ ] Build a read-only research/reporting workflow using only confirmed free capabilities.
- [ ] Test with synthetic or public data; keep all new scenarios inactive until reviewed.

## Phase 2 — Agent platform feasibility
Evaluate Activepieces Community Edition first, then Dify Community Edition:
- [ ] Confirm current license terms for the exact intended internal/business use.
- [ ] Identify an always-on host with adequate CPU, RAM, storage and backups.
- [ ] Confirm hosting has no incremental cost and does not violate provider terms.
- [ ] Identify a model that can be used at CAD $0, including rate limits, data handling and commercial-use terms.
- [ ] Test local-model inference or a genuinely free hosted model without entering payment details.
- [ ] Verify mobile browser access for administration; do not assume the Android phone/tablet can host production services.
- [ ] Complete security review before connecting any real account.

**Go/no-go rule:** if hosting or model inference requires payment, stop and continue with existing Make/GitHub capabilities. Do not create a trial that requires a card or activates billable usage.

## Phase 3 — Controlled pilot
- [ ] Deploy only after Phase 2 passes.
- [ ] Create one read-only Research & Reporting Agent.
- [ ] Add source citations, run logs, rate limits and a manual stop switch.
- [ ] Test prompt injection, malformed inputs, unavailable services, duplicate events and incorrect outputs.
- [ ] Keep external write actions disabled.
- [ ] Obtain owner review before connecting another division.

## Phase 4 — Organisation-wide readiness
- [ ] Add agents one division at a time according to the charters.
- [ ] Verify every agent's permissions, owner, dependencies, failure behavior and reporting route.
- [ ] Run an organisation-wide readiness review before any operational launch.
- [ ] Keep all consequential actions behind explicit owner approval.

## Current blockers
1. No confirmed zero-cost always-on host is identified.
2. No zero-cost model inference provider has been approved.
3. Make private workspace has no scenarios; the standard team has an existing Printify Store Analyst scenario that must be preserved.
4. No new external account connection or deployment has been authorized.

## Definition of done
The division is not considered operational merely because its code or design exists. It must be deployed on an approved runtime, pass documented tests, have verified permissions and failure handling, and produce a successful test report without incurring cost.

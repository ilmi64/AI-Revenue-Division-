# Decision & Agreement Register

**Purpose:** Append-only record of confirmed owner agreements and material governance decisions. This register is mirrored in the AI Revenue and Trading & Technology repositories. Company-specific decisions remain in the relevant company's own register; shared decisions are mirrored without merging company authority.

## Recording rule

Every explicit owner agreement is recorded here during the same work session where practical. Each entry preserves:
- Decision ID and date (UTC)
- Scope: shared, AI Revenue, Trading & Technology, or a named division
- Decision and rationale
- Status: **AGREED**, **PROPOSED**, **PENDING VERIFICATION**, **APPROVED FOR EXECUTION**, **ON HOLD**, or **REJECTED**
- Dependencies, cost implications, risks, and approval gates
- Source discussion/context and links to affected architecture documents
- Supersession history; prior decisions are not silently overwritten

An agreement to research or prepare is not permission to install, activate, connect, spend, publish, merge, deploy, trade, move funds, contact customers, or take another consequential external action. Those actions retain their separate explicit approval gates.

## DR-2026-11-21-001 — Shared cloud-compute and workstation strategy

- **Date:** 2026-11-21
- **Scope:** Shared infrastructure serving AI Revenue and Trading & Technology
- **Status:** **AGREED — strategy; individual services remain subject to verification**
- **Decision:**
  1. GitHub Codespaces is the current, free-first development environment for coding and repository-centred work, subject to actual account allowance, quotas, and no-cost limits.
  2. Zo Computer is the planned future persistent cloud workstation for shared infrastructure and desktop-dependent workflows. It is not deployed, activated, or approved for paid use.
  3. Cloudroom is an investigation candidate; its advertised 3,000 monthly cloud credits, eligibility, expiry, runtime limits, persistence, and billing/overage conditions must be independently verified.
  4. E2B is an investigation candidate for bounded agent sandboxes; any free allowance, usage limits, and billing safeguards must be verified before use.
  5. Rig is a candidate software layer but depends on E2B compute; it is not considered free merely because its software is open source.
  6. PequeRoku is a free/open-source cloud-lab candidate that requires an independently available computer or server; it does not itself provide free persistent compute.
- **Rationale:** Use existing/free development capacity now, preserve a path to persistent cloud compute later, and avoid paid infrastructure before revenue or a separate explicit owner decision.
- **Architecture requirements:** Portable deployment; Android-accessible administration where supported; company-scoped identities, credentials, data, memory, queues, permissions, budgets and audit trails; no cross-company secret or authority sharing; deterministic policy enforcement outside model prompts; fail-closed behavior.
- **Cost and safety constraints:** CAD $0 incremental spend by default. No paid subscriptions, upgrades, paid API usage, payment-backed trials, automatic renewals, overages, deposits, borrowing, or leverage. Do not activate a service that risks billing without explicit approval.
- **Non-authorization:** This agreement does not authorize account creation, trial activation, installation, compute execution, API calls, production connections, repository permission changes, deployments, tests, or any external side effect. Existing approval gates remain in force.
- **Dependencies / next work:** Verify current free allowances and billing controls from official provider documentation; compare persistence, runtime/OS, CPU/RAM/storage, session limits, secrets handling, network access, region/data handling, Android access, and portability. Then prepare a no-cost hosting decision matrix and a synthetic, read-only pilot plan. No pilot execution without explicit approval.
- **Related architecture:** Shared AI workforce architecture; workforce platform current technical assessment; shared infrastructure tenancy and failover; Main Hub/OCC governance and security architecture.
- **Supersession:** This is the current agreed shortlist and ordering. Update by appending a new decision entry; do not erase this historical record.

## DR-2026-11-21-002 — Mandatory logging of owner agreements

- **Date:** 2026-11-21
- **Scope:** Both companies and shared organisation-level divisions
- **Status:** **AGREED**
- **Decision:** Every explicit owner agreement, material change, approval, rejection, hold, and superseding decision must be recorded in the appropriate GitHub decision register. Shared decisions are mirrored in both company repositories. Company-specific decisions are recorded in the affected company's register. Chat memory is supplementary and is not a substitute for the durable repository record.
- **Required discipline:** Preserve exact scope and status; distinguish agreement to research/prepare from authorization to execute; record approvals separately from proposals; verify every repository write; never silently convert a proposal into an approval.
- **Rationale:** Maintain continuity across conversations, prevent repeated questions, preserve accountability, and reduce contradictory or lost decisions.
- **Operating constraint:** Repository documentation updates do not authorize merges, workflow runs, tests, installations, deployments, spending, publishing, financial transactions, or other consequential actions.

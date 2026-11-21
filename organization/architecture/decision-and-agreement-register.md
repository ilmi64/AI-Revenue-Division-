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


## Research evidence update — 2026-11-21 (not a new execution approval)

This evidence snapshot supplements DR-2026-11-21-001. It does not change the agreed strategy or authorize account creation, activation, installation, compute use, or spending.

### GitHub Codespaces
- Official GitHub documentation states personal Free accounts include 120 core-hours and 15 GB-month of storage; Pro includes 180 core-hours and 20 GB-month.
- Core-hours are multiplied by machine size. A 2-core codespace consumes 2 core-hours per running hour, so 120 core-hours equates to up to 60 hours on a 2-core machine, before other storage/usage constraints.
- If the included quota is exhausted and no payment method is configured, chargeable usage is blocked. Free quotas are for personal accounts; organisation/enterprise plans do not include the same free quota by default.
- Source: https://docs.github.com/en/billing/concepts/product-billing/github-codespaces
- Source: https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage
- Assessment: **PREFERRED CURRENT DEVELOPMENT ENVIRONMENT**, subject to confirming the user's actual account quota and ensuring no payment method/paid overage is enabled.

### Cloudroom
- Cloudroom documentation currently describes a Free plan with 3,000 Cloud Credits every 30 days; typical agent work is estimated at approximately 100 credits/hour, light work around 20/hour, and heavy work 500+/hour.
- Cloud credits are consumed while agents actively work in cloud sandboxes; idle/waiting/sleeping time is normally zero. GPU sessions consume credits and are separately approved.
- The documentation says free-plan cloud threads that are unused are deleted after 7 days. This is not equivalent to a persistent always-on workstation.
- A separate pricing page currently labels Free as “SOON” and lists different prospective limits (100 cloud agents/30 days and 25 compute hours). The product pages therefore contain a material availability/entitlement discrepancy.
- Sources: https://www.cloudroom.dev/docs/cloud-credits
- Source: https://www.cloudroom.dev/docs/faq
- Source: https://www.cloudroom.dev/pricing
- Source: https://www.cloudroom.dev/terms
- Assessment: **INVESTIGATE ONLY / PENDING VERIFICATION**. Do not rely on the free tier until the actual account entitlement, current plan limits, session persistence, deletion policy, overage/top-up behavior, and no-payment setup are confirmed. No account creation or activation authorized.

### E2B
- Current public pricing describes a Hobby tier with a one-time US$100 usage credit, sessions up to one hour, and no recurring monthly credit grant. Paid usage is metered; Pro is advertised at US$150/month plus usage costs.
- The E2B site notes that some accounts may be asked for a one-time US$5 card payment for abuse prevention; the amount is added as non-refundable usage credit.
- Public pages differ on concurrency counts (10 versus 20), so the exact current account limit requires verification.
- Sources: https://e2b.dev/pricing
- Source: https://e2b.dev/
- Assessment: **OPTIONAL SHORT-LIVED SANDBOX CANDIDATE ONLY**. Not a persistent workstation. Do not proceed if card verification, payment details, paid usage, or billing exposure is required. One-time credits are not treated as recurring free capacity.

### PequeRoku
- The project describes itself as MIT-licensed and self-hosted, providing Linux VMs through QEMU/KVM and an MCP/API interface. Its documented setup requires Docker Compose and a Linux host; hardware with /dev/kvm is recommended for fast VMs.
- The project explicitly runs on the user's own hardware; it does not supply hosted compute. Its website describes phone/tablet browser access to a running installation, which is not proof that an Android device can host the service itself.
- Source: https://pequeroku.net/
- Assessment: **SELF-HOSTED SOFTWARE CANDIDATE**, dependent on separate suitable hardware/host. Not a standalone free cloud computer.

### Remaining verification items
- Rig's exact current identity, license, supported E2B integration, and cost boundary remain unverified in this evidence pass; retain as a candidate only.
- Zo Computer remains the agreed future persistent workstation candidate; its earlier reviewed pricing/trial terms remain subject to the no-spending rule and were not reactivated or reapproved.
- OpenHands remains a bounded engineering-agent candidate, not a cloud-hosting provider.
- No service has been installed, activated, connected, or tested. No account status, free entitlement, uptime, persistence, or production suitability is claimed as verified for the user's own accounts.


### Additional previously discussed compute and cloud-desktop candidates — recovered and classified

#### Google Colab
- Officially a hosted Jupyter notebook service with free access to compute, including GPUs/TPUs when available. Google states free-tier limits are dynamic and not guaranteed; maximum runtime can be up to 12 hours depending on availability and usage, with idle timeouts and GPU restrictions.
- Suitable for notebook-based research, data analysis, and bounded experiments; **not a persistent always-on workstation or general-purpose production host**.
- Sources: https://research.google.com/colaboratory/faq.html
- Status: **FREE RESEARCH/NOTEBOOK CANDIDATE**, no activation or compute execution authorized.

#### Kaggle Notebooks
- Official notebook documentation describes remote CPU/GPU/TPU environments, free accelerators subject to availability/queues, and session limits. Published technical details include up to 12 hours for CPU/GPU sessions, 9 hours for TPU sessions, and a 20 GB autosaved working disk; GPU quota is subject to weekly limits and change.
- Suitable for bounded research, data science and ML experiments; **not a persistent workstation or dependable always-on agent host**.
- Sources: https://www.kaggle.com/docs/notebooks
- Source: https://www.kaggle.com/page/GPU-tips-and-tricks
- Status: **FREE RESEARCH/NOTEBOOK CANDIDATE**, no activation or compute execution authorized.

#### Rig — identity and cost now verified
- Exact project identified as kaijiabo/rig / Rig, an MIT-licensed open-source cloud-desktop manager for AI coding agents. It creates Linux desktops through E2B, supports browser/computer use, and pauses idle desktops.
- Rig itself is free software, but the hosted desktop compute is metered through E2B. The project currently estimates approximately US$0.46/hour for a 4-CPU/16-GB desktop at E2B rates. Therefore it is **not a zero-cost cloud-computer solution** under the current CAD $0 constraint.
- Rig's optional browser-cookie import can copy many signed-in sessions into cloud desktops (banking/payment sites excluded by default); this creates a material credential/session-exposure risk and must not be used without a dedicated security review and explicit approval. The setup also requires Bun and an E2B account/API key.
- Source: https://github.com/kaijiabo/rig
- Status: **HOLD / NO PAID COMPUTE**. Retain only as a future candidate if metered compute becomes affordable and the credential-handling design passes security review.

#### Grok Bot cloud computer
- Previously reviewed as US$20.99 for the first month, then US$41.99/month or US$419.90/year.
- Status: **REJECTED under the no-spending constraint**. Do not reactivate or recommend unless the owner explicitly changes the restriction.

#### “Open Frames” name — unresolved
- The user recalls an additional candidate sounding like “Open Frames.” Its exact product identity has not been verified from prior records or reliable sources.
- Do not silently replace this name with OpenHands or another similarly named product. OpenHands remains separately classified as a bounded engineering-agent candidate, not a confirmed cloud-computer provider.
- Status: **UNRESOLVED — recover exact name before classifying or recommending**.

### Updated role classification
- **Current development:** GitHub Codespaces (free personal-account quota, subject to account confirmation).
- **Future persistent workstation:** Zo Computer (planned; no paid activation).
- **Cloud agent desktops / sandboxes:** Cloudroom (free entitlement discrepancy unresolved); E2B (one-time credits, short sessions, possible card verification); Rig (E2B-metered; hold).
- **Self-hosted VM lab:** PequeRoku (requires separate suitable Linux hardware/host).
- **Notebook/research compute:** Google Colab and Kaggle Notebooks (ephemeral, dynamic quotas; not production hosting).
- **Rejected:** Grok Bot cloud computer under current cost rule.

# Shared AI Workforce Architecture
**Status:** Proposed architecture baseline — owner-approved for scoped implementation; not deployed  
**Applies to:** Trading & Technology Company and AI Revenue Company  
**Governance:** Main Hub / OCC  
**Target:** One shared workforce foundation integrated into both independent companies; prepare both in parallel for the January 4–8, 2027 target window, subject to separate readiness gates, available capital and owner approval

## 1. Purpose and governing decision

Build one shared, model-agnostic technology foundation for AI workforce management, orchestration, memory, evaluation and observability, serving two independent companies.

The shared foundation is a reusable technical capability, not a merger of the companies. Each company retains its own executive leadership, agent roster, operational authority, budgets, records, customer data, risk controls and approval boundaries. Shared services must be explicitly scoped and audited.

Both companies are developed in parallel using the same reusable workforce foundation, integrated into each company's own operating structure. Each company has its own deployment/tenant boundary, executives, agent identities, queues, memory, records, budgets, permissions, policies and launch decision. The portfolio objective is to prepare both for the owner's January 4–8, 2027 target window if each independently passes its readiness gates and the owner approves. Trading & Technology does not universally depend on AI Revenue already generating revenue: if adequate lawful starting capital is unavailable, Trading moves to standby while AI Revenue continues its own revenue work. Any AI Revenue capital support requires a separately approved, lawful, documented and properly accounted-for arrangement that protects AI Revenue's solvency and operating needs. Capital is only one Trading launch gate; no date overrides safety, regulatory, security, operational or risk readiness.

AI Revenue is intended to be AI-operated from its executive leadership through its specialist departments and routine permitted workflows. It is not merely a conventional business with AI assistants. Trading & Technology likewise has its own AI executive and specialist workforce, with independent trading risk authority.

## 2. Reference architecture

| Layer | Leading candidate / capability | Intended responsibility |
|---|---|---|
| Workforce control plane | Paperclip | Company org charts, agent identities, goals, tasks, approvals, budgets and run records |
| Swarm / agent orchestration | Ruflo | Specialist-agent coordination, task decomposition, MCP integration, memory-assisted workflows and bounded swarm execution |
| Engineering agent runtime | Claude Code, OpenAI Codex, OpenHands | Repository analysis, code drafting, test creation and controlled engineering tasks |
| Model layer | Claude, GPT/Codex, Qwen, Llama, Gemini and compatible alternatives | Select the appropriate model for each bounded role; avoid single-provider dependence |
| Model interoperability | Native adapters, OpenCode/provider routing, MCP, HTTP/OpenAI-compatible endpoints, local runtimes such as Ollama | Connect models where supported; verify each adapter and model combination before use |
| Memory / knowledge | Ruflo memory capabilities; AgentMemory or other scoped stores if needed | Durable, access-controlled company and agent context |
| Observability / evaluation | Langfuse and/or OpenLIT; deterministic test and audit tooling | Trace runs, evaluate outputs, inspect failures and measure model/agent reliability |
| Security / governance | OCC policies, least privilege, sandboxing, deterministic controls and human approval gates | Enforce company boundaries, action restrictions, evidence and incident handling |

This is a candidate stack, not a claim that any component is installed, connected, running or production-ready.

## 3. Company separation and shared-service boundaries

The platform may share source code, deployment patterns, generic skills, model adapters and non-sensitive infrastructure. It must not silently share company authority or private data.

Required boundaries:
- Maintain distinct company identities, executive hierarchies, agent registries, task queues, budgets, accounting ledgers, audit records and operational workspaces.
- Separate customer data, credentials, secrets, private documents, model context and persistent memory by company.
- Trading & Technology's market, trading and risk data must not become available to AI Revenue agents by default.
- AI Revenue's customer, sales, pricing and financial data must not become available to Trading & Technology agents by default.
- Cross-company work requires an explicit, scoped, logged data-sharing contract and approval appropriate to the data/action.
- OCC coordinates governance and reports status. It does not own or move either company's money, override its executive authority, or bypass the company's independent risk controls.
- If Paperclip's multi-company isolation cannot be demonstrated by tests, use separate instances or otherwise stronger isolation rather than assuming tenant separation.

## 4. Model-agnostic workforce

Model names are replaceable implementation choices, not organisational roles.

| Model / runtime | Candidate use | Integration condition |
|---|---|---|
| Claude Code | Engineering swarm, architecture and specialist coding | Paperclip adapter / Ruflo integration; provider access and permissions verified |
| Codex | Independent engineering, review, rescue and task handoff | Paperclip adapter / MCP integration; access and cost verified |
| Qwen | Local or provider-backed research, coding and structured specialist work | Use a verified local runtime or compatible endpoint; no assumption of native Paperclip adapter |
| Llama | Independent critique, classification and review | Use a verified local runtime or compatible endpoint; test quality for each task |
| Gemini | Optional research and engineering specialist | Verify adapter, account access, model availability and cost |
| Other models | Future replaceable specialists | Must satisfy adapter, security, privacy, reliability and cost checks |

A second model's opinion is not independent assurance if it receives the same flawed evidence or shares the same upstream dependency. Critical decisions require source validation, deterministic checks and appropriate human approval.

## 5. Company workforce design

### Trading & Technology Company
Its own AI CEO and executive functions coordinate specialist research, Crypto, Forex, indices, Gold/XAUUSD, PolyBot, market-data intelligence, risk, security, finance and recovery. Trading decisions remain subject to independent deterministic risk controls. Research and paper trading do not imply live-trading authority.

### AI Revenue Company
Its own AI CEO and executive functions coordinate:
- COO / operations and delivery;
- CFO / accounting, cash flow, budgets and verified-revenue ledger;
- CTO / engineering, infrastructure, products and automation;
- CMO / brand, marketing and distribution;
- CRO / sales, business development and partnerships;
- CHRO / agent workforce planning, role design and performance;
- CISO / security, access control and incident response;
- legal/compliance review function;
- product and service development;
- AI Creative Studio;
- customer support, fulfilment, quality assurance, research and administration.

These are required organisational functions, not a claim that agents have already been deployed. The Creative Studio is a division of AI Revenue, not a third company, and does not have to be complete for company launch if another approved revenue stream satisfies the launch gate.

## 6. Permission model and fail-closed defaults

All agent runtimes must be configured more restrictively than their permissive convenience defaults.

Default permissions:
- Read-only repository and research access unless a specific task has an approved write scope.
- No unrestricted host filesystem, shell, browser, MCP, network, personal account or connected-app access.
- No access to secrets, wallet seed phrases, private keys, passwords, MFA codes or unneeded customer information.
- No spending, paid API calls, subscriptions, paid trials, credit consumption, purchases or financial transactions.
- No GitHub Actions runs or reruns without explicit owner approval.
- No merges, deployments, publication, external messages, applications, contracts, customer commitments, permission changes, wallet connections, transaction signing or live trading without the applicable explicit approval.
- No agent may change its own permissions, budgets, safety policy, approval rules or audit history.
- Tool calls and cross-company access must be logged with actor, company, task, scope, evidence and outcome.
- Missing, stale, conflicting or unauthenticated evidence fails closed for consequential decisions.
- Stop controls and human vetoes take precedence over swarm consensus or model output.

Paperclip documentation describes full-auto defaults for some coding adapters. Those defaults must not be accepted blindly. Explicitly configure restrictive permissions, sandboxed execution and denied non-interactive permission requests where supported. Verify the effective runtime policy rather than trusting a configuration label.

Ruflo includes optional autopilot, hooks, workers, plugins and federation capabilities. Evaluate these individually; do not enable unattended loops, background workers, broad MCP tools or cross-installation federation by default. Start with read-only and dry-run workflows.

## 7. Free-first, licence and cost policy

Prefer open-source, self-hostable components and free local inference where practical. A free software licence does not make model inference, hosting, storage, networking or maintenance free.

Before adopting a component, record:
- exact repository and version/commit;
- licence and any separate plugin/model/data licences;
- maintenance activity and security advisories;
- hardware and persistent-storage requirements;
- provider/API requirements and actual cost exposure;
- telemetry and data-egress behaviour;
- authentication, sandboxing and isolation model;
- backup, recovery and upgrade procedure;
- exit strategy and replacement options.

Paperclip is documented as MIT-licensed and self-hostable, but it does not supply free model inference; provider/runtime access remains a separate dependency. Ruflo's repository and npm package identify an MIT licence, but its plugins and integrations must be reviewed individually. No paid services, API use, credits, upgrades or payment-backed trials are permitted under the current zero-spend policy.

## 8. Implementation sequence

1. **Architecture baseline:** record this decision in the Main Hub and reconcile legacy single-division language with the two-company model.
2. **Repository and licence audit:** pin exact versions; inspect dependencies, permissions, telemetry, plugins and model adapters.
3. **Threat model:** define company data classes, trust boundaries, tool permissions, secret handling, prompt-injection controls and incident response.
4. **Offline prototype:** prepare Paperclip and Ruflo configurations without installing or running them; define two isolated company workspaces and a minimal agent roster.
5. **Compatibility tests:** verify Claude Code, Codex, Qwen and Llama integration paths individually. Record unsupported paths rather than implying universal compatibility.
6. **Controlled sandbox pilot:** only after separate owner approval for installation/compute; use synthetic data, read-only repository mounts and no external credentials.
7. **Deterministic evaluation:** test tenant isolation, permission denial, audit integrity, recovery, cost ceilings, model disagreement, prompt injection and failure handling.
8. **Operational rehearsal:** prove each company's own AI executives and departments can complete permitted workflows, with OCC oversight and safe escalation.
9. **Launch decision:** require separate evidence-based readiness gates for both companies and owner approval for simultaneous activation.

## 9. Readiness and revenue evidence

An architecture document, agent roster, demo, generated code or passing unit test does not prove a company is operational.

AI Revenue must demonstrate a functioning AI-operated permitted workflow, genuine customer delivery and actual payment received, with evidence recorded in its own finance ledger. Leads, invoices not paid, forecasts, grants not received and unpaid work do not count as received revenue.

Trading & Technology must demonstrate validated data provenance, risk controls, paper-exit protection, stop/veto behaviour, incident escalation, recovery and repeatable rehearsals. Live trading is a separate approval and readiness decision.

The Main Hub/OCC must demonstrate governance, authenticated evidence handling, cross-company boundary enforcement, incident reporting and recovery. No company may be marked operational based solely on planned architecture.

## 10. Status ledger

| Component | Status at baseline |
|---|---|
| Two-company shared workforce architecture | Owner-approved design; implementation proposed in this document |
| Paperclip | Leading candidate; not installed or deployed |
| Ruflo | Leading candidate; not installed or deployed |
| Claude Code / Codex swarm | Planned integration; not deployed as a company workforce |
| Qwen / Llama | Model candidates; runtime and compatibility not verified here |
| OpenHands | Bounded engineering candidate; not deployed |
| AgentMemory / Langfuse / OpenLIT | Supporting candidates; adoption not decided |
| Company isolation tests | Not yet demonstrated |
| Autonomous company operations | Not established |
| Evidence-based launch sequence | Both prepared in parallel; separate company gates and owner approval; Trading may enter standby if lawful starting capital or another gate is unavailable |

## 11. References

- [Current Paperclip + Ruflo Technical Assessment](workforce-platform-current-technical-assessment.md)
- [Workforce Platform Adapter Contract](workforce-platform-adapter-contract.json)


- Paperclip: https://github.com/paperclipai/paperclip
- Paperclip adapter overview: https://github.com/paperclipai/paperclip/blob/master/docs/adapters/overview.md
- Ruflo: https://github.com/ruvnet/ruflo
- OpenHands: https://github.com/OpenHands/OpenHands
- AgentMemory: https://github.com/rohitg00/agentmemory
- Langfuse: https://github.com/langfuse/langfuse
- OpenLIT: https://github.com/openlit/openlit

---
**Owner approval boundary:** This document authorises architecture planning and scoped repository documentation only. It does not authorise installation, execution, paid usage, external account access, workflow runs, deployment, publication, financial actions or live trading.


## Current implementation-preparation artifacts

- [Shared infrastructure hosting decision matrix](shared-infrastructure-hosting-decision-matrix.md) — distinguishes development workspaces, ephemeral research compute, bounded sandboxes and persistent hosting; confirms that no zero-cost always-on host is currently verified.
- [Initial workforce roster and tenant blueprint](initial-workforce-roster-and-tenant-blueprint.md) — maps the two independent company workforces, first-class Research & Intelligence and Security & Recovery services, Paperclip tenant topology, bounded Ruflo profiles, role permissions and acceptance gates.
- [Decision & Agreement Register](decision-and-agreement-register.md) — durable append-only owner agreements and material governance decisions.

These are architecture/preparation artifacts only. They do not represent deployed agents, a live host, validated isolation, executed tests or operational coverage.

- [Workforce parent–child task envelope contract](workforce-parent-child-task-envelope-contract.md) — defines deterministic identity/scope inheritance, child-task restrictions, revocation, audit and future synthetic denial cases. Draft only; not implemented or tested.

## Role and org-chart configuration

- [Paperclip Role IDs and Organisation-Chart Configuration Draft](paperclip-role-id-and-org-chart-configuration-draft.md) — stable company/shared-service role IDs, first-pass org charts, identity metadata and default-deny permission profiles; draft only, not imported or provisioned.

## Bounded orchestration profiles

- [Ruflo Bounded Swarm Profile Registry](ruflo-bounded-swarm-profile-registry-draft.md) — recipient-scoped research, engineering, quant, PolyBot, business, security and OCC profiles; finite limits, CRO veto, cancellation and synthetic denial cases. Draft only; not installed or tested.

## Security & Recovery service contract

- [Security & Recovery Service Contracts and Boundary/Revocation Standard](security-recovery-service-contracts-and-boundary-revocation-standard.md) — defines identity/access governance, company isolation, revocation propagation, incident severity, backup/recovery and Trading loss-reconciliation boundaries. Design only; not implemented or tested.

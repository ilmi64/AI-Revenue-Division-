# Paperclip + Ruflo — Current Technical Assessment

**Assessment date:** 2026-11-21  
**Applies to:** AI Revenue Company and Trading & Technology Company  
**Status:** Read-only vendor assessment; no software installed, executed, connected or approved for production  
**Cost status:** CAD $0 spent; no paid services or inference authorized

## 1. Executive decision

Retain Paperclip as the leading workforce-management/control-plane candidate and Ruflo as the leading bounded swarm/orchestration candidate. The combination remains architecturally plausible, but it is not yet compatibility-validated as an integrated stack.

The intended division of responsibility is:

- **Paperclip:** company org chart, agent lifecycle, goals, tasks, approvals, budgets, schedules and run history.
- **Ruflo:** bounded decomposition and coordination of specialist sub-agents inside an explicitly scoped parent task.
- **Claude Code / Codex / other runtimes:** perform the actual specialist work under the permissions and tool gateway assigned to that task.
- **External deterministic policy, identity, tool/data and audit services:** enforce company isolation, authorization, cost limits, revocation and approval rules. Paperclip, Ruflo and models are not security authorities.

Do not let Paperclip and Ruflo both independently schedule or own the same work. Paperclip owns the company-level task and accountability record; Ruflo coordinates subordinate work within that task's limits.

## 2. Current upstream evidence snapshot

The following are observed upstream release/documentation facts on the assessment date. They are not a recommendation to install the latest release blindly; production candidates must be pinned to reviewed versions and their dependencies.

| Component | Observed upstream baseline | Licence / runtime evidence | Assessment |
|---|---|---|---|
| Paperclip | Latest release page showed v2026.1106.0, released 2026-11-06 | Repository LICENSE is MIT. Current quickstart requires Node.js 24.11+ and pnpm 9.15+. Native Linux runner binaries target glibc 2.39+ on x64/ARM64. | Leading control-plane candidate; host/runtime requirements are material. |
| Ruflo | Latest release page showed v3.76.0, released 2026-11-11 | Repository README identifies MIT. Full CLI initialization adds project files, hooks, MCP server and daemon; README describes 98 agents, 60+ commands and 30 skills. | Leading swarm candidate; broad install surface must be reduced and audited. |
| Claude Code | Paperclip lists a built-in Claude Code adapter; Ruflo is explicitly positioned as a Claude Code/Codex meta-harness | Exact provider account, model access, local runtime and cost are separate requirements | Strong initial integration candidate; not yet tested in this stack. |
| Codex | Paperclip lists a built-in Codex adapter; Ruflo documents Codex/MCP client use | Exact account/runtime/credential topology and cost require separate verification | Strong alternate engineering/review runtime; not yet tested in this stack. |
| Gemini CLI | Paperclip adapter documentation describes it as experimental / not yet in the stable adapter type enum | Availability and stability need a fresh check before use | Do not put on the critical path. |
| Qwen / Llama | No native Paperclip adapter is assumed by this assessment | Requires a separately selected local runtime or compatible endpoint and model-specific evaluation | Candidate model families only; not yet connected or validated. |
| OpenHands | Existing architecture treats it as a bounded engineering candidate | Separate integration, sandbox and cost assessment required | Optional later; not a prerequisite for initial workforce. |

## 3. Important technical findings

### Paperclip

- Paperclip describes multi-organization support in one deployment, with company-scoped tasks, agents, permissions and activity histories. This is a useful capability, not proof that our particular configuration provides sufficient isolation.
- The current release line has a native Runner for Claude and Codex on qualified macOS/Linux hosts. Current Linux native binaries require glibc 2.39 or newer.
- Paperclip's adapter documentation also lists OpenCode, Pi, Hermes and other adapter types. Adapter presence does not prove a model, credential, sandbox or permission profile is suitable.
- Paperclip's native runner and adapter defaults have changed over time. Configure the restrictive policy explicitly and inspect effective runtime permissions; never assume a UI label alone proves a deny rule.
- Paperclip is the company workforce manager, not our identity issuer, deterministic policy engine, secret vault, owner-approval authority or trading risk engine.

### Ruflo

- Ruflo offers two materially different install surfaces: a lighter Claude Code plugin route and a full CLI initialization route. The full route writes project-level configuration, agents/skills, hooks, MCP configuration and daemon components.
- Ruflo documentation says installed plugins/mods can run with the connected account's permissions. Each plugin, hook, helper, MCP tool and command therefore requires source and permission review before use.
- Ruflo's optional autopilot, background workers, hooks, plugins, memory, federation and model-routing features are not all required for the first pilot. Keep them disabled unless a specific feature is reviewed and needed.
- Recent release notes contain security changes involving MCP authentication, federation trust-key pinning, input validation and dependency fixes. This is evidence of active security work, not proof that the current release is risk-free.
- Do not enable federation between the two companies. Cross-company data exchange remains default-deny and must go through the approved exchange contract.

## 4. Recommended integration pattern

1. A company-specific Paperclip tenant owns the parent task, accountable agent, deadline, budget ceiling and task record.
2. The assigned worker runtime (initially Claude Code or Codex) receives only the task's approved workspace and tools.
3. Ruflo is exposed to that worker as a bounded MCP/orchestration capability, not as a second company control plane.
4. Ruflo child agents inherit the parent task's company identity, data scope, tool allowlist, expiry, cost cap and approval boundary. Child tasks cannot expand any of them.
5. All tool and data access is mediated by the external deterministic gateways specified in the company adapter contract.
6. Paperclip records the parent task and deliverables; the audit sink records child runs, model/runtime, tool calls, policy decisions, source provenance, costs and output digests.
7. High-impact work receives independent review; a second model is not considered independent if it shares the same flawed source or upstream dependency.

If Paperclip cannot reliably pass the required scoped identity and context to Ruflo, or if Ruflo cannot preserve parent restrictions across child agents, the integration is rejected or reduced to a manual supervised handoff.

## 5. Device and hosting constraint

The currently known user devices are Android phone and Android tablet. They are not an established or qualified production host for the full Paperclip + Ruflo stack.

Paperclip's published native-runner baseline is macOS/Linux, with its Linux binaries requiring glibc 2.39+. Android uses a different userspace/runtime environment and is not listed as a qualified Paperclip runner target. Do not assume the Android device can host the production control plane or swarm workers merely because it can open a browser or run some command-line utilities.

A later host decision must compare:
- existing computer hardware, if available;
- a genuinely free, persistent, policy-compliant host if one can be verified;
- a separately approved paid host only after revenue or an explicit change to the zero-spend rule.

Do not use a free trial requiring payment details, a service with automatic billing risk, or a free compute tier whose sleep/expiry limits make it unsuitable for reliable company operations. No cloud host has been selected or provisioned.

## 6. Security and compatibility blockers before any pilot

The following are mandatory acceptance items, not optional enhancements:

- two isolated company configurations, identities, secrets, databases/workspaces, task queues, memory stores, audit streams and budgets;
- proof that Paperclip company scoping is enforced for every relevant API, attachment, task, transcript, schedule, connection and agent-discovery surface;
- proof that Ruflo child agents cannot escape parent task scope or discover the other company;
- explicit denial of shell, filesystem, browser, network, MCP and connected-account capabilities unless individually approved;
- no direct model-to-tool path that bypasses the policy/tool gateway;
- no self-granted permissions, self-approved hires, policy edits or budget increases;
- secret redaction and credential separation;
- prompt-injection and malicious-repository-content handling;
- cost metering and hard CAD $0 billable-work block under the current policy;
- cancellation, revocation, emergency stop, audit integrity and recovery;
- provider outage and shared-platform outage drills;
- export/exit path so either company can replace Paperclip or Ruflo without losing its own records or controls.

No credentials, real customer data, trading data or live accounts belong in the first compatibility pilot. Use synthetic data only after a separate owner authorization to install/execute.

## 7. Initial minimal workforce pilot — design only

Use the smallest useful pilot rather than deploying every advertised agent:

- one company CEO/operations coordinator identity;
- one task coordinator;
- one Claude Code worker;
- one Codex reviewer or alternate worker (not concurrently enabled until cost/access checks pass);
- one independent QA/security reviewer;
- one bounded Ruflo swarm limited to synthetic, read-only tasks;
- one external policy/tool gateway stub and append-only audit capture.

Run the same synthetic task through each company tenant with distinct test identities and data. Include negative tests attempting cross-company reads, parent-scope expansion, unauthorized shell/network/tool calls, cost-limit bypass, self-approval and revoked-task continuation. All negative cases must be denied and evidenced.

This pilot does not authorize production use, tests, installation, API calls, compute consumption, repository workflow runs or any external side effect. Those require separate approval.

## 8. Version and adoption policy

- Record exact Git commit/tag, package version, dependency lockfile, adapter version and configuration digest for every candidate.
- Do not use floating `latest` tags for any eventual controlled deployment.
- Review release notes and security advisories before every update.
- Pin the first candidate only after compatibility and security review; pinning is not the same as approval to install.
- Keep Paperclip and Ruflo replaceable. Company policies, identities, audit and data contracts remain outside their proprietary/runtime-specific configuration.
- Re-evaluate the versions at the time of installation; this snapshot will become stale.

## 9. Decision ledger

| Decision | Status |
|---|---|
| Paperclip remains leading workforce-control-plane candidate | Retain provisionally |
| Ruflo remains leading swarm/orchestration candidate | Retain provisionally |
| Paperclip + Ruflo compatibility | Not verified |
| Claude Code / Codex runtime compatibility in our configuration | Not verified |
| Qwen / Llama / Gemini runtime compatibility | Not verified |
| Android as production host | Not qualified; do not assume support |
| Shared deployment vs separate instances | Undecided pending isolation evidence; prefer separate instances if isolation cannot be proven |
| Installation / execution / deployment | Not authorized |
| Paid API, hosting, inference or subscriptions | Not authorized |
| Company data or credentials in pilot | Not authorized |
| Cross-company federation | Disabled / not approved |

## 10. Source register

- Paperclip repository and capability overview: https://github.com/paperclipai/paperclip
- Paperclip releases: https://github.com/paperclipai/paperclip/releases
- Paperclip adapter overview: https://github.com/paperclipai/paperclip/blob/master/docs/adapters/overview.md
- Paperclip Runner platform baseline: https://github.com/paperclipai/paperclip/blob/master/packages/paperclip-runner/README.md
- Ruflo repository and installation modes: https://github.com/ruvnet/ruflo
- Ruflo releases and security changes: https://github.com/ruvnet/ruflo/releases
- Ruflo changelog: https://github.com/ruvnet/ruflo/blob/main/CHANGELOG.md

---
**Owner boundary:** This assessment authorizes read-only research and documentation only. It does not authorize installation, execution, tests, API usage, account connection, credentials, hosting, spending, deployment, publication or external actions.

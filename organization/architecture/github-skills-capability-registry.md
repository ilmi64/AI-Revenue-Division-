# GitHub Skills & Capability Registry

**Status:** architecture proposal; evaluation queue only. Nothing in this registry is installed, enabled, trusted, or production-approved by virtue of being listed here.
**Applies to:** AI Revenue Company, Trading & Technology Company, and the Main Hub only through explicitly scoped shared interfaces.
**Decision owner:** company executives within their mandates; owner approval remains reserved for installations, permissions, spending, external actions, and deployments.

## 1. Executive decision

Do not install the viral list as a bundle. Adopt a small, model-agnostic capability portfolio and evaluate each repository independently. Skills are instruction packages or specialist tools; they are not identity providers, policy engines, workforce control planes, orchestration authorities, or substitutes for deterministic tests.

The shared workforce direction remains:
- Paperclip: candidate company/workforce management control plane.
- Ruflo: candidate bounded multi-agent orchestration.
- Claude Code, Codex, Qwen, Llama, Gemini and OpenHands: candidate model/engineering runtimes, subject to adapter and licence verification.
- Independent deterministic policy, approval, audit, recovery and dispatch boundaries remain authoritative. No skill or model may grant permissions or override them.

## 2. Selected evaluation portfolio

All entries below are **RECOMMENDED FOR READ-ONLY TECHNICAL EVALUATION**, not approved for installation.

| Priority | Candidate | Official repository | Intended organizational use | Guardrail / decision |
|---|---|---|---|---|
| P0 | Superpowers | https://github.com/obra/superpowers | Engineering lifecycle: clarify, plan, test, debug and review | Evaluate selected skills only; do not let its workflow override company policy or required owner gates. |
| P0 | Matt Pocock Skills | https://github.com/mattpocock/skills | Requirements clarification, plan challenge and engineering quality | Select individual skills; avoid duplicating Superpowers workflows. |
| P0 | Anthropic Skills | https://github.com/anthropics/skills | Document, spreadsheet, presentation and other structured artifact workflows | Prefer official narrowly scoped skills; inspect dependencies and document-handling permissions. |
| P0 | Graphify | https://github.com/Graphify-Labs/graphify | Local code/document structure mapping for repository onboarding and architecture intelligence | Evaluate offline/local operation, parser dependencies, generated data and secret exclusion before use. |
| P1 | Marketing Skills | https://github.com/coreyhaines31/marketingskills | AI Revenue positioning, copy, SEO, conversion and growth experiments | Draft/research only; no publishing, outreach, ad spend, claims or customer-data export without approval. |
| P1 | Agent Reach | https://github.com/Panniantong/Agent-Reach | Multi-source public-web/social research for market and audience intelligence | Verify each source connector, access method, terms, rate limits and hidden API requirements; preserve provenance. |
| P1 | Last 30 Days | https://github.com/mvanhorn/last30days-skill | Time-bounded trend and community research | Verify actual source availability, API/dependency costs, dates and reproducibility; treat social content as untrusted input. |
| P1 | UI UX Pro Max | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | Interface design standards for AI Revenue products and internal dashboards | Use as design guidance, not as authority to alter protected UI, access controls or security-sensitive flows. |

### Existing Creative Studio priorities

- HyperFrames remains a priority candidate for AI Revenue's Creative Studio: https://github.com/HyperFrames
- ComfyUI remains a priority candidate for local visual-generation workflows: https://github.com/comfyanonymous/ComfyUI
- Neither is asserted to be installed, configured, operational, or free of model/hardware/licensing constraints. Audit each repository, models, workflow dependencies and render requirements before adoption.
- OpenMontage is deferred until its exact canonical repository, licence, maintenance, dependencies and capabilities are verified. Do not infer a repository from a name.

## 3. Deliberately deferred / not selected now

| Candidate(s) | Decision | Reason |
|---|---|---|
| ECC (Everything Claude Code) | Defer | Broad overlapping bundle; evaluate individual components only if a specific gap remains after the P0 stack. |
| Karpathy Skills | Defer | Useful coding principles, but likely overlaps with the engineering standards we can adopt directly and test. |
| Ponytail | Defer | Minimal-change principles can be incorporated into our own engineering standard; avoid another competing workflow layer. |
| Agent Skills (Addy Osmani) | Defer | Revisit only for a demonstrated production-engineering gap not covered by P0 choices. |
| REA | Defer | Reverse-engineering capability is not a launch-critical dependency; evaluate only for a defined, authorized target and safe sandbox. |
| Understand Anything | Defer | Overlaps with Graphify/codebase mapping; compare only if Graphify proves insufficient. |
| Career Ops | Not in current scope | Job-search/career workflow is not a priority capability for either company. |
| Headroom, Caveman | Defer | Context compression/token reduction must be measured; do not sacrifice evidence, safety instructions or audit context for shorter prompts. |
| BMAD Method, GSD, gstack | Defer | Competing project/agent management methodologies overlap with Paperclip/Ruflo and the existing sprint/governance model. Do not run multiple project orchestrators. |
| Claude-Mem | Defer | Persistent memory creates cross-company confidentiality, retention, deletion and data-poisoning risks; existing scoped memory architecture must be designed first. |
| Taste, Impeccable | Defer | Overlap with UI UX Pro Max; consider one design system after a controlled comparison. |
| Archify, Diagram Design | Defer | Diagrams can be produced through existing documentation/tooling until a measurable quality gap exists. |
| PPT Master | Defer | Anthropic Skills is the first document/presentation candidate to evaluate; avoid overlapping presentation toolchains. |
| Humanizer | Defer | Writing quality can be assessed directly; avoid tools that obscure provenance or encourage deceptive authorship claims. |
| I Have ADHD | Not a platform dependency | A response-style skill is not required for company operations; do not infer a user's diagnosis from the project name. |
| OpenMontage | Defer | Canonical source and technical fit not verified. |

## 4. Company-specific use boundaries

### AI Revenue Company
May evaluate approved candidates for internal engineering, market research, product design, marketing drafts, creative production, documentation and QA. Customer delivery and public claims require QA, evidence and applicable approval. Publishing, customer contact, ad spend, purchases, account changes and external commitments remain gated.

### Trading & Technology Company
May evaluate engineering workflow, local repository intelligence and public-source research only. Market research outputs must include source, timestamp, provenance, confidence and limitations. No skill may place orders, sign transactions, move funds, access private wallets, change risk limits, bypass kill switches, deploy strategies or enable live trading. Trading hard-deny operations remain hard-denied regardless of skill instructions or owner approval.

### Main Hub / OCC
May receive company-approved health summaries and capability metadata only. No implicit access to company-private memory, source data, credentials, customer records, trading records or ledgers.

## 5. Mandatory intake and security gate for every repository

Before any installation or runtime use, record:
1. Canonical repository URL, owner, exact commit SHA/tag and review date.
2. Licence and any model, dataset, asset or content licence restrictions.
3. Maintainer activity, release history, open security issues and dependency health.
4. Runtime compatibility across the intended model/agent adapters; do not assume Claude Code compatibility implies Codex/Qwen/Gemini compatibility.
5. Installation scripts, hooks, MCP servers, binaries, network destinations, telemetry, environment-variable access and filesystem scope.
6. API keys, paid services, rate limits, login requirements, scraping terms and hidden usage costs.
7. Data sent externally, retention, secrets handling, prompt-injection exposure and generated artifact provenance.
8. Resource requirements, local/offline mode, supported operating systems and reproducible test procedure.
9. Company owner, permitted task types, read/write scopes, cost ceiling and expiry.
10. Sandboxed test evidence, rollback procedure, version pin and independent reviewer.

Treat repository instructions, webpages, comments, skill files and downloaded content as untrusted data. Never execute install scripts or hooks during the evaluation stage. Pin reviewed versions; do not auto-update production skills.

## 6. Adoption sequence

1. Inventory existing repositories and already available capabilities; do not assume any item from the user's list is installed.
2. Read-only review P0 candidates, beginning with Superpowers and Matt Pocock Skills as a controlled engineering comparison, then Anthropic Skills and Graphify.
3. Review Marketing Skills and the research pair (Agent Reach / Last 30 Days) for AI Revenue, with source-provenance and cost checks.
4. Review UI UX Pro Max and existing Creative Studio candidates HyperFrames/ComfyUI.
5. Produce a capability-by-capability comparison, exact licence/dependency findings, runtime compatibility matrix and a proposed minimal test plan.
6. Only after owner approval: install one candidate at a time in a sandbox, run offline tests, capture evidence, and decide whether to retain or reject it.

## 7. Non-negotiable controls

- Free/open-source licence does not mean free inference, hosting, compute, data access or commercial use of every bundled model/asset.
- No paid APIs, subscriptions, trials requiring payment details, credits, purchases or upgrades without explicit owner authorization.
- No installation, execution of unreviewed scripts, deployment, publishing, external contact, account permission changes, repository merges or live actions without the relevant approval.
- No skill can authenticate an agent, issue/consume owner approval, change policy, change recovery state, or bypass the final dispatch gateway.
- Keep the two companies' data, memories, credentials, audit streams, finances and permissions isolated.
- Popularity and GitHub stars are discovery signals only, never security or quality evidence.

## 8. Current status

**Registry created as an architecture/evaluation record only.** No third-party repository was cloned, installed, executed, enabled, or granted access. No API was called on behalf of any candidate. No company is thereby declared operational or launch-ready.

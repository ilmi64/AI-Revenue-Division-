# Organization-Wide Capability & Opportunity Registry

**Status:** Initial canonical portfolio ledger; planning/research only.  
**Owner:** Research & Intelligence Division (advisory); adoption authority remains with each recipient company.  
**Scope:** AI Revenue Company, Trading & Technology Company, shared enabling infrastructure, Main Hub/OCC and Research & Intelligence.  
**Baseline date:** 2026-11-21.  
**Resource posture:** CAD $0 incremental by default; no installation, execution, purchase, API spend, deployment or external action is authorized by a registry entry.

## 1. Purpose and source-of-truth rules

This is the canonical cross-organization index for capability opportunities and existing named workstreams. It consolidates the portfolio already discussed and documented; it does not replace detailed company-owned research records, strategy evidence, bot records, decision history, code, or source registries.

Before adding or changing an entry:
1. Search the relevant company and Research & Intelligence records for an existing ID/name and exact source revision.
2. Link to the existing record rather than cloning it.
3. Preserve historical status and decisions; record changes as dated updates with evidence.
4. Keep company-private evidence in its company tenant. This index stores only public/approved metadata and recipient scope.
5. Unknown fields remain UNKNOWN / NOT_VERIFIED; never infer compatibility, current maintenance, performance, cost, license or operational status.

This first ledger is a portfolio-level inventory of the explicitly preserved workstreams and candidates. It is **not** proof that every legacy registry, repository or source has been exhaustively re-read. Detailed source-level reconciliation remains an open inventory task before any integration decision.

## 2. Status vocabulary

- **DISCUSSED** — explicitly discussed or named in the existing portfolio; no current source review implied.
- **RESEARCH_PENDING** — needs current-source, license, security, cost, platform and capability review.
- **RESEARCH_IN_PROGRESS** — active documented research with a cited revision or current work record.
- **VERIFIED** — a narrowly defined claim independently checked against a recorded source/revision; does not imply production readiness.
- **REPRODUCED** — capability independently reproduced in a controlled environment; not equivalent to production acceptance.
- **INTEGRATION_PENDING** — adoption has been selected in principle but implementation and acceptance evidence are incomplete.
- **DEFERRED** — deliberately held; do not reactivate without a priority decision.
- **REJECTED** — rejected with a recorded rationale.
- **STALE** — previously useful information whose source/revision or operating status needs refresh.

No item in this initial portfolio is promoted to VERIFIED or REPRODUCED merely because it was discussed, documented, starred, marketed or included in a plan.

## 3. Portfolio registry

| ID | Capability / workstream | Recipient scope | Existing decision / priority | Current registry status | Next safe action |
|---|---|---|---|---|---|
| ORG-AI-WORKFORCE-01 | Paperclip company/agent workforce management | Both companies, isolated tenants | Leading candidate | RESEARCH_PENDING | Verify current architecture, license, security, deployment/runtime and company isolation fit |
| ORG-AI-ORCH-02 | Ruflo multi-agent orchestration and swarms | Both companies, separate orchestration scopes | Leading candidate | RESEARCH_PENDING | Verify model adapters, boundaries, failure modes, cost and deterministic-policy integration |
| ORG-AI-CODE-03 | Claude Code and OpenAI Codex coding-agent runtimes | Both companies | Cross-review / bounded engineering candidates | DISCUSSED | Map supported runtimes, permission controls, review workflow and free-use constraints |
| ORG-AI-MODEL-04 | Qwen, Llama, Gemini and other compatible models | Both companies | Model-agnostic adapter portfolio | RESEARCH_PENDING | Maintain per-model capability, license, hosting/inference cost, data handling and adapter matrix |
| ORG-AI-ENG-05 | OpenHands bounded engineering agent | Both companies | Candidate only | RESEARCH_PENDING | Review isolation, tools, network/filesystem permissions and runtime requirements |
| ORG-AI-MEM-06 | AgentMemory / scoped persistent memory | Both companies, strictly separated | Candidate only | RESEARCH_PENDING | Compare tenancy, deletion, provenance, retrieval leakage and recovery |
| ORG-AI-OBS-07 | Langfuse and OpenLIT observability/evaluation | Both companies, separate streams | Candidates | RESEARCH_PENDING | Compare telemetry privacy, self-hosting, model coverage, quotas and redaction |
| ORG-AI-ROUTE-08 | OmniRoute and model routing options | Both companies | Existing named workstream | DISCUSSED | Inventory source, supported providers, routing policy, cost controls and failover |
| ORG-AGENT-09 | Agency Agents | Organization-level research; recipient-scoped use | Preserve existing workstream | DISCUSSED | Locate existing source record and reconcile exact project identity/status |
| ORG-AGENT-10 | Agent Reach | Organization-level research; recipient-scoped use | Preserve existing workstream | DISCUSSED | Locate existing source record; verify supported channels, permissions and current state |
| ORG-RESEARCH-11 | Grok Desk / HyperGrok research concepts | Research & Intelligence | Core planned research capability | DISCUSSED | Define lawful source access, shift handover, verification and cost/runtime gates |
| ORG-REA-12 | Reverse Engineer Anything MCP (morluto/rea) | Shared research method; separate company work orders | Priority capability; runtime gate applies | RESEARCH_PENDING | Continue public-source review only; no install, execution, repo modification or PolyBot integration until supported desktop runtime and separate approval |
| ORG-TOOLS-13 | Superpowers, Matt Pocock Skills, Anthropic Skills, Graphify | Both companies | P0 skills/tool portfolio | DISCUSSED | Reconcile exact repo revisions, license, platform and applicability before use |
| ORG-TOOLS-14 | Marketing Skills, Agent Reach, Last 30 Days, UI UX Pro Max | AI Revenue primarily; shared where suitable | P1 skills/tool portfolio | DISCUSSED | Verify source, license, compatibility and measured value |
| ORG-CREATIVE-15 | HyperFrames | AI Revenue / AI Creative Studio | Priority candidate | RESEARCH_PENDING | Verify current repo/docs, runtime, license, render requirements and zero-cost workflow |
| ORG-CREATIVE-16 | ComfyUI | AI Revenue / AI Creative Studio | Priority candidate | RESEARCH_PENDING | Verify hardware/runtime requirements, model licensing, storage and free local workflow |
| ORG-OCC-17 | Main Hub/OCC read-only control plane | Organization-level | M0 inventory complete; M1 drafted; M2 prototype untested | RESEARCH_IN_PROGRESS | Preserve exact-source validator and test execution as awaiting explicit authorization |
| ORG-RI-18 | Research & Intelligence Division | Organization-level shared service | Core division; not a third company or launch prerequisite | DISCUSSED | Build source-level registry reconciliation, shift/handover and recipient-scoped queues |
| ORG-POLICY-19 | Deterministic policy gateway and approval enforcement | Each company independently | Existing contracts and reference prototypes consolidated; production enforcement not implemented | RESEARCH_IN_PROGRESS | Reconcile exact code/schema revisions and close approval-schema, cryptographic trust and enforcement gaps using the integration plan |
| ORG-SKILL-20 | GitHub Skills & Capability Registry | Both companies, scoped by recipient | Existing P0/P1 evaluation portfolio; no installations authorized | DISCUSSED | Reconcile exact candidate revisions, license/runtime/security and measured fit before any approval |
| AR-COMM-01 | AI Revenue funded-opportunity / customer-problem scanner | AI Revenue only | Early commercial capability priority | DISCUSSED | Reconcile prior PR #3 and existing offer/opportunity records; no customer contact |
| AR-COMM-02 | AI workflow/business-process automation offers | AI Revenue only | Early offer candidate | DISCUSSED | Define one narrow customer problem, delivery scope, cost ceiling and QA evidence |
| AR-COMM-03 | Small-business websites / landing pages | AI Revenue only | Early offer candidate | DISCUSSED | Define reproducible delivery slice, support boundary and acceptance checklist |
| AR-COMM-04 | Content / creative packages and SEO/research briefs | AI Revenue only | Early offer candidates | DISCUSSED | Build sample workflow and QA rubric; publishing/customer contact requires approval |
| AR-COMM-05 | Digital templates, guides and workflow assets | AI Revenue only | Early offer candidates | DISCUSSED | Validate demand and rights before production or listing |
| AR-CREATIVE-06 | AI Creative Studio | AI Revenue only | Active department; HyperFrames and ComfyUI priority candidates | DISCUSSED | Continue zero-cost architecture/research and define first demonstrable deliverable |
| TT-CRYPTO-01 | Crypto / PolyBot | Trading & Technology only | First Trading capability priority | RESEARCH_IN_PROGRESS | Preserve existing Phase 4 research; inventory exact strategy/code/evidence revisions |
| TT-POLY-02 | PolyBot Phase 4: EMA20/50, RSI, volume anomalies, ATR, regime classification, paper signals | Trading only | Named research components, not proven profitable | DISCUSSED | Reconcile existing work and define component-specific data and paper acceptance criteria |
| TT-DATA-03 | Coinbase + Binance normalized comparison / Colab plan | Trading only | Existing named workstream | DISCUSSED | Reconcile prior notebook/data work, API terms/limits and reproducible comparison criteria |
| TT-MCP-04 | TradingView MCP | Trading only | Existing named workstream | DISCUSSED | Verify exact repo, license, data entitlements, permissions and platform |
| TT-FLOW-05 | Flow Surface | Trading only | One of five preserved order-flow candidates | DISCUSSED | Verify exact repository identity and compare features/data needs |
| TT-FLOW-06 | Order Book Heat Map | Trading only | One of five preserved order-flow candidates | DISCUSSED | Verify exact repository identity and compare features/data needs |
| TT-FLOW-07 | NinjaTrader Kit | Trading only | One of five preserved order-flow candidates | DISCUSSED | Verify exact repository identity, platform/license and market-data requirements |
| TT-FLOW-08 | Order Flowchart | Trading only | One of five preserved order-flow candidates | DISCUSSED | Verify exact repository identity and compare features/data needs |
| TT-FLOW-09 | OrderFlowMap | Trading only | One of five preserved order-flow candidates | DISCUSSED | Verify exact repository identity and compare features/data needs |
| TT-QUANT-10 | Quantpedia | Trading only | Existing strategy discovery source | DISCUSSED | Review source/license, strategy claims and reproducibility; no profitability inference |
| TT-QUANT-11 | FlowGPT | Trading only | Existing strategy/workflow discovery source | DISCUSSED | Verify exact source, quality, provenance and applicable licensing |
| TT-MARKET-12 | Forex, indices and Gold/XAUUSD / MT5 | Trading only | Preserved specialist workstreams | DISCUSSED | Maintain separate instrument/data/venue/risk and halal issue reviews |
| TT-CAPFLOW-13 | Crypto Capital Flow & Opportunity Intelligence | Trading only, Research-fed | Approved workstream | DISCUSSED | Reconcile J7, Buildix.trade, Sanbase/Santiment and existing capital-flow research |
| TT-J7-14 | J7 | Trading only | Named specialist intelligence source | DISCUSSED | Verify exact product/source, capabilities, access and cost |
| TT-BUILDIX-15 | Buildix.trade | Trading only | Named specialist intelligence source | DISCUSSED | Verify exact product/source, capabilities, access and cost |
| TT-SAN-16 | Sanbase / Santiment | Trading only | Named specialist intelligence source | DISCUSSED | Verify exact product/source, data coverage, plan limits and cost |
| TT-REA-17 | REA bot/strategy capability intelligence | Trading only, using shared REA research method | P0 specialist application | DISCUSSED | Continue public-source research; do not integrate or execute |
| TT-RISK-18 | Strategy validation, execution costs, risk, recovery and halal issue review | Trading only | Mandatory independent controls | DISCUSSED | Reconcile risk register and define evidence gates; no live execution |
| DEFER-ANIMORA-01 | Animora | Separate project | Deferred / on hold | DEFERRED | Do not reactivate without explicit instruction |
| DEFER-ECOM-02 | Ecommerce / MidnightOtaku / eBay-Printify automation | Separate project | Deferred | DEFERRED | Do not reactivate without explicit instruction |
| DEFER-TIKTOK-03 | TikTok distribution | AI Revenue marketing | Explicitly excluded | REJECTED | Keep excluded unless user reintroduces |

## 4. Priority and scoring method

Use a 0–5 score for each factor, supported by evidence rather than intuition:

- **Value (V):** expected revenue, cost reduction, reliability, security or research-quality improvement.
- **Urgency (U):** how strongly the capability blocks an independent company milestone or closes a time-sensitive opportunity.
- **Time-to-value (T):** shorter, demonstrable path scores higher.
- **Evidence confidence (E):** quality, recency and independent reproducibility of supporting evidence.
- **Compatibility (C):** fit with current free-first, supported runtimes, company isolation and existing architecture.
- **Reversibility (R):** ability to trial or discard safely without lock-in or irreversible effects.
- **Effort (F):** engineering/research effort; higher effort scores lower.
- **Risk (K):** security, legal, privacy, operational, financial and market risk; higher risk scores lower.
- **Cost (M):** total cost including inference, hosting, data, maintenance and opportunity cost; higher cost scores lower.

Initial decision-support score (not an automatic approval):

**Priority = 4V + 3U + 3T + 3E + 2C + 2R − 2F − 3K − 3M**

All factors must be recorded with short rationale and evidence references. Unknown cost, compatibility, license or security is not scored as zero risk: mark the candidate BLOCKED / RESEARCH_PENDING until clarified. Hard gates override any numeric score.

### Fast-track selection rules

1. First resolve safety, policy, data integrity and company-isolation blockers.
2. Prioritize high-value, high-urgency, high-confidence, low-cost, reversible capability slices.
3. Prefer work that advances one company's independent readiness without creating a dependency on the other.
4. Parallelize research and preparation that do not share mutable state or require serial approval.
5. Do not select a tool solely because it is popular, novel, has many agents or claims high performance.
6. Defer duplicates, unclear licenses, unsupported runtimes, unknown recurring costs and weakly evidenced claims.
7. For Trading, no score can override risk authority, paper-mode gates, owner approval or the separate live-trading gate.
8. For AI Revenue, no score authorizes customer contact, publication, contract, purchase or delivery commitment.

## 5. REA work-order and publication model

Research & Intelligence owns the shared method and public/authorized source stewardship. Each company issues its own scoped work order with:
- target and lawful access scope;
- recipient company and permitted data class;
- baseline capability and acceptance criteria;
- source/revision, license/terms and retrieval date;
- workflow/interface/capability decomposition;
- security, privacy, dependency, runtime and cost assessment;
- reproduction plan using synthetic/public data;
- independent reviewer and confidence;
- recipient-specific recommendation and follow-up.

A finding for AI Revenue is not automatically available to Trading & Technology, and vice versa. Cross-company publication is a separately scoped, minimal metadata summary only. No raw private records, credentials, customer data or trading data are copied into this registry.

## 6. Update and governance cadence

- Update only when a source, decision, evidence state, blocker, cost, compatibility or owner changes.
- Preserve prior state and record date, actor, reason and evidence reference.
- Mark time-sensitive entries stale when source freshness expires.
- Research & Intelligence may recommend; each company independently accepts, rejects, funds and implements.
- OCC receives only allowlisted aggregate counts, statuses and evidence references; it cannot rank company readiness or authorize adoption.
- This registry is a design-time ledger, not a live database or continuously monitored feed.

## 7. Immediate next actions

1. Reconcile the detailed existing registries and source records against this index; preserve their IDs and exact revisions.
2. Prioritize the deterministic policy gateway and approval-enforcement architecture using existing artifacts, not a duplicate design.
3. Create separate recipient-scoped REA work orders for AI Revenue workflow intelligence and Trading bot/strategy intelligence.
4. Reconcile Trading's existing PolyBot Phase 4 and capital-flow evidence before new strategy/tool research.
5. Identify the smallest AI Revenue commercial capability slice with a realistic path to a first independently delivered, quality-checked offer.
6. Update the capability scorecard only when evidence changes; do not equate architecture documents with operational progress.

**Current disposition:** initial named portfolio consolidated; detailed source-level registry reconciliation, scoring, independent reproduction and adoption decisions remain pending. No candidate is installed or operational by virtue of appearing here.

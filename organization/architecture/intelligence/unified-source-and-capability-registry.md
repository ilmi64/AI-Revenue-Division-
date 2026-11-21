# Research & Intelligence — Unified Source & Capability Registry

**Status:** Canonical registry design and initial inventory; no sources connected and no agents/tools installed by this document.
**Owner:** Data & Knowledge Governance Lead.
**Budget:** CAD $0 incremental by default.

## 1. Purpose

Maintain one discoverable inventory for sources, datasets, model providers, agent frameworks, specialist tools and research methods. A registry entry is a candidate record, not an endorsement, integration, licence grant or operational dependency. Detailed source scorecards, licence evidence, capability dossiers and incident history remain linked records. Never store secrets, credentials or private company records here.

## 2. Record classes

- SOURCE: publication, official documentation, API, MCP server, dataset, public ledger or vendor data product.
- MODEL_PROVIDER: hosted or local model and inference endpoint.
- AGENT_CAPABILITY: agent runtime, workforce manager, orchestration layer, coding agent, memory, evaluation or observability component.
- SPECIALIST_TOOL: domain-specific analytics, research, reverse-engineering or workflow tool.
- METHOD: documented research, data-quality, benchmarking, backtesting or review method.
- INTERNAL_CAPABILITY: organization-owned workflow, registry, schema or reusable capability.

## 3. Required fields

Every entry records a stable ID; exact product/repository and canonical locator; publisher/operator/developer and identity confidence; version/revision and last-checked/next-review times; purpose and supported domains; deployment form (hosted, API, MCP, local, library, repository or manual); dependencies and compatibility; data inputs/outputs and privacy exposure; licence, terms, commercial-use and redistribution rights; free-tier status, quotas, compute and cost limits; source-quality scorecard and reviewer; maturity and adoption disposition; owner, recipient scope, permitted/prohibited uses; alternatives, lock-in, failure mode and fallback; evidence, conflicts and limitations; halal issue flag where relevant. Unknown fields remain UNKNOWN.

## 4. Status semantics

- RESEARCHED: public documentation reviewed; claims may remain unverified.
- REPRODUCED: a specific capability independently reproduced in an authorized environment.
- APPROVED_FOR_PREPARATION: design/documentation work only.
- APPROVED_FOR_SANDBOX: separate approval for bounded isolated testing; not currently granted.
- APPROVED_FOR_PRODUCTION: all licensing, security, cost, reliability, legal, privacy and operational gates passed and deployment separately authorized.
- HOLD: identity, terms, risk, evidence or cost uncertainty blocks use.
- CONTEXT_ONLY: limited read-only context may be considered; no dependency or automated signal.
- DEPRECATED: retain historical record; do not newly adopt.

Open source, popularity or free download does not establish fitness, safety or commercial rights.

## 5. Initial portfolio inventory

| ID | Entry | Class | Intended value | Initial disposition |
|---|---|---|---|---|
| RI-CAP-001 | Official project, issuer, governance and regulator disclosures | SOURCE | Primary fundraising, tokenomics, treasury, grants and corporate facts | CANDIDATE |
| RI-CAP-002 | Public chain explorers and ledger records | SOURCE | Direct transaction and contract-event observation | CANDIDATE; chain-specific review |
| RI-CAP-003 | Official exchange market-data documentation | SOURCE | Venue market-data semantics and provenance | CANDIDATE; venue/jurisdiction review |
| RI-CAP-004 | Sanbase / Santiment | SPECIALIST_TOOL | On-chain and social analytics context | CONTEXT_ONLY; access/lag limits |
| RI-CAP-005 | Buildix.trade | SPECIALIST_TOOL | Hyperliquid perpetuals analytics context | CONTEXT_ONLY; estimates/cadence limits; derivative issue flag |
| RI-CAP-006 | J7 / J7Tracker intended product | SPECIALIST_TOOL | Smart-money/capital-flow candidate | HOLD; exact identity unresolved |
| RI-CAP-007 | Official launchpads and vesting contracts | SOURCE | Launch and unlock verification | CANDIDATE |
| RI-TECH-001 | NVIDIA Build / NVIDIA NIM | MODEL_PROVIDER | Optional hosted model evaluation | CANDIDATE; developer access is not production entitlement |
| RI-TECH-002 | Qwen model family | MODEL_PROVIDER | Open-weight/hosted model candidate | CANDIDATE; per-version review |
| RI-TECH-003 | Llama model family | MODEL_PROVIDER | Open-weight/hosted model candidate | CANDIDATE; per-version review |
| RI-TECH-004 | Gemini | MODEL_PROVIDER | Hosted model candidate | CANDIDATE; terms/quota/privacy review |
| RI-TECH-005 | Claude | MODEL_PROVIDER | Hosted model and coding-agent candidate | CANDIDATE; terms/cost review |
| RI-TECH-006 | OpenAI models / Codex | MODEL_PROVIDER / AGENT_CAPABILITY | Reasoning and coding-agent candidate | CANDIDATE; entitlement/cost review |
| RI-AGT-001 | Paperclip | AGENT_CAPABILITY | Workforce management/control-plane candidate | APPROVED_FOR_PREPARATION; not installed |
| RI-AGT-002 | Ruflo | AGENT_CAPABILITY | Orchestration and agent-swarm candidate | APPROVED_FOR_PREPARATION; not installed |
| RI-AGT-003 | Claude Code | AGENT_CAPABILITY | Coding-agent runtime candidate | CANDIDATE; no installation approved |
| RI-AGT-004 | OpenHands | AGENT_CAPABILITY | Bounded engineering-agent candidate | CANDIDATE; sandbox/security review |
| RI-AGT-005 | AgentMemory | AGENT_CAPABILITY | Scoped persistent-memory candidate | CANDIDATE; tenant isolation review |
| RI-AGT-006 | Langfuse | AGENT_CAPABILITY | Tracing/evaluation candidate | CANDIDATE; privacy/hosting review |
| RI-AGT-007 | OpenLIT | AGENT_CAPABILITY | Observability candidate | CANDIDATE; telemetry minimization |
| RI-AGT-008 | Agent Reach | AGENT_CAPABILITY | Research/agent integration candidate | CANDIDATE; adapter/terms review |
| RI-AGT-009 | Agency Agents | AGENT_CAPABILITY | Reusable specialist-agent patterns | CANDIDATE; quality/licence review |
| RI-AGT-010 | Superpowers | METHOD / AGENT_CAPABILITY | Engineering workflow skills | CANDIDATE; revision/licence review |
| RI-AGT-011 | Anthropic Skills / Matt Pocock Skills | AGENT_CAPABILITY | Reusable workflow patterns | CANDIDATE; scope/licence review |
| RI-AGT-012 | Graphify | AGENT_CAPABILITY | Codebase knowledge-graph candidate | CANDIDATE; no execution approved |
| RI-ENG-001 | REA — Reverse Engineer Anything MCP | SPECIALIST_TOOL | Broad lawful capability/workflow analysis | APPROVED_FOR_PREPARATION; no install/execute |
| RI-ENG-002 | HyperFrames | SPECIALIST_TOOL | AI Creative Studio video candidate | CANDIDATE; runtime review |
| RI-ENG-003 | ComfyUI | SPECIALIST_TOOL | AI Creative Studio media workflow candidate | CANDIDATE; compute/security/licence review |
| RI-DATA-001 | Coinbase Exchange public market-data docs | SOURCE | Crypto market-data semantics | CANDIDATE; public docs only |
| RI-DATA-002 | Binance Spot public market-data docs | SOURCE | Comparative market-data semantics | CANDIDATE; research source only |
| RI-DATA-003 | Frankfurter | SOURCE | Blended FX reference rates | CANDIDATE; not executable quotes |
| RI-DATA-004 | SEC EDGAR | SOURCE | US issuer filings | CANDIDATE; not Canadian filing substitute |
| RI-DATA-005 | OpenAlex | SOURCE | Scholarly metadata/discovery | CANDIDATE; usage limits review |
| RI-DATA-006 | DefiLlama | SOURCE | DeFi ecosystem context | HOLD pending endpoint/terms review |
| RI-DATA-007 | CoinGecko Demo API | SOURCE | Crypto reference data | HOLD for commercial integration; rights/limits constrain use |
| RI-METHOD-001 | Source-quality scorecard | METHOD | Source fitness and hard-stop assessment | APPROVED_FOR_PREPARATION |
| RI-METHOD-002 | Specialist desk coverage/handover protocol | METHOD | Shift continuity and honest coverage | APPROVED_FOR_PREPARATION |
| RI-METHOD-003 | PolyBot backtesting protocol | METHOD | Strategy evidence and falsification | APPROVED_FOR_PREPARATION; no backtest run |
| RI-METHOD-004 | Instrument classification matrix | METHOD | Product and halal issue classification | APPROVED_FOR_PREPARATION |

## 6. Model-provider policy

NVIDIA Build is optional. Preserve the model-agnostic architecture and avoid provider lock-in. Evaluate each model against named task benchmarks, recording quality, latency, context, tool reliability, privacy, terms, quotas, availability and total cost. Free developer access is not assumed commercially deployable, durable or unrestricted. Model outputs are drafts or hypotheses, not sources of truth. Models cannot grant permissions, approve their own work or control funds/trades.

## 7. Registry maintenance

New entries require exact identity, canonical locator and accountable steward. Material changes create a new version; preserve history. Licence/terms uncertainty means HOLD. Security/privacy incidents trigger quarantine. Expired scorecards become STALE. Similar names are not merged until identity is verified. Quarterly review is a target cadence, not a claim that reviews are scheduled or running.

## 8. Recipient boundaries

Trading receives approved market, capital-flow, instrument, strategy and technology intelligence. AI Revenue receives approved customer, product, competitor, pricing, distribution and creative-technology intelligence. Cross-recipient publication requires separate review. OCC receives aggregate health and approved references only.

## 9. Current disposition

This initial curated inventory is not exhaustive and is not an integration plan. J7 remains HOLD; Buildix and Santiment remain context-only candidates; NVIDIA is optional; Paperclip/Ruflo remain uninstalled preparation candidates; REA remains uninstalled and unexecuted. No API use, subscriptions, installations, connections, data jobs, tests or production dependencies are authorized.

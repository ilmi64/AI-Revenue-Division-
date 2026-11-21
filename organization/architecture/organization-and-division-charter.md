# Organization and Division Charter

**Status:** Canonical architecture baseline; implementation and staffing remain staged and unverified  
**Applies to:** Main Hub/OCC, AI Revenue Company, Trading & Technology Company, and the Research & Intelligence Division  
**Operating principle:** Build the two companies in parallel for a coordinated launch window; preserve independent authority, operations and launch decisions.

## 1. Organizational structure

The organization begins with two standalone operating companies, one central coordination layer, and one organization-level research division/shared service:

1. **AI Revenue Company** — a complete AI-native company, operated through its own AI executive leadership, departmental agent workforce, products/services, customer lifecycle, finance, security and operations.
2. **Trading & Technology Company** — a standalone specialist technology and trading company with its own executive leadership, engineering, market systems, data, finance, risk controls and operating workforce.
3. **Main Hub / Operations Control Centre (OCC)** — shared coordination, governance interfaces, approved infrastructure oversight, evidence reporting and organization-level visibility. It is not a parent executive team or company operator.
4. **Research & Intelligence Division** — an organization-level division/shared intelligence service, not a third operating company. It maintains its own leadership, workforce, research queue, knowledge governance and research records, and supplies scoped intelligence outputs to both companies and future divisions.

The operating-company registry remains exactly two companies. The Research & Intelligence Division is represented separately as an organization-level division/shared service.

The coordinated build method is specified in `parallel-build-launch-programme.md`: AI Revenue, Trading & Technology, Main Hub/OCC and Research & Intelligence proceed in parallel, with independent company launch decisions.

## 2. Parallel build and independent launch

- Build AI Revenue and Trading & Technology simultaneously, using parallel workstreams and their existing company prototypes, repositories, decisions and architecture. Do not restart either company from scratch.
- Target a coordinated January 2027 launch window, subject to each company's own readiness evidence.
- Neither company is a prerequisite, funding source, customer, supplier or operational dependency for the other's launch.
- Neither company must first generate revenue, receive customer payment, complete a customer delivery, or become operational before the other can launch.
- Each company owns its own launch decision and readiness gates. A delay or failure in one company must not block the other.
- AI Revenue's readiness is judged against its own AI-company operational, product/service, customer, security, finance and delivery requirements. No Trading & Technology condition is part of its launch gate.
- Trading & Technology's readiness is judged against its own technology, data, security, risk, paper-mode, exit protection, recovery, incident and rehearsal requirements. No AI Revenue condition is part of its launch gate.
- Company launch does not authorize live trading, external publishing, spending, or other separately gated actions. Trading live execution remains a distinct decision with its own owner approval.

## 3. Shared infrastructure boundary

The companies may use common infrastructure only to cooperate, reduce duplicated engineering and gain a competitive edge. Shared infrastructure does not merge the companies.

### Permitted shared foundations

- Reusable compute/runtime and deployment patterns when available within the no-spend policy.
- Model adapters and compatibility interfaces for Claude Code, Codex, Qwen, Llama, Gemini and other approved models/runtimes.
- Common orchestration technology such as the Paperclip workforce-control candidate and Ruflo orchestration candidate, with separate company configurations and identities.
- Common evaluation, tracing, observability and engineering standards.
- Approved research/intelligence products and scoped technical discoveries.
- Shared security baselines, interface contracts and non-sensitive reusable components.

### Required separation

- Separate company executives, decision rights, budgets, accounting, ledgers and financial records.
- Separate company agents/swarms, identities, task queues, memory, prompts/context, permissions, audit streams and operational control.
- Separate customer data, trading data, strategies, private company records and confidential work products.
- No default cross-company access to private data or memory.
- No agent, model, orchestration layer or Main Hub may grant itself access, change company policy, approve its own permissions or override company risk controls.
- Shared orchestration is a common platform only. Each company runs its own workforce/swarms and can operate if the other company's swarm, company or Main Hub is unavailable.
- If a specialist agent is ever loaned or delegated across a boundary, it must use an explicitly scoped task, minimum necessary data, separate receiving-company identity/context, an auditable handoff and owner-approved permissions. No implicit shared agent identity.
- A shared infrastructure outage must not create a shared operational dependency. Each company needs a bounded fallback and recovery path.

## 4. Main Hub / OCC

Main Hub/OCC provides:
- organization-level coordination and decision/commitment registers;
- approved company status summaries and evidence references;
- shared infrastructure inventory and dependency visibility;
- cross-company opportunity coordination using approved, non-confidential intelligence;
- incident visibility and escalation coordination without taking over company incident command;
- governance, security baselines and approval-state visibility;
- a record of organization-level decisions and the history of superseded decisions.

Main Hub/OCC does not:
- act as a parent company or shared executive;
- own either company's finance, private memory, customer records, trading records or risk decisions;
- move funds, place trades, publish content, contact customers, change accounts, deploy systems or approve consequential external actions;
- make one company's readiness or launch conditional on the other;
- become a single point of failure for company operations.

The initial OCC is read-only and evidence-oriented. Company adapters publish only allowlisted, authenticated, minimal summaries after the required security work is implemented.

## 5. Research & Intelligence Division

Detailed research governance, roles, specialist desks, source standards, archive rules, service catalogue and day/night handover are specified in `research-intelligence-division-charter.md`.

Research & Intelligence is a first-class organization-level division/shared service with its own:
- division leadership and research operations lead;
- specialist AI workforce, identities and task queue;
- scoped memory, research archives and knowledge base;
- source registry, provenance, timestamps, freshness, confidence and reliability grading;
- research methodology, evidence standards, historical records and handover process;
- day/night coverage plan, including the previously discussed Grok Desk and HyperGrok concepts;
- service catalogue, delivery records, escalation and quality review.

Its research portfolio preserves and extends prior work rather than starting again:
- crypto, market structure, capital flows, whale/smart-money and on-chain intelligence;
- Forex, indices, Gold and other approved market research;
- strategy discovery, bot capability analysis, reverse engineering and competitive benchmarking;
- technology, AI models, agents, orchestration, engineering and security research;
- customer, product, business-model, commercial and competitive intelligence for AI Revenue;
- risk, data quality, source reliability and organizational intelligence.

Named specialist research workstreams to preserve include REA (Reverse Engineer Anything), Crypto Capital Flow & Opportunity Intelligence, J7, Buildix.trade, Sanbase/Santiment, and the Grok Desk/HyperGrok concepts. Existing findings, registries and strategy agreements must be consolidated with provenance and confidence; do not silently discard or re-create prior research.

Research outputs are advisory intelligence, not company commands. They are delivered through scoped, company-appropriate interfaces. The division cannot access private company records by default and cannot make company executive, financial, customer, trading or risk decisions. Day/night continuous coverage is a target operating model, not a claim that a staffed or automated 24/7 service is already live.

## 6. AI Revenue Company — complete AI-native organization

AI Revenue is a full company, not a department or service provider for Trading & Technology. Its own AI executive team and workforce cover the full business lifecycle.

### Executive leadership

- CEO — company direction, priorities and accountable operating decisions.
- COO — operating system, delivery, service quality and cross-department execution.
- CFO — budgets, cash controls, accounting, pricing economics and financial reporting.
- CTO — product engineering, systems, model/runtime architecture and technical delivery.
- CMO — positioning, marketing, content and distribution.
- CRO — sales pipeline, partnerships, customer acquisition and commercial conversion.
- CHRO / Workforce lead — agent roles, staffing plans, performance and workforce governance.
- CISO — security, privacy, access control, incident readiness and recovery.
- Legal/compliance review — jurisdiction, contracts, IP, privacy, platform and regulatory issue spotting; escalates matters requiring qualified professional advice.

### Operating departments

1. **AI Product & Service Development** — identify needs, validate opportunities, define offers, build products/services and manage roadmaps.
2. **Engineering & Automation** — websites, workflows, integrations, internal tools, testing, deployment preparation and maintenance.
3. **AI Creative Studio** — creative strategy, promotional video, advertisements, social content, product visuals, branding and production workflows; HyperFrames and ComfyUI remain priority research/build candidates.
4. **Sales & Business Development** — prospect research, offer design, proposals, pipeline, partnerships and customer onboarding.
5. **Marketing & Distribution** — positioning, SEO, content systems, social distribution and campaign analysis. TikTok remains excluded unless explicitly reintroduced.
6. **Customer Success & Support** — onboarding, requirements, communications, support, retention and feedback.
7. **Delivery & Quality Assurance** — acceptance criteria, review, revisions, handover, service-level tracking and proof of completion.
8. **Business & Product Intelligence** — customer demand, competitor research, market gaps, pricing, product discovery and opportunity assessment, coordinated with Research & Intelligence through scoped outputs.
9. **Finance & Administration** — independent company books, budget, cash management, invoices, costs, profitability and reporting.
10. **Security, Privacy & Recovery** — company-specific access, secrets handling, data boundaries, backup, incident response and recovery.
11. **Workforce & Agent Operations** — separate company agent identities, roles, permissions, queues, memory, evaluations, supervision and handovers.

The company may build revenue through AI automation and digital services, websites and workflows, creative production, digital products, reusable software and later SaaS or other validated offers. These are opportunity tracks, not claims that the services are already built, sold or generating income.

## 7. Trading & Technology Company — standalone specialist organization

Trading & Technology has its own executive leadership, engineering and specialist workforce, financial controls, records, security and risk authority. Its internal specialist workstreams include:

1. **Crypto & PolyBot** — market/venue coverage, bot architecture, execution simulation, monitoring and strategy research.
2. **Forex** — currency-market data, strategy research, execution constraints and risk modelling.
3. **Indices** — index-market research, instruments, data quality and strategy validation.
4. **Gold / XAUUSD** — specialist market structure, data, volatility and risk research.
5. **Quantitative & Strategy Research** — hypothesis management, independent implementation, backtesting, paper validation and evidence grading.
6. **Market Data & Intelligence Integration** — source quality, timestamps, market data pipelines and approved intelligence ingestion.
7. **Crypto Capital Flow & Opportunity Intelligence** — fundraising, launches, VC/fund flows, whale movements, smart-money rotations, token unlocks, treasury activity and ecosystem capital flows.
8. **Bot Reverse Engineering & Competitive Intelligence** — REA-led lawful public/open-source capability discovery, architecture analysis, strategy mechanics, benchmarking and reproducible implementation specifications.
9. **Execution, Risk & Capital Protection** — independent limits, pre-trade checks, exposure controls, kill switches, exit protection and veto authority.
10. **Security, Incident Response & Recovery** — key isolation, system hardening, monitoring, incident containment, backups and recovery rehearsal.
11. **Finance & Administration** — separate company books, capital controls, operating costs, reporting and approved financial processes.
12. **Engineering & Infrastructure** — trading technology, adapters, observability, storage and reliability.

Flash loans and other specialist execution concepts remain research-only until independently modelled and reviewed, including fees, gas, slippage, MEV, smart-contract, counterparty and Shafi'i/halal considerations. No live execution is implied.

## 8. Shared AI workforce technology and model governance

- Paperclip remains the leading candidate for workforce management/control-plane functions.
- Ruflo remains the leading candidate for bounded multi-agent orchestration and swarms.
- Claude Code, Codex, Qwen, Llama, Gemini and other compatible model/runtime options are candidates to be integrated through verified adapters, MCP/API interfaces or local runtimes as appropriate.
- OpenHands remains a bounded engineering-agent candidate.
- AgentMemory, Langfuse and OpenLIT remain scoped memory/observability candidates.
- Compatibility, licensing, privacy, inference costs, compute requirements and data residency must be checked before adoption. Open source does not mean inference or hosting is free.
- No third-party tool is installed or executed merely because it appears in this architecture.
- Model outputs are proposals. Deterministic policy, least privilege, audit evidence and owner approvals remain outside model control.

## 9. Governance, evidence and approval controls

- Each company owns its own authority, policy, finances, memory, data, workforce and audit history.
- Research & Intelligence owns its own research methodology and archives, subject to organization-level security and scoped access rules.
- Shared infrastructure owners may maintain common components but cannot use infrastructure access to cross company boundaries.
- External actions, spending, paid APIs, paid credits, installations, deployments, publishing, account/permission changes, wallet actions, transfers, withdrawals, broker orders, live trading and third-party commitments remain approval-gated.
- No credentials, private keys, seed phrases, passwords or MFA codes are stored in research, OCC or model memory.
- Evidence records distinguish proposed, authored, reviewed, executed, verified and operational states. Documentation or a prototype is never described as a live service without evidence.

## 10. Current implementation posture and next build stages

This charter records the agreed organizational architecture; it does not assert that all divisions, agents, services or systems are staffed, deployed or operational.

Continue from the existing repositories and prototypes:
- AI Revenue architecture branch: `architecture/shared-ai-workforce-foundation` in `ilmi64/AI-Revenue-Division-`.
- Trading & Technology architecture branch: `architecture/shared-ai-workforce-integration` in `ilmi64/Solana-memecoins`.

Build in parallel:
1. Preserve and complete each company's existing organizational/workforce architecture and department-specific plans.
2. Formalize Research & Intelligence leadership, workstreams, knowledge governance, service catalogue and handover design.
3. Continue Main Hub/OCC M2 validation and then implement the read-only evidence presentation and company-specific adapters in gated stages.
4. Define separate company agent swarms on shared, bounded infrastructure with explicit identity, memory, task and permission isolation.
5. Build each company's independent readiness evidence and rehearsal plan for the coordinated launch window.

No paid services, package installations, GitHub Actions runs, merges, deployments, production connections, publishing or external commitments are authorized by this charter.

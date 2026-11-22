# Two-Company Architecture Reconciliation and Migration Map

**Status:** Proposed implementation contract; not deployed  
**Applies to:** Main Hub/OCC, Trading & Technology Company, AI Revenue Company  
**Companion:** `two-company-workforce-registry.json`  
**Launch objective:** January 2027 simultaneous activation, conditional on independent readiness gates

## 1. Target state

The target is two independent companies developed in parallel and coordinated through a shared Main Hub/OCC:

- **Trading & Technology Company:** its own AI CEO/executive functions, specialist market desks, finance, security, independent risk authority, task queues, records and operational workspace.
- **AI Revenue Company:** its own AI CEO/executive functions and AI-operated departments covering product/service development, engineering, creative production, research, sales, marketing, customer delivery, finance, support, QA, security, workforce management and administration.
- **Main Hub/OCC:** shared governance, coordination, security standards, evidence reporting and controlled shared-service interfaces. It does not merge leadership, funds, records or risk authority.

Paperclip remains the leading workforce control-plane candidate; Ruflo remains the leading swarm/orchestration candidate. Claude Code, Codex, Qwen, Llama, Gemini and other compatible models are replaceable worker runtimes, subject to individually verified adapters and permissions.

## 2. Legacy baseline findings

The existing OCC division registry is not the agreed target model. It lists eleven divisions under one organisation and places AI Revenue, Crypto, Finance, Risk, Technology and other functions within a single division-based structure. Its strategic-priority text also conflicts with the current equal-priority two-company agreement and includes Animora/Ecommerce as active workstreams.

The existing AI workforce proposal is useful but incomplete for the target:
- It defines one executive coordinator, a Qwen research analyst, a Llama reviewer candidate, a generic division specialist and a risk reviewer.
- The model registry records Qwen2.5 1.5B through Ollama as integrated in the main branch but not end-to-end verified; Llama 3.2 1B remains an uninstalled evaluation candidate.
- It does not yet define separate executive boards, company-specific agent registries, separate memory namespaces or complete AI Revenue departmental operations.

The existing risk-control proposal correctly keeps external and financial actions disabled, live trading disabled, and owner approvals mandatory. Those restrictions must be preserved and applied to both companies.

## 3. Migration mapping

| Legacy capability | Target placement | Required treatment |
|---|---|---|
| Executive Management / executive coordinator | Main Hub/OCC plus two separate company CEO roles | OCC coordinates; each company CEO owns its own company strategy and internal delegation. Owner retains reserved approvals. |
| AI Revenue division | Independent AI Revenue Company | Promote to a complete company with its own AI executive board, workforce, budget, ledger, memory, task queue and customer operations. |
| Crypto and PolyBot | Trading & Technology Company | Retain research/paper-only controls and independent trading risk authority. |
| Forex, indices and Gold/XAUUSD research | Trading & Technology Company | Specialist desks under Trading & Technology; preserve separate market/instrument readiness evidence. |
| Finance and Treasury | Separate company CFO/finance functions | Shared accounting standards/templates may be reused; no merged ledgers, funds, credentials or unilateral cross-company access. |
| Risk, Security and Recovery | Company-specific risk/security authority plus shared OCC standards | Trading risk veto remains independent; AI Revenue receives its own security, compliance and delivery-risk controls. |
| Technology and Infrastructure | Shared technical platform service | Shared generic code/adapters only; company workspaces, secrets, permissions and audit records remain separated. |
| Research and Intelligence | Shared methods/catalogue, isolated company workspaces | Source material and findings are shared only when permitted, scoped and logged. |
| Business & Commercial | AI Revenue commercial departments | AI Revenue owns its own pipeline, offers, sales, delivery and customer records. |
| Animora | Deferred project; not reactivated | Do not treat historical PR content as authorization to resume. |
| Ecommerce | Deferred project; not reactivated | Do not allocate active resources or treat historical PR content as authorization to resume. |
| AI Creative Studio | AI Revenue department | Continue no-cost preparation; it is not a third company and need not be complete for AI Revenue launch if another revenue stream qualifies. |

## 4. Required company-specific records

Before a company can be considered operational, it must have its own:
1. Executive and department registry with accountable AI roles.
2. Agent registry with model/runtime identity, version, permissions, owner, status and evidence.
3. Task queue and handoff acknowledgements.
4. Company-specific memory and knowledge namespace with access tests.
5. Budget, commitments, accounting ledger and verified cash-receipt evidence.
6. Audit log with authenticated actor identity, timestamp, scope and tamper-evident storage.
7. Risk register, incident process, stop conditions and recovery plan.
8. Customer/data classification and retention controls where applicable.
9. Tested workflow catalogue showing which routine tasks are autonomous, which require owner approval and which are prohibited.
10. Company readiness dossier with test evidence, unresolved gaps and explicit owner decision.

## 5. Shared platform implementation order

1. Reconcile the legacy OCC division registry and operating framework to the two-company target; preserve legacy records for traceability rather than silently overwriting history.
2. Define two company workspaces/tenants in the Paperclip evaluation design. If tenant isolation cannot be demonstrated, require separate instances.
3. Define Ruflo as a bounded orchestration layer, not an authority layer. Disable unattended autopilot, broad hooks, unrestricted tools and federation in the initial design.
4. Register model adapters individually: Claude Code, Codex, Qwen/Ollama, Llama/Ollama, Gemini and later alternatives. A model is not available merely because it appears in a list.
5. Establish company-scoped memory, logs and observability. No cross-company memory by default.
6. Add sandboxed engineering agents only after isolated execution, filesystem/network restrictions and secret redaction are verified.
7. Reuse existing deterministic OCC, risk and market-specialist components; do not replace deterministic controls with model consensus.
8. Run synthetic-data isolation, permission-denial, prompt-injection, model-outage, audit-integrity, recovery and cost-ceiling tests.
9. Conduct separate operational rehearsals for each company, then a cross-company coordination rehearsal.
10. Require separate readiness decisions and owner approval before simultaneous activation.

## 6. Minimum acceptance tests

- An AI Revenue agent cannot read Trading & Technology private files, memory, queue, secrets or ledger.
- A Trading & Technology agent cannot read AI Revenue customer records, pipeline, private files, memory, secrets or ledger.
- OCC can read only approved status/evidence summaries and cannot write to either company's ledger or change either company's permissions.
- A cross-company request without a valid scope and approval is denied and logged.
- A model or orchestrator cannot override deterministic trading HALT/STOP controls or the owner approval gate.
- A failed, stale, unavailable or malformed model response creates a blocked/review state rather than an invented success.
- Agent-generated tests are not counted as passed until actually executed and independently reviewed.
- The system records actual model/provider cost exposure; a free software licence is not treated as proof of free inference or hosting.
- Company-specific backups can be restored without exposing the other company's data.
- All external, financial, publishing, deployment, merge and live-trading actions remain denied absent the applicable explicit approval.

## 7. Status and non-claims

This migration map and registry are architecture artifacts only. They do not mean Paperclip or Ruflo has been installed, a swarm is running, company workspaces exist, agents are staffed, model adapters are connected, tests have passed, or either company is operational.

The January 2027 date remains a target, not a waiver. Extend the window only when evidence shows an unresolved safety, security, commercial or operational gate makes extension necessary.

## 8. Approval boundary

This change records the owner-approved architecture and migration plan. It does not authorize merges, workflow runs, software installation, paid inference, account/permission changes, deployments, external communications, financial transactions, publication or live trading.

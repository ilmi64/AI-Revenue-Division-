# Paperclip Role IDs and Organisation-Chart Configuration Draft

**Date:** 2026-11-21
**Status:** Architecture/configuration draft only — not imported, provisioned, installed, tested or activated.
**Companion:** Initial Workforce Roster and Tenant Blueprint; Workforce Parent–Child Task Envelope Contract.

## 1. Intent and topology

This catalogue converts the approved workforce roster into stable machine-friendly role identifiers and a first-pass organisation-chart draft. IDs define accountabilities, not agent accounts; no agents are created or authorized by this document.

Use two independent company tenants/instances as the safe default: ai_revenue and trading_technology. Shared Research & Intelligence and Security & Recovery use separately scoped service identities and explicit interfaces. Main Hub/OCC is a read-only consumer, not a privileged tenant.

## 2. Identifier conventions

- ar_ = AI Revenue; tt_ = Trading & Technology; ri_ = shared Research & Intelligence; sr_ = shared Security & Recovery; occ_ = read-only oversight.
- Lowercase ASCII snake_case; stable across model/provider changes.
- IDs identify accountability/permission profiles, not models, vendors, people or runtime instances.
- A worker may cover multiple roles only when each role is explicit in the task envelope and reviewer independence is preserved.
- Never repurpose a role ID for materially different authority. Agent instance IDs are issued by the deterministic identity service, never invented by a model.

## 3. AI Revenue tenant — ai_revenue

| Role ID | Display role | Reports to | Initial authority |
|---|---|---|---|
| ar_ceo | CEO / Executive Office | Owner | Internal strategy and coordination; no owner-reserved action |
| ar_coo | COO / Operations | CEO | Internal workflow and service coordination |
| ar_cfo | CFO / Finance | CEO | Approved finance inputs; draft budgets, forecasts and reconciliations |
| ar_cto | CTO / Engineering & Product | CEO | Architecture and engineering planning; no production release |
| ar_cmo | CMO / Marketing | CEO | Research and draft assets; no publishing or ad spend |
| ar_cro | CRO / Sales & Partnerships | CEO | Lead research and proposal drafts; no outreach or commitments |
| ar_chro | CHRO / Workforce | CEO | Role/capacity planning; no permission grants |
| ar_ciso | CISO / Security & Privacy | CEO, owner escalation | Security review and incident coordination; no unilateral destructive remediation |
| ar_legal_review | Legal & Compliance Review | CEO | Issue spotting/research; no legal sign-off |
| ar_product_delivery | Product & Service Delivery | COO | Delivery within approved internal scope |
| ar_customer_ops | Customer Operations | COO | Internal triage and response drafts; no customer contact |
| ar_admin | Administration & Records | COO | Internal documentation and records |
| ar_ai_creative_studio | AI Creative Studio | CTO / CMO | Creative drafts; no publishing or paid generation |
| ar_qa_reviewer | Independent Delivery QA | COO | Read-only review; cannot approve own work |
| ar_finance_controller | Finance Controller | CFO | Reconciliation/ledger drafts; no payments |
| ar_cost_analyst | Cost & Unit-Economics Analyst | CFO | Approved cost analysis and scenarios |
| ar_market_researcher | Market & Demand Researcher | CMO / CRO | Approved-source research; no customer data by default |
| ar_content_strategist | Content Strategist / SEO Analyst | CMO | Content/SEO drafts; no publishing |
| ar_opportunity_researcher | Opportunity & Lead Researcher | CRO | Public/approved lead research; no outreach |
| ar_platform_architect | Platform Architect | CTO | Architecture proposals and scoped review |
| ar_engineering_worker | Engineering Worker | CTO | Scoped sandbox changes only when separately authorized |
| ar_engineering_reviewer | Independent Engineering Reviewer | CTO | Read-only review; no merge/deploy |
| ar_workforce_planner | Workforce Planner | CHRO | Role/capacity recommendations; no provisioning |
| ar_security_analyst | Security Analyst | CISO | Read-only assessment; no secrets |
| ar_compliance_researcher | Compliance Researcher | Legal Review | Source-cited issue spotting; no legal sign-off |

## 4. Trading & Technology tenant — trading_technology

| Role ID | Display role | Reports to | Initial authority |
|---|---|---|---|
| tt_ceo | CEO / Executive Lead | Owner | Internal strategy and coordination |
| tt_coo | COO / Operations | CEO | Internal workflow, cadence and handovers |
| tt_cto | CTO / Trading Technology | CEO | Research-system architecture and engineering plans |
| tt_cfo | CFO / Finance & Capital | CEO | Separate books, budget and capital evidence drafts |
| tt_cro_risk | Independent Chief Risk Officer | Owner / independent risk line | Independent stop/veto; cannot be overridden by swarm consensus |
| tt_legal_review | Legal & Regulatory Review | CEO, owner escalation | Issue spotting and cited research; no legal sign-off |
| tt_crypto_research | Crypto Research Desk Lead | CEO / COO | Approved market/source research; paper-only |
| tt_forex_research | Forex Research Desk Lead | CEO / COO | FX research and paper hypotheses |
| tt_indices_research | Equity Indices Research Desk Lead | CEO / COO | Index research and paper hypotheses |
| tt_gold_research | Gold / XAUUSD Research Desk Lead | CEO / COO | Metals research and paper hypotheses |
| tt_quant_research | Quantitative Research & Simulation Lead | CTO; CRO oversight | Hypothesis/simulation design; no unapproved execution |
| tt_polybot_systems | PolyBot / Trading Systems Lead | CTO | Indicator/data-contract design; no live signal routing |
| tt_market_data_steward | Market Data & Source Integrity Lead | CTO; independent source review | Provenance, timestamps, units, gaps and freshness |
| tt_portfolio_intelligence | Portfolio & Capital Flow Intelligence Lead | CEO / COO | Capital-flow research; no wallet control |
| tt_risk_analyst | Risk Analyst | Independent CRO | Independent risk calculations and challenge |
| tt_strategy_challenger | Strategy Challenger / Falsification | Independent CRO | Read-only challenge; no self-approval |
| tt_performance_auditor | Independent Performance Auditor | Independent CRO | Read-only performance/data audit |
| tt_finance_controller | Finance Controller & Capital Ledger Steward | CFO | Ledger/reconciliation drafts; no transfers |
| tt_platform_architect | Trading Platform Architect | CTO | Architecture proposals |
| tt_data_engineer | Data Engineer | CTO | Synthetic/scoped data engineering only when approved |
| tt_engineering_worker | Engineering Worker | CTO | Scoped sandbox changes only when separately authorized |
| tt_engineering_reviewer | Independent Engineering Reviewer | CTO | Read-only review; no merge/deploy |
| tt_security_analyst | Trading Security Analyst | Security lead / CISO interface | Read-only assessment; no secrets or funds |
| tt_recovery_specialist | Trading Loss Recovery & Capital Reconciliation Specialist | Security & Recovery | Evidence review and case drafts; no fund movement or recovery guarantee |

Trading remains research/paper-only. No wallet, broker or exchange execution connections; no keys, signing, deposits, withdrawals, live orders or capital movement. CRO veto and deterministic risk controls are outside Ruflo authority.

## 5. Shared service identities — separate least-privilege scopes

| Role ID | Display role | Service scope | Initial authority |
|---|---|---|---|
| ri_head | Head of Research & Intelligence | Shared Research | Intake, priority and recipient-scoped assignment; no raw cross-company access |
| ri_operations | Research Operations Desk | Shared Research | Work-order routing, deadlines and delivery tracking |
| ri_grok_desk | Grok Desk / HyperGrok Research Lead | Shared Research | Evaluate research methods; no assumed API or continuous coverage |
| ri_source_steward | Source Stewardship & Verification | Shared Research | Registry, provenance, freshness, rights and source quality |
| ri_crypto_capital_flow | Crypto Capital Flow & Opportunity Intelligence | Shared Research | Recipient-scoped capital-flow research; no wallet control |
| ri_cross_domain | Cross-Domain Intelligence | Shared Research | Approved public-source research |
| ri_independent_challenge | Independent Challenge & Falsification | Shared Research | Read-only challenge with minimum necessary evidence |
| ri_knowledge_governance | Knowledge Governance Steward | Shared Research | Registry/retention proposals; no broad raw tenant access |
| sr_head | Head of Security & Recovery | Shared Security | Security governance and owner escalation |
| sr_identity_access | Identity & Access Governance | Shared Security | Review identity/permission proposals; cannot self-grant |
| sr_incident_response | Incident Response Coordinator | Shared Security | Triage, containment recommendations and evidence preservation |
| sr_backup_recovery | Backup & Recovery Steward | Shared Security | Backup/restore planning; no production restore without approval |
| sr_boundary_auditor | Cross-Company Boundary & Revocation Auditor | Shared Security | Read-only boundary audit; no cross-tenant browsing |
| occ_readonly | Main Hub / OCC Read-only Consumer | Oversight | Authenticated status/evidence read only; no commands, writes or approvals |

Shared-service identities receive a per-work-order recipient scope: one company, or a specifically approved sanitised cross-company summary. A shared role ID does not imply shared credentials, memory or access to both tenant datasets.

## 6. First-pass organisation chart

AI Revenue: Owner → ar_ceo → ar_coo (ar_product_delivery, ar_customer_ops, ar_admin); ar_cfo (ar_finance_controller, ar_cost_analyst); ar_cto (ar_platform_architect, ar_engineering_worker, ar_engineering_reviewer, ar_ai_creative_studio); ar_cmo (ar_market_researcher, ar_content_strategist); ar_cro (ar_opportunity_researcher); ar_chro (ar_workforce_planner); ar_ciso (ar_security_analyst); ar_legal_review (ar_compliance_researcher). Independent QA role ar_qa_reviewer reviews delivery outputs and does not approve its own work.

Trading & Technology: Owner → tt_ceo → tt_coo (tt_crypto_research, tt_forex_research, tt_indices_research, tt_gold_research, tt_portfolio_intelligence); tt_cto (tt_platform_architect, tt_data_engineer, tt_polybot_systems, tt_market_data_steward, tt_quant_research, tt_engineering_worker, tt_engineering_reviewer); tt_cfo (tt_finance_controller); tt_legal_review. Independent owner-facing veto line: tt_cro_risk (tt_risk_analyst, tt_strategy_challenger, tt_performance_auditor).

Shared Research & Intelligence, Security & Recovery and OCC remain separate service scopes, not subordinate to either company CEO.

## 7. Mandatory identity metadata

Every instantiated agent must receive externally issued immutable identity and validated metadata:

- company_id: ai_revenue | trading_technology | shared_research | shared_security | oversight
- role_id: one identifier from this catalogue
- agent_instance_id: externally issued immutable identifier
- role_version and service_scope
- recipient_scope: one company or approved sanitised summary
- parent_task_id, reviewer_role_id where applicable
- tool_allowlist and data_class_allowlist
- finite resource_ceiling and absolute deadline
- approval_state (denied by default), revocation_epoch and audit_correlation_id

This is a conceptual schema, not a validated Paperclip import format. Exact field names and adapter mappings must be verified against the selected release. Models cannot supply or override trusted identity, company, role, approval, budget or revocation fields.

## 8. Permission profiles

| Profile ID | Applies to | Default allowed | Explicitly denied |
|---|---|---|---|
| P_READ_RESEARCH | Research/intelligence | Approved source/file read, analysis, citations, internal drafts | Production writes, credentials, external messages, unrestricted browsing |
| P_INTERNAL_DOCUMENT | Admin/documentation | Internal draft preparation | Repository writes unless separately approved; publication |
| P_CODE_SANDBOX | Engineering | Scoped synthetic workspace and approved source files | Secrets, production, unrestricted shell/network, unapproved test execution, merge/deploy |
| P_FINANCE_DRAFT | Finance | Approved finance inputs, calculations and ledger drafts | Payments, transfers, purchases, account changes |
| P_MARKETING_DRAFT | Marketing/sales | Research and content/outreach drafts | Send, publish, ads, contracts, customer commitments |
| P_TRADING_PAPER | Trading research | Approved data, offline analysis and paper-only artifacts | Wallet/broker/exchange execution, signing, deposits, withdrawals, live orders, risk-policy edits |
| P_INDEPENDENT_REVIEW | QA/CRO/challenge/auditors | Read-only evidence necessary for review | Editing reviewed artifact, self-approval, permission changes |
| P_SHARED_RECIPIENT_SCOPED | Shared services | Minimum request/output fields for named recipient | Broad tenant browsing, shared credentials, unrestricted cross-company access |
| P_OCC_READONLY | Main Hub/OCC | Authenticated status/evidence read and display | Commands, writes, approvals, permissions, spending, publishing, funds, trades |

All profiles are default-deny. Runtime controls must be verified; labels and prompts do not enforce permissions. Paperclip adapter convenience defaults must be overridden with the most restrictive supported policy. Ruflo cannot grant tools or authority.

## 9. Mapping and acceptance sequence

1. Validate role IDs against the workforce charter and decision register.
2. Verify exact Paperclip version, supported organisation/role fields and import/export schema from official source documentation.
3. Produce separate tenant configuration files; do not merge company secrets, logs, memories or data stores.
4. Map each role to a reviewed adapter/runtime and permission profile.
5. Name accountable executive, independent reviewer and owner escalation for each consequential workflow.
6. Prepare synthetic negative cases: wrong-company identity, role mismatch, recipient-scope expansion, expired task, revoked agent, missing approval, self-approval and CRO-veto bypass.
7. Obtain explicit owner approval before installation, import, provisioning, tests, compute, account connections or permission changes.

## 10. Non-authorization and status

This draft does not create Paperclip organisations, users, agents, roles or tasks. It does not authorize installation, imports, tests, code execution, compute use, account connections, secret provisioning, repository permission changes, GitHub Actions, merges, deployments, external messages, publishing, spending, financial transactions, wallet/broker/exchange connections or live trading.

No role is currently staffed or operational. 24/7 Research & Intelligence coverage remains an unproven target, not a current capability.
# AI Revenue Company — Department Workforce & Agent Role Catalogue

**Status:** Design specification; no agents are installed, staffed or authorized by this document.  
**Company boundary:** AI Revenue Company only.  
**Authority:** AI Revenue CEO; deterministic company policy and owner approval gates remain controlling.  
**Operating mode:** Draft, research, analysis and local preparation by default.

## 1. Workforce design rules

Every agent identity is company-scoped and has a named accountable human/AI executive owner, role version, permitted tools, data classification, queue, output contract, review path, escalation route and expiry/revocation mechanism. A model is a replaceable runtime, not an identity or authority.

Agents receive least-privilege, task-bounded access. They cannot self-assign broader permissions, create external commitments, publish, contact prospects/customers, spend, change account permissions, deploy, or use paid APIs unless a separate explicit approval and technical control authorizes that exact action. Drafting a customer message is allowed; sending it is not. Preparing a release is not deploying it.

## 2. Executive and control agents

| Role ID | Agent role | Queue / core outputs | Review and KPI |
|---|---|---|---|
| AR-CEO | CEO Strategy & Portfolio | Strategy briefs, priority decisions, launch recommendation | Owner review for reserved decisions; strategic objectives and gate evidence |
| AR-COO | Operations Orchestrator | Department plans, dependencies, weekly operating pack, blockers | CEO review; on-time handoffs, unresolved blocker age |
| AR-CFO | Finance Controller | Cost ledger, unit economics, pricing models, cash-flow scenarios | Owner review for commitments; cost accuracy, margin visibility |
| AR-CTO | Architecture & Engineering Lead | Architecture decisions, technical plans, reliability risks | Security/peer review; change failure and defect rates |
| AR-CMO | Marketing Director | Positioning, channel plans, campaign briefs, analytics summaries | CMO/CEO review before publication; qualified reach and conversion evidence |
| AR-CRO | Revenue & Sales Director | Offer qualification, lead research, proposal drafts, pipeline records | Owner approval before contact/contract; qualified pipeline and close evidence |
| AR-WF | Workforce Manager | Role assignments, workload plans, handover and evaluation records | COO review; queue age, rework, coverage |
| AR-CISO | Security & Privacy Officer | Threat models, access reviews, incident playbooks, privacy checks | CTO/owner escalation; control coverage and incident closure |
| AR-COMP | Legal & Compliance Issue Spotter | Jurisdiction, IP, privacy, platform and consumer-law issue lists | Qualified counsel/owner review; unresolved issue tracking |

## 3. Department specialist roles

| Department | Specialist roles | Required deliverables |
|---|---|---|
| Product & Service Development | Customer Problem Researcher; Offer Strategist; Product Manager; Pricing Analyst | Evidence-backed problem briefs, buyer profile, scope/exclusions, acceptance criteria, pricing assumptions, roadmap |
| Engineering & Automation | Solution Architect; Full-stack Builder; Automation Engineer; Integration Analyst; Code Reviewer | Design, implementation proposal, threat model, tests authored, rollback notes, dependency inventory |
| AI Creative Studio | Creative Director; Visual Designer; Motion/Video Producer; Scriptwriter; Asset QA Reviewer | Creative brief, scripts/storyboards, editable asset plan, rights/provenance notes, QA checklist |
| Sales & Business Development | Market Mapper; Prospect Researcher; Qualification Analyst; Proposal Drafter | Source-cited prospect dossiers, fit score with rationale, proposal drafts, follow-up queue; no outbound sending |
| Marketing & Distribution | Brand Strategist; SEO Researcher; Content Planner; Channel Analyst; Community Listening Analyst | Brand rules, keyword/topic clusters, channel-native drafts, performance analysis; TikTok excluded unless owner reintroduces |
| Customer Success & Support | Onboarding Designer; Support Triage Analyst; Knowledge-base Curator; Feedback Analyst | Support taxonomy, response drafts, issue routing, FAQ updates; no direct customer replies without approval |
| Delivery & QA | Delivery Planner; Acceptance Tester; Accessibility Reviewer; Release Readiness Reviewer | Delivery plan, acceptance evidence, defect register, accessibility findings, release checklist |
| Business & Product Intelligence | Competitor Analyst; Demand Analyst; Trend Analyst; Customer Voice Synthesizer | Source/provenance-tagged intelligence, market gaps, demand signals, opportunity hypotheses |
| Finance & Administration | Bookkeeping Assistant; Cost Analyst; Invoice Drafting Assistant; Records Steward | Reconciled draft records, cost allocation, invoice drafts, retention schedule; no payment initiation |
| Security, Privacy & Recovery | Access Auditor; Data Steward; Backup Planner; Incident Analyst | Access map, data inventory, backup/restore plan, incident timeline and remediation proposals |
| Agent Workforce Operations | Queue Dispatcher; Runtime Evaluator; Prompt/Policy Librarian; Handover Coordinator | Queue health, model evaluations, versioned role/prompt records, handover packs |

## 4. Standard task lifecycle

1. Intake creates an immutable task ID, company ID, requester, objective, scope, sensitivity, due date, source references and requested action class.
2. Dispatcher selects a role by capability and permitted scope, not by model brand.
3. Agent receives only the task payload and explicitly allowlisted context.
4. Agent returns a structured deliverable, sources, assumptions, uncertainty, risks, files changed (if any), and recommended next action.
5. Independent reviewer checks factual support, quality, policy compliance and acceptance criteria.
6. Deterministic policy gate classifies any proposed external action. Reserved actions require explicit owner approval for the exact action.
7. Accepted output is versioned into company-owned records; rejected work is returned with reason and preserved history.

## 5. Queue taxonomy

- `AR-INTAKE`: new requests and triage.
- `AR-PRODUCT`: product/service research and definition.
- `AR-ENGINEERING`: build plans, code review and automation design.
- `AR-CREATIVE`: scripts, design, motion and creative QA.
- `AR-PIPELINE`: lead research and proposal preparation.
- `AR-MARKETING`: SEO, content and distribution planning.
- `AR-DELIVERY`: customer delivery preparation and QA.
- `AR-SUPPORT`: support drafts and feedback analysis.
- `AR-FINANCE`: internal financial analysis and draft records.
- `AR-SECURITY`: security, privacy and recovery work.
- `AR-EXEC-REVIEW`: cross-department decisions and launch evidence.

Each queue has an owner, priority, SLA target, retry limit, dead-letter state, escalation threshold and retention rule. Queue names do not imply permission to execute.

## 6. Department operating cadence

Daily when active: intake triage, critical blocker review, delivery/incident queue review and handover. Weekly: CEO/COO portfolio review, CFO cost and margin review, CRO pipeline review, CMO channel review, CTO/CISO reliability and security review, workforce quality review. The cadence is a design target until staffing and monitoring are proven.

## 7. Minimum KPIs

Measure accepted-output rate, first-pass acceptance, rework rate, task age, missed handoffs, evidence completeness, source freshness, cost per accepted deliverable, gross margin by offer, customer outcome/acceptance, incident rate and policy-blocked action attempts. Do not optimize for raw agent volume or unreviewed content output.

## 8. Launch and isolation

AI Revenue launch requires its own viable offer, delivery capability, support path, financial records, security/recovery controls, evidence of customer value and explicit owner authorization. It does not require Trading & Technology, Main Hub/OCC or Research & Intelligence to be live. Its workforce, customer data, finance, memory, queues, policies and audit trail remain private to this company.

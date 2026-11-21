# Ruflo Bounded Swarm Profile Registry — Draft

**Date:** 2026-11-21
**Status:** Architecture/configuration draft only — not installed, imported, executed or tested.
**Authority:** Parent task issued by the relevant company control plane plus deterministic identity/policy service. Ruflo is a subordinate orchestrator, never an authority issuer.

## 1. Global execution contract

Ruflo may decompose and coordinate specialist work only after validating a live parent-task envelope. If validation is unavailable, stale, ambiguous, expired or revoked, the profile does not run.

- Parent company_id, recipient_scope, task purpose, data classification, tool allowlist, resource ceiling, deadline, approval state, reviewer independence, revocation epoch and audit ID are immutable inputs.
- Every child receives the intersection of parent permissions, role permissions and policy permissions. No child may widen scope, tools, data, budget, deadline or approval state.
- Child count, nesting depth, concurrency, retries, wall-clock duration and total resource consumption must have finite externally enforced ceilings.
- Parent cancellation, expiry, incident, policy denial or revocation cancels all descendants and prevents new child creation.
- Ruflo cannot issue identity, grant tools, approve spending, modify policy, change risk limits, self-approve or alter audit records.
- Child outputs are proposals/evidence. The parent owner remains accountable; independent reviewers remain separate from authors.
- No unattended autopilot, daemon/background workers, federation, broad hooks/plugins, arbitrary MCP tools or unrestricted shell/browser/network.
- No credentials, secrets, wallet keys, broker/exchange access or production data by default.
- No tests, code execution, deployments, external messages, publishing or paid compute unless separately approved.

## 2. Common bounded profile fields

Each profile instance must bind to:

- profile_id and profile_version
- parent_task_id and externally validated company_id
- one recipient_scope and service_scope
- permitted role IDs and reviewer role ID
- allowed input references and data classifications
- tool_allowlist and network/source allowlist (empty unless explicitly approved)
- max_children, max_depth, max_parallel, max_retries
- wall_clock_deadline and finite resource/cost ceiling
- output schema, evidence/citation requirements and audit correlation ID
- approval_state, revocation_epoch and cancellation signal

These are conceptual policy fields, not asserted native Ruflo configuration keys. Map them to actual controls only after release-specific documentation and enforcement tests. Prompt instructions are not enforcement.

## 3. Profile registry

| Profile ID | Use | Permitted child roles | Required sequence | Output |
|---|---|---|---|---|
| RUFLO_RESEARCH_SYNTHESIS | Company-scoped research synthesis | Relevant desk researcher, source steward, independent challenger, synthesizer | Scope check → source retrieval → specialist analysis → independent challenge → synthesis | Cited report with confidence, conflicts and unknowns |
| RUFLO_SOURCE_VERIFICATION | Verify a specific factual claim or source set | Source steward, domain researcher, independent challenger | Claim decomposition → source provenance/freshness → independent corroboration → disposition | Claim/source ledger and unresolved gaps |
| RUFLO_ENGINEERING_REVIEW | Review a scoped design or code artifact | Platform architect, engineering reviewer, security reviewer if requested | Read-only inspection → specialist findings → independent review → consolidated recommendations | Review report and proposed patch outline; no write by default |
| RUFLO_QUANT_HYPOTHESIS | Develop and challenge a Trading research hypothesis | Relevant market desk, quant researcher, market-data steward, independent CRO delegate/challenger | Define hypothesis → validate data semantics → counter-hypothesis → risk challenge → paper-test plan | Hypothesis card, assumptions, data requirements and falsification plan |
| RUFLO_POLYBOT_CONTRACT_REVIEW | Review indicator/data-contract semantics | PolyBot systems, market-data steward, quant researcher, independent challenger | Contract extraction → edge-case inventory → data-source challenge → risk review | Contract discrepancy report; no implementation or signal routing |
| RUFLO_BUSINESS_DELIVERY | Prepare an AI Revenue internal deliverable | Product/service delivery, domain specialist, QA reviewer, finance analyst when relevant | Approved brief → draft → independent QA → economics/constraint review → handover | Internal draft, QA findings and delivery/economics evidence |
| RUFLO_MARKET_OPPORTUNITY | Research AI Revenue demand/opportunities | Market researcher, opportunity researcher, source steward, compliance reviewer | Public-source discovery → evidence/fit assessment → challenge → prioritised shortlist | Evidence-backed opportunity brief; no outreach or commitment |
| RUFLO_SECURITY_REVIEW | Review architecture, access or incident procedures | Security analyst, identity/access reviewer, boundary auditor, independent reviewer | Scope confirmation → read-only review → threat/impact analysis → challenge → recommendations | Threat/risk report and remediation proposals; no secret access or destructive action |
| RUFLO_RI_CROSS_DOMAIN | Shared Research & Intelligence work order | RI operations, relevant specialist, source steward, independent challenger | Recipient validation → minimum-data intake → research → challenge → recipient-scoped output | Recipient-specific intelligence report; sanitised cross-company output only if approved |
| RUFLO_OCC_EVIDENCE_SUMMARY | Prepare a read-only status summary | OCC read-only consumer and source-specific evidence validator | Verify signed envelope → freshness/revision checks → summarize only validated fields | Read-only status summary; invalid/stale evidence quarantined |

## 4. Hard-deny profile constraints

### Trading & Technology
- All Trading profiles are research/paper-only. No wallet, broker or exchange execution adapters; no keys, signing, deposits, withdrawals, live orders or capital movement.
- No strategy agent or swarm can modify risk limits, stop controls, kill switches, CRO authority or approval rules.
- The independent CRO veto is an external parent-policy condition. A veto cancels/blocks the affected strategy workflow; majority vote cannot reverse it.
- Data gaps, stale timestamps, mixed units, ambiguous venue semantics or unverified source provenance produce skip/escalation, not inferred safety.

### AI Revenue
- Business and creative profiles may draft internal work only. No customer contact, sending, publishing, paid promotion, contracts, purchases, payment actions or production releases.
- Finance profiles can calculate and draft records only; no account changes or movement of money.
- Customer or personal data is excluded unless a separate owner-approved scope, lawful basis, data minimisation and retention controls are established.

### Shared services and OCC
- Shared Research & Intelligence receives only minimum necessary, recipient-scoped inputs. No general cross-company search or shared memory.
- Security & Recovery reviews identity, boundaries and recovery evidence; it does not gain broad tenant data access or unilateral authority to move funds.
- OCC is read-only. It cannot command, assign, approve, grant access, write to company systems or override executives/CRO/owner.

## 5. Suggested bounded defaults for future synthetic pilot

These are conservative design ceilings for a later owner-approved synthetic pilot, not current runtime settings or authorization:

| Control | Proposed ceiling |
|---|---:|
| Maximum child tasks per parent | 6 |
| Maximum nesting depth | 2 |
| Maximum concurrent children | 3 |
| Automatic retries | 0; retry requires parent revalidation |
| Parent wall-clock duration | 15 minutes |
| Child wall-clock duration | 5 minutes |
| Network access | Deny by default; explicit source allowlist only |
| Filesystem | Read-only scoped synthetic fixture by default |
| Secrets | Deny all |
| External side effects | Deny all |
| Trading execution actions | Hard deny |
| Paid resource use | Hard deny under current zero-spend rule |

Any actual values must be reconciled with host quotas, provider limits and task complexity before use. Exhaustion or timeout terminates safely; no automatic escalation to a paid tier or larger resource budget.

## 6. Cancellation, revocation and failure semantics

1. Validate the parent envelope and current revocation epoch before orchestration and before every child dispatch.
2. Validate child role, recipient scope, tool/data intersection, resource budget and expiry before dispatch.
3. Propagate parent cancellation, expiry, incident hold, CRO veto and policy revocation to all descendants.
4. On timeout, tool error, missing source, schema violation or budget exhaustion: stop the affected branch, preserve audit evidence, mark incomplete and return a reason-coded failure.
5. Never retry with broader permissions, a different tenant, a new source class, longer deadline or higher budget without a newly approved parent envelope.
6. Preserve independent review: an author cannot be its own challenger, QA reviewer or final approver.

## 7. Synthetic acceptance cases — not executed

- Child attempts to change company_id or recipient_scope: reject.
- Child requests a tool not in parent ∩ role ∩ policy: reject.
- Child asks for broader data classification or a cross-company dataset: reject.
- Parent expires or is cancelled while children run: cancel descendants and reject late outputs.
- Revocation epoch changes between dispatch and tool call: deny and quarantine output.
- Strategy worker attempts to bypass CRO veto or edit risk limits: hard deny and incident log.
- Agent attempts self-approval, budget increase, permission grant or audit deletion: hard deny.
- Missing/stale source or conflicting venue units: return incomplete/skip, never assert safe.
- OCC attempts write/command/approval: hard deny.
- Any profile attempts paid API, cloud upgrade, purchase, publication, customer message or financial transaction: deny pending separate explicit owner approval.

These cases are specifications only. No tests or runtime calls have been performed or authorized.

## 8. Mapping and activation gates

Before any import or execution: verify Ruflo release and exact configuration schema; inspect plugins, hooks, MCP tools, adapters and daemon behavior; establish external identity/policy enforcement; map each profile to actual restricted tool permissions; demonstrate cancellation/revocation; validate company isolation; prove immutable audit and finite budgets; and obtain explicit owner approval for installation, compute and synthetic tests.

## 9. Status and non-authorization

No Ruflo profile is installed, configured, imported, executed or tested. No agents are provisioned. This document does not authorize installation, tests, compute consumption, API use, repository workflow runs, account connections, secrets, permission changes, merges, deployment, publication, customer contact, spending, financial transactions, wallet/broker/exchange connections or live trading. The 24/7 Research & Intelligence objective remains a target pending persistent compute, monitoring, coverage, restart/recovery and handover evidence.
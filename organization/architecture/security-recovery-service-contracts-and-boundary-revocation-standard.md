# Security & Recovery Service Contracts and Boundary/Revocation Standard

**Date:** 2026-11-21
**Status:** Architecture contract draft — not implemented, tested, provisioned or operational.
**Classification:** First-class shared organisation-level Security & Recovery Division plus company-scoped security units. Independent from Research & Intelligence and Main Hub/OCC.

## 1. Purpose and authority

Security & Recovery (S&R) protects the confidentiality, integrity, availability and recoverability of both independent companies and their shared services. It provides identity/access governance, security review, incident coordination, boundary audits, backup/recovery standards and Trading Loss Recovery & Capital Reconciliation expertise.

S&R has an independent escalation path to the owner. It can recommend or initiate a pre-authorized safe stop/containment only where a future implementation has a separately approved deterministic control. This draft itself grants no runtime access or incident command capability. S&R cannot move funds, sign transactions, trade, make payments, contact third parties, delete evidence or perform destructive remediation without explicit authority.

Research & Intelligence's independent challenge function is not a substitute for security review. OCC remains read-only and cannot command S&R or change permissions.

## 2. Service catalogue and contracts

| Service ID | Service | Inputs | Outputs | Hard boundary |
|---|---|---|---|---|
| SR-IDENTITY | Agent and service identity governance | Approved role/task identity requests, company scope, policy revision | Identity lifecycle decision, role mapping and audit record | Cannot self-approve, self-provision or grant broader access |
| SR-ACCESS | Least-privilege access review | Proposed tool/data/network permissions and task envelope | Allow/deny recommendation, expiry and review record | No secret disclosure; no authority inferred from model prompts |
| SR-BOUNDARY | Cross-company isolation audit | Tenant configuration, synthetic access logs and policy evidence | Boundary findings, negative-test plan and remediation proposal | No broad cross-tenant browsing or production probing |
| SR-REVOCATION | Cancellation and revocation coordination | Incident/policy trigger, identity, revocation epoch and descendant map | Revocation event, descendant cancellation evidence and audit | Cannot revive revoked identity or reduce epoch |
| SR-THREAT | Threat modelling and secure design review | Scoped architecture, dependency list, trust boundaries | Threat model, severity/risk register and mitigations | Read-only by default; no unapproved scans or exploit tests |
| SR-INCIDENT | Incident intake and coordination | Alert, report, system status and evidence references | Incident record, triage, containment recommendation, escalation | No evidence destruction, external contact or irreversible action without approval |
| SR-BACKUP | Backup and restore governance | Data inventory, backup policy and recovery requirements | Backup plan, restore evidence, RPO/RTO and gap report | No production restore or deletion without explicit approval |
| SR-TRADING-RECOVERY | Trading Loss Recovery & Capital Reconciliation | Owner-approved case evidence, transaction references, account statements and incident timeline | Evidence ledger, reconciliation, recoverability assessment and case options | No keys, signatures, transfers, recovery guarantee or direct counterparty contact |
| SR-PRIVACY | Data classification, retention and deletion review | Data inventory, purpose, jurisdiction and retention needs | Classification, minimisation and retention recommendations | No collection of personal/customer data without approved basis |
| SR-RESILIENCE | Continuity and disaster recovery | Dependency map, host/service health and recovery evidence | Runbooks, failover plan and rehearsal report | No production failover or paid capacity activation without approval |

## 3. Company and shared-service boundary model

Distinct security principals and policy namespaces are required for:

- AI Revenue company tenant and its agent identities, repositories, records, customer/commercial data and finance.
- Trading & Technology company tenant and its agent identities, research, market data, strategies, risk controls and finance.
- Shared Research & Intelligence service, with request-scoped recipient permissions.
- Shared Security & Recovery service, with minimum necessary evidence access and separate company case scopes.
- Main Hub/OCC, with authenticated read-only status/evidence envelopes only.

Shared infrastructure does not imply shared authority or unrestricted shared data. Default-deny applies between every scope. If a platform cannot demonstrate isolation, use separate instances or stronger external isolation rather than relying on labels or prompts.

Each access grant must be bound to one company_id, one service_scope, one recipient_scope, one role_id, one task/parent_task, an allowlisted tool/data set, an expiry, an approval reference, a policy revision and an audit correlation ID.

## 4. Identity lifecycle contract

Lifecycle states: REQUESTED → REVIEWED → APPROVED_LIMITED → ACTIVE → SUSPENDED → REVOKED → RETIRED. Invalid transitions are rejected. Approval and activation are separate states.

Identity issuance and policy validation belong to a deterministic service outside the model and outside Ruflo. An identity record must bind:

- immutable principal_id and agent_instance_id;
- company_id and service_scope;
- role_id and role_version;
- recipient_scope and parent_task_id;
- tool_allowlist, data_class_allowlist and network/source allowlist;
- finite resource ceiling and absolute expiry;
- approval_state, approver reference and policy_revision;
- revocation_epoch and audit_correlation_id.

Models and orchestration workers may request a narrower scope but cannot create or alter trusted identity fields, extend expiry, raise budgets, add tools, change company_id or modify approval state.

## 5. Revocation and descendant cancellation protocol

1. A valid revocation trigger is recorded with source, timestamp, affected principal/task, reason and severity.
2. The deterministic policy service increments the relevant revocation epoch and marks the principal/task revoked or suspended.
3. Every tool gateway checks the current epoch before dispatch and before accepting consequential results; cached approval is insufficient.
4. Parent-task revocation, expiry, cancellation or incident hold propagates to all child tasks, subagents, queued jobs and delegated tokens.
5. Queued work is cancelled; running work receives a cancellation signal; outputs arriving after revocation are quarantined and cannot be published or acted upon.
6. Credentials/tokens are invalidated through their approved issuer; no secrets are copied into incident logs.
7. Audit records capture trigger, actor, scope, epoch transition, descendants, tool outcomes, cancellation acknowledgements and any residual uncertainty.
8. Restoration requires a new review and new approval; a revoked identity is never silently reactivated.

If any gateway cannot confirm current policy/revocation state, it fails closed. A network partition or policy-service outage must not cause cached permissions to become broader or remain valid indefinitely.

## 6. Incident severity and response workflow

| Severity | Example | Required response |
|---|---|---|
| S0 Critical | Suspected secret/key exposure, unauthorized transaction, cross-tenant data leak, compromised signing/execution path | Stop affected workflow; preserve evidence; owner escalation immediately; no recovery action or fund movement without separate approval |
| S1 High | Policy bypass, identity compromise, revoked worker still executing, material integrity tampering | Suspend affected principal/workflow; investigate scope; notify owner and affected company lead |
| S2 Moderate | Source/adapter drift, isolated data exposure without confirmed exfiltration, backup failure, suspicious dependency | Contain within approved authority; create remediation plan; track until independently verified |
| S3 Low | Documentation defect, non-sensitive configuration drift, minor service degradation | Queue corrective action; monitor and document |

Incident lifecycle: DETECTED → TRIAGED → CONTAINMENT_PROPOSED → CONTAINED (only with evidence) → INVESTIGATING → RECOVERY_PLANNED → RECOVERY_APPROVED → RECOVERED (verified) → CLOSED. Closure requires evidence, residual-risk statement, reviewer and owner/authority disposition.

Never claim an incident is contained, recovered or closed solely because an agent reported success. Require independent evidence and readback.

## 7. Trading Loss Recovery & Capital Reconciliation protocol

### 7.1 Case classes

- Operational failure: incorrect process, data, system, configuration or settlement handling.
- Unauthorized access or transaction: suspected compromise, account misuse or transaction not authorized by the owner.
- Fraud, theft or custody issue: evidence of deception, misappropriation or custody failure.
- Payment/settlement error: duplicate, misdirected, delayed or mis-reconciled movement.
- Ordinary market/strategy loss: adverse price movement, volatility, slippage or strategy underperformance without evidence of operational wrongdoing.

All categories may be investigated, but ordinary market/strategy loss is not represented as recoverable. No recovery guarantee, recovery-agent solicitation, advance fee, seed phrase disclosure, signature request, revenge trading, martingale, leverage or chasing losses.

### 7.2 Case record and evidence

Record case_id/version, company and owner, event time, discovery time, classification, asset/currency, amount and units where verified, platform/venue, transaction references, account statement references, wallet/public address only when necessary, source evidence, timeline, access/approval records, communication evidence, known gaps, chain of custody, analyst and independent reviewer.

Do not request or store private keys, seed phrases, passwords, MFA codes, signing payloads or remote-control access. Redact personal and account identifiers not needed for the case.

### 7.3 Reconciliation and action boundary

Reconcile opening balance + verified inflows − verified outflows ± documented adjustments = closing balance. Distinguish booked, pending, failed, reversed, disputed and unverified entries. Record currency/network/asset units and valuation timestamp; do not combine unlike assets or infer missing values.

Permitted preparation: evidence inventory, discrepancy report, timeline, official support-channel research and draft correspondence. Prohibited without separate owner approval: submitting claims, contacting exchanges/banks/authorities, moving funds, signing transactions, changing security settings or paying recovery services.

## 8. Backup, restore and resilience contract

Each company must maintain separate backup scopes and encryption/access ownership. A backup plan defines data inventory, classification, frequency, retention, encryption, access, offline/immutable copy where feasible, integrity verification, restore owner, RPO, RTO, dependencies and deletion policy.

Restore is not proven by a successful backup job. Acceptance requires documented restore into an isolated target, integrity comparison, application-level validation, access-control verification and reviewer sign-off. No production restore, failover or paid storage/compute activation is authorized by this draft.

## 9. OCC and R&I interfaces

- R&I submits source/evidence quality incidents to S&R when integrity, privacy, rights, identity or security concerns arise; S&R owns security disposition.
- S&R may provide sanitized incident/readiness status to OCC through authenticated envelopes; raw case data remains company-scoped.
- OCC may display status and raise an owner-facing alert but cannot issue commands, grant permissions, approve remediation, suppress incidents or override the CRO.
- Trading CRO remains independently empowered to block Trading research/strategy progression under its own risk mandate; S&R does not replace or subordinate the CRO.

## 10. Future acceptance matrix — not executed

| Test case | Expected result | Evidence required |
|---|---|---|
| AI Revenue principal requests Trading data | Deny and audit | Denial event with both scopes and policy revision |
| Trading principal requests AI Revenue customer records | Deny and audit | Denial event; no data returned |
| Shared R&I request has no recipient | Reject | Validation error and no child task |
| Parent task revoked while child runs | Cancel child; quarantine late output | Epoch change, cancellation and quarantine records |
| Tool gateway has stale policy cache | Deny | Fail-closed trace |
| OCC attempts write or command | Deny | Read-only enforcement evidence |
| Revoked principal presents old token | Deny | Token/epoch validation record |
| Backup exists but restore integrity differs | Fail recovery acceptance | Comparison and unresolved discrepancy |
| Recovery case is ordinary market loss without operational evidence | Classify accurately; no recovery promise | Case rationale and source references |
| Agent attempts to access secrets or signing material | Deny; incident if attempted | Redacted policy/audit record |

These are future synthetic acceptance cases only. No tests or probes have been run or authorized.

## 11. Implementation dependencies and activation gates

Before implementation: define authoritative identity issuer, policy decision point, tool enforcement gateways, signed revocation events, descendant registry, audit storage, key management, tenant-specific backup/restore and incident escalation. Verify the chosen runtime's actual enforcement behavior; Paperclip and Ruflo are not substitutes for the deterministic security layer.

Before activation: owner-approved synthetic tests; independent security review; cross-tenant negative tests; cancellation/revocation proof; audit tamper controls; secret redaction; incident tabletop; backup/restore rehearsal; RPO/RTO acceptance; company executive and owner approval.

## 12. Non-authorization and current state

This document does not create identities, provision agents, connect accounts, access secrets, scan production, run tests, change permissions, install software, deploy services, use paid compute, contact third parties, submit claims, move funds, restore production systems or authorize trading.

No S&R service is represented as live by this design. Existing charters, incident standards, Trading recovery playbook and loss-recovery case template remain controlling companion artifacts; reconcile before implementation and preserve their prior evidence.
# Workforce Parent–Child Task Envelope Contract

**Date:** 2026-11-21  
**Status:** Draft interface contract for architecture review; not implemented, tested, signed, or deployed.  
**Scope:** Paperclip candidate control plane → Ruflo bounded orchestration → specialist workers → company-scoped audit/OCC reporting.

## 1. Purpose

Ensure that a specialist agent or swarm can do no more than the company-authorized parent task permits. Company identity, recipient scope, data classification, tools, budget, deadline, approval state and revocation must be enforced by deterministic services outside model prompts.

This contract complements the shared workforce architecture, hosting matrix and initial workforce roster. It does not make Paperclip or Ruflo a security boundary by themselves.

## 2. Trust boundaries

1. **Owner / company authority:** approves the relevant action or delegation.
2. **External identity and policy service:** issues/validates agent identity, policy decision, scope and revocation state.
3. **Paperclip candidate:** manages company org, task, role, approval and run lifecycle; cannot independently grant authority.
4. **Ruflo candidate:** decomposes and coordinates work inside the signed parent envelope; cannot widen scope.
5. **Worker runtime/model:** performs only the task and tools permitted by the effective envelope.
6. **Audit/OCC publisher:** receives signed, minimal status evidence; OCC remains read-only.

If the policy service, identity evidence, signature, tenant identity, expiry, revocation state or audit correlation cannot be verified, the task is denied or quarantined.

## 3. Required parent envelope fields

| Field | Required meaning | Enforcement |
|---|---|---|
| schema_version | Version of this contract | Reject unknown incompatible versions |
| envelope_id | Unique immutable envelope identifier | Deduplicate/replay protection |
| company_id | Exact owning company identity | Immutable; cannot be model-selected |
| service_scope | Approved company department or shared service | Must match approved service identity |
| recipient_scope | Company/team/person the result is intended for | Prevent unintended cross-company disclosure |
| task_id / parent_task_id | Parent task and lineage | Every child links to one valid parent |
| issuer_identity | Deterministic issuing authority | Must be authenticated and authorized |
| agent_identity | Agent ID, role ID, runtime and version | Must be active and mapped to a role |
| reviewer_identity | Independent reviewer for required review gates | Must differ from author for critical review |
| objective | Bounded task objective | Must be within parent task |
| allowed_actions | Explicit action allowlist | Deny all unlisted actions |
| allowed_tools | Exact tool names and operation scopes | Deny wildcard or unapproved tools |
| data_classification | Maximum permitted data sensitivity | Child cannot increase classification |
| data_references | Approved source/file IDs and access scope | No ambient filesystem or account access |
| budget_ceiling | Maximum compute/API/tool cost and currency | External metering; stop at ceiling |
| runtime_ceiling | Maximum elapsed execution duration | Hard timeout and cancellation |
| child_depth / child_count | Maximum delegation depth and fan-out | Enforced by orchestrator/policy service |
| approval_state | Required approvals and current signed status | No action before required approval |
| issued_at / not_before / expires_at | Validity interval | Reject early, expired or clock-invalid envelope |
| revocation_epoch | Current policy/identity revocation generation | Re-check before child execution and side effects |
| audit_correlation_id | End-to-end audit link | Required on all events and outputs |
| source_revision / policy_revision | Exact task, role and policy revisions | Prevent silent policy drift |
| signature | Cryptographic signature over canonical envelope | Verify issuer, integrity and audience |

No actual secret, API key, wallet key, password, session cookie or private credential is carried in the envelope. It may carry a secret reference only where the approved runtime retrieves it through a separate least-privilege secret broker; current default is no secrets available to research and coding agents.

## 4. Child inheritance rules

Every child envelope is derived from its parent by deterministic intersection, never by model-authored expansion.

- company_id must be identical to the parent.
- service_scope and recipient_scope must remain the same or become narrower under an explicitly approved shared-service contract.
- allowed_actions and allowed_tools = parent allowlist ∩ child role allowlist ∩ current policy allowlist.
- data classification may stay the same or decrease, never increase.
- data references must be a subset of parent-approved references.
- budget ceiling must be less than or equal to the parent's remaining budget.
- runtime deadline must be no later than the parent's expiry.
- child depth and fan-out must remain within parent limits.
- approval state cannot become more permissive than the parent state.
- reviewer identity cannot be replaced by the author or the agent being reviewed.
- child identity must be independently authenticated and mapped to an active company role.

If a child needs broader scope, the current task stops and a new parent task with fresh owner/company approval is required. Ruflo must not negotiate or infer permission expansion.

## 5. Action classes

### Class R — read and reason
Read explicitly approved source data; perform analysis; draft findings. No external writes.

### Class D — draft internal artifact
Create a proposed internal document, code patch or report in a scoped draft area. No merge, publish, send or deployment.

### Class T — execute approved synthetic test
Run a pre-authorized test against synthetic data in an isolated test environment. This class remains disabled until explicit owner approval for the specific pilot and environment.

### Class E — consequential external action
Send messages, publish content, contact customers, change account permissions, install/activate external services, spend, purchase, move funds, submit orders, connect wallets/brokers/exchanges, deploy or otherwise affect external systems. Always deny by default. Requires separate explicit owner approval and applicable company/risk/compliance gate; parent task consent alone is insufficient.

Trading-specific execution, wallet signing and live order actions remain hard-denied by this contract.

## 6. Required lifecycle

1. Company executive creates/approves parent task in its own company tenant.
2. Policy service validates issuer, company, role, action class, data scope, resource ceilings, approval state and current revocation epoch.
3. Signed parent envelope is issued to the approved orchestration runtime.
4. Ruflo decomposes only within the parent objective and requests child envelopes.
5. Policy service derives each child envelope by intersection and signs it.
6. Worker runtime verifies signature, identity, scope, expiry and tool permissions before each task.
7. All tool invocations, denials, outputs, child creation, cancellations and policy changes emit correlated audit events.
8. Independent reviewer checks required work without authoring or approving its own output.
9. Company executive receives result and evidence; external actions remain separately gated.
10. Minimal signed status is published to read-only OCC with source revision, sequence, timestamp, digest and freshness.

## 7. Cancellation, revocation and incident behavior

- Parent cancellation or expiry cancels all descendants and revokes outstanding child envelopes.
- Agent suspension, company identity change, policy revision, security incident or revocation-epoch change invalidates outstanding envelopes.
- Workers must re-check policy before every tool call that can access data or change state, not only at startup.
- On lost connection to the policy/revocation service, no new child work or side-effecting tool call is allowed. Read-only local work may be retained only if explicitly permitted by the offline policy; default is stop and checkpoint.
- Audit events are append-only and cannot be edited by the agent whose actions they record.
- Recovery requires a new authorized envelope; a model cannot resume itself after revocation.

## 8. Minimum denial cases for future synthetic acceptance tests

Tests are proposed but **not authorized or executed**. The future owner-approved synthetic pilot must prove denial for:
- child changes company_id;
- child attempts to read another company's data;
- child requests tool not in parent allowlist;
- child raises data classification;
- child exceeds parent budget, deadline, depth or fan-out;
- child attempts to mark an unapproved action as approved;
- worker uses expired, revoked, replayed or wrong-audience envelope;
- parent is cancelled while child is running;
- policy service is unavailable;
- agent attempts to access secrets, wallet, exchange, payment, customer-contact or publishing tools without specific approval;
- reviewer is same identity as author on a required independent review;
- stale or mismatched policy/source revision is supplied.

Passing a synthetic pilot would be necessary but not sufficient for production readiness.

## 9. Trading-specific hard boundaries

- Trading research workers have read-only access to approved datasets and paper-simulation interfaces.
- No wallet connections, private keys, signing, deposits, withdrawals, broker/exchange credentials or real orders.
- Risk limits, stop conditions, position constraints and CRO veto are owned by deterministic company risk policy, not by the strategy agent, Paperclip, Ruflo or model.
- A strategy, model, swarm consensus or profitability claim cannot grant trading permission.
- Missing/stale/ambiguous market data produces skip/escalation, not inferred permission to trade.

## 10. Explicit non-authorization

This contract is a design artifact only. It does not authorize installation, API calls, identity provisioning, keys, compute execution, tests, synthetic pilot execution, repository workflow runs, permissions changes, production data access, deployment, external actions, spending or trading.

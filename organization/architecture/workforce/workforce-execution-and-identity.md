# AI Revenue — Workforce Execution & Identity Architecture

**Status:** Architecture specification only; no workforce runtime, identities, credentials or production queues are deployed.
**Scope:** AI Revenue Company only.
**Default posture:** Deny external actions; internal scoped work only.

## 1. Design principles

The AI Revenue workforce is a company-owned tenant. Every agent, task, queue, memory namespace, tool grant and audit event is bound to `ai_revenue`. Shared model providers or orchestration software do not create shared authority or shared memory with Trading & Technology. The company must continue safely if Paperclip, Ruflo, a model provider, Research & Intelligence or the OCC is unavailable.

Paperclip remains the leading workforce-management candidate; Ruflo remains the bounded orchestration candidate. Neither is a security boundary. Deterministic enforcement sits in a company-controlled policy gateway outside model prompts.

## 2. Agent identity lifecycle

Each agent receives an immutable internal principal ID, company ID, role, department, permitted queues, capability profile, data classification ceiling, approved runtime/model adapter, owner, creation record and lifecycle state. IDs are never recycled. Human-readable names are labels, not identities.

Lifecycle: PROPOSED → REVIEWED → ACTIVE_SCOPED → SUSPENDED → REVOKED or RETIRED. Activation requires company owner/delegated administrator approval, least-privilege capability review and a recorded policy version. Suspension immediately denies new claims and external operations; revocation invalidates grants and queued leases. Re-enablement requires a new review. Credential rotation/revocation is a future implementation requirement; no live credentials are created by this document.

Each runtime receives short-lived, audience-bound, task-scoped grants where supported. No shared root token, shared service account, model-visible secret, cross-company credential or long-lived agent key. Secrets belong in a dedicated secret manager when one is later approved; they never enter prompts, task bodies, logs or OCC snapshots.

## 3. Role-to-queue and capability assignment

| Department / accountable role | Primary queues | Permitted work profile |
|---|---|---|
| COO / Operations | AR-INTAKE, AR-EXEC-REVIEW | Triage, routing, capacity and escalation |
| Product lead | AR-PRODUCT | Customer-problem research, requirements, offer briefs |
| CTO / Engineering | AR-ENGINEERING | Local code/design drafts, bounded repository work, technical review |
| Creative Director | AR-CREATIVE | Scripts, visual concepts, asset briefs, rights checklist |
| CRO / Sales | AR-PIPELINE | Market and prospect research, proposal drafts; no sending |
| CMO / Marketing | AR-MARKETING | SEO, content and channel drafts; no publishing |
| Delivery lead | AR-DELIVERY | Internal delivery plans, QA evidence and acceptance packs |
| Customer Success | AR-SUPPORT | Support analysis and response drafts; no customer contact |
| CFO / Finance | AR-FINANCE | Internal cost, pricing and reconciliation analysis; no payments |
| CISO / Security | AR-SECURITY | Threat analysis, access review and incident recommendations |
| CEO / Executive review | AR-EXEC-REVIEW | Company decisions and readiness review; no bypass of owner gates |

A capability is an explicit tuple of action, resource, scope, environment, data class and expiry. Queue membership alone grants no tool access. Agents receive only the smallest capability set needed for a task. Cross-department delegation is a handoff, not inherited access.

## 4. Assignment, review and separation of duties

The queue service assigns work using role fit, declared capability, current load, conflict rules and priority. An agent cannot assign itself elevated permissions. The task creator cannot be the sole approver of its own consequential action. The producing agent cannot be the sole reviewer of its deliverable.

Engineering changes require an independent reviewer and security-sensitive review where applicable. Creative/marketing outputs require rights/brand checks; financial analysis requires independent reconciliation; customer-facing material requires a separate quality/compliance review. CEO review does not replace owner approval. For any high-impact task, reviewers must be distinct principals and record their own evidence and rationale. If staffing does not permit independence, the task remains BLOCKED for review rather than self-approved.

## 5. Durable task lifecycle

Canonical states: DRAFT → READY → CLAIMED → IN_PROGRESS → REVIEW → ACCEPTED → CLOSED. Alternate terminal or paused states: BLOCKED, CANCEL_REQUESTED, CANCELLED, DEAD_LETTER, EXPIRED. Every transition records task ID/version, company, actor principal, previous/new state, timestamp, policy version, reason and evidence references.

Claim uses a bounded lease with owner, expiry and monotonically increasing fencing token. Expired leases may be reclaimed only after the previous token is invalidated. A stale worker cannot commit after losing its lease. Task mutations use optimistic version checks. Every task has an idempotency key scoped to company and operation; duplicate submissions return the existing outcome rather than repeating side effects.

Retries are bounded by failure class and attempt budget. Read-only transient retrieval may retry with capped exponential backoff and jitter. Policy denial, identity mismatch, schema failure, data-scope violation, approval expiry, reviewer rejection and external-action failure are not blindly retried. Dead-letter entries preserve original task reference, attempts, failure class, last safe state and disposition. Cancellation blocks new work and invalidates leases; already-started local computation may finish only if safe, but cannot publish or contact anyone.

## 6. Company-local policy and approval enforcement

The policy gateway evaluates principal, task, resource, action, environment, data classification, current risk state, approval record and policy version. Missing or unavailable policy service means deny. Model text, task content, a Paperclip role, a Ruflo workflow or a reviewer statement cannot override this gateway.

Owner approvals are exact, scoped, time-limited and single-use. The signed approval record binds approver identity, action digest, exact target/destination, content or payload digest, amount/cost ceiling if relevant, environment, expiry, nonce and policy version. A changed payload, target, timing, price or scope requires a new approval. Approval is consumed atomically before dispatch; uncertain dispatch is reconciled, never blindly replayed. Draft approval is not send/publish approval.

Standing restrictions remain: no spend, paid API, subscriptions, purchases, customer/prospect contact, publication, account/permission changes, deployments, destructive changes or external commitments without separate explicit owner approval. No approval in this architecture enables financial action by itself.

## 7. Memory, data and audit boundaries

Company memory namespaces are partitioned by department/project/customer with explicit ACLs, retention and deletion policy. Customer data is purpose-limited and excluded from general model training or unrelated tasks. Agent memory is not an authority source; stale or untrusted memory must be revalidated against current records.

Append-only company audit records capture identity issuance/revocation, task transitions, policy decisions, approvals, tool calls, handoffs, reviewer decisions, failures and recovery. Audit integrity, retention and backup require a later production design. OCC receives only allowlisted aggregate counts and sanitized event summaries.

## 8. Recovery and outage behaviour

On orchestrator/model outage, stop new dispatch and preserve durable task state. On policy-gateway or identity-service outage, deny actions and do not fall back to model judgment. On queue-store uncertainty, freeze claims until consistency is restored. On suspected compromise, suspend affected principal/runtime, revoke grants, quarantine impacted tasks and preserve evidence. Recovery requires company-authorized review and reconciliation of leases, idempotency keys, approvals and outbox state. No automatic failover may broaden permissions.

## 9. Acceptance gates before production

- Tenant isolation proven with adversarial cross-company and cross-department tests.
- Identity lifecycle, expiry, revocation and credential rotation demonstrated.
- Policy enforcement tested independently of prompts and orchestration.
- Lease fencing, idempotency, retry limits, cancellation and dead-letter recovery demonstrated.
- Reviewer independence and approval binding enforced atomically.
- Audit integrity, backup/restore and incident recovery rehearsed.
- No external-action path exists without exact owner approval.
- Company can operate in safe degraded mode without OCC, Research or shared orchestration.

All gates are NOT_RUN until supported by recorded evidence. This specification is not proof of implementation or operational readiness.

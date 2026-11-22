# AI Revenue — Canonical Operation Taxonomy and Policy Profile

**Status:** Documentation-only policy design; not implemented, enforced, tested or deployed.  
**Company:** `ai_revenue` only.  
**Companion:** `organization/security/policy-gateway-integration-and-gap-closure-plan.md`  
**Default:** deny unless an exact operation, resource, scope, identity, task and policy rule explicitly allow it. CAD $0 incremental spend.

## 1. Purpose and authority

This taxonomy gives the AI Revenue policy gateway a stable vocabulary for classifying requested operations. It resolves ambiguity between task actions (READ, RESEARCH, DRAFT, ANALYZE, LOCAL_FILE_PREPARATION) and real capabilities at the scheduler, runtime, data, cost and external-action boundaries.

It does not grant permissions, create owner approvals, change budgets, or authorize execution. The deterministic policy service remains outside model and orchestrator control. The owner retains approval authority. A task's allowed-action list is necessary but never sufficient.

## 2. Operation record required for every request

A policy request must identify, at minimum:

- `operation_id`: canonical value from this taxonomy; unknown values deny.
- `company_id`: exactly `ai_revenue`.
- `principal_id`, role, runtime, session and authenticated identity reference.
- `task_id`, queue, task status, assignment, expiry and immutable task-scope digest.
- `resource_type`, exact resource identifier and resource revision where applicable.
- `data_classification`: PUBLIC, INTERNAL or CONFIDENTIAL_COMPANY.
- `action_scope`: exact fields, files, records, recipients or destinations touched.
- `cost_cad`: exact upper bound including inference, tool, compute, hosting, transfer and third-party charges; unknown cost is not zero.
- `approval_class` and single-use approval reference when the operation is eligible for approval.
- `policy_version`, nonce, idempotency key, request digest and trusted timestamps.
- `requested_effect`: read-only, local-only mutation, or external side effect.

Missing, contradictory, stale, untrusted or unbounded fields deny. Model-generated claims are not trusted evidence.

## 3. Operation classes

| Class | Canonical operations | Initial disposition |
|---|---|---|
| Read-only research | `AR.READ.PUBLIC_SOURCE`, `AR.READ.COMPANY_SCOPED`, `AR.RESEARCH.WEB`, `AR.RESEARCH.COMPETITOR`, `AR.RESEARCH.CUSTOMER_NEEDS` | Allow only within assigned task, approved source class and data boundary; company-private data remains tenant-scoped |
| Analysis | `AR.ANALYZE.DATASET`, `AR.ANALYZE.WORKFLOW`, `AR.ANALYZE.OFFER`, `AR.ANALYZE.PERFORMANCE` | Allow on authorized data; preserve provenance and avoid unsupported claims |
| Drafting | `AR.DRAFT.CONTENT`, `AR.DRAFT.PROPOSAL`, `AR.DRAFT.CUSTOMER_RESPONSE`, `AR.DRAFT.CREATIVE_BRIEF` | Allow as an internal draft only; no send, publish or customer contact |
| Local preparation | `AR.FILE.READ`, `AR.FILE.CREATE_DRAFT`, `AR.FILE.UPDATE_APPROVED_BRANCH`, `AR.CODE.PREPARE_DIFF`, `AR.DATA.PREPARE_SYNTHETIC` | Allow only within approved workspace/path and task scope; no production or protected branch changes |
| Internal evaluation | `AR.QA.STATIC_REVIEW`, `AR.QA.OFFLINE_REVIEW`, `AR.PRODUCT.PROTOTYPE_REVIEW` | Allow only for offline, non-billable, non-deploying review |
| External communication | `AR.CUSTOMER.CONTACT`, `AR.LEAD.OUTREACH`, `AR.SOCIAL.PUBLISH`, `AR.CONTENT.DISTRIBUTE`, `AR.SUPPORT.SEND` | Deny by default; requires a separate, exact owner approval and destination/content review before any future implementation |
| Commercial commitments | `AR.CONTRACT.ACCEPT`, `AR.QUOTE.COMMIT`, `AR.ORDER.PLACE`, `AR.REFUND.ISSUE`, `AR.CUSTOMER.DATA.EXPORT` | Deny by default; separate legal, privacy, finance and owner gates required |
| Spend and billing | `AR.PAID_INFERENCE`, `AR.PAID_API`, `AR.PURCHASE`, `AR.SUBSCRIPTION.CREATE`, `AR.HOSTING.UPGRADE`, `AR.AD.SPEND`, `AR.PAYMENT.INITIATE` | Hard deny under current CAD $0 policy; an ordinary task approval cannot override the budget restriction |
| Account/security changes | `AR.CREDENTIAL.CREATE`, `AR.PERMISSION.CHANGE`, `AR.SECRET.READ`, `AR.KEY.ROTATE`, `AR.ACCOUNT.CONNECT` | Deny; privileged owner/security procedure required, secrets never enter model context |
| Production changes | `AR.DEPLOY`, `AR.PRODUCTION.WRITE`, `AR.DOMAIN.CHANGE`, `AR.REPOSITORY.MERGE`, `AR.GITHUB_ACTIONS.RUN` | Deny absent separate explicit authorization; deployment and production controls are distinct from code preparation |

## 4. Approval classes and non-overridable rules

- **A0 — Read-only:** no external side effect; still requires identity, task, source and data-scope checks.
- **A1 — Internal draft/preparation:** local-only, reversible and confined to an explicitly approved workspace. No production branch, external publication or account change.
- **A2 — External communication/publication:** requires exact content, destination, account, timing and scope approval immediately before dispatch.
- **A3 — Commercial/legal/customer-data action:** requires exact counterparty, terms, amount/currency or data fields, jurisdictional review where relevant, and separate owner approval.
- **A4 — Financial/spend/security/production action:** requires a distinct privileged owner procedure and the relevant CFO/security/technical control. Current CAD $0 and no-deployment restrictions remain hard denies.

Approval is not transferable across companies, tasks, recipients, resources, amounts, currencies, policy versions or time windows. Any material change requires a new approval. Agent consensus, executive-agent approval or an approval reference supplied by a model is not owner authorization.

## 5. Universal hard-deny conditions

Deny if any of the following applies:

- Unknown operation, wildcard permission, ambiguous resource or scope expansion.
- Company identity is missing or is not `ai_revenue`.
- Identity, task, policy, owner authority, clock, audit or revocation state is missing, stale, unauthenticated or unavailable.
- Task is not assigned, is cancelled/expired, or the requested operation is outside its exact scope.
- Cost is unknown, exceeds the current zero-CAD budget, or may trigger an unapproved billable event.
- Request would expose credentials, secrets, private customer data or another company's data to an unauthorized principal or model.
- Request bypasses the scheduler, runtime/tool gateway, data gateway, cost meter, approval authority, audit or external-action gateway.
- Request attempts to alter policy, issue its own approval, modify another principal's authority, erase audit evidence or disable security controls.
- Required approval is absent, expired, revoked, replayed, mismatched or not durably consumed.
- An external outcome is ambiguous; do not automatically resend.

## 6. Enforcement mapping

| Boundary | Required check |
|---|---|
| Scheduler | Identity, role, company, active assignment, task scope and task expiry |
| Runtime/tool gateway | Canonical operation allowlist, exact resource, no direct-tool bypass |
| Data gateway | Company tenant, classification, field-level scope, read/write distinction |
| Cost meter | Preflight total cost; deny unknown or positive spend under current policy |
| Approval authority | Owner-only authentication, exact binding, nonce and expiry; agents cannot mint approvals |
| Outbox/external-action gateway | A2–A4 approval, single-use consumption, final recheck, idempotency and destination binding |
| Audit sink | Record allow and deny decisions, source revisions, policy version and reason codes; audit failure blocks consequential work |

## 7. Relationship to existing task schema

The existing AI Revenue task schema remains the task-envelope contract. Its `allowed_actions` values (READ, RESEARCH, DRAFT, ANALYZE, LOCAL_FILE_PREPARATION) are coarse task capabilities, not gateway operation IDs. The gateway must require both a permitted coarse action and a specific canonical operation from this taxonomy. Its `excluded_actions` and `AI_REVENUE_DEFAULT_DENY` profile remain restrictive and must not be weakened by this document.

## 8. Change control and open decisions

- Taxonomy changes require versioned owner-approved change control, impact review and audit.
- Adding an operation never implies that it is allowed; its initial disposition is deny until an explicit policy profile is reviewed.
- Before PG-2/PG-4 integration, reconcile this taxonomy against the actual SQLite approval fields, trusted façade types, task scheduler contract and every enforcement point.
- Define exact approval evidence and jurisdictional review for customer data, commercial commitments and Canadian consumer/privacy obligations.
- No runtime, database, API, account or external connection is authorized by this document.

**Current disposition:** canonical vocabulary drafted for review. No policy enforcement, tests, approvals or production capability is claimed.

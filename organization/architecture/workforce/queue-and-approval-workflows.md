# AI Revenue — Queue Operations & Approval Workflows

**Status:** Operating design; no production queue service is deployed.  
**Company:** AI Revenue only.  
**Default:** Internal drafting and preparation; external actions denied until individually approved.

## 1. Queue topology

| Queue | Accountable owner | Intake examples | Exit condition |
|---|---|---|---|
| AR-INTAKE | COO | New request, incident, idea | Classified, scoped and routed |
| AR-PRODUCT | Product lead | Customer problem, offer hypothesis | Evidence-backed brief accepted |
| AR-ENGINEERING | CTO | Build request, defect, integration | Reviewed implementation artifact and release checklist |
| AR-CREATIVE | Creative Director | Campaign asset, script, video concept | Creative package passes rights and quality review |
| AR-PIPELINE | CRO | Market/lead research, proposal request | Qualified dossier or approved proposal draft |
| AR-MARKETING | CMO | SEO, content and channel request | Channel-ready draft and measurement plan |
| AR-DELIVERY | Delivery lead | Accepted customer scope | QA and acceptance evidence complete |
| AR-SUPPORT | Customer Success lead | Feedback, support issue | Draft response/knowledge update reviewed |
| AR-FINANCE | CFO | Cost, pricing, invoice or cash question | Reconciled analysis or draft record |
| AR-SECURITY | CISO | Access, privacy, threat or incident | Risk disposition and remediation plan |
| AR-EXEC-REVIEW | CEO | Cross-department decision, launch gate | Decision recorded with evidence and owner |

## 2. Priority and service targets

P0: active security/privacy/customer-harm incident or imminent integrity failure; interrupt normal work and escalate immediately. P1: launch-critical blocker or committed delivery risk; same operating day triage when staffed. P2: normal planned work; assign by capacity and due date. P3: backlog/improvement; schedule after P0–P2. These are target policies, not evidence of staffed coverage.

## 3. Standard handoff

A task can move only when the current owner supplies a structured handoff: task ID, sending/receiving queue, reason, completed work, unresolved questions, source/evidence refs, data classification, deadline, acceptance criteria and next accountable role. The receiving queue acknowledges acceptance. Rejected handoffs return to sender with a reason. No silent queue transfer.

## 4. Review separation

The agent that produces a deliverable should not be its sole reviewer. Engineering changes require peer review; marketing and creative outputs require brand/rights review; finance outputs require reconciliation/review; customer-facing drafts require CRO/Customer Success review. High-impact company decisions go to the executive review queue.

## 5. Approval classes

- A0 Internal read/research/draft: allowed within task scope.
- A1 Local artifact preparation: allowed on approved working branch/path, with diff and rollback note.
- A2 External publication, customer/prospect contact, platform changes or public release: denied by default; requires explicit owner approval for the exact content, destination and timing.
- A3 Spending, paid API, subscription, purchase, payment, contract, financial commitment or account permission change: denied by default; requires separate explicit owner approval and cost/terms review.
- A4 Production deployment, destructive action, credential/key operation or irreversible data change: denied by default; requires explicit owner approval, security review, backup/rollback and exact target confirmation.

Approval records bind to action digest, actor, target, scope, expiry, single-use nonce and policy decision. An approval for a draft is not approval to send/publish it; an approval for one target does not authorize another.

## 6. Dead-letter and retry

Transient failure may retry only within configured bounded attempts and backoff. Policy denial, schema failure, identity mismatch, data-classification violation or approval expiry is not retryable automatically. Dead-letter records preserve original task, failure class, attempts and reviewer disposition. Never retry external actions automatically.

## 7. Customer delivery lifecycle

Research/qualification → offer and scope draft → owner approval of proposal/terms → delivery plan → internal build → independent QA → owner approval to deliver/publish/contact → customer acceptance evidence → support handoff → finance record. No customer data is copied into shared Research/OCC by default.

## 8. Daily/weekly operations

Daily when staffed: P0/P1 incident and blocker review, queue aging, handoff acceptance, delivery QA. Weekly: portfolio, pipeline, margin, channel performance, delivery quality, security and workforce evaluation. Missed coverage is explicitly recorded.

## 9. Metrics

Queue age by priority, acceptance/rejection rate, handoff delay, rework, task completion evidence, approval-blocked attempts, customer acceptance, delivery defects, unit economics and policy violations. Raw agent output volume is not a success metric.

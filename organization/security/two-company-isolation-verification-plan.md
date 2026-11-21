# Two-company isolation verification plan

Status: proposed acceptance plan; not executed against a deployed system.
Applies independently to AI Revenue and Trading & Technology.

## Security invariants
1. Each company has its own immutable company identifier, executive authority,
   agent assignments, task queue, memory namespace, ledger, audit stream,
   approval issuer and policy version.
2. Shared infrastructure is a transport/orchestration layer only. It receives
   the minimum scoped task envelope and cannot infer or grant authority.
3. Main Hub/OCC receives summary and health data by default, not private
   prompts, memory, customer records, account data, credentials or ledger rows.
4. Every data read, write, tool call, handoff, export and external action is
   authorized server-side against trusted identity and company scope.
5. Missing identity, policy, tenant context, audit service or revocation state
   fails closed.
6. Cross-company work is denied unless an owner-approved, time-bounded,
   resource-specific delegation exists. Delegation cannot grant broader scope
   than the originating authority.
7. Trading risk controls, halt state, capital limits and live-execution denies
   cannot be modified by AI Revenue, OCC summaries, agent consensus or model
   output.
8. A company cannot issue, revoke, consume or inspect the other company's
   approvals or audit events.
9. Secrets are company-scoped and denied to shared orchestration by default.
10. No company can use the other company's credentials, budget or external
    identity to perform an action.

## Required adversarial verification
- Tenant ID spoofing in task payload, headers, metadata and tool arguments.
- Agent attempts to read another company's memory, ledger, customer records,
  audit events, secrets or task queue.
- Shared scheduler retries a task under the wrong tenant context.
- Child task attempts to widen parent scope or change company ID.
- Cross-company delegation expired, revoked, replayed or resource-mismatched.
- OCC requests raw records rather than permitted summary fields.
- AI Revenue attempts Trading halt, risk-limit, wallet, order or funds actions.
- Trading agent attempts AI Revenue customer, publishing or billing actions.
- Cache, vector index, object-store path, logs and backup restore tenant leakage.
- Database query missing tenant predicate; test with adversarial identifiers.
- Queue dead-letter, trace export, crash dump and error report leakage.
- Identity issuer, policy service, audit sink or key service unavailable.
- Company deletion, restore, key rotation and employee/agent offboarding.
- Concurrent requests with interleaved company contexts.

## Pass criteria
Every unauthorized read/write/action is denied before data is returned or side
effects occur; denial is audited in the correct company stream without leaking
the protected value. Authorized summary sharing returns only allowlisted fields.
Tests must include negative assertions and side-effect counters, not just
expected response codes. Run against the actual deployed database, cache,
queue, vector store, object store, model gateway and tool gateway before
claiming isolation.

## Evidence required
For each test retain test ID, build/version, policy version, tenant identities,
sanitized request, expected/actual decision, side-effect counter, audit event
ID, reviewer and timestamp. Synthetic unit tests alone do not establish
infrastructure isolation.

## Current status
Architecture and acceptance criteria only. No deployed multi-tenant runtime,
database, cache, queue, vector store, secrets service or model gateway has
been verified. No isolation control is certified as passed.

# Security Control-Plane Reference Implementation — Static Review

**Review type:** Read-only static review of existing repository reference modules and their contracts.  
**Execution status:** No Python executed; no tests run; no services started.  
**Scope:** Trading & Technology branch `architecture/shared-ai-workforce-integration`. AI Revenue contains mirrored counterparts for the shared control-plane modules.  
**Purpose:** Convert existing tangible code artifacts into a precise implementation backlog without mistaking reference code for production enforcement.

## 1. Executive finding

The repository already contains more than architecture prose: it includes offline reference modules for policy evaluation, policy gateway enforcement, synthetic identity/approval verification, transactional SQLite approval consumption, and hash-linked audit records, alongside acceptance-test files and production-contract documents.

These artifacts form a useful reference implementation chain, but they are explicitly offline/synthetic or local prototypes. They are not a deployed trusted control plane. The next step is integration and assurance work, not a fresh rewrite or an install.

**Current state:**
- Policy engine: offline deterministic reference; mutable in-memory replay/revocation/cancellation state.
- Policy gateway: deterministic orchestration point with injected identity, emergency-stop, policy-version and approval-consumer callbacks; deny-by-default on callback exceptions.
- Identity: HMAC fixture-key demonstration; not a production key/issuer system.
- Owner approval: exact-scope signed demonstration plus a separate SQLite one-time consumption ledger.
- Audit: in-memory hash-linked reference plus a per-company hash-linked approval audit table; neither is a complete production audit platform.
- Acceptance tests: authored files exist, but this review did not execute them and no pass claim is made.

## 2. Module-by-module findings

### 2.1 Offline policy decision engine

**Artifact:** `docs/security/reference_policy_engine.py`

Existing controls observed statically:
- Rejects malformed input, unavailable policy, expired/revoked identity, company mismatch, cancelled task and active/unverified emergency stop.
- Requires operation allowlisting and resource-prefix scope.
- Enforces cost caps and a market-data provenance flag.
- Hard-denies selected Trading live financial operations.
- Requires an exact owner approval matching company, task, operation, resource, expiry, single-use flag and request nonce when approval is required.
- Adds the nonce to a replay cache after an allow decision.

Limitations and next work:
1. Replay protection is an in-memory set and is not durable or distributed. Integrate with a single authoritative durable replay/approval-consumption service; do not rely on process-local cache for production.
2. Revocation and cancelled-task state are caller-supplied sets. Replace these with authenticated, current, fail-closed control-plane reads and explicit version/epoch checks.
3. The engine is a synthetic evaluator and does not itself authenticate the identity envelope or execute/enforce a tool boundary. It must only run behind the verified identity and policy gateway chain.
4. Resource-prefix checks and cost fields need a canonical resource grammar, currency/amount representation and exact policy schema alignment.
5. Keep the Trading hard-deny list central and versioned so it cannot drift between this module, the gateway and the company policy registry.

**Disposition:** Keep as an offline reference and conformance oracle; do not describe it as production enforcement.

### 2.2 Deterministic policy gateway

**Artifact:** `docs/security/policy_gateway_reference.py`  
**Contract:** `docs/security/policy-gateway-production-contract.md`

Existing controls observed statically:
- Requires explicit Trading company IDs at construction.
- Calls injected identity verification, emergency-stop and current-policy-version dependencies.
- Checks principal active/expiry, task expiry, tenant equality, assigned-agent equality and task/request policy-version consistency.
- Enforces protected-operation denial, Trading hard-deny actions, task operation/resource allowlists and owner-approval consumption.
- Catches dependency exceptions and returns a deny decision.

Limitations and next work:
1. The security of the gateway depends on the injected callbacks being trusted infrastructure, not model/agent-supplied values. Define authenticated interfaces and deployment ownership for every callback.
2. Bind the request to a canonical parent-child task envelope, revocation epoch, data classification, recipient scope, action digest and audit correlation ID. The current compact reference dataclasses do not express the complete enterprise task envelope.
3. Ensure all tool/data/connector/outbox calls are physically forced through the gateway; document and later test bypass resistance.
4. Validate input types and clock provenance at the boundary; dependency failures already deny, but production clock integrity and policy freshness need explicit service contracts.
5. Preserve independent CRO veto and Security & Recovery stop authority; neither can be modified by a strategy agent or ordinary workforce role.

**Disposition:** Strong candidate for the policy enforcement seam, subject to static reconciliation, threat review, adapter inventory and separately authorised synthetic validation.

### 2.3 Identity and owner-approval cryptographic demonstration

**Artifact:** `docs/security/identity_lifecycle_reference.py`

Existing controls observed statically:
- Uses HMAC-SHA256 over canonicalised claims.
- Separates issuer and owner keys in the function contracts.
- Binds identity to issuer, agent, company, role and expiry.
- Binds owner approval to owner, company, task, operation, resource, nonce, issued/expiry times and single-use semantics.
- Uses constant-time signature comparison and checks revocation/consumption state supplied to the verifier.

Limitations and next work:
1. The module explicitly says fixture keys/HMAC are demonstration-only. Production identity requires a separately designed key lifecycle, protected signing service, rotation, revocation, issuer separation, audit and recovery.
2. The verifier's revocation and consumed-nonce inputs are passed as in-memory state. They must be resolved from authoritative durable services and checked atomically with action authorization/consumption.
3. The current signed envelope is not a complete production token format: add audience, token/identity version, policy version or epoch, parent-task binding where applicable, key ID, and canonical schema/version rules.
4. Do not reuse fixture keys or share one secret across company tenants. Tenant and service key separation is mandatory.

**Disposition:** Synthetic cryptographic example only; never deploy or connect with fixture keys.

### 2.4 Durable approval ledger

**Artifact:** `docs/security/durable_approval_ledger_reference.py`

Existing controls observed statically:
- Uses SQLite transactions with `BEGIN IMMEDIATE` for issue, revoke and consume paths.
- Stores exact approval scope, expiry, owner, company, agent, session, task, operation, resource and policy version.
- Uses unique constraints for approval ID, nonce, consumption approval ID, nonce and action ID.
- Atomically records approval issuance/consumption and appends a per-company hash-linked audit event in the same transaction.
- Checks exact scope, expiry, revocation and optional amount limit at consume time.
- Provides an audit-chain verifier for its local approval audit rows.

Limitations and next work:
1. This is a local SQLite reference, not a distributed control store or multi-host linearizable authority. Production concurrency, failover, durability, backup/restore and recovery require the separately documented control-store design and evidence.
2. The code explicitly treats owner signature verification as upstream. The trusted call chain must prove that verified approval identity and the stored approval record refer to the same owner, payload and approval digest.
3. Define how approval revocation, task cancellation, identity revocation and policy epoch changes are serialized against consumption.
4. Define operational database file protection, encryption/key handling, permissions, backup, restore and corruption recovery before any host use.
5. Keep the unique-constraint replay/duplicate outcome distinguishable from unrelated integrity failures, and retain auditable denial reasons.

**Disposition:** Useful local transactional reference; not the selected production database or shared authority store.

### 2.5 Hash-linked audit reference

**Artifact:** `docs/security/audit_chain_reference.py`

Existing controls observed statically:
- Canonicalises event data and rejects secret-like field names.
- Rejects floating-point values in audit payloads.
- Links events with SHA-256 hashes, sequence numbers and previous hashes.
- Detects duplicate IDs, sequence gaps/reordering, previous-hash mismatches and hash mismatches.

Limitations and next work:
1. `InMemoryAuditChain` is explicitly process-memory-only and neither durable nor tamper-proof. A hash chain alone does not stop an attacker with write access from rewriting the full chain.
2. Production audit requires durable append controls, tenant partitioning, authenticated writers, restricted readers, signed checkpoints or external anchoring, retention, export and independent verification.
3. Align event schemas with the approval ledger's audit envelope; avoid two incompatible canonical event formats.
4. The secret-key name filter is a safety aid, not a complete data-loss-prevention classifier. Define classification-aware field allowlists and redaction rules.
5. Define audit availability/failure behaviour: consequential actions must not proceed if mandatory audit evidence cannot be durably committed.

**Disposition:** Offline audit algorithm reference; not a production log store.

## 3. Integration chain and hard dependency order

The reference modules imply the following implementation chain:

1. **Trusted identity issuer and verifier** — establishes principal, company, role, session, expiry, audience and revocation epoch.
2. **Canonical parent-child task envelope** — binds task authority and bounded delegation to the principal.
3. **Policy decision point** — evaluates company, role, task, policy version, action/resource, classification, risk/emergency stop and required approval.
4. **Durable owner-approval service** — verifies owner-originated exact-scope approval and atomically consumes it once.
5. **Policy enforcement gateway** — mediates every tool, data, connector and authorized outbox boundary.
6. **Transactional audit/outbox** — records decision and authorized action intent with replay/idempotency controls.
7. **Revocation/cancellation service** — invalidates principals, approvals, tasks, descendants, sessions and pending actions.
8. **Monitoring and Security & Recovery** — detects dependency failure, stale policy, missed revocation, audit gap and recovery condition.

No layer may be bypassed by Paperclip, Ruflo, model adapters, agents, prompts or direct connector calls.

## 4. Required conformance crosswalk before tests

| Area | Existing reference | Required crosswalk |
|---|---|---|
| Identity claims | identity lifecycle module + identity contract | Exact claim names, issuer, audience, tenant, role, expiry, key ID, revocation epoch |
| Parent/child authority | task envelope + agent task schema | Inherited tenant, recipient, classification, action, budget, expiry, reviewer and cancellation fields |
| Policy evaluation | reference policy engine + gateway | One allow/deny truth table; no conflicting hard-deny lists; exact resource/action grammar |
| Owner approval | identity approval + durable ledger | Signature/payload digest → stored approval → one-time consume → audit/outbox transaction |
| Revocation | identity lifecycle + gateway + security contract | Epoch update and cancellation acknowledgement across queues, workers, adapters and pending actions |
| Audit | audit chain + approval ledger + durable audit contract | One canonical event schema, tenant ordering, signed checkpoint, durability and fail-closed rule |
| Tool mediation | gateway + authorized outbox contract | Full adapter inventory and proof every path uses enforcement |
| Recovery | transactional dispatch/recovery and S&R contract | Crash, duplicate, partial commit, stale approval, restore and quarantine handling |

## 5. Priority findings

- **P0 — Contract alignment:** reconcile policy engine and gateway deny lists, action names, tenant IDs, resource grammar and approval requirements into one canonical policy vocabulary.
- **P0 — Durable authority:** define the authoritative production identity, revocation, policy-version and replay/approval-consumption services. Process-local sets are not sufficient.
- **P0 — Approval transaction:** prove the exact owner-signed approval is the same approval consumed by the gateway and committed to the authorized outbox/audit record.
- **P0 — Bypass resistance:** inventory every worker adapter, MCP connector, API, file/data path and external outbox; require policy enforcement at every boundary.
- **P1 — Audit consolidation:** align in-memory audit and SQLite approval audit with the durable audit/checkpoint contract and tenant-specific chain semantics.
- **P1 — Operational recovery:** define persistence, backup/restore, concurrency, failover, key rotation and emergency-stop recovery.
- **P1 — Independent review:** threat model and independent security review before any production deployment decision.

## 6. Approval boundary and next action

This review was read-only. It does not authorise code changes, Python execution, tests, CI, installations, database provisioning, key generation, account connections, hosting, deployment or production use.

Next safe work:
1. Crosswalk these findings to the existing PG-1–PG-7 blocker/evidence documents and production-readiness register.
2. Mark each PG stage as contract present, reference code present, tests authored, tests executed (NOT RUN), independent review and production evidence.
3. Identify exact duplicate or inconsistent contract fields and propose a single canonical schema before editing code.
4. Submit a bounded synthetic-test plan for owner approval only after the static crosswalk is complete.

**Non-claim:** No security certification, production readiness, distributed consistency, successful test run or active enforcement is claimed.

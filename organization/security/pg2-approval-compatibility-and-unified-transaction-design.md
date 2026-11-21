# PG-2 — Full-Scope Approval Compatibility and Unified Transaction Design

**Status:** Architecture-only reconciliation and target design. No migration, database, code wiring, tests or deployment.  
**Applies independently to:** AI Revenue and Trading & Technology, each with its own database/tenant, issuer, owner authority, keys, policy and audit stream.  
**Decision:** Do not wire the trusted façade to either current SQLite approval prototype or the standalone PostgreSQL approval adapter until the field and transaction mismatches below are resolved.

## 1. Executive finding

The existing repository contains several overlapping approval/control-store designs. They are useful reference work, but they are not interchangeable implementations of one repository contract:

1. `sqlite_control_store.py` has a minimal `approvals` table and a separate `tasks` table. Its approval record does not persist the trusted façade's full owner/principal/session/stream/policy/recipient/amount/currency/audience/signature/scope evidence.
2. `linearizable_control_store_reference.py` has a richer approval shape and a unified local action/recovery/audit design, but still does not persist the full signed owner envelope and all façade scope/authenticity fields. It remains a local SQLite reference.
3. `owner-approval-repository-schema.sql` defines `owner_approval_records`, `owner_approval_consumptions` and a separate approval audit stream. The matching PostgreSQL adapter follows that repository contract.
4. `transactional-audit-approval-schema.sql` defines a different `control_plane.owner_approvals` / `approval_consumptions` schema with a unified control-plane audit and outbox direction. Its columns and repository interface do not match the standalone approval schema or adapter.

The central problem is therefore larger than adding a few columns: there are multiple schema names, repository contracts, audit authorities and transaction boundaries. A field-only migration to one prototype would leave the other incompatible contracts unresolved.

## 2. Exact source baseline reviewed

The following exact branch files were read from the active AI Revenue architecture branch; corresponding Trading paths exist in its own branch:

| Artifact | Blob SHA | Relevant contract |
|---|---|---|
| `organization/security/sqlite_control_store.py` | `ad03f6d771d5f34d36776df0d75f240d286dad96` | Minimal approval/task/outbox/audit SQLite prototype |
| `organization/security/trusted_control_plane_facade_reference.py` | `6ce4856270fb0dbb9fc770b257d9d1d2c497e76e` | Full façade claim validation and repository receipt contract |
| `organization/security/owner-approval-repository-schema.sql` | fetched from active branch | Standalone full-scope PostgreSQL approval schema |
| `organization/security/owner_approval_postgres_repository.py` | fetched from active branch | Adapter for standalone approval schema and separate approval audit |
| `organization/security/transactional-audit-approval-schema.sql` | fetched from active branch | Unified control-plane audit, approval, consumption and outbox proposal |
| `organization/security/linearizable_control_store_reference.py` | fetched from active branch | Richer local SQLite recovery/dispatch reference |

The standalone approval schema and unified transactional schema are distinct proposals, not additive migrations that may simply both be deployed. The exact Trading copies must remain company-local; no cross-company database or shared approval authority is implied.

## 3. Field-by-field compatibility matrix

### 3.1 Trusted façade claims and repository receipt

The façade requires the verified owner-approval claims below before it calls the repository:

| Façade claim | Minimal SQLite `approvals` | Standalone PostgreSQL `owner_approval_records` | Unified `control_plane.owner_approvals` proposal | Canonical target |
|---|---|---|---|---|
| approval_id | Yes | Yes | Yes | Yes, immutable primary key |
| company_id | Yes | Yes | Yes | Yes, tenant-bound |
| stream_id | No | Yes | No | Yes, bound to company stream |
| owner_id | No | Yes | `owner_subject` | Yes, canonical `owner_id` |
| agent_id | No | `principal_agent_id` | `agent_id` | Yes |
| session_id | No | Yes | Yes | Yes |
| task_id | Yes | Yes | Yes | Yes |
| operation | Yes | Yes | Yes | Yes, canonical taxonomy ID |
| resource | Yes | Yes | Yes | Yes, exact resource binding |
| recipient | No | Yes | No | Yes, nullable only for operations without recipient |
| intent_digest | No | Yes | No | Yes, nullable only for non-payload-bound actions |
| policy_version | No | Yes | Yes | Yes |
| audience | No | Yes | Yes | Yes |
| nonce / nonce_hash | Hash only | Raw nonce | Hash only | Hash only; unique per company |
| single_use | Implicit via consumed table | Yes | Implicit via consumption | Explicit true |
| issued_at | No | Yes | Yes | Yes |
| expires_at | Yes | Yes | Yes | Yes |
| amount_minor + currency | No | Yes | Yes, differently named | Yes, paired integer minor units + ISO currency |
| scope_digest | No | No explicit column | No | Yes, computed/verified by trusted service |
| signer_key_id | No | Yes | `signing_key_id` | Yes |
| signed_payload_digest | No | Yes | No | Yes |
| signature_digest | No | Yes | No | Yes |
| signed_envelope | No | Yes | Signature bytes only | Yes, retained in restricted evidence storage |
| revoked_at / revoked_by | Boolean only | Yes | `revoked_at` only | Yes |
| consumed action binding | Separate idempotency key | Separate action_id | `idempotency_key` | Yes, action_id + idempotency key |
| receipt audit_event_id | No | Adapter-specific | Not a façade receipt | Yes, durable event ID |
| receipt scope_digest | No | Not clearly persisted as a receipt field | No | Yes, exact equality with verified claims |

**Result:** the minimal SQLite schema is not façade-compatible. The two PostgreSQL proposals are each incomplete or differently shaped relative to the façade and each other. No adapter should silently fill missing fields with defaults or infer them from agent input.

### 3.2 Trusted task resolution

The façade's scheduler contract returns:

- task_id, company_id, assigned_agent_id, stream_id and policy_version;
- expires_at;
- explicit non-empty allowed_operations and allowed_resources.

The minimal SQLite `tasks` table contains only task_id and cancelled. It cannot prove company, assignment, stream, policy version, expiry or task capability/resource scope. A trusted scheduler/task repository is a separate required dependency; an approval-table migration alone does not fix this gap.

## 4. Additional conflict: audit and transaction ownership

The standalone approval repository schema defines its own `owner_approval_audit_heads/events`. The transactional control-plane schema defines `control_plane.audit_stream_heads/events`. Running both as independent append authorities would split the audit history and make it unclear which event sequence is authoritative.

The adapter contract also states that `consume_in_transaction()` must not commit and that its caller must share the authoritative transaction with recovery stream/action state, dispatch state and unified audit/outbox. This is the correct integration direction, but the standalone adapter's separate audit tables do not by themselves establish that shared transaction.

**Canonical decision:** one company-local control-store transaction domain and one canonical audit stream per company/stream. Approval issue, revoke and consume events must append to that same audit authority. Do not deploy a second approval-only audit chain as an independent source of truth. Independent signed checkpoints/WORM exports remain a separate tamper-resistance layer.

## 5. Canonical target record — proposed, not executable DDL

The future approval record should persist these immutable fields:

- Identity/scope: approval_id, company_id, stream_id, owner_id, principal_agent_id, session_id, task_id.
- Operation binding: canonical operation_id, exact resource, optional recipient, optional immutable intent digest.
- Policy binding: policy_version, audience, explicit single_use=true, scope_digest.
- Time/replay: issued_at, expires_at, nonce_hash; unique approval ID and unique (company_id, nonce_hash).
- Amount: optional non-negative integer amount_minor and currency; both null or both present, currency normalized to ISO 4217.
- Signature provenance: signer_key_id, signed_payload_digest, signature_digest, restricted signed_envelope evidence reference or retained envelope.
- Lifecycle: revoked_at/revoked_by; consumption is a separate one-to-one record bound to action_id, idempotency_key and consumed_at.

The repository receives claims only after an independent trusted asymmetric verifier has checked owner identity, signature, key status, issuer, audience, canonical payload, expiry and exact scope. The repository is not a signature verifier and must not trust a Boolean such as `owner_approved=true` supplied by an agent.

A repository receipt must contain approval_id, company_id, scope_digest, expires_at and audit_event_id. The façade must verify exact equality with the already verified claims before returning it.

## 6. Canonical transaction protocol

All steps below are design requirements; none is implemented or authorized by this document.

### ISSUE

1. Authenticate the caller as the dedicated owner-approval service identity; agents and models cannot invoke the owner endpoint.
2. Verify the owner signature, signer key status, company-specific issuer/audience, trusted time, single-use flag and complete claims.
3. Resolve the task independently from the trusted scheduler. Check assignment, company, stream, task expiry, policy version, operation and resource allowlists.
4. Compute/verify the canonical scope digest and persist only the verified claims.
5. In one company-local transaction: insert approval, append `approval_issued` to the canonical audit stream and advance its head. Roll back both on any failure.

### REVOKE

1. Authenticate an authorized owner/security authority.
2. Lock the exact company-scoped approval row and verify it is not already revoked.
3. Set revoked_at/revoked_by and append `approval_revoked` to the same canonical audit stream in the same transaction.
4. Invalidate outstanding permits/grants through the separately monitored revocation mechanism. Revocation cannot undo an already dispatched external effect.

### CONSUME + RESERVE DISPATCH

1. Begin the authoritative company transaction and lock the relevant approval, task, recovery stream and action state in a fixed, documented lock order.
2. Recheck owner signature status/key revocation, company, owner, principal, session, task assignment/status/expiry, operation, resource, recipient, intent digest, amount/currency, policy version, audience, approval expiry/revocation, emergency stop and current recovery epoch.
3. Re-evaluate hard denies before approval. A valid approval never overrides a company hard-deny rule.
4. Insert one-use consumption with unique approval_id, company/nonce_hash, action_id and idempotency_key.
5. Insert immutable action intent/outbox record; bind company, recipient, operation, amount/currency, payload digest and recovery epoch.
6. Append the consumption/dispatch-reserved audit event and advance the same canonical audit head.
7. Commit once. Any audit, constraint, scope or state failure rolls back consumption and outbox together.
8. Only after commit may a separately authorized dispatcher act. An ambiguous remote result becomes outcome_unknown and is never automatically resent without receiver-side reconciliation.

This transaction must also serialize correctly against quarantine, task cancellation, revocation and recovery-epoch changes. Local SQLite writer serialization is not proof of multi-node production correctness.

## 7. Company-specific policy overlays

### AI Revenue

- Company ID and issuer/audience must be fixed to AI Revenue.
- CAD $0 incremental spend remains the active hard budget. Positive or unknown-cost inference, APIs, compute, hosting, subscriptions, purchases and ads remain denied.
- External publication, customer contact, commercial commitments, customer-data export and payments are not enabled by the taxonomy or this schema design.
- If a future action is eligible for approval, it must bind exact content/payload digest, destination/recipient, amount/currency where relevant and short expiry.

### Trading & Technology

- Company ID and issuer/audience must be fixed to Trading & Technology.
- Research/backtest/paper remain the only operating modes in the current programme.
- Live orders, wallet signing, deposits, transfers, withdrawals, broker/exchange orders and risk-limit/HALT/STOP changes remain hard-denied before approval lookup/consumption.
- Risk authority retains independent veto. The approval repository cannot grant live authority or override the risk service.
- Halal/Shafi'i issue flags remain an independent review dimension, not a Boolean inferred by the database.

## 8. Required invariants before any future migration

- Exactly one canonical approval repository contract per company.
- Exactly one canonical audit append authority per company/stream.
- No approval field may be silently omitted, defaulted or sourced from agent-controlled request data.
- No raw private key, seed phrase, credential or reusable bearer secret is stored.
- Nonce uniqueness, approval uniqueness and one-time consumption are enforced by database constraints and an authoritative transaction.
- Amounts use integer minor units with explicit currency; no floating-point money.
- Signed payload and scope digest use a documented canonicalization version and reject duplicate keys, non-finite numbers and ambiguous numeric forms.
- Company, audience, signer key and issuer are pinned; company keys and owner authorities are separate.
- Task assignment and scope are resolved from a trusted scheduler, not reconstructed from the approval request.
- Audit append failure, clock uncertainty, key/revocation unavailability, policy uncertainty or recovery conflict fails closed.
- Receiver idempotency and recovery-epoch fencing are required; exactly-once remote effects are not claimed.
- Schema migrations are versioned, reversible where safe, backed up and reviewed; no destructive migration or live DB operation without separate explicit authorization.

## 9. Open decisions for PG-2 review

1. Select the single canonical target schema by merging the full façade claims with the unified control-store transaction model—not by deploying both current PostgreSQL schemas.
2. Decide whether signed_envelope is retained inline as restricted JSONB or in encrypted immutable evidence storage, with a digest and reference in the row.
3. Define canonicalization (proposed RFC 8785 with additional safe-number restrictions) and scope-digest versioning.
4. Define a fixed lock order covering task, stream/recovery state, approval, action/outbox and audit head; document concurrency and deadlock handling.
5. Define exact action recipient/intent/amount semantics per operation class and how no-recipient operations are represented.
6. Reconcile task scheduler persistence and company assignment with the approval repository contract.
7. Design a migration plan only after these decisions; no migration SQL is approved here.

## 10. Explicit non-authorization and status

- No database was created, altered or connected.
- No migration, test, validation, GitHub Actions run, package installation, key generation, account connection or deployment occurred.
- The existing SQLite and PostgreSQL files remain offline reference designs.
- AI Revenue and Trading & Technology remain separate companies with separate approval authorities, keys, policies, audit streams and risk boundaries.
- This PG-2 document is a compatibility/design review, not evidence of implemented controls or production readiness.

**Disposition:** PG-2 compatibility findings documented; migration and runtime integration remain blocked pending owner/architecture review and separate authorization.

## 11. Exact source blob manifest for PG-2 reconciliation

The source reads above correspond to these exact AI Revenue branch blobs:

| Source | Blob SHA |
|---|---|
| `sqlite_control_store.py` | `ad03f6d771d5f34d36776df0d75f240d286dad96` |
| `trusted_control_plane_facade_reference.py` | `6ce4856270fb0dbb9fc770b257d9d1d2c497e76e` |
| `owner-approval-repository-schema.sql` | `525c701718479b0f5c297d58745d33ae98fe80da` |
| `owner_approval_postgres_repository.py` | `a91b32e46c564da9e295b972b09c8056e9f68eb9` |
| `transactional-audit-approval-schema.sql` | `41dd71bcc25649c1f03212e668d31d704043bd9a` |
| `linearizable_control_store_reference.py` | `563cdbcccabef48ff2e9da7f0630822450d56250` |
| `identity-lifecycle-production-requirements.md` | `d09636c2b08112f2d1b2b0783610e744eecf7293` |
| `trusted-identity-approval-clock-and-receiver-boundary-contract.md` | `6fed9ef726bd2e1eba7b3b2340bf025376c6514b` |

This manifest pins the reviewed inputs for this design pass only. It is not a claim that the files are merged, deployed, validated by tests or production-approved. Any source revision change requires the compatibility review to be refreshed.

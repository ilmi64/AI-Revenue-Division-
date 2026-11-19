# Durable approval and audit transaction contract

Status: SQLite reference implementation only. No production owner-signature verifier, deployment or live dispatch.

## Atomicity invariant
Approval consumption and the corresponding audit event are written in the same database transaction. Either both commit or neither commits. The unique constraints on approval ID, nonce and action ID make replay/duplicate consumption fail closed across independent SQLite connections.

## Scope
Each approval record binds owner, company, agent, session, task, operation, resource, policy version, expiry and optional integer minor-unit amount ceiling. The trusted approval issuer must verify owner identity/signature before inserting an approval. This reference does not verify cryptographic signatures.

## Revocation
Revocation and its audit event commit in one transaction. The final dispatch consumer must consult this ledger immediately before action dispatch. Revocation after successful consumption cannot retroactively undo an already dispatched action; cancellation/reconciliation is a separate workflow.

## Audit
Events are hash-linked per company. Audit writes share the transaction with approval issue, revoke and consume. A failed audit insert rolls back the approval state transition. The chain detects accidental/tampered event changes but does not prevent a privileged database owner from rewriting the entire database and chain.

## Concurrency
SQLite BEGIN IMMEDIATE serializes writers; unique constraints provide a second line of defence. Tests use two independent connections to the same file database. Production multi-node deployments require a shared transactional database with serializable/appropriate row locking and unique constraints, tested under failover and isolation anomalies.

## Production requirements
- Verify signed approvals using a separate owner approval authority and asymmetric signatures.
- Bind exact action amount/currency, recipient/account, company, task, agent/session, operation/resource, policy version, nonce and short expiry.
- Enforce one-use with database uniqueness and transactionally append audit/outbox state.
- Use PostgreSQL or equivalent managed durable database with backups, point-in-time recovery, restricted roles, TLS, key management, monitoring and tested restore.
- Ensure action outbox intent and approval consumption participate in one database transaction; remote effects still need receiver idempotency and reconciliation.
- Separate company databases or strict company-scoped authorization and database policies; no cross-company reads by default.
- Signed checkpoints and independently stored immutable/WORM audit exports are required to resist privileged full-chain rewrite.

## Limits
This is a local SQLite reference, not a distributed consensus system, production ledger, cryptographic verifier or financial control. A successful test run does not authorize external actions.

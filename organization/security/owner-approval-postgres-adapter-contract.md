# PostgreSQL owner-approval repository adapter

Status: reference adapter and mocked DB-API contract tests only. Not deployed, connected, migrated, or tested against a live PostgreSQL instance.

## Boundary
- A trusted approval verifier must authenticate the owner signature, signer key status, audience, company, exact scope, expiry, and nonce before calling issue().
- The adapter binds to one company and one audience at construction. It receives no agent-controlled DB credentials or verifier/clock dependencies per request.
- The connection factory must return psycopg-compatible connections with mapping rows (dict_row).
- signed_envelope is retained in the approval record; logs/audit payloads contain digests and references, not the full envelope.

## Transactions
- issue() inserts the approval and approval_issued audit event/head update in one transaction.
- revoke() updates revocation and appends approval_revoked in one transaction.
- consume_in_transaction() deliberately never commits or rolls back. The caller must use the same authoritative transaction that locks recovery stream/action state, consumes the approval, starts dispatch, and appends the unified audit/outbox records.
- The consuming transaction must roll back on any failure, including audit append failure. Unique constraints enforce one-time use under concurrency.
- The current SQL schema's separate approval audit stream is not yet reconciled with the unified control-store audit schema. Production integration must choose one canonical audit append protocol and one transaction domain; do not deploy both as independent authorities.

## Known limitations / production blockers
- No actual asymmetric signature verifier, trusted clock, owner identity service, PostgreSQL installation, schema migration, live connection, receiver, network sender, or deployment is included.
- DB-API fake tests do not prove PostgreSQL syntax, isolation, locking, constraint behavior, or race safety.
- A PostgreSQL integration suite must verify concurrent duplicate consumption, nonce collision, audit rollback, revoke-vs-consume serialization, company isolation, backup/restore, and migration compatibility.
- Hash chaining is tamper-evident, not immutable against privileged rewrite. Add signed checkpoints and independently administered WORM storage.
- Never claim exactly-once remote execution. Receiver idempotency and signed evidence remain required.
- Trading live orders, wallet signing, transfers, withdrawals, and risk-control modification remain hard-denied by the separate policy/control plane.

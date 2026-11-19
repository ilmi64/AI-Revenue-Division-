# SQLite transactional prototype — validation and limits

Status: offline reference prototype; not production-ready and not connected to any company runtime.

## What it demonstrates
- Durable local SQLite records across process/store reconstruction.
- SQLite write transactions using BEGIN IMMEDIATE, WAL mode, busy timeout and synchronous=FULL.
- Unique constraints on approval IDs, nonce hashes and outbox idempotency keys.
- Atomic approval consumption plus outbox-intent insertion in one transaction.
- Exact company/task/operation/resource matching, expiry, revocation and cancellation checks.
- A local hash-linked audit stream with sequence/head verification.
- A two-thread same-database race test in which exactly one approval consumer should win.

## Critical limits
- SQLite is a local prototype, not the production PostgreSQL design. Its locking and durability guarantees depend on filesystem, journal, OS and deployment configuration.
- This does not authenticate owner approval signatures or agent identities. Inputs are trusted test fixtures.
- The outbox is only a durable intent queue. No dispatcher or external side-effect handler is implemented.
- No external action is executed. A production dispatcher must re-check policy and approval state, use provider idempotency where available, record outcomes, and reconcile uncertain outcomes before retry.
- Audit hashes are not signed checkpoints; an administrator able to rewrite the database can recompute the chain. Production requires external signed checkpoints, independent immutable retention and separate writer/auditor authorities.
- Tests are local acceptance evidence only, not a security certification, multi-host distributed-systems proof, or live PostgreSQL validation.

Run from this directory:
`python -m unittest -v test_sqlite_control_store.py`

Do not connect to Paperclip, Ruflo, model runtimes, brokers, exchanges, wallets, customer systems or external-action gateways without separate approval and production security review.

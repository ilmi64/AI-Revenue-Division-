-- PostgreSQL reference schema only. NOT applied or tested against a live database.
-- Requires a reviewed migration, least-privilege roles, backup/recovery plan and security review.
CREATE SCHEMA IF NOT EXISTS control_plane;

CREATE TABLE control_plane.audit_stream_heads (
    stream_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    last_sequence BIGINT NOT NULL DEFAULT 0 CHECK (last_sequence >= 0),
    last_hash BYTEA NOT NULL CHECK (octet_length(last_hash) = 32)
);

CREATE TABLE control_plane.audit_events (
    stream_id TEXT NOT NULL REFERENCES control_plane.audit_stream_heads(stream_id),
    company_id TEXT NOT NULL,
    sequence BIGINT NOT NULL CHECK (sequence > 0),
    event_id UUID NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    actor_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    previous_hash BYTEA NOT NULL CHECK (octet_length(previous_hash) = 32),
    event_hash BYTEA NOT NULL CHECK (octet_length(event_hash) = 32),
    hash_algorithm TEXT NOT NULL CHECK (hash_algorithm = 'sha256'),
    schema_version INTEGER NOT NULL CHECK (schema_version > 0),
    PRIMARY KEY (stream_id, sequence),
    UNIQUE (event_id),
    CHECK (jsonb_typeof(payload) = 'object')
);

CREATE TABLE control_plane.audit_checkpoints (
    stream_id TEXT NOT NULL REFERENCES control_plane.audit_stream_heads(stream_id),
    sequence BIGINT NOT NULL CHECK (sequence > 0),
    checkpoint_hash BYTEA NOT NULL CHECK (octet_length(checkpoint_hash) = 32),
    signature BYTEA NOT NULL,
    signing_key_id TEXT NOT NULL,
    signed_at TIMESTAMPTZ NOT NULL,
    external_anchor_reference TEXT,
    PRIMARY KEY (stream_id, sequence)
);

CREATE TABLE control_plane.owner_approvals (
    approval_id UUID PRIMARY KEY,
    nonce_hash BYTEA NOT NULL UNIQUE CHECK (octet_length(nonce_hash) = 32),
    company_id TEXT NOT NULL,
    owner_subject TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    resource TEXT NOT NULL,
    amount_minor_units BIGINT,
    currency CHAR(3),
    policy_version TEXT NOT NULL,
    audience TEXT NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    signature BYTEA NOT NULL,
    signing_key_id TEXT NOT NULL,
    revoked_at TIMESTAMPTZ,
    CHECK (expires_at > issued_at),
    CHECK ((amount_minor_units IS NULL) = (currency IS NULL))
);

CREATE TABLE control_plane.approval_consumptions (
    approval_id UUID PRIMARY KEY REFERENCES control_plane.owner_approvals(approval_id),
    nonce_hash BYTEA NOT NULL UNIQUE,
    company_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    resource TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    consumed_at TIMESTAMPTZ NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('reserved', 'dispatched', 'succeeded', 'failed', 'uncertain'))
);

CREATE TABLE control_plane.action_outbox (
    outbox_id UUID PRIMARY KEY,
    approval_id UUID NOT NULL UNIQUE REFERENCES control_plane.approval_consumptions(approval_id),
    idempotency_key TEXT NOT NULL UNIQUE,
    company_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    resource TEXT NOT NULL,
    payload_reference TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'leased', 'succeeded', 'failed', 'uncertain', 'cancelled')),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    lease_expires_at TIMESTAMPTZ,
    result_reference TEXT
);

CREATE TABLE control_plane.task_cancellations (
    company_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    cancelled_at TIMESTAMPTZ NOT NULL,
    reason_code TEXT NOT NULL,
    PRIMARY KEY (company_id, task_id)
);

-- Operational requirements:
-- 1. Lock the relevant approval/task rows and validate current identity, signature,
--    audience, scope, policy version, expiry, revocation and cancellation.
-- 2. In ONE transaction insert approval_consumptions and action_outbox; unique
--    constraints make replay/duplicate reservations fail closed.
-- 3. Commit before dispatch. Dispatcher leases outbox rows and uses the same
--    idempotency_key at the downstream gateway. Never blindly retry an uncertain
--    non-idempotent side effect; reconcile its outcome first.
-- 4. Append audit_events in the same transaction where practical. Allocate stream
--    sequence by locking audit_stream_heads, verify previous hash, insert event,
--    then update head. No application role may UPDATE/DELETE audit rows.
-- 5. A DBA able to alter schema/data can still attack the database: use separate
--    writer/auditor roles, signed external checkpoints and immutable external anchors.
-- 6. Never store bearer tokens, private keys, seed phrases, passwords or raw reusable
--    approval secrets in payload, outbox or audit rows. nonce_hash is a one-way digest.

-- Proposed PostgreSQL schema only. NOT applied or tested.
-- One database/service identity per company is preferred. Do not grant agents SQL access.
-- Owner signature verification must complete in a trusted approval service before INSERT.

CREATE TABLE owner_approval_records (
    approval_id UUID PRIMARY KEY,
    company_id TEXT NOT NULL,
    stream_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    principal_agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    resource TEXT NOT NULL,
    recipient TEXT,
    intent_digest CHAR(64),
    amount_minor BIGINT,
    currency CHAR(3),
    policy_version TEXT NOT NULL,
    audience TEXT NOT NULL,
    nonce TEXT NOT NULL,
    single_use BOOLEAN NOT NULL CHECK (single_use IS TRUE),
    issued_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    signer_key_id TEXT NOT NULL,
    signed_payload_digest CHAR(64) NOT NULL,
    signature_digest CHAR(64) NOT NULL,
    signed_envelope JSONB NOT NULL,
    revoked_at TIMESTAMPTZ,
    revoked_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT owner_approval_lifetime CHECK (expires_at > issued_at),
    CONSTRAINT owner_approval_amount_nonnegative CHECK (amount_minor IS NULL OR amount_minor >= 0),
    CONSTRAINT owner_approval_amount_currency_pair CHECK (
        (amount_minor IS NULL AND currency IS NULL) OR
        (amount_minor IS NOT NULL AND currency ~ '^[A-Z]{3}$')
    ),
    CONSTRAINT owner_approval_intent_digest CHECK (
        intent_digest IS NULL OR intent_digest ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT owner_approval_payload_digest CHECK (signed_payload_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT owner_approval_signature_digest CHECK (signature_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT owner_approval_nonce_unique UNIQUE (company_id, nonce)
);

CREATE TABLE owner_approval_consumptions (
    approval_id UUID PRIMARY KEY REFERENCES owner_approval_records(approval_id),
    company_id TEXT NOT NULL,
    nonce TEXT NOT NULL,
    action_id TEXT NOT NULL UNIQUE,
    consumed_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT owner_approval_consumption_nonce_unique UNIQUE (company_id, nonce),
    CONSTRAINT owner_approval_consumption_record_fk
        FOREIGN KEY (company_id, nonce)
        REFERENCES owner_approval_records(company_id, nonce)
);

CREATE TABLE owner_approval_audit_heads (
    company_id TEXT NOT NULL,
    stream_id TEXT NOT NULL,
    last_sequence BIGINT NOT NULL CHECK (last_sequence >= 0),
    head_hash CHAR(64) NOT NULL CHECK (head_hash ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (company_id, stream_id)
);

CREATE TABLE owner_approval_audit_events (
    company_id TEXT NOT NULL,
    stream_id TEXT NOT NULL,
    sequence BIGINT NOT NULL CHECK (sequence > 0),
    event_id UUID NOT NULL UNIQUE,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('approval_issued','approval_revoked','approval_consumed','approval_denied')
    ),
    occurred_at TIMESTAMPTZ NOT NULL,
    approval_id UUID,
    action_id TEXT,
    payload JSONB NOT NULL,
    previous_hash CHAR(64) NOT NULL CHECK (previous_hash ~ '^[0-9a-f]{64}$'),
    event_hash CHAR(64) NOT NULL CHECK (event_hash ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (company_id, stream_id, sequence),
    FOREIGN KEY (approval_id) REFERENCES owner_approval_records(approval_id)
);

CREATE INDEX owner_approval_active_lookup
    ON owner_approval_records(company_id, stream_id, principal_agent_id, task_id, expires_at)
    WHERE revoked_at IS NULL;

CREATE INDEX owner_approval_audit_by_approval
    ON owner_approval_audit_events(company_id, approval_id, sequence);

-- Transaction protocol (service implementation, not SQL trigger):
-- ISSUE:
--   1. Verify owner signature, issuer key status, audience, trusted time and exact scope.
--   2. BEGIN; insert owner_approval_records.
--   3. SELECT owner_approval_audit_heads ... FOR UPDATE (create genesis head safely if absent).
--   4. Append approval_issued event with canonical payload and previous hash.
--   5. Update audit head; COMMIT. Any failure rolls back both record and audit.
--
-- CONSUME:
--   1. BEGIN; SELECT approval row FOR UPDATE using company_id + approval_id.
--   2. Recheck exact company/stream/owner/agent/session/task/operation/resource/recipient,
--      intent digest, amount/currency, policy version, audience, expiry and revocation.
--   3. INSERT owner_approval_consumptions. Unique constraints enforce single use under races.
--   4. Lock the same stream audit head, append approval_consumed event and update head.
--   5. COMMIT. A duplicate-key error is classified as replay only after querying the
--      conflicting consumption key; unrelated integrity/audit failures must fail closed.
--
-- REVOKE:
--   1. BEGIN; lock approval row; set revoked_at/revoked_by once.
--   2. Append approval_revoked event and advance audit head in the same transaction.
--   3. COMMIT.
--
-- Security operations:
--   - Service roles only; no direct agent, model, Paperclip or Ruflo DB credentials.
--   - Separate company DBs/credentials/keys or independently reviewed equivalent isolation.
--   - Append-only permissions for audit events; head updates only through trusted procedure.
--   - Signed external checkpoints and independently administered immutable/WORM storage remain required.
--   - This schema does not authenticate owners, verify signatures, provide trusted time,
--     enforce policy, or serialize recovery/dispatch with approval consumption by itself.

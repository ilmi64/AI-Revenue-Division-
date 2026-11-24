-- Provision deliberately in a separate, company-local synthetic database.
CREATE TABLE fixture_scheduler_clock (
    company_id TEXT PRIMARY KEY CHECK(company_id = 'ai_revenue'),
    last_seen INTEGER NOT NULL CHECK(last_seen >= 0)
);
INSERT INTO fixture_scheduler_clock VALUES ('ai_revenue', 0);

CREATE TABLE scheduled_fixture (
    request_id TEXT PRIMARY KEY NOT NULL,
    request_bytes BLOB NOT NULL,
    expires_at INTEGER NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('QUEUED', 'RUNNING', 'REVIEW_READY', 'SUPERVISOR_HOLD')),
    claim_until INTEGER,
    reason TEXT,
    result BLOB,
    result_sha256 TEXT,
    CHECK (
        (state = 'QUEUED' AND claim_until IS NULL)
        OR (state IN ('RUNNING', 'REVIEW_READY') AND claim_until IS NOT NULL)
        OR state = 'SUPERVISOR_HOLD'
    ),
    CHECK (
        (state = 'REVIEW_READY' AND result IS NOT NULL AND result_sha256 IS NOT NULL)
        OR (state != 'REVIEW_READY' AND result IS NULL AND result_sha256 IS NULL)
    )
);

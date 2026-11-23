-- Provision in the separate verifier-owned synthetic audit database.
CREATE TABLE audit_identity (
    company_id TEXT PRIMARY KEY NOT NULL,
    store_id TEXT NOT NULL UNIQUE
);
CREATE TABLE review_audit (
    sequence INTEGER PRIMARY KEY CHECK (sequence > 0),
    previous TEXT NOT NULL,
    epoch INTEGER NOT NULL,
    nonce TEXT NOT NULL UNIQUE,
    manifest TEXT NOT NULL,
    observed_at INTEGER NOT NULL,
    digest TEXT NOT NULL
);

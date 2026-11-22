-- Provision only in a verifier-controlled synthetic database.
CREATE TABLE evidence_review_replay (
    company_id TEXT NOT NULL,
    nonce TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    verified_at INTEGER NOT NULL,
    PRIMARY KEY (company_id, nonce)
);

-- Apply once with fixture scheduler clients stopped, after v2 if upgrading from v1.
BEGIN IMMEDIATE;
CREATE TABLE fixture_claim_owner (
    request_id TEXT PRIMARY KEY NOT NULL REFERENCES scheduled_fixture(request_id),
    process_identity BLOB NOT NULL,
    recovery_custody BLOB
);
-- Never infer process ownership for a pre-existing claim.
COMMIT;

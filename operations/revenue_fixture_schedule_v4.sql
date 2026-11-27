-- Apply once with fixture scheduler clients stopped, after any prior migrations.
BEGIN IMMEDIATE;
CREATE TABLE fixture_bundle_acceptance (
    request_id TEXT PRIMARY KEY NOT NULL REFERENCES scheduled_fixture(request_id),
    receipt BLOB NOT NULL,
    receipt_sha256 TEXT NOT NULL
);
COMMIT;

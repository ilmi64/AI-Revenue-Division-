-- Pre-provision only in a synthetic company-specific custody fixture.
CREATE TABLE custody_identity (
    company_id TEXT NOT NULL,
    store_id TEXT NOT NULL UNIQUE
);
CREATE TABLE custody_event (
    sequence INTEGER PRIMARY KEY CHECK(sequence > 0),
    previous TEXT NOT NULL,
    payload TEXT NOT NULL,
    head TEXT NOT NULL
);

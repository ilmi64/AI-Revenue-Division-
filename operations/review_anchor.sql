-- Provision in the separately administered synthetic anchor database.
CREATE TABLE review_anchor (
    company_id TEXT PRIMARY KEY NOT NULL,
    store_id TEXT NOT NULL UNIQUE,
    epoch INTEGER NOT NULL CHECK (epoch > 0),
    trust_fingerprint TEXT NOT NULL,
    policy TEXT NOT NULL,
    sequence INTEGER NOT NULL CHECK (sequence >= 0),
    head TEXT NOT NULL
);

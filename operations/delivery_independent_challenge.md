# Aevora AI independent delivery challenge

Baseline is draft #38 at `f8f66146d853a132dba199cccec73c532a335259`. The
challenge adds tests and records observed prototype behavior. It uses fictional
identities, local SQLite copies, deterministic scope, synthetic bytes and HMAC
fixture keys. There is no production approval or external delivery.

| Challenge | Observed synthetic behavior | Production acceptance requirement |
| --- | --- | --- |
| Writer exits before or immediately after COMMIT | The subprocess exits without normal cleanup. An unfinished nonce claim disappears. An acknowledged commit survives a fresh connection and blocks replay. The subsequent valid review receipt, when issued, denies release. | Fault testing on the actual storage and backup topology with durability and recovery objectives. |
| Trust snapshot rollback | The current registry blocks a revoked signer. A stale internally consistent registry accepts the old signer for review, with release false. | Company-scoped monotonic signed trust versions, managed revocation, freshness enforcement and fail-closed handling of unavailable authority. |
| Replay store restore/clone | The current store stops the duplicate. A clone taken before consumption accepts a second review receipt with release false. The #38 rehearsal detects restoration against its in-run checkpoint. | Durable independently managed checkpoint, authenticated store identity, anti-rollback recovery and failover testing across process restarts. |
| Signer status, identity separation and authority outage | Missing registry/store, revoked or expired authority, role principals that collide and shared credentials block verification. | Independent asymmetric identities, owner-controlled trust and issuer separation, verified custody, key rotation and authoritative revocation. |
| Manifest/artifact, recipient or policy substitution | Altered artifact bytes and mismatched company, source, recipient and downgraded policy are rejected against current expected scope. | Bind trusted expected scope and policy version to current independently issued records. |
| Corrupted or missing audit evidence | Deleting the audit fixture or changing its final event is invisible to the artifact verifier. No independently sealed audit chain exists on this path. Review receipts still deny release. | Independently administered append-only audit with signed checkpoint continuity. Missing or invalid chain must block production operation. |
| OCC contamination | Receipt status is rejected as an aggregate input. Private digest, company identifier and extra authorization or audit fields are excluded. Aggregate grants no execution authority. | Keep company-specific receipts and audit evidence scoped to AI Revenue and its independent Security & Recovery oversight. Main Hub/OCC receives read-only counters. |

The three reproduced trust gaps are production blockers even though their
characterization tests pass. A review receipt grants zero delivery authority.
The challenge does not change the verifier, the intake checklist, or OCC
authority.

## Reproduction

Run from `operations` in a local network-denied environment using an existing
Python 3.12 interpreter and its standard library.

```sh
python -m unittest -v test_delivery_independent_challenge
python -m unittest discover -v
```

The focused run passed 8 tests. The full operations run passed 56 tests.
The crash cases used a separate process with an immediate exit and a fresh
parent connection.

## Production commissioning and owner signoff

- Security & Recovery independent review and signed audit chain evidence: **PENDING**.
- AI Revenue owner signoff for a specific action, artifact, scope, channel,
  and recipient: **NOT GRANTED**. Record the accountable owner, expiry and
  restricted evidence reference only after a separately authorized decision.
- Final external delivery authority: **false**.

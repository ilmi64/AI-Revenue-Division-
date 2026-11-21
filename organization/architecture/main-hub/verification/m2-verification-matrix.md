# Main Hub / OCC M2 verification matrix

**Status:** Test plan only. The rows below are requirements and execution records, not claims that tests have run. The current 29-test Python suite has not been rerun after strict-JSON hardening.

## 1. Verification layers

Keep these layers separate in reports:

1. **Source integrity:** exact repository, branch, commit and blob SHAs are recorded.
2. **JSON parsing:** UTF-8, duplicate-key rejection, non-standard constant rejection, bounded input and strict parse behavior.
3. **Schema validity:** the exact committed schema and exact committed complete envelope are checked with a Draft 2020-12 implementation; format checking or equivalent timestamp-format assertion is enabled.
4. **Semantic validity:** company identities, record uniqueness, evidence-reference resolution, gate semantics and freshness rules are checked by application logic.
5. **Security protocol:** signature, key scope, audience, replay, sequence, revocation, quarantine and receipt-store behavior are tested independently.
6. **Operational resilience:** restart, storage outage, recovery, clock skew and incident handling are tested without weakening trust controls.

A pass in one layer does not imply a pass in another. JSON Schema validity does not authenticate a publisher or prove the truth of reported data.

## 2. M2 execution matrix

| ID | Area | Required case | Expected result | Current record |
|---|---|---|---|---|
| M2-001 | Source integrity | Record exact commit and blob SHA for schema, fixtures, prototype and tests | Reproducible source identity | Pending consolidated run record |
| M2-002 | Meta-schema | Validate committed schema against Draft 2020-12 meta-schema | Schema accepted | Not formally recorded against exact fetched blob |
| M2-003 | Root envelope | Validate complete committed envelope against exact schema | Zero validation errors | Not formally recorded against exact fetched blobs |
| M2-004 | Format assertion | Enable date-time format checking | Invalid timestamps rejected | Pending |
| M2-005 | Company cardinality | Exactly one registry record and snapshot per company | Valid pair accepted; duplicates/missing company rejected | Schema rules authored; execution pending |
| M2-006 | Strict parsing | Duplicate object keys | Reject before business validation | Code and regression test authored; execution pending |
| M2-007 | Strict parsing | NaN, Infinity and -Infinity | Reject before business validation | Code and regression test authored for NaN; execution pending |
| M2-008 | Structure | Unknown fields and malformed nested records | Reject cleanly with controlled error | Existing tests authored; expanded run pending |
| M2-009 | Identity | Company A data presented as company B | Reject | Existing tests authored; expanded run pending |
| M2-010 | Uniqueness | Duplicate gate, blocker or evidence IDs | Reject | Existing tests authored; expanded run pending |
| M2-011 | Evidence | Gate references missing evidence ID | Reject | Existing tests authored; expanded run pending |
| M2-012 | Evidence | Duplicate gate evidence reference | Reject | Existing tests authored; expanded run pending |
| M2-013 | Freshness | Stale, future or malformed reference time | Mark untrusted/stale or reject | Existing tests authored; expanded run pending |
| M2-014 | Fail-closed | Missing/unreadable fixture and invalid JSON | Controlled error; no partial trusted report | Existing tests authored; expanded run pending |
| M2-015 | Status | WAIVED critical gate | Never counts as PASS | Existing behavior; regression verification pending |
| M2-016 | Negative schema | Missing required field, extra field, invalid enum, wrong company cardinality | Reject | Negative cases partly checked in a reconstructed local copy; exact-blob run pending |
| M2-017 | Resource bounds | Oversized fixture, excessive nesting and oversized arrays/strings | Reject within bounded resource use | Explicit parser bounds and four regression tests authored; execution pending. Not a hostile-network parser. |

## 3. Authenticated publisher protocol test matrix (future M2/M3 security work)

These tests must use deterministic synthetic keys and payloads only. Do not connect company records or production keys.

| ID | Area | Required case | Expected result |
|---|---|---|---|
| SEC-001 | Signature | Valid signed message, active scoped key | Accept as authenticated, not automatically trusted as true |
| SEC-002 | Integrity | Mutate payload, digest or signature | Reject and quarantine |
| SEC-003 | Domain binding | Mutate company, publisher, audience or protocol version | Reject |
| SEC-004 | Key trust | Unknown, pending, expired, revoked or out-of-scope key | Reject |
| SEC-005 | Key freshness | Stale/unavailable trust or revocation registry | Fail closed for new ingestion |
| SEC-006 | Rotation | Approved overlap and post-rotation old-key message | Follow explicit transition policy; reject after revocation/effective expiry |
| SEC-007 | Replay | Duplicate message ID, duplicate sequence, lower sequence | Reject idempotently; do not advance accepted state |
| SEC-008 | Concurrency | Two simultaneous deliveries of same sequence | Exactly one acceptance |
| SEC-009 | Restart | Replay after receiver restart | Reject using durable receipt ledger |
| SEC-010 | Time | Future, expired, timezone-naive and excessive-age message | Reject or quarantine |
| SEC-011 | Schema | Extra field, invalid type, invalid timestamp | Reject |
| SEC-012 | Evidence | Unknown evidence ID or invalid gate reference | Reject or mark evidence unverified; never upgrade readiness |
| SEC-013 | Isolation | AI Revenue key signs Trading & Technology payload and vice versa | Reject |
| SEC-014 | Quarantine | Invalid message follows a previously accepted message | Preserve prior accepted snapshot and mark feed issue |
| SEC-015 | Storage | Receipt database unavailable | Defer/reject; no bypass or unauthenticated fallback |
| SEC-016 | Recovery | Restore receipt ledger and trust registry from backup | Reconcile sequence/revocation state before accepting messages |
| SEC-017 | Resource limits | Oversized body, deeply nested JSON, excessive array/string sizes | Reject within bounded resource use |
| SEC-018 | Secret hygiene | Logs and quarantine diagnostics | No private keys, credentials or unrestricted payloads |

## 4. Execution policy

- Do not install packages, start services, create keys, connect external systems, or invoke GitHub Actions under the current approval restrictions.
- Use only already-available offline tooling. Record tool name/version, exact source SHAs, command, timestamp and raw result for every execution.
- If the exact committed files cannot be materialized and hash-verified, label the result as a reconstructed-copy check, not a repository-commit validation.
- Never convert an authored test, a static inspection, or a reconstructed check into a passed execution record.
- Keep all signing keys synthetic and disposable until a separate owner-approved key-management design and isolated test boundary exist.

## 5. Exit criteria

M2 is not complete until the exact committed schema and envelope pass standards-compliant validation; the current full prototype suite passes against exact committed source and fixtures; negative tests prove fail-closed behavior; semantic evidence checks pass; and all results are tied to immutable commit/blob identifiers.

The authenticated-publisher protocol remains a design-only workstream until the protocol is frozen and separately tested. No production publisher, key, adapter or company connection is implied by this matrix.

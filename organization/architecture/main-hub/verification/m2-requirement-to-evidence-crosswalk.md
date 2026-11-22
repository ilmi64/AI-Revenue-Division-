# Main Hub / OCC M2 requirement-to-evidence crosswalk

**Status:** Static evidence mapping completed; NOT_EXECUTED. This is a traceability artifact, not a test report, security approval, or operational-readiness declaration.
**Scope:** AI Revenue and Trading & Technology company snapshots; synthetic fixtures only; read-only OCC.
**Branch:** `architecture/shared-ai-workforce-foundation`.

## 1. Exact source baseline inspected

| Artifact | Repository path | Blob SHA | What it contributes |
|---|---|---|---|
| Root record schema | `organization/architecture/main-hub/schema/records.schema.json` | `5b2dd53a7d5a72b8eed7ab647fcdb54d21edf3a0` | Draft 2020-12 root envelope and record definitions |
| Offline reader | `organization/architecture/main-hub/prototype/occ_readonly.py` | `9a39b3d5f1e6a3708bee4271b6be52c1a72b64e5` | Strict fixture parser, semantic checks, stale/untrusted display |
| Reader tests | `organization/architecture/main-hub/prototype/test_occ_readonly.py` | `e7c38a0365d604a04ac6d23f2cb7441fe3f6097f` | 29 authored standard-library regression tests |
| Exact-source validator | `organization/architecture/main-hub/prototype/validate_m2_schema.py` | `c02f2b20fc176a13c5348120ece4b1fb7fd7142d` | Git-blob pins, Draft 2020-12 meta-schema and complete-envelope validation |
| M2 verification matrix | `organization/architecture/main-hub/verification/m2-verification-matrix.md` | `2c5d93fee2ff19ece674e14261fe1cdf5f2ae988` | M2-001–018 and SEC-001–018 test requirements |
| Publisher design | `organization/architecture/main-hub/security/authenticated-publisher-design.md` | `3641240802b5d8de4cf7486fb825565c377c611c` | Signed-message trust, key lifecycle, replay, quarantine and rollout gates |
| Main Hub README | `organization/architecture/main-hub/README.md` | `c39e136e531d5361119f791186be8b502085b9e6` | Current truthful status and placement boundary |

The schema's expected blob SHA is also pinned in `validate_m2_schema.py`. The validator pins six inputs: schema, root envelope, two company snapshots, registry/workstreams fragment, and decisions fragment. The current inspection independently confirmed the schema pin. The other exact pin values are recorded in the validator and still require an execution record against the complete committed source set.

## 2. Requirement-to-evidence crosswalk

| Requirement | Contract / schema evidence | Implementation evidence | Test / validation evidence | Remaining gap and status |
|---|---|---|---|---|
| Two independent operating companies only | Root `company_registry` exactly two; company enum; `authority_boundary=independent_company`; `records_isolated=true` | `EXPECTED` allowlists `ai_revenue` and `trading_technology`; report iterates them separately | `test_both_companies_remain_separate_and_untrusted`; validator checks exact company set | Authored; execution pending |
| One snapshot per company | Root `status_snapshots` exactly two, with one of each company via contains/minContains/maxContains | `build_report` requires one named fixture per expected company | Validator checks unique company IDs and exact set; reader pair test | Formal schema + semantic execution pending |
| Strict root envelope | Schema `additionalProperties=false`, required top-level fields | Current reader consumes company snapshot fragments, not the complete root envelope | `validate_m2_schema.py` validates complete root envelope | Keep root-envelope validation distinct from snapshot-reader tests; validator unrun |
| Strict snapshot allowlist | `$defs.snapshot` required fields and no additional properties | `_keys(snapshot, required, set(), "snapshot")` | `test_unapproved_extra_field_rejected` | Authored; execution pending |
| Company identity binding | Snapshot company enum | `assess_snapshot` compares expected company against snapshot company and fixed allowlist | `test_company_identity_mismatch_rejected` | Authored; execution pending |
| Schema version pin | Snapshot schema version const `0.1` | Reader rejects unsupported schema version | No separately named regression test identified in current 29-test file | Add explicit negative case in a future authorized test update; current status gap |
| Source revision identity | Schema requires string minLength 7 | Reader requires non-empty source revision and minimum length 7; synthetic prefix remains untrusted | Source pin validator covers schema/fixture blobs, not semantic company revision authenticity | Company source revision is an identifier claim, not authenticated provenance |
| Overall/subsystem status vocabulary | Schema enums | `VALID_OVERALL`, `VALID_SUBSYSTEM` | Current test set exercises stale and untrusted status, not every enum | Negative enum coverage not fully evidenced; execution pending |
| Gate structure and state | `$defs.gate`; PASS/FAIL/BLOCKED/NOT_RUN/WAIVED; critical boolean; evidence refs | Reader validates exact fields, enum, boolean, notes type, non-empty refs, unique gate IDs | `test_critical_waived_gate_is_not_pass`; malformed gate and non-string enum tests | Authored; execution pending |
| Gate evidence resolution | Schema defines evidence and references as strings | Reader resolves every gate evidence ref to an evidence ID in same snapshot | `test_gate_rejects_unknown_evidence_id`; duplicate reference test | Reference existence only; does not verify evidence truth or independent review |
| Blocker structure and severity | `$defs.blocker` | Reader validates exact fields, severity, summary and unique blocker IDs | Malformed blocker and duplicate blocker tests | Authored; execution pending |
| Incident summary | Required open_count, highest_severity, quarantined | Reader rejects bool-as-int, negative counts, invalid severity and non-boolean quarantine | Malformed incident record test | Boundary-value coverage not fully mapped; execution pending |
| Evidence record structure | `$defs.evidence`; type enum; optional verified_at | Reader validates exact fields, evidence type, timestamp and unique evidence IDs | Malformed evidence, unexpected field, duplicate ID tests | Reference strings are not proof of evidence integrity; independent verification absent |
| Timestamp and freshness | date-time schema format; publisher design issued_at/expires_at and max age | `_parse_time` requires timezone; reader computes age and future tolerance; stale display | timezone, naive clock, invalid clock type, negative/non-integer max-age, stale tests | Formal format assertion and full future-boundary tests pending |
| Strict JSON parsing | Verification matrix M2-006/007 | duplicate-key hook, non-standard constant rejection, UTF-8 decode, bounded iterative walk | duplicate key, NaN, oversized file/depth/string/array tests | Infinity/-Infinity, node count, object member and invalid UTF-8 cases not individually evidenced in current suite |
| Resource limits | M2-017 | 1 MiB fixture; depth 32; 20,000 nodes; 1,000 array items; 256 object members; 8,192-char strings/keys | Four authored tests for file size, nesting, string and array | No hostile-network parser claim; execution pending |
| Exact-source integrity | M2-001/M2-018 | Validator computes GitHub blob SHA-1 and compares six pinned source blobs | `validate_m2_schema.py` | Authored only; not run; source-pin completeness requires full exact-blob execution |
| Draft 2020-12 schema validity | M2-002 | Validator calls `Draft202012Validator.check_schema` | Exact-source validator | Requires already-available jsonschema package; no install authorized; not run |
| Full root-envelope validity | M2-003/M2-004 | Validator applies Draft202012Validator and FormatChecker to complete envelope | Exact-source validator | Not run; not equivalent to snapshot-fragment reader tests |
| Semantic record uniqueness | M2-005/M2-010–012 | Reader checks gate/blocker/evidence IDs and evidence refs; validator checks company/workstream/decision IDs | 29-test suite and validator | Cross-record referential integrity beyond gate-to-evidence is not established |
| Publisher authentication | SEC-001–006 | Ed25519/RFC 8785 design only | No publisher/receiver implementation or cryptographic test vectors | NOT_IMPLEMENTED; no authenticated message can currently be accepted |
| Replay and atomic ordering | SEC-007–009 | Design specifies durable uniqueness and monotonic sequence | No receiver or durable replay ledger | NOT_IMPLEMENTED |
| Tenant isolation | SEC-013 | Schema and reader bind company ID; publisher design scopes keys to one company | Identity mismatch test only | No cryptographic cross-company test; no live tenant connection |
| Quarantine and last-known-good preservation | SEC-014 | Publisher design defines quarantine without replacing last accepted snapshot | Reader fails closed on malformed fixture but has no receiver quarantine store | NOT_IMPLEMENTED |
| Storage outage and recovery | SEC-015/016 | Design requires durable receipt ledger and tested restore | No production store or recovery implementation | NOT_IMPLEMENTED |
| Secret hygiene | SEC-018 | Schema excludes unlisted fields; publisher design excludes private keys and secrets | Unexpected-field tests | No log inspection, secret scanning or operational controls executed |
| OCC authority boundary | README and publisher design state read-only consumer | Prototype emits report only; no action interface | Static source inspection | No production deployment; no command, approval, budget or trading authority |

## 3. Important implementation distinctions

1. The offline reader validates two per-company snapshot fixture files. It does not ingest or authenticate a signed publisher envelope.
2. The exact-source validator validates the complete root envelope against the schema. It is a separate utility, not part of `build_report`.
3. The schema allows a publisher-reported `HEALTHY` claim, but the reader's `display_status` remains `UNKNOWN` for fresh unauthenticated data and `STALE` for stale data. This separation must be preserved.
4. The reader's evidence list is a collection of references and types. It does not fetch, hash, inspect or independently verify the referenced artifacts.
5. The publisher design is a protocol proposal. There is no implemented Ed25519 verifier, canonicalization boundary, trusted key registry, atomic sequence ledger, quarantine store, adapter, company publisher or production receipt database.
6. The schema's `verified_at` is a timestamp field, not proof that an independent reviewer verified evidence.
7. No OCC data may authorize an external action or override either company's own decision rights.

## 4. Execution register — intentionally unchanged

| Verification item | Current state |
|---|---|
| 29-test latest reader suite | AUTHORED / NOT_RUN |
| Exact-source validator | AUTHORED / NOT_RUN |
| Draft 2020-12 meta-schema validation | NOT_RUN |
| Full root-envelope validation with format checker | NOT_RUN |
| Security protocol SEC-001–018 | DESIGN / NOT_IMPLEMENTED / NOT_RUN |
| Independent security review | NOT_PERFORMED |
| Recovery rehearsal | NOT_PERFORMED |
| Company publisher adapters | NOT_IMPLEMENTED |
| Production OCC | NOT_OPERATIONAL |
| Live company connections | NONE |
| Owner authorization to connect | NOT_GRANTED |

## 5. Recommended next sequence

1. Preserve this exact source baseline and confirm all six validator pins against repository blobs.
2. In an already-available offline environment, and only after explicit authorization, run the exact-source validator without installing dependencies; capture interpreter/package versions, command, timestamp, exit code and output.
3. Separately run the 29-test suite against the exact committed source and fixtures; do not merge this result with schema-validation evidence.
4. Add missing negative cases only through a separately authorized source change: unsupported schema version, invalid UTF-8, Infinity/-Infinity, node/member bounds, future timestamp boundary and missing company fixture.
5. Reconcile any failures, update the evidence ledger, and rerun only with authorization.
6. Freeze the signed-publisher protocol and deterministic vectors before any adapter implementation proposal.
7. Require independent security and recovery review before any owner decision about a limited read-only connection.

**Conclusion:** M2 has meaningful reference implementation and authored verification coverage, but it is not verified complete. The accurate state is **REFERENCE_CODE_PRESENT_UNVERIFIED; TESTS_AUTHORED_NOT_RUN; SCHEMA_VALIDATION_AUTHORED_NOT_RUN; AUTHENTICATED_PUBLISHER_NOT_IMPLEMENTED; OCC_NOT_OPERATIONAL**.

# M2 static source-pin confirmation and coverage delta

**Status:** STATIC_REVIEW_COMPLETE / NOT_EXECUTED. This is a source-inspection addendum, not a validation run, test result, security review, or operational-readiness claim.
**Branch:** `architecture/shared-ai-workforce-foundation`
**Scope:** Exact GitHub blob identity for the six files pinned by the M2 validator, plus a static comparison of the committed reader and 29-test suite against the verification matrix.

## 1. Six pinned source blobs independently matched

The six values below were fetched from this exact branch using the repository file API. Each returned Git blob SHA equals the corresponding `EXPECTED_BLOB_SHAS` value in `prototype/validate_m2_schema.py`.

| Validator pin | Fetched blob SHA | Static result |
|---|---|---|
| `schema/records.schema.json` | `5b2dd53a7d5a72b8eed7ab647fcdb54d21edf3a0` | MATCH |
| `fixtures/main-hub-envelope.example.json` | `9f3d7d83ee0d87f7cba1fbda7002c5b9b7d856d0` | MATCH |
| `fixtures/ai-revenue.snapshot.example.json` | `e2a1019ae9327dd4bed56f1bf8a1801b49aaae33` | MATCH |
| `fixtures/trading-technology.snapshot.example.json` | `ecc536031e115eadc71493a3da81ec3c8839e3ac` | MATCH |
| `fixtures/registry-and-workstreams.example.json` | `d001e4ee87544ab6628ad6b95d1ddb9e5c87ea98` | MATCH |
| `fixtures/decisions.example.json` | `a6ebb6a7596248568f0c26888b2984e66b48c9e0` | MATCH |

**Interpretation:** The six pinned input files currently match the validator's committed expected blob identities. This was a static comparison of repository metadata. The validator was not executed, and no claim is made that its Python dependencies are installed or that schema/format validation passed.

## 2. Exact inspected implementation baseline

| Artifact | Blob SHA | Static observation |
|---|---|---|
| `prototype/occ_readonly.py` | `9a39b3d5f1e6a3708bee4271b6be52c1a72b64e5` | Strict per-company fixture reader; schema-version equality check; bounded JSON walk; fail-closed unauthenticated display |
| `prototype/test_occ_readonly.py` | `e7c38a0365d604a04ac6d23f2cb7441fe3f6097f` | Exactly 29 authored test methods; NOT_RUN |
| `prototype/validate_m2_schema.py` | `c02f2b20fc176a13c5348120ece4b1fb7fd7142d` | Six pinned input files; Draft 2020-12 schema check; complete-envelope validation with FormatChecker; NOT_RUN |
| `verification/m2-verification-matrix.md` | `2c5d93fee2ff19ece674e14261fe1cdf5f2ae988` | M2-001–018 and SEC verification plan |
| `security/authenticated-publisher-design.md` | `3641240802b5d8de4cf7486fb825565c377c611c` | Protocol design only; no receiver or publisher implementation |

## 3. Coverage corrections and deltas

1. **Schema-version check exists in the reader.** `assess_snapshot` rejects any snapshot whose `schema_version` is not exactly `0.1`. However, none of the 29 named test methods directly mutates this field to verify that rejection. Mark implementation present, dedicated regression fixture absent.
2. **Non-finite numeric constants:** the reader's `parse_constant` hook rejects any non-standard JSON constant, not only NaN. The authored suite has a NaN regression test; Infinity and -Infinity do not have separate named tests.
3. **Resource limits:** implementation defines limits for bytes, nesting depth, total nodes, array items, object members and string/key lengths. The 29 tests explicitly cover bytes, depth, array length and string length. No dedicated named test covers total node count or object-member count.
4. **UTF-8:** the reader catches invalid UTF-8 and converts it to a controlled `SnapshotError`; no dedicated named invalid-UTF-8 test is present.
5. **Missing company fixture:** `build_report` reads both expected filenames and fails on an unreadable/missing file. No dedicated named missing-file test is present in the 29-test suite.
6. **Freshness boundary:** the suite covers stale snapshots, timezone requirements and invalid reference clocks/max-age inputs. It does not have a dedicated named test for the exact future-timestamp tolerance boundary or the just-at-max-age boundary.
7. **Exact-source scope:** the validator pins the schema and five fixture inputs. It does not self-pin its own source, the reader source, the test source, the verification matrix, or publisher design. Therefore its six-input pin check is not a complete source attestation for the whole M2 implementation/test bundle.
8. **Schema and semantic layers remain distinct:** the validator checks the complete root envelope; the reader checks per-company snapshot fixture files. Neither authenticates a publisher, independently verifies referenced evidence, or establishes readiness.

## 4. Revised evidence ledger

| Evidence item | State |
|---|---|
| Six validator input blob identities | STATIC_MATCHED |
| Reader source inspected | REFERENCE_CODE_PRESENT_UNVERIFIED |
| 29 reader tests enumerated | AUTHORED / NOT_RUN |
| Draft 2020-12 schema validator | AUTHORED / NOT_RUN |
| Full root-envelope and format validation | AUTHORED / NOT_RUN |
| Missing negative cases listed above | GAP_TO_SPECIFY |
| Ed25519 publisher/receiver | DESIGN_ONLY / NOT_IMPLEMENTED |
| Replay ledger, quarantine store, durable receipts | NOT_IMPLEMENTED |
| Independent security review | NOT_PERFORMED |
| Production OCC / company connections | NOT_OPERATIONAL / NONE |

## 5. Recommended next sequence

1. Preserve this source baseline.
2. If and when explicitly authorized, run the validator and test suite separately in an already-available offline environment; do not install dependencies.
3. Record interpreter and dependency versions, exact command, timestamp, exit code and full output.
4. Only after reviewing those results, prepare a narrow test-only change for the missing negative cases. Do not alter production-facing behaviour merely to increase test count.
5. Separately complete protocol test vectors and threat-model review before any publisher/receiver implementation proposal.

**Conclusion:** The six pinned schema/fixture inputs match their expected repository blob identities. M2 still remains unexecuted and unverified; authenticated publishing and operational OCC remain unimplemented.

# Main Hub / OCC M2 Static Gap-Closure and Source-Attestation Plan

**Status:** STATIC PLAN ONLY / NOT EXECUTED / NOT TESTED / NOT AUTHORIZED FOR IMPLEMENTATION.  
**Review date:** 2026-11-21  
**Boundary:** Synthetic fixtures only; OCC remains read-only. No publisher/receiver, production connection or operational claim.

## 1. Baseline

This plan follows the M2 static source-pin and coverage review. The six schema/fixture input blobs were statically matched to the validator's expected Git blob identities. The offline reader and 29 authored tests were inspected; tests and schema validation remain NOT_RUN.

Exact inspected baseline from the source-pin review:

| Artifact | Blob SHA | Status |
|---|---|---|
| prototype/occ_readonly.py | 9a39b3d5f1e6a3708bee4271b6be52c1a72b64e5 | Inspected reference reader; not executed |
| prototype/test_occ_readonly.py | e7c38a0365d604a04ac6d23f2cb7441fe3f6097f | 29 authored tests; NOT_RUN |
| prototype/validate_m2_schema.py | c02f2b20fc176a13c5348120ece4b1fb7fd7142d | Authored validator; NOT_RUN |
| schema/records.schema.json | 5b2dd53a7d5a72b8eed7ab647fcdb54d21edf3a0 | One of six validator-pinned inputs |
| security/authenticated-publisher-design.md | 3641240802b5d8de4cf7486fb825565c377c611c | Design only; no receiver/publisher |

These hashes are a historical inspection baseline, not proof that the branch has not changed since the review. Re-fetch exact blob SHAs before any later edit or validation plan.

## 2. Static negative-test gap register

The following additions are test-design proposals only. Preserve existing test names and behavior; use isolated fixture copies and assert explicit fail-closed outcomes.

| Gap ID | Missing dedicated case | Proposed test intent | Expected result | Risk addressed |
|---|---|---|---|---|
| M2-GAP-01 | Unsupported snapshot schema version | Change only schema_version to an unsupported value | Snapshot rejected with controlled SnapshotError | Prevent schema drift being silently accepted |
| M2-GAP-02 | Positive Infinity JSON constant | Supply a fixture containing Infinity | Strict parse rejection | Non-standard JSON numeric acceptance |
| M2-GAP-03 | Negative Infinity JSON constant | Supply a fixture containing -Infinity | Strict parse rejection | Non-standard JSON numeric acceptance |
| M2-GAP-04 | Total-node boundary | Construct a structurally valid fixture just above max_nodes | Controlled resource-limit rejection | Parser resource exhaustion |
| M2-GAP-05 | Object-member boundary | Construct an object above max_object_members | Controlled resource-limit rejection | Oversized object parsing |
| M2-GAP-06 | Invalid UTF-8 | Provide invalid UTF-8 bytes through the reader's supported input seam | Controlled SnapshotError, no traceback leakage | Encoding failure handling |
| M2-GAP-07 | Missing company fixture | Omit one expected company file | Controlled fail-closed report error | Incomplete two-company view |
| M2-GAP-08 | Future timestamp tolerance | Test exactly at and just beyond the allowed future skew | Boundary behavior matches documented tolerance | Clock-skew ambiguity |
| M2-GAP-09 | Just-at-max-age boundary | Test exactly at and just beyond the configured age limit | Freshness decision matches the declared inclusive/exclusive rule | Freshness off-by-one |
| M2-GAP-10 | Validator pins its own source | Verify validator blob against an external, reviewed manifest | Exact source identity mismatch blocks validation | Validator self-integrity |
| M2-GAP-11 | Reader and test source identity | Compare exact reader/test blobs against same reviewed manifest | Unreviewed reader/test revision cannot be presented as attested | Source bundle completeness |
| M2-GAP-12 | Matrix and publisher-design identity | Pin exact verification matrix and publisher design alongside code | Report names exact inspected design/source set | Traceability completeness |

The current implementation's existing broad exception handling, JSON parse hooks and resource-limit checks were not changed by this plan. Whether each proposed test can be written without altering production code must be determined during a separately authorized code review.

## 3. Source-attestation model

The current validator pins six inputs but does not self-pin the validator, reader, tests, matrix or publisher design. A future attestation manifest should therefore contain:

- repository full name, branch/ref and exact commit SHA;
- schema and all fixture blob SHAs;
- reader, validator and test blob SHAs;
- verification matrix and publisher-design blob SHAs;
- manifest version and canonical digest;
- reviewed-by identities, review date and review disposition;
- exact command/environment and validation output references, if later authorized.

The manifest must be reviewed and anchored independently of the validator it attests. A manifest stored beside the files is useful for reproducibility but is not, by itself, an independent trust root. No signing key or trusted publishing mechanism currently exists in this M2 prototype.

## 4. Validation sequencing and authorization boundary

1. Freeze an exact revision and re-fetch all relevant blob SHAs.
2. Review proposed test additions and test seams; do not alter runtime behavior merely to increase test count.
3. Review schema, fixture, reader and validator compatibility as separate layers.
4. Obtain explicit owner authorization for offline validation against the exact frozen revision.
5. Use only already-available dependencies; no package installation or network fetch.
6. If authorized, run schema validation and reader tests as separate commands and record interpreter/dependency versions, command, timestamp, exit code and full output.
7. Reconcile every failure; do not weaken assertions to make the suite pass.
8. Independently review source attestation, signature/replay protocol and tenant-isolation design before proposing publisher/receiver implementation.
9. Keep production publisher, receiver, replay ledger, quarantine store, durable receipts and key lifecycle unimplemented until separate approval and assurance gates pass.

This document authorizes none of the above execution steps.

## 5. Cross-company mirror rule

Trading & Technology must receive an equivalent static crosswalk and gap register in its own repository. Each mirror is company-scoped, with the same semantic criteria but independently pinned source revisions. One company's validation or source hashes cannot attest the other company's code, fixtures or policy. OCC remains a read-only consumer and cannot issue approvals or alter company state.

## 6. Current disposition

- Six validator-pinned schema/fixture inputs: STATIC_MATCHED at the recorded inspection point.
- Reader source: INSPECTED / NOT_EXECUTED.
- 29 authored tests: NOT_RUN.
- Schema validation: NOT_RUN.
- Missing dedicated negative cases: SPECIFIED AS GAPS.
- Complete source attestation: NOT ESTABLISHED.
- Publisher/receiver, signature verification, replay ledger, quarantine and durable receipts: NOT_IMPLEMENTED.
- Independent security review: NOT_PERFORMED.
- Production OCC: NOT_OPERATIONAL.

**Next action:** static review this gap register against the current M2 matrix and both company mirrors; do not run tests or edit implementation until separately authorized.

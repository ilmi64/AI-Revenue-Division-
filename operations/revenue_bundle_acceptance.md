# Aevora AI private scheduled bundle acceptance

This local synthetic review step uses the existing fixture scheduler and
deterministic internal review ZIP. Only an exact, already reviewed result
can enter acceptance. It does not contact a requester, dispatch a worker,
publish a package, approve commissioning or authorize external delivery.

## Local interface

Bootstrap `InternalBundleAcceptor(scheduler, authority=...)` with the
current company-local trust provider. Reuse the scoped provider contract
from signed reservation recovery. Provision a separate active Ed25519
principal with the `ar_engineering_reviewer` purpose in the AI Revenue
partition. The verifier checks role, company, validity, revocation and
separation from every fixture participant in the reviewed handoffs.
The pinned [workforce role catalogue][roles] is the source for the role.
The test provider and signing keys are synthetic.

For a completed scheduled request, `claim(request_id)` provides private
review metadata. It binds the exact company and recipient, request ID,
canonical request digest, persisted result digest, deterministic ZIP
digest and manifest digest. The independent reviewer inspects the private
internal bundle and signs the bytes returned by
`acceptance_payload(BundleAcceptanceAuthorization(...))`. The signature
has a separate purpose, role, key ID, current trust epoch and short
validity window.

`accept(request_id, bundle, authorization)` regenerates the ZIP from
the validated scheduler result and requires exact byte equality. It
does not parse a caller's archive. It validates signature and trust,
checks current epoch again and rechecks expiry before recording one
private acceptance. The SQLite transaction compares the exact persisted
request and result before and after insert. Duplicate acceptance or
an in-transaction change blocks. The receipt is
`INTERNAL_EVIDENCE_ACCEPTED`, commissioning stays `HOLD`, and
`release_authorized` is always false.

`private_record(request_id)` returns canonical historical evidence for
the company-local caller. It preserves the signed payload, signature,
reviewer and digests. Readback checks the stored record and exact local
result. It is not a new authority decision, live signer re-verification
or independent anti-rollback storage. Restrict this local interface,
SQLite store and output to authorized company users. OCC continues to
receive only the existing read-only aggregate.

New databases use `revenue_fixture_schedule.sql`. Apply
`revenue_fixture_schedule_v4.sql` once to an existing v3 fixture with
all scheduler clients stopped. For earlier fixtures, apply prior
migrations in order. Existing review results are not modified.

## Reproduce offline

Run from `operations` in a network-denied Python environment. The
package and scheduler use the standard library. This acceptance step
requires an already available Ed25519 backend, a separately provisioned
company reviewer key and a verified existing private package. The
tests use existing `cryptography` and deterministic synthetic keys.
Missing trust or verifier backend blocks acceptance.

```sh
python -m unittest -v test_revenue_bundle_acceptance test_revenue_internal_review_bundle
python -m unittest -v test_revenue_bundle_acceptance test_revenue_internal_review_bundle test_revenue_reservation_recovery test_revenue_priority_schedule test_revenue_fixture_schedule test_revenue_workflow_demo
python -m unittest discover -v
```

An approved offline native pilot would separately require vetted local
version-pinned Paperclip/Ruflo artifacts and transitive dependencies, an
approved model runtime and local weights where applicable, and independent
identity, tool/data, revocation, audit and recovery evidence. None of
those inputs is installed, validated or approved by this work. See
[the native commissioning blockers](revenue_native_commissioning.md).
Production roles, durable independent custody and real owner approval
remain open. Local tests do not authorize release.

[roles]: https://github.com/ilmi64/AI-Revenue-Division-/blob/c8cb3b92d9a783802ec017670b8ef70a36ff9572/organization/architecture/paperclip-role-id-and-org-chart-configuration-draft.md

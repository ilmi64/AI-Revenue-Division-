# OCC read-only prototype v0.1

**Classification:** Offline reference prototype; synthetic data only; not operational.

## Run locally

From this directory:

```sh
python occ_readonly.py
python -m unittest -v
python validate_m2_schema.py
```

The default fixture directory is the sibling `../fixtures` directory. The program reads two JSON snapshots and prints a JSON report to stdout. An optional `--output` path writes a report file locally.

## Safety limits

- Python standard library only; no package installation required.
- This is an offline fixture demonstrator, not a hardened parser for hostile network input. It applies explicit caps: 1 MiB per fixture, nesting depth 32, 20,000 JSON nodes, 1,000 items per array, 256 members per object and 8,192 characters per string/key. These are prototype safety bounds, not a substitute for a hardened network-facing parser.
- No network calls, web server, database, credentials, external actions, or company adapter.
- Strict field allowlist; rejects identity mismatch, unexpected fields, duplicate JSON object keys, non-standard JSON constants, invalid reference clocks, and invalid freshness limits.
- Rejects duplicate gate, blocker, and evidence IDs; gate evidence references must resolve to evidence IDs in the same company snapshot.
- Malformed or missing fixture files fail closed with a concise contextual error.
- Synthetic source revisions are explicitly untrusted.
- All unauthenticated sources remain `UNKNOWN`; stale sources display `STALE`.
- A critical gate is considered unresolved unless its state is exactly `PASS`; `WAIVED` is not a pass.
- This prototype does not authenticate publishers, verify signatures, prevent replay, prove source-revision provenance, or validate the full JSON Schema. It is not a readiness authority.
- `validate_m2_schema.py` is a separate offline validation utility. It pins exact GitHub blob identities for the schema and synthetic fixtures, invokes the Draft 2020-12 validator with date-time format checking, and checks company/record identity uniqueness. It requires the already-available `jsonschema` package; do not install anything if it is unavailable. The validator script has been authored but has **not** been executed.

## Current verification record (2026-11-21)

- Latest prototype code commit: `415946922ecf6fd1e4573cfeb0ce18d38dcc2441` (blob `9a39b3d5f1e6a3708bee4271b6be52c1a72b64e5`).
- Latest test-suite commit: `5a91e4210b3ed7d8e2fcc4a8d5f7f41a27f036a8` (blob `e7c38a0365d604a04ac6d23f2cb7441fe3f6097f`; 29 authored tests; execution pending).
- A custom, offline structural check was applied to the exact committed schema and fixtures. The complete envelope, both company snapshots, registry companies, workstreams, and decisions produced no errors under the checker's implemented schema assertions.
- Negative checks rejected a missing company snapshot, a duplicated company identity, and an unexpected field.
- This is a custom structural check, **not** a standards-compliant Draft 2020-12 validator. Formal schema validation remains open. The latest resource-bound code and four regression tests are authored but have not yet been executed.
- The exact prior committed source, test and fixture contents were reproduced locally and the 14-test suite passed (2026-11-20). That run predates the current integrity hardening and the expanded 29-test suite; rerun the latest exact revision before treating the expanded suite as verified.

## Next required work

1. Re-run the expanded standard-library test suite against the exact updated commit and record the result.
2. Execute `python validate_m2_schema.py` against the exact pinned schema/fixture blobs, using the already available `jsonschema` package and date-time format assertion. The script is authored; execution and evidence recording remain pending.
3. Design authenticated, company-owned publishers and freshness/replay protections before accepting any non-synthetic data.
4. Keep company data stores and decision authority separate.

### Unified company visibility (offline)

Run the aggregate viewer with independently assigned synthetic inputs:

```sh
python occ_company_visibility.py \
  --ai-revenue-snapshot ../fixtures/ai-revenue.snapshot.example.json \
  --trading-snapshot ../fixtures/trading-technology.snapshot.example.json
```

The optional `--aevora-operations` path accepts the redacted output of
Aevora AI's `revenue_workflow_demo --mode anchored --view occ`. That
aggregate contains no publication timestamp or publisher authentication, so
its counters are labeled `UNVERIFIED_UNTIMED`.

The viewer displays allowlisted subsystem states and aggregate counts by
company. Missing data stays unknown. A rejected, stale, or quarantined company
snapshot contributes no counts, and each other input is evaluated independently.
Synthetic and unauthenticated inputs never establish operational readiness. The
viewer writes only to stdout and does not expose evidence references, raw
identifiers, descriptions, approvals, or action controls.

### Authenticated synthetic visibility

`occ_signed_visibility.py` implements an offline prototype for the publisher
design above. It uses Ed25519, existing `cryptography` and `jsonschema` modules,
and an explicit SQLite receipt journal. It does not attach to the viewer CLI,
run a service, discover publishers, or read signing secrets. A verifier accepts
a caller-provisioned `PublisherTrust` for each company's own synthetic public
key, publisher ID, key ID, validity window and exact producer commit. Trading's
optional `payload_source_revision` distinguishes the paper source revision
reported by M2 from the revision of the publisher code.

A synthetic fixture incidentally re-signed under the wrong company key fails
scope and signature checks. Only the M2 report for Trading and the existing
redacted Aevora operations aggregate have prototype report type IDs. The signed
format is a local test format. It uses the UTF-8-compatible ASCII output of
Python JSON with sorted object keys, no spaces, escaped non-ASCII, no floats,
and safe-range integers. The wire record has exactly `claims` and
`signature_hex`. Ed25519 signs the bytes of `daivora.occ.visibility/synthetic-v1`
followed by NUL and the canonical claims. Claims bind the company and publisher,
key, audience, type, source revision, snapshot ID, sequence, UTC timestamps,
and SHA-256 of the canonical payload; inbound messages must be byte-for-byte
canonical. This format does not assert RFC 8785 or cross-language conformance.

For synthetic verification, provision a new temporary
`ReceiptJournal.initialize(path)`, wrap redacted fixtures with `sign_fixture`
using test-only keys, and supply the resulting bytes with
`build_authenticated_visibility`. This adds to the OCC-owned journal only.
A missing journal or stale, invalid or replayed message cannot produce a
summary. Each company's acceptance and sanitized display remain separate. The
view's authentication flag attests to the scoped signature and local receipt;
it confers no evidence verification, readiness, or company-side authority.

For a company-isolated rehearsal, initialize separate files with
`ReceiptJournal.initialize(path, company_id=company)` and pass them as
`journal_by_company` keyed by `ai_revenue` and `trading_technology`. The stored
company binding rejects a journal assigned to the wrong scope. Missing or
unavailable state for one company rejects its receipt while the peer still uses
its own journal. Shared-journal mode remains available for earlier offline
fixtures. An isolated call never falls back to it.

For an anchored offline rehearsal, give `FixtureReceiptAnchor` a mapping from
company ID to `(journal_id, PublisherTrust)` and keep it separate from the
journal files. Initialize each journal with
`ReceiptJournal.initialize(path, company_id=company, anchor=authority)` and
reopen it with `ReceiptJournal(path, company, authority)`. Use the same
independent authority across journal reopen or replacement. The trusted
custody pin covers the company, publisher, key ID and public key, valid dates,
revocation flag, and source revision pins. The authority retains a checkpoint
over the ordered receipt digests for each company.

An anchored journal rejects replays, wrong scope, custody changes, lost
authority, and local history that differs from the independent checkpoint.
Restoring an exact checkpoint-aligned journal resumes normal verification.
When the authority advances and the local write cannot be confirmed, suspend
that company's feed until its exact anchored state is recovered. The peer
retains its own verification path. No private report body, publisher key
material, or authority is included in the output.

The in-memory authority is a fixture implementing the `ReceiptAnchor`
interface. It does not survive process loss and must not be reconstructed
from a restored journal to approve a rollback. Production custody, key
transitions, an independently durable authority, a crash reconciliation
runbook, privacy-reviewed authenticated channels and protocol review remain
open.

A separately stored `DurableReceiptAnchor` implements the same interface with
transactional compare-and-advance. Provide an out-of-band synthetic custodian
public key for each company. Use a distinct authority file per company to
isolate authority outages, and keep each authority outside its receipt
journal's restore domain. Reopening the authority requires the original
public verification key. Neither verification store is created during an
ordinary replay check.

After a lost local receipt commit, `reconcile_pending_receipt` repairs only
one exact signed receipt when that wire is still valid and matches the
independent checkpoint. It does not publish or advance the checkpoint. Other
mismatches require an exact aligned backup and independent review. Replacing
publisher custody requires `transition_custody`, aligned journal history,
and an independent Ed25519 authorization bound to the exact company,
current checkpoint, replacement configuration and approval window. Existing
receipt history is retained and approval replay fails closed. Aevora's
aggregate uses sequence-derived snapshot IDs, so a replacement publisher
must continue with fresh IDs even if its key-local sequence could restart.

Rolling back the authority and journals together remains outside this local
fixture threat model. Production key custody, protected independent storage,
recovery drills, and owner authorization remain separate requirements.

### Company-scoped divisional telemetry

A company publisher can opt in through its approved
`PublisherTrust(divisional_telemetry=True, ...)` custody configuration and
company-anchored journal. The extended signed report wraps the existing
company report in `report` and adds `divisional_telemetry`. Its
`company_totals` and each named row in `divisions` carry exactly
`open_incident_count`, `pending_approval_count`, and `blocker_count`.

Report counts by primary division without duplication. The sum of disclosed
division counts cannot exceed the company totals. An omitted division has
unknown counts. A reported zero applies only to that named scope. Trading's
company incident and blocker totals must agree with its pinned M2 snapshot.
Aevora's operations queue statuses and pending approval count are distinct
reporting dimensions. OCC does not infer one from the other.

Invalid, stale, replayed, or quarantined data exposes no new counts. Previously
approved basic-only custody and wire formats remain valid for their original
scope. An extended publisher cannot switch its approved custody by changing
the signed report type. Authentication does not establish operational
readiness or approve any pending action.

The mobile export shows the named commissioning gate when a validated M2
snapshot includes it. For signed, available reports with divisional
telemetry, it also displays company totals and expandable division counts
for open incidents, pending approvals and unresolved blockers. Missing
divisions display Unknown. Export the unsigned fixture view with
`occ_company_visibility.py --format mobile-html`, or pass the verified
in-process report to `occ_mobile_visibility.render_mobile_visibility`.
The HTML uses embedded styling and exposes no external resources or actions.

### Witnessed publisher enrollment

A new durable offline authority can require a possession proof from the
publisher and a witness signature from the separately configured company
custodian. The operator supplies a fresh external challenge, the expected
journal ID and pinned publisher custody. Those values, the custodian's public
key, and a short UTC validity interval bind both signatures. The witness
signs the publisher's exact proof as well as its binding.

Pass `enrollments={company: (expected_challenge, proof)}` and a trusted
`now` to `DurableReceiptAnchor.initialize`. Check every configured scope
before creating a file. Retain the returned `enrollment_pins` in independent
fixture configuration with the original custodian public keys. Reopen with
`DurableReceiptAnchor(path, authority_public_keys, enrollment_pins)`.
Missing or changed proof pins fail closed for the affected company. Proof
signatures, challenges, private keys and evidence digests do not appear in a
company view.

Earlier un-witnessed fixtures remain available as legacy mode. A witnessed
authority cannot reopen in that mode. This is an offline enrollment check
for a newly provisioned authority, with synthetic keys. Subsequent custody
transitions retain their separate exact-approval gate. Production key
provisioning, independently protected configuration, and recovery review
remain separate requirements.

The mobile export records the UTC time used to assess the source reports.
For signed in-process exports, pass the same verifier clock reading to
`render_mobile_visibility(report, assessed_at=now)` that was supplied to
`build_authenticated_visibility`. Saved HTML shows the historical assessment
time. The timestamp does not promote untimed evidence or grant release.

Witnessed enrollment also requires a separate company custodian witness for
single-receipt repair. Call `pending_repair_checkpoints` with the still-valid
signed wire to preview the current local checkpoint, advanced independent
checkpoint, and wire SHA-256. The call is read-only. The custodian signs
`pending_repair_bytes` over that exact tuple and a short UTC window. Supply
the resulting `CustodyAuthorization` to `reconcile_pending_receipt`, which
rechecks current scope and state before writing the missing local row.

This repair does not advance the authority, return a company view, grant
release, or approve a new receipt. Missing, expired, wrong-scope, and stale
witnesses fail closed. An unavailable witness verifier does not permit legacy
repair in a witnessed journal.

### Company commissioning procedure

1. Security & Recovery supplies a new company-scoped challenge and records
   the intended publisher ID, journal ID, source pin, validity window,
   custodian public key and expected company. Trading and Revenue each have
   separate publisher and custodian principals. Keep private keys out of
   OCC and give each company an independently protected store and backup.
2. The publisher signs the exact enrollment binding. The company custodian
   verifies publisher identity and possession and witnesses those bytes.
   Provision each company's anchor and journal separately. Retain the
   resulting enrollment digest outside both SQLite files in protected
   company-specific verifier configuration, with the approving custodian
   and an audit reference. Store signed enrollment and recovery evidence
   in that company's restricted custody, separate from the dashboard.
3. Open the isolated journals with their respective anchors. Supply
   `witnessed_enrollment_pins={company_id: retained_digest, ...}` to
   `build_authenticated_visibility` alongside `journal_by_company`. In this
   configuration a missing or incorrect company pin, an unanchored journal,
   or a missing local witness binding rejects that feed without consuming
   its receipt. The other enrolled feed is checked independently. A
   verified view shows only a redacted witnessed-enrollment status.
4. Exercise restart, stale and replayed input, wrong trust, unavailable
   custody, publisher revocation or replacement, and one-company recovery
   while the peer continues. Compare the exact anchored and local states
   before witnessed repair. Pass the same protected company digest as
   `expected_enrollment` to `pending_repair_checkpoints`,
   `reconcile_pending_receipt` and `transition_custody`. A mismatched
   digest blocks the operation before mutation even if both presented
   stores omit their witness state. Obtain a fresh exact recovery signature and
   retain the authorization and readback privately. Do not restore both
   copies to a common older checkpoint or recreate a missing anchor.
5. Require the company operator and independent custodian to attest
   observed evidence and custody separation before the company owner
   decides commissioning. The shared hub records status and unresolved
   signoffs through the existing redacted reporting contract.

Local tests and SQLite exercise the protocol. Production still requires
a trusted clock, independent custody with anti-rollback controls and
company-controlled publisher provisioning. The compatible fixture call
without separately retained pins is for the offline fixture path.

Company-scoped resource qualification can be included in a signed
`divisional_telemetry.resource_qualification` object. Revenue can report
`native_workforce`, `coding_service` and `publisher_custody`. Trading can
report `historical_data`, `paper_operations` and `publisher_custody`.
The permitted values are `BLOCKED`, `STAGED_FOR_REVIEW`,
`APPROVAL_REQUIRED` and `NOT_VERIFIED`. Missing items remain unknown.
The verifier requires the company's separately retained witnessed
enrollment pin before accepting a signed report containing these fields.
The mobile view shows the bounded company statuses. Keep artifact paths,
credentials, digests, dataset rows and release decisions in each company's
private operating record.

### Operator enrollment and recovery preflight

The company custodian retains the enrollment digest independently of
both stores. After provisioning, the verifier calls
`journal.preflight_witnessed_custody(trust=company_trust, now=trusted_utc,
expected_enrollment=retained_digest)` before a witnessed test receipt or
after exact witnessed repair. It reads the local journal in SQLite
read-only mode, verifies company and publisher scope, compares the
independently retained enrollment, and checks that local and independent
checkpoint histories agree. It returns a company-scoped status without
receipt details, key material, sequence counters or release authority.

Assign a company publisher, independent custodian, verifier operator
and witness before the exercise. Keep the private enrollment packet
and source evidence company-local. Take a scoped baseline, interrupt
only the designated journal with an approved synthetic receipt,
confirm the peer continues to report, and perform exact witnessed
repair through the existing recovery path. Recheck custody alignment,
deny replay, and retain the separately witnessed record. A failed or
changing preflight stops that company for review. Real key provision,
separate storage and staffed authorization still require operational
verification.

For commissioning against already enrolled and operator-provisioned local
state, `preflight_protected_custody` adds file-protection checks to the existing
witnessed checkpoint preflight. Supply independently retained enrollment and
publisher trust, a trusted UTC clock, and the explicitly configured OS owner
UID of each database. The receipt and authority must occupy distinct private
directories and owner-private unaliased SQLite files. Keep both quiescent.
The check rejects SQLite sidecars and WAL-format files before opening SQLite
in read-only mode. It returns only redacted verification status.

This verifies local file protections and existing custody alignment. Distinct
administrators, independent restore domains, protected external enrollment
configuration, and production key ceremonies require operator evidence.

# Aevora AI durable commissioning evidence pack

This offline fixture extends draft #49 at
`bc3c625202f551f701281addef66f508dcf3c50a`. The anchored-only rehearsal,
company authority and read-only Main Hub/OCC remain in force. No evidence
record grants release. No external delivery is performed.

## Scope and custody

Provision the SQLite schema and company/store identity separately from the
write port. Inject an already provisioned, company-scoped
`ExternalCustodyPin` for the exact genesis. Every SQLite event commits
canonical content, sequence, previous digest and identity into a hash
chain. Open requires agreement with the independent expected pin. The pin
must implement authenticated, durable, monotonic compare-and-swap outside
the custody, review anchor and audit files. Recovery must never create a new
pin from the untrusted SQLite files after a fault.

The fixture serializes writes using a SQLite immediate transaction. It
checks the proposed local chain before moving the independent pin and
commits SQLite only after the pin advances. An unknown result or process
exit between them creates an unavailable or mismatched state. That state
blocks until independently reviewed recovery. No automatic retry or
reseeding is supplied. A byte-identical clone may match the current pin
until the pin advances. A prior clone rejects with a retained current pin.
Coordinated rollback of both the external pin and the SQLite evidence
store is outside this fixture guarantee.

`SyntheticDurableCustody.record_if_current` is a trusted reviewer service
port and must be callable only by the authenticated company-scoped
commissioning reviewer. It compares the full custody observation, scoped
request and expiry, verifies both Ed25519 review signatures against current
provisioned keys and records at most one evidence bundle per company,
checkpoint and request. The reviewer front door is still required to
validate distinct roles and the anchored proof. The adapter persists both
signed review records with the company/checkpoint/manifest and lifecycle
revisions. Existing key IDs and key material stay fixed and revoked IDs
remain as tombstones. Rotation uses a new key ID and new material. Stale
revisions, reused material, mutation and revocation rollback fail closed.

The independent pin double lives outside SQLite for each test. It has no
real independent administrator or durable custody. The subprocess restart
test opens SQLite from a fresh process using the separately retained pin.
Production storage, authenticated pin custody, managed asymmetric signer
provisioning and real independent reviewers remain requirements.

## Evidence outputs

- Private synthetic manifest:
  `fixtures/commissioning-evidence.synthetic.json`. Its SHA-256 is
  `1c5df5b254012cc7a0f7da389189ff94b7cc41e5deba43acd869a7126a3b27be`.
  The record includes private-scope relationships and signed **fixture**
  evidence. Do not use this schema as OCC input.
- Separate allowlisted Main Hub/OCC aggregate:
  `fixtures/commissioning-occ.synthetic.json`. Its SHA-256 is
  `f7f25048cbc8e27be54dcacaf40b8ab674f0b17e6ae681998b26a87f13e96de2`.
  It includes only existing aggregate fields, with execution authority false.
  The fixture test regenerates both outputs and checks exact bytes.

## Independent production signoff matrix

| Role | Required evidence | Status |
| --- | --- | --- |
| Aevora AI owner | Real action-specific decision, named accountable owner, exact scope, expiry, approval reference | **NOT GRANTED** |
| CRO / independent risk | Verified separation of company risk and trading authority, no live execution or veto override | Pending |
| Security & Recovery | Authenticated independent custody, monotonic durable pin, rotation/revocation controls, interrupted-write and rollback recovery evidence | Pending |
| External audit reviewer | Signed company-scoped checkpoint and evidence review, version/digest and exception disposition | Pending |
| External recovery reviewer | Separate signed recovery review against pinned continuity, approved restore procedure and exception disposition | Pending |
| Research & Intelligence | Evidence provenance, recipient isolation, classification and independent reporting review | Pending |
| Day operations | Named shift lead, reproducible exact evidence, approved exception handling and signed handoff | Pending |
| Night operations | Named on-call lead, accepted handoff, demonstrated no-release handling of outage and recovery | Pending |

A fixture signature cannot satisfy any row. Security & Recovery can review
the restricted private evidence within company authority. OCC sees the
separate read-only projection.

## Reproduction

From `operations`, use the existing Python 3.12 Ed25519-capable environment
with external network unavailable:

```sh
python -m unittest -v test_durable_commissioning_custody
python -m unittest -v test_durable_commissioning_custody test_continuity_commissioning test_signed_audit_continuity test_anchored_evidence_verifier test_anchored_delivery_rehearsal test_delivery_independent_challenge
python -m unittest discover -v
```

The focused suite passed 7 tests, the adversarial/integration suite 47,
and the full operations suite 95. Tests cover reopening, concurrent owners
of the same evidence request, revoked and rotated signer material, external
pin divergence/ambiguity, wrong-company evidence, custody outages,
rollback and reproducibly separated outputs.

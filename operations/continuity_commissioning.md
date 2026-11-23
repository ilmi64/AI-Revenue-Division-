# Aevora AI continuity commissioning boundary

This separate offline boundary builds on draft #47 at
`f2859d6052e925796d5452bb602bd59b1b254791`. It records private synthetic
commissioning evidence. The anchored-only rehearsal, read-only OCC
projection, and company operating authority retain their existing contracts.

## Inputs and authority

A bootstrap-controlled `CommissioningAuthority` must observe a current
company checkpoint and signer lifecycle. Bootstrap pins the company,
custodian and separate signer registrar. Freshness and monotonic custody
and signer revisions must be maintained outside both local databases.
Only a separately administered signer registrar provisions exact
company-scoped Ed25519 public keys, role, principal identity, validity
window and revocation. Registration, rotation, revocation, supersession
and recovery move the lifecycle revision forward. Stale, missing or
uncertain authority is unavailable. This interface never provisions keys
from an applicant request or returns private keys.

`CommissioningReviewer` verifies the #47 signed proof against the observed
checkpoint and complete local audit. External audit and recovery reviewers
sign separate purpose-specific evidence hashes for the exact company,
checkpoint, manifest, request ID and custody/signer revisions. The two
reviewer principals, checkpoint signer, proof signer, custodian and key
registrar must be separate. A valid review package is evidence for review
only. Every record carries `release_authorized: false`.

The independent sink's `record_if_current` must compare the entire
observation under its own trusted time and atomically record at most one
bundle per company/checkpoint/request. A revision transition, duplicate,
expired evidence or ambiguous commit blocks. Maintain the sink and its
idempotency history beyond both local databases, with independent
reconciliation after a disputed write. The test double uses only a lock
and in-memory fixture state. It does not demonstrate durability, production
identity, transparency or independent administrative custody. Coordinated
rollback of both local databases is detected only while the external
authority retains its genuinely current pin.

## Owner and oversight evidence checklist

| Responsible authority | Independent evidence required | State |
| --- | --- | --- |
| Continuity custodian | Authenticated company-specific custody and independently retained monotonic checkpoint, rollback and availability controls, recovery across restart | Pending |
| Signer registrar | Ed25519 key custody, scoped issuance, rotation/supersession, revocation propagation, stale-key denial and accountable emergency procedures | Pending |
| External audit reviewer | Signed artifact-backed audit chain and checkpoint continuity with named independent reviewer, digest, and resolution of exceptions | Pending |
| External recovery and Security & Recovery reviewers | Independent recovery challenge across outage, corruption, clone/rollback and disputed atomic record, documented recovery decision and approved procedures | Pending |
| Research & Intelligence | Verifiable evidence provenance, classified research origin, reviewed reporting scope and data minimization | Pending |
| CRO / independent risk review | Evidence of isolation from Trading & Technology, risk vetoes and live trading authority where shared services are used | Pending |
| AI Revenue operations | Reproducible pinned rehearsal, named handoffs and exception escalation, no external deliveries, OCC redacted counters only | Pending |
| AI Revenue owner | A separately scoped real decision with evidence reference, accountable identity and expiry | **NOT GRANTED** |

No row, synthetic status or signed fixture approves an external action.

## Reproduction

From `operations` in a network-denied environment with the existing
Ed25519 backend:

```sh
python -m unittest -v test_continuity_commissioning
python -m unittest -v test_continuity_commissioning test_signed_audit_continuity test_anchored_evidence_verifier test_anchored_delivery_rehearsal test_delivery_independent_challenge
python -m unittest discover -v
```

The test fixture checks missing/unavailable or stale custody, revoked and
expired role keys, mismatched company and request scope, contested distinct
signed packages, checkpoint and lifecycle changes, absent/rejected recovery
review, expired-at-record evidence, and coordinated local rollback.

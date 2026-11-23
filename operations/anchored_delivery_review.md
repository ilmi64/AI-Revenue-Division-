# Aevora AI anchored delivery-review prototype

This offline prototype addresses the three gaps reproduced in draft #40 at
`a2d5be97d63e822713289e0b0a96be3eab6cf5c2`. It adds a separate hardened
verifier. The previous fixture verifier, historical challenge, checklist and
read-only OCC projection still exercise their original contracts. Adoption
requires an explicit migration with Security & Recovery review. Every
anchored receipt remains private and carries `release_authorized: false`.

## Fixture provisioning and trust

Provision `review_anchor.sql` and `review_audit.sql` in separate existing
SQLite files. The trusted fixture provisioning authority sets a unique
company/store identity in both files, pins the approved policy and complete
trust snapshot fingerprint with a positive epoch in the anchor, and starts
the audit at sequence zero with a 64-character zero head. Only a separately
authorized operator may advance the pinned trust/policy epoch. The caller
supplies independently obtained expected scope and trusted time. Verifier
inputs cannot set the anchor epoch, expected company, or approved policy.

Use `AnchoredEvidenceVerifier` for evidence review and
`verify_anchored_receipt` to independently re-read the private receipt
against the externally held chain head. Shape and digest checks cover the
full audit chain, including earlier rows. An audit row binds company, store,
epoch, manifest digest, nonce, observation time, sequence and parent digest.
The anchor is the authority for continuity and trust freshness. HMAC keys,
clock and local filesystem are synthetic fixtures.

## Failure behavior

| Case | Observed boundary |
| --- | --- |
| Stale trust or policy | The monotonic epoch, complete trust fingerprint and exact policy must all match. Advancing trust uses an expected-epoch compare-and-swap. A revoked signer is denied by the verifier. |
| Restart, stale clone or duplicate nonce | The independent anchor serializes claims and pins the current audit head, sequence and store identity. A stale clone diverges. A current duplicate cannot re-claim the same nonce. Two handles using the same authoritative anchor yield at most one receipt for a nonce. |
| Missing or corrupted audit / independent review | Missing files, missing rows, modified history or tampered receipt digests block. The readback API checks both the pinned chain and the private receipt row before returning. |
| Interrupted dual commit | The audit commits first. The anchor commits second. A child exit in between leaves an ahead audit and a stale anchor. The next operation blocks on divergence. A fault reported after both commits can consume the nonce without a delivered receipt. Preserve evidence and require separately approved reconciliation. |
| Time, recipient or company mismatch | Invalid or rolled-back trusted time and expiry at claim are denied. Scope comparison requires exact company, recipient, channel, source commit and policy. |

A byte-identical current audit clone shares the same continuity point until
the anchor advances. This is single-anchor serialization rather than
physical-model detection of copies. Restoring or replacing **both** files
with a mutually consistent old pair defeats the local fixture. The design
assumes a pinned, independently controlled anchor with rollback protection.
A different trusted anchor must never be selected by a delivery request.
The prototype performs no automatic recovery or reseeding.

Production gates remain open for asymmetric identity and key custody, managed
revocation, a separately administered anti-rollback anchor and signed audit
checkpoints, durable recovery and independent review. Retain private evidence
within Aevora AI, subject to independent Security & Recovery oversight.
Main Hub/OCC stays read-only and receives aggregate status only. Real owner
approval is **NOT GRANTED**.

## Reproduction

From `operations`, run the existing Python 3.12 standard library in a local
network-denied environment:

```sh
python -m unittest -v test_anchored_evidence_verifier
python -m unittest discover -v
```

The synthetic focused suite passed 9 cases and the operations suite passed
65 cases. The crash test exited a child between the two real SQLite commits.

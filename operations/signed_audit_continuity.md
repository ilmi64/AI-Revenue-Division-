# Aevora AI private Ed25519 audit continuity proof

Draft #45 at `72676bc339de3d12dc1a3ccd88a9f870facae67d` remains the
anchored-only synthetic rehearsal. This separate offline proof verifies its
private local review records and produces no delivery authority.

The checkpoint signer authenticates canonical company, store, trust epoch,
trust fingerprint, policy, sequence, chain head and validity interval. A
distinct auditor signs a private receipt binding the checkpoint digest and
the exact anchored review receipt. The two Ed25519 payloads have separate
domain tags and use sorted compact ASCII JSON. Both roles and key IDs are
explicit. A verified receipt carries `release_authorized: false`.

Provision a trusted `ContinuityAuthority` outside both local review
databases. For the configured company it supplies the **current** pinned
checkpoint digest and currently trusted key metadata. Caller-supplied old
signed checkpoints cannot replace that pin. The verifier checks scope,
expiry, role independence, revocation, both signatures, the local chain and
receipt integrity, and equality between the locally observed and
independently pinned checkpoint. Unavailable authority or Ed25519 backend
blocks the proof. The authority interface is read-only; this branch supplies
no remote authority or production key provisioning and does not create or
send audit receipts. Test fixtures generate their own synthetic keys.

| Challenge | Expected fixture result |
| --- | --- |
| Simultaneous rollback of both local stores | The old signed proof fails the independently retained pin. The current proof fails against the restored stores. |
| Stale epoch or modified audit | The checkpoint or complete audit validation fails. |
| Tampered or cross-purpose signatures, revoked keys, collapsed roles, wrong company | Verification is blocked. An asserted release flag is denied even with a valid audit signature. |
| Torn local commit and recovery | Proof verification blocks while local files diverge. A reviewed restoration of known matching bytes permits proof readback and preserves nonce replay denial. The pinned anchored suite also tests a real process exit between commits. |
| OCC contamination | Private proof status is rejected and private fields are absent from allowed aggregates. OCC has no execution authority. |

The external pin in tests is held by a separate in-process fixture outside
both database files. This does not establish real independent or durable
custody, notify the authority of local writes, or protect against rollback
of the trusted authority itself. Production requires independently managed
monotonic publication and rollback protection, verified asymmetric key
custody and signer role separation, live revocation and clock assurance,
signed audit and reviewed recovery. Maintain company-local records under
Security & Recovery oversight and send only redacted aggregate information
to read-only Main Hub/OCC. Real owner approval is **NOT GRANTED**.

## Reproduction

From `operations`, use an existing Python interpreter in an offline
environment. Focused Ed25519 tests require the installed `cryptography`
package with Ed25519 support. No new install or download is required by the
legacy workflow.

```sh
python -m unittest -v test_signed_audit_continuity
python -m unittest -v test_signed_audit_continuity test_anchored_evidence_verifier test_anchored_delivery_rehearsal test_delivery_independent_challenge
python -m unittest discover -v
```

# Aevora AI opportunity-to-delivery gate — engineering handoff

Status: **draft, offline only, not deployed**. This branch contains no opportunity crawler, task executor, Codex Cloud launcher, automatic submissions, invoicing or payment collection.

## Components
- `operations/opportunity_intake.py`: accepts a **local JSON array** of opportunities, classifies each for human review. The `review_ready` status is not authorization to work, access systems or contact customers.
- `operations/delivery_gate.py`: accepts a **local JSON object** with opportunity, evidence and approvals. Even when all caller-supplied checklist fields are positive, the result is **`checklist_complete_unverified`**, not delivery authorization. `release_authorized` and `evidence_verified` are always false until a separately implemented independent verifier is available.
- `operations/test_opportunity_intake.py` and `operations/test_delivery_gate.py`: authored offline regression tests.

## Reproducible checks
From a checkout of this exact branch at a recorded commit:

```sh
python -m unittest discover -s operations -p 'test_*.py' -v
```

Save the command, Python version, commit SHA, stdout/stderr, exit code and UTC timestamp in a review evidence record. Do not mark tests passed until executed. Do not claim CI is configured or Codex Cloud can start automatically from GitHub Issues.

## Trust and approvals
- The intake's `scope_authorized` flag and the delivery gate's `delivery_authorized` and `scope_reviewed` flags are **self-declared input fields**, not authenticated signatures or independent authorization verification.
- A source URL is syntax-checked, **not fetched or reputation-checked**.
- The SHA is format-checked, **not compared to an actual GitHub commit**.
- `tests_passed` and `test_log_ref` are self-reported, **not independently validated**.
- The delivery gate intentionally **fails closed**: its local checklist does not grant release authority, even if every input flag is true. A future verifier must bind company, opportunity, artifact digest, actual source commit, independently retained QA log, reviewer identity, recipient, delivery channel, owner approval and expiry; this verifier is **not implemented**.
- Therefore neither script may be used to bypass an actual authorized human review or trigger delivery, payment, credential access, code execution or a public submission.
- Do not put private customer data, credentials or confidential bounty information in public Issues or PRs.

## Follow-on integration gates
1. Execute exact-source unit tests and retain evidence.
2. Introduce signed/verified approval provenance with company-scoped authority.
3. Verify source commit and QA artifacts rather than trusting user-supplied strings.
4. Add append-only audit events and assignment/QA transitions.
5. Connect to the Main Hub/OCC via **read-only, redacted** summaries only.
6. Validate an actual authorized task runner before describing the GitHub → Codex Cloud handoff as automatic.
7. Keep Aevora Trading & Technology separate: no shared treasury, trade execution or secrets.

January 4–8, 2027 remains the preferred launch window, with a mid/late-January extension when warranted by security, operational and revenue-readiness evidence.

## Synthetic delivery-evidence verification

`evidence_verifier.py` is an offline prototype for AI Revenue review. A trusted
caller supplies the exact expected company, opportunity, source commit,
recipient, channel, policy version and producer. The manifest binds these
fields to artifact and test-log SHA-256 digests, nonce and expiry. The
prototype encodes the manifest as sorted, compact ASCII JSON and authenticates
the same digest in separate, purpose-bound independent QA and owner-review
attestations.

The synthetic harness provisions `evidence_verifier_replay.sql` in its own
temporary database. The verifier requires that existing store and consumes
the company-scoped nonce once before returning a receipt. Keep the scope,
clock, current revocation records, fixture keys and replay database under
verifier control. Production signing, identity, revocation freshness, store
backup/rollback protection and independent audit require a separate design
and review. The prototype uses synthetic HMAC credentials only and verifies
the binding of test-log bytes to an attestation. The independent QA reviewer
is responsible for the test result's meaning.

The only receipt is `verified_for_owner_review` with
`release_authorized: false`. The checklist and OCC summary retain their current
behavior. There is no sender, customer access or publication path.

### Fictional manual-delivery commissioning rehearsal

The public rehearsal requires explicit anchored mode. Run these commands from
`operations` in a local sandbox with external sockets blocked.

```sh
python -m synthetic_delivery_rehearsal --mode anchored
python -m unittest -v test_anchored_delivery_rehearsal
python -m unittest -v test_anchored_delivery_rehearsal test_anchored_evidence_verifier test_delivery_independent_challenge
python -m unittest discover -v
```

The same intake and checklist drive the hardened verifier and a separately
provisioned synthetic anchor and audit database. A verified receipt is
read back against the audit chain before the rehearsal reports it. The
workflow projects only allowlisted counts to the read-only OCC summary.
Every scenario denies release and external delivery. The full report
contains private audit evidence and stays in Aevora AI's review scope.
The CLI refuses omitted or unanchored mode. The historical Python fixture
is retained for the pinned challenge regressions.

| Rehearsal fault | Expected outcome |
| --- | --- |
| Anchor or audit missing | Block verification. No fallback. |
| Revocation/trust epoch or policy stale | Reject against the current anchor. |
| Company or recipient differs from trusted scope | Reject the manifest. |
| Audit row corrupted | Reject during receipt readback. |
| Audit committed with stale anchor | Block on divergence. The hardened-verifier suite separately exercises actual child exit between commits. |
| Nonce used after verifier reopen | Reject the replay. |
| Anchor and audit restored together | Reject receipt readback against the receipt retained outside both files for this run. |

The coordinated rollback case uses a retained receipt within the rehearsal.
Restoring that reference as well as both local stores is outside the local
proof. The fixture keys and identities are synthetic. This workflow
does not provision production trust or change Aevora AI's eligible markets.

Before production review, obtain asymmetric signer and independent
reviewer identity provisioning, managed revocation and current policy,
an independently controlled monotonic anchor, signed audit with custody
and restore validation, a reviewed interrupted-commit recovery procedure,
independent Security & Recovery signoff, and a real owner decision.

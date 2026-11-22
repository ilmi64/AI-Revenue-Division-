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

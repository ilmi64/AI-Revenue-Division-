# Aevora AI offline revenue workflow demo

Run from `operations` with the existing Python standard library, offline.

```sh
python -m revenue_workflow_demo --mode anchored
python -m revenue_workflow_demo --mode anchored --view occ
python -m revenue_workflow_demo --mode anchored --scenario missing_anchor
```

The fixed fictional Canadian opportunity is a zero-upfront-cost listing
preflight prototype. The workflow qualifies the opportunity, builds the
existing delivery plan, creates four proposed queue handoffs linked to the
Technology & Infrastructure and Risk & Recovery charters, and drafts an
internal-only proposal. It then runs the existing read-only portfolio CSV
validator on two invented rows. The expected evidence is a duplicate SKU
and a fractional quantity on row 3. Its expected exit code is 1 because it
correctly identifies both deliberately introduced errors. The workflow checks
those observations and passes the exact artifact bytes and SHA-256 through
the existing task-evidence review for the build handoff. A separate
synthetic quality role reviews the engineering assignment. Task evidence
review records structural review only. It does not verify completion or
authorize execution. The existing anchored synthetic verifier then receives
the canonical artifact and test log with the recorded role review.

The private artifact includes the proposed roles, plan, internal draft and
concrete findings. The private test log binds the source bytes of the
validator, the stdout digest and the observed test conditions. The anchored
receipt is private review evidence with `release_authorized: false`. Only
existing aggregate status counters belong in the separate `--view occ`
output. An unavailable anchor blocks receipt issuance. Unverified scope or
nonzero upfront cost stops the workflow before local validation.

The prototype accepts fixed fixtures only. Proposal estimates and authority
flags are fictional and do not record commercial income or actual customer
permission. No agent dispatch, store upload, customer contact, submission,
external delivery, spending or deployment occurs. There is no installed
agent runtime or model. Named operational handoff owners, actual customer
scope and consent, production custody and independent commissioning,
reviewed commercial terms, and real owner approval remain pending.

```sh
python -m unittest -v test_revenue_workflow_demo
python -m unittest -v test_revenue_workflow_demo test_revenue_intake_sandbox test_revenue_delivery_plan test_revenue_agent_queue test_revenue_proposal_draft test_revenue_task_evidence test_anchored_delivery_rehearsal
python -m unittest discover -v
```

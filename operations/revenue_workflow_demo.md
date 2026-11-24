# Aevora AI offline workforce demo

Run from `operations` with the existing Python standard library, offline.

```sh
python -m revenue_workflow_demo --mode anchored --service app_build
python -m revenue_workflow_demo --mode anchored --service coding
python -m revenue_workflow_demo --mode anchored --service ai_setup
python -m revenue_workflow_demo --mode anchored --service app_build --view occ
python -m revenue_workflow_demo --mode anchored --scenario missing_anchor
```

The demo uses the existing opportunity qualifier, delivery plan, proposed
queue, internal proposal, task-evidence QA and anchored verifier. It
dispatches exactly one repository-owned worker per qualified synthetic task.
The ticket fixes company and recipient to AI Revenue, the engineering role,
the fixture, the tool, and a CAD 0 cost ceiling. The selected task must match
its exact queue position. The CLI accepts these three named synthetic
fixtures, with no commands, source paths, code, secrets, model settings,
customer data or external destinations supplied by callers.

| Service | Fictional jurisdiction | Bounded worker output |
| --- | --- | --- |
| App development | CA | The existing read-only portfolio CSV validator finds duplicate SKU and fractional quantity on row 3. Exit code 1 is the expected known answer because the invented rows contain errors. |
| Coding | US | An integer-cent invoice rounding fixture shows legacy truncation of 224 cents, corrected tax of 225 cents, total of 4724 cents and a fixed proposed before/after diff. The diff is output text for inspection only. |
| AI workflow | GB | A deterministic review-router fixture sends complete internal evidence to the QA queue and holds missing evidence or requested outbound actions. |

The independent fixture checks compare observed outcomes with fixed
answers. The existing evidence review checks the exact artifact bytes and
SHA-256 against the selected engineering handoff using a separate synthetic
quality role. The anchored verifier binds artifact and test-log bytes after
this review. This establishes synthetic role separation and known-answer
behavior. Operational independent approval remains pending. A receipt remains private, preserves `release_authorized:
false`, and provides no real approval. Missing scope or upfront cost stops
the run before dispatch. Invalid tickets, failed or malformed outputs, QA
mismatch and missing anchor block a receipt. Only aggregate status counters
appear in the separate OCC view.

## Workforce compatibility boundary

The governing [adapter contract][adapter], [technical assessment][technical]
and [acceptance scenarios][scenarios] were examined at
`954a5c25720af01e00d3b79899d05b60e34edcc2`. The [role catalogue][roles]
and [bounded swarm profiles][profiles] were also examined at
`c8cb3b92d9a783802ec017670b8ef70a36ff9572`.

| Candidate boundary | What this demo exercises | Remaining proof |
| --- | --- | --- |
| Paperclip parent task and accountability | Company-local plan/queue, stable task identifiers, `ar_product_delivery`, `ar_engineering_worker`, `ar_qa_reviewer` and `ar_security_analyst` role labels. | Real company tenant isolation, authenticated mapping of actor/issuer/task IDs, deadlines, durable idempotency, approvals, budgets and audited lifecycle callbacks. |
| Ruflo scoped subordinate work | A fixed local worker inherits company, recipient, tool and cost restrictions. The ordering corresponds to the internal preparation and QA portion of `RUFLO_BUSINESS_DELIVERY`. | A version-pinned native adapter, deterministic parent-to-child permission intersection, current signed scope, cancellation and revocation propagation, and tested controls outside model prompts. |
| Model-agnostic runtime | The task and evidence shapes do not select any model. All three workers are deterministic. | Provider/runtime and permission verification, cost metering, evaluation and tenant-scoped tool/data gateways. No Paperclip, Ruflo, model or remote adapter has been run. |
| R&I, Security & Recovery and Main Hub/OCC | Private artifacts stay in AI Revenue. The separate OCC projection is read-only. Synthetic QA role labels are not operational authority. | Authorized recipient-scoped R&I handoffs, independent security and recovery approval, signed oversight publishing, and exact source/pin verification before shared imports. |

No autonomous agents are invoked and no agent execution capability is
granted. The only subprocess is the existing app-development fixture's
fixed repository CSV validator command. Proposal estimates and jurisdiction
inputs are fictional. A named operational workforce, verified customer
scope and consent, custody, independent commissioning and real owner
approval are still open gates. No external contact, delivery, spending,
deployment, publishing or real commercial transactions occur.

```sh
python -m unittest -v test_revenue_fixture_dispatch test_revenue_workflow_demo
python -m unittest -v test_revenue_fixture_dispatch test_revenue_workflow_demo test_revenue_intake_sandbox test_revenue_delivery_plan test_revenue_agent_queue test_revenue_proposal_draft test_revenue_task_evidence test_anchored_delivery_rehearsal
python -m unittest discover -v
```

[adapter]: https://github.com/ilmi64/AI-Revenue-Division-/blob/954a5c25720af01e00d3b79899d05b60e34edcc2/organization/architecture/workforce-platform-adapter-contract.json
[technical]: https://github.com/ilmi64/AI-Revenue-Division-/blob/954a5c25720af01e00d3b79899d05b60e34edcc2/organization/architecture/workforce-platform-current-technical-assessment.md
[scenarios]: https://github.com/ilmi64/AI-Revenue-Division-/blob/954a5c25720af01e00d3b79899d05b60e34edcc2/organization/security/workforce-platform-adapter-acceptance-tests.json
[roles]: https://github.com/ilmi64/AI-Revenue-Division-/blob/c8cb3b92d9a783802ec017670b8ef70a36ff9572/organization/architecture/paperclip-role-id-and-org-chart-configuration-draft.md
[profiles]: https://github.com/ilmi64/AI-Revenue-Division-/blob/c8cb3b92d9a783802ec017670b8ef70a36ff9572/organization/architecture/ruflo-bounded-swarm-profile-registry-draft.md

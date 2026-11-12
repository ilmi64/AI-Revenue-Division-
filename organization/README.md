# Organisation Control Centre

This directory defines the organisation-level operating model. It is the coordination layer for all divisions, not a replacement for their specialist systems.

## Objectives
- Maintain one authoritative view of divisions, ownership, responsibilities, dependencies, and readiness.
- Coordinate shared priorities and cross-division support.
- Make risks, blockers, evidence, and approval gates visible.
- Support sustainable funding through the AI Revenue Division while protecting the organisation from dependence on any single revenue source.

## Core records
- `division-registry.json`: division mandates, status, dependencies, and approval boundaries.
- `readiness-register.json`: evidence-based readiness checks and current status.

## Operating cycle
1. Each division reports deliverables, evidence, blockers, risks, and next actions.
2. The executive layer reviews cross-division dependencies and prioritises work.
3. Risk and advisory functions can flag or recommend stopping unsafe work; they cannot authorise financial or operational execution.
4. Readiness changes only when evidence is recorded and reviewed.
5. Decisions requiring owner approval remain pending until explicitly approved.

## Status vocabulary
- `planned`: defined but not yet established.
- `building`: active development.
- `testing`: implementation exists and is undergoing verification.
- `standby`: tested for its defined scope, with dependencies and limitations documented.
- `operational`: approved for its stated non-sensitive operating scope.
- `blocked`: cannot progress until a named blocker is resolved.
- `deferred`: intentionally postponed.

A division is never marked operational merely because a document, repository, or prototype exists.

## Approval boundaries
This framework does not authorise spending, borrowing, banking activity, trades, wallet access, signing, external client commitments, public launches, production deployments, merges, or permission changes. Those actions require the applicable explicit owner approval and any required independent review.

## Reporting minimum
Every division update should include: current status, completed work with links/evidence, tests and results, open risks, dependencies, owner actions needed, and next measurable deliverable.

## Current implementation scope
This is a documentation-and-data foundation on a feature branch. It is not yet an integrated dashboard, automated control plane, or proof that any division is launch-ready.

## Local validation

From the repository root, run:

```sh
python organization/tools/validate_readiness.py
python -m unittest discover -s organization/tests -v
```

The validator checks registry references, status vocabulary, assessment structure,
and evidence gates. It deliberately blocks `standby` or `operational` claims
unless every required check has an explicit `passed` result with evidence and
there are no open gaps. Missing division assessments are reported as warnings;
they are not silently treated as ready. This is a data-integrity check, not a
substitute for real operational testing or owner approval.

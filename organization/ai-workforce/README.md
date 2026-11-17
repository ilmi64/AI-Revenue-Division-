# Organisation AI Workforce Foundation

This package adds the first machine-checkable AI workforce contracts for the organisation.

## Contents
- `model-registry.json`: model identity, evidence, scope, routing and zero-spend policy.
- `agent-roles.json`: bounded agent roles, all 11 canonical divisions, and division-to-role templates.
- The OCC dashboard prepares read-only task packets using those role templates; it never assigns owners or dispatches work.
- `task-handoff-contract.json`: common task, evidence and handover contract.
- `validator.py`: fail-closed consistency validator.
- `test_validator.py`: offline regression tests.

## Verified baseline
- Qwen2.5 1.5B via Ollama was merged through PR #2 on 2026-11-13 (merge commit `874dabc99ed04814b3e024964b158322669c9ba8`). The workflow has not yet been executed successfully end-to-end; runner/model runtime and output quality remain unverified.
- Llama 3.2 1B is an evaluation candidate only; no installation is asserted.
- Qwen3.5 0.8B is a benchmark candidate only; it does not replace the existing Qwen pilot.
- No paid API, paid trial, deployment, or external write action is enabled.

## Task packet semantics
- A role template is not a named human or active agent assignment.
- A prepared packet is not dispatched, acknowledged, approved, or executable.
- Unresolved dependencies block the packet; named owner assignment still requires owner acknowledgement.
- Risk remains `unassessed` until a real evidence-based review is recorded.

## Run offline tests
From this directory:
```sh
python -m unittest -v
python validator.py
```

## Guardrails
- This package does not execute trades, publish content, contact third parties, spend money, alter accounts, merge code or deploy services.
- Models produce drafts and reviews, not approvals.
- Missing evidence fails closed.
- GitHub Actions are intentionally not invoked as part of this change.
- No live operational readiness is claimed by passing these local contract tests.

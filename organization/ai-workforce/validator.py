"""Fail-closed validation for the organisation AI workforce records."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATUSES = {"proposed", "ready", "in_progress", "blocked", "review", "complete"}
RISKS = {"low", "moderate", "high", "critical"}
APPROVALS = {"none", "owner_review", "explicit_owner_approval"}

def load(name: str) -> dict:
    with (ROOT / name).open(encoding="utf-8") as handle:
        return json.load(handle)

def validate() -> list[str]:
    errors: list[str] = []
    model_registry = load("model-registry.json")
    roles = load("agent-roles.json")
    contract = load("task-handoff-contract.json")
    # The canonical division registry lives one level above this package.
    with (ROOT.parent / "division-registry.json").open(encoding="utf-8") as handle:
        division_registry = json.load(handle)

    policy = model_registry.get("policy", {})
    if policy.get("incremental_spend_cad") != 0:
        errors.append("incremental_spend_cad must remain zero")
    if policy.get("paid_apis") is not False:
        errors.append("paid APIs must remain disabled")
    if policy.get("paid_trials") is not False:
        errors.append("paid trials must remain disabled")

    models = model_registry.get("models", [])
    if not isinstance(models, list):
        errors.append("models must be a list")
        models = []
    model_ids = [m.get("id") for m in models if isinstance(m, dict)]
    if len(model_ids) != len(models) or len(model_ids) != len(set(model_ids)) or None in model_ids:
        errors.append("model IDs must be present, valid and unique")
    model_map = {m.get("id"): m for m in models if isinstance(m, dict)}
    qwen = model_map.get("qwen-primary-pilot")
    llama = model_map.get("llama-review-candidate")
    if not qwen or qwen.get("status") != "integrated_in_main_unverified_end_to_end":
        errors.append("Qwen pilot status/evidence must be preserved accurately")
    if not llama or llama.get("status") != "evaluation_candidate":
        errors.append("Llama must remain an evaluation candidate until verified")

    role_rows = roles.get("roles", [])
    if not isinstance(role_rows, list):
        errors.append("roles must be a list")
        role_rows = []
    role_ids = [r.get("id") for r in role_rows if isinstance(r, dict)]
    if len(role_ids) != len(role_rows) or len(role_ids) != len(set(role_ids)) or None in role_ids:
        errors.append("role IDs must be present, valid and unique")
    role_id_set = set(role_ids)
    for role in role_rows:
        if not isinstance(role, dict):
            continue
        model_id = role.get("model_id")
        if model_id and model_id not in model_map:
            errors.append(f"role {role.get('id')} references unknown model {model_id}")

    canonical = {d.get("id"): d.get("name") for d in division_registry.get("divisions", [])
                 if isinstance(d, dict) and isinstance(d.get("id"), str)}
    declared_names = roles.get("divisions", [])
    if set(declared_names) != set(canonical.values()) or len(declared_names) != len(canonical):
        errors.append("AI workforce division names must match the canonical OCC registry exactly")
    role_map = roles.get("division_role_map", {})
    if not isinstance(role_map, dict) or set(role_map) != set(canonical):
        errors.append("division_role_map must map every canonical division exactly once")
    else:
        for division_id, role_id in role_map.items():
            if role_id not in role_id_set:
                errors.append(f"division {division_id} references unknown role {role_id}")

    required = contract.get("required_fields", {})
    for field in ("task_id", "division", "title", "objective", "owner_role",
                  "status", "risk_class", "inputs", "output_contract",
                  "acceptance_tests", "dependencies", "approval_gate", "evidence"):
        if field not in required:
            errors.append(f"task contract missing required field: {field}")
    if set(required.get("status", [])) != STATUSES:
        errors.append("task statuses do not match the controlled status set")
    if set(required.get("risk_class", [])) != RISKS:
        errors.append("risk classes do not match the controlled risk set")
    if set(required.get("approval_gate", [])) != APPROVALS:
        errors.append("approval gates do not match the controlled approval set")
    return errors

if __name__ == "__main__":
    problems = validate()
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        raise SystemExit(1)
    print("PASS: AI workforce registry, roles, divisions and handoff contract are consistent.")

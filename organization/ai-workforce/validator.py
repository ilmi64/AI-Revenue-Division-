"""Fail-closed validation for the organisation AI workforce records."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIVISIONS = {
    "Executive Management", "AI Revenue", "Technology and Infrastructure",
    "Research and Intelligence", "Finance and Treasury", "Risk, Security and Recovery",
    "Crypto and PolyBot", "Ecommerce", "Animora and Future Creative Studio",
    "Trader Intelligence & Strategy Replication", "Business & Commercial",
}
STATUSES = {"proposed", "ready", "in_progress", "blocked", "review", "complete"}
RISKS = {"low", "moderate", "high", "critical"}
APPROVALS = {"none", "owner_review", "explicit_owner_approval"}

def load(name: str) -> dict:
    with (ROOT / name).open(encoding="utf-8") as handle:
        return json.load(handle)

def validate() -> list[str]:
    errors: list[str] = []
    registry = load("model-registry.json")
    roles = load("agent-roles.json")
    contract = load("task-handoff-contract.json")

    if registry.get("policy", {}).get("incremental_spend_cad") != 0:
        errors.append("incremental_spend_cad must remain zero")
    if registry.get("policy", {}).get("paid_apis") is not False:
        errors.append("paid APIs must remain disabled")
    if registry.get("policy", {}).get("paid_trials") is not False:
        errors.append("paid trials must remain disabled")

    models = registry.get("models", [])
    model_ids = [m.get("id") for m in models]
    if len(model_ids) != len(set(model_ids)) or None in model_ids:
        errors.append("model IDs must be present and unique")
    model_map = {m.get("id"): m for m in models}
    qwen = model_map.get("qwen-primary-pilot")
    llama = model_map.get("llama-review-candidate")
    if not qwen or qwen.get("status") != "integrated_in_main_unverified_end_to_end":
        errors.append("Qwen pilot status/evidence must be preserved accurately")
    if not llama or llama.get("status") != "evaluation_candidate":
        errors.append("Llama must remain an evaluation candidate until verified")

    role_ids = [r.get("id") for r in roles.get("roles", [])]
    if len(role_ids) != len(set(role_ids)):
        errors.append("role IDs must be unique")
    for role in roles.get("roles", []):
        model_id = role.get("model_id")
        if model_id and model_id not in model_map:
            errors.append(f"role {role.get('id')} references unknown model {model_id}")
    if set(roles.get("divisions", [])) != DIVISIONS:
        errors.append("division registry must contain exactly the 11 registered divisions")

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

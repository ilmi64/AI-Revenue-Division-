"""Offline, side-effect-free policy decision reference.

Synthetic fixtures only. This module does not execute tools, issue credentials,
connect to services, or establish production security enforcement.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Decision:
    outcome: str
    reason: str

    @property
    def allowed(self) -> bool:
        return self.outcome == "allow"


def authorize(
    request: dict[str, Any],
    identity: dict[str, Any],
    policy: dict[str, Any],
    *,
    now: int,
    approvals: list[dict[str, Any]] | None = None,
    replay_cache: set[str] | None = None,
    revoked_agents: set[str] | None = None,
    cancelled_tasks: set[str] | None = None,
) -> Decision:
    """Evaluate a synthetic request; never performs the requested operation."""
    approvals = approvals or []
    replay_cache = replay_cache if replay_cache is not None else set()
    revoked_agents = revoked_agents or set()
    cancelled_tasks = cancelled_tasks or set()

    def deny(reason: str) -> Decision:
        return Decision("deny", reason)

    # Fail closed for malformed or unavailable control inputs.
    if not isinstance(request, dict) or not isinstance(identity, dict) or not isinstance(policy, dict):
        return deny("malformed_input")
    if policy.get("available") is not True:
        return deny("policy_unavailable")
    required_identity = ("agent_id", "company_id", "role", "expires_at")
    if any(not identity.get(k) for k in required_identity):
        return deny("invalid_identity")
    if not isinstance(identity.get("expires_at"), int) or identity["expires_at"] <= now:
        return deny("identity_expired")
    if identity["agent_id"] in revoked_agents:
        return deny("identity_revoked")

    required_request = ("task_id", "company_id", "operation", "resource", "nonce")
    if any(not request.get(k) for k in required_request):
        return deny("malformed_request")
    if request["company_id"] != identity["company_id"]:
        return deny("company_mismatch")
    if request["task_id"] in cancelled_tasks:
        return deny("task_cancelled")
    if policy.get("emergency_stop") is True:
        return deny("emergency_stop_active")
    if request["nonce"] in replay_cache:
        return deny("replayed_nonce")

    # No agent may mutate policy or risk authority through a tool request.
    operation = request["operation"]
    if operation in {"policy.change", "risk.halt.change", "risk.stop.change", "permission.grant"}:
        return deny("protected_control_plane_operation")
    if policy.get("company_id") != identity["company_id"]:
        return deny("policy_company_mismatch")

    allowed = policy.get("allowed_operations", [])
    if operation not in allowed:
        return deny("operation_not_allowlisted")
    resource = request["resource"]
    resource_prefixes = policy.get("allowed_resource_prefixes", [])
    if not any(isinstance(p, str) and resource.startswith(p) for p in resource_prefixes):
        return deny("resource_out_of_scope")

    # Spending is zero unless a separate, exact, owner-approved budget exists.
    cost = request.get("cost_cad", 0)
    if not isinstance(cost, (int, float)) or cost < 0:
        return deny("invalid_cost")
    cost_cap = policy.get("cost_cap_cad", 0)
    if cost > cost_cap:
        return deny("cost_cap_exceeded")

    # Trading live execution remains categorically disabled in this reference.
    if identity["company_id"] == "trading_technology" and operation in {
        "trade.live_order", "wallet.sign", "funds.transfer"
    }:
        return deny("live_financial_action_disabled")

    if operation == "market_data.read" and request.get("provenance_verified") is not True:
        return deny("market_data_provenance_unverified")

    if policy.get("approval_required", False) or request.get("requires_approval") is True:
        match = any(
            a.get("status") == "approved"
            and a.get("company_id") == identity["company_id"]
            and a.get("task_id") == request["task_id"]
            and a.get("operation") == operation
            and a.get("resource") == resource
            and a.get("expires_at", 0) > now
            and a.get("single_use") is True
            and a.get("nonce") == request["nonce"]
            for a in approvals
        )
        if not match:
            return deny("exact_owner_approval_missing_or_invalid")

    # Consume the nonce only after every check succeeds. This is an in-memory
    # demonstration cache, not durable distributed replay protection.
    replay_cache.add(request["nonce"])
    return Decision("allow", "synthetic_policy_checks_passed")

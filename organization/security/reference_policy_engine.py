"""Offline, side-effect-free policy decision reference.

Synthetic fixtures only. This module does not execute tools, issue credentials,
connect to services, or establish production security enforcement.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class Decision:
    outcome: str
    reason: str

    @property
    def allowed(self) -> bool:
        return self.outcome == "allow"


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_timestamp(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_amount(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if isinstance(value, int):
        return value >= 0
    return math.isfinite(value) and value >= 0


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
    def deny(reason: str) -> Decision:
        return Decision("deny", reason)

    if not isinstance(request, dict) or not isinstance(identity, dict) or not isinstance(policy, dict):
        return deny("malformed_input")
    if not _valid_timestamp(now):
        return deny("invalid_evaluation_time")
    if approvals is None:
        approvals = []
    if not isinstance(approvals, list) or any(not isinstance(item, dict) for item in approvals):
        return deny("malformed_approval_set")
    if replay_cache is None:
        replay_cache = set()
    if revoked_agents is None:
        revoked_agents = set()
    if cancelled_tasks is None:
        cancelled_tasks = set()
    if not isinstance(replay_cache, set) or not isinstance(revoked_agents, set) or not isinstance(cancelled_tasks, set):
        return deny("malformed_control_state")
    if any(not _nonempty_string(x) for x in replay_cache | revoked_agents | cancelled_tasks):
        return deny("malformed_control_state")

    if policy.get("available") is not True:
        return deny("policy_unavailable")

    for key in ("agent_id", "company_id", "role"):
        if not _nonempty_string(identity.get(key)):
            return deny("invalid_identity")
    if not _valid_timestamp(identity.get("expires_at")):
        return deny("invalid_identity_expiry")
    if identity["expires_at"] <= now:
        return deny("identity_expired")
    if identity["agent_id"] in revoked_agents:
        return deny("identity_revoked")

    for key in ("task_id", "company_id", "operation", "resource", "nonce"):
        if not _nonempty_string(request.get(key)):
            return deny("malformed_request")
    if request["company_id"] != identity["company_id"]:
        return deny("company_mismatch")
    if request["task_id"] in cancelled_tasks:
        return deny("task_cancelled")
    if policy.get("emergency_stop") is not False:
        return deny("emergency_stop_active_or_unverified")
    if request["nonce"] in replay_cache:
        return deny("replayed_nonce")

    operation = request["operation"]
    if operation in {"policy.change", "risk.halt.change", "risk.stop.change", "permission.grant"}:
        return deny("protected_control_plane_operation")
    if policy.get("company_id") != identity["company_id"]:
        return deny("policy_company_mismatch")

    allowed = policy.get("allowed_operations")
    if not isinstance(allowed, list) or any(not _nonempty_string(x) for x in allowed):
        return deny("malformed_operation_allowlist")
    if operation not in allowed:
        return deny("operation_not_allowlisted")

    resource = request["resource"]
    prefixes = policy.get("allowed_resource_prefixes")
    if not isinstance(prefixes, list) or any(not _nonempty_string(x) for x in prefixes):
        return deny("malformed_resource_allowlist")
    if not any(resource.startswith(prefix) for prefix in prefixes):
        return deny("resource_out_of_scope")

    cost = request.get("cost_cad", 0)
    cap = policy.get("cost_cap_cad", 0)
    if not _valid_amount(cost):
        return deny("invalid_cost")
    if not _valid_amount(cap):
        return deny("invalid_cost_cap")
    if cost > cap:
        return deny("cost_cap_exceeded")

    if identity["company_id"] == "trading_technology" and operation in {
        "trade.live_order", "wallet.sign", "funds.transfer", "broker.order", "exchange.withdraw"
    }:
        return deny("live_financial_action_disabled")
    if operation == "market_data.read" and request.get("provenance_verified") is not True:
        return deny("market_data_provenance_unverified")

    approval_required = policy.get("approval_required", False)
    requires_approval = request.get("requires_approval", False)
    if not isinstance(approval_required, bool) or not isinstance(requires_approval, bool):
        return deny("malformed_approval_requirement")
    if approval_required or requires_approval:
        def exact_approval(item: dict[str, Any]) -> bool:
            expiry = item.get("expires_at")
            return (
                item.get("status") == "approved"
                and item.get("issuer") == "owner"
                and item.get("company_id") == identity["company_id"]
                and item.get("task_id") == request["task_id"]
                and item.get("operation") == operation
                and item.get("resource") == resource
                and _valid_timestamp(expiry)
                and expiry > now
                and item.get("single_use") is True
                and item.get("nonce") == request["nonce"]
            )
        if not any(exact_approval(item) for item in approvals):
            return deny("exact_owner_approval_missing_or_invalid")

    # In-memory demonstration only; not durable or distributed replay protection.
    replay_cache.add(request["nonce"])
    return Decision("allow", "synthetic_policy_checks_passed")

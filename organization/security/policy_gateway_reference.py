"""Offline deterministic policy gateway reference. No external actions are performed."""
from dataclasses import dataclass
from typing import Callable, FrozenSet

TRADING_ALWAYS_DENY = frozenset({
    "trade.live_order", "wallet.sign", "funds.transfer", "broker.order",
    "exchange.withdraw", "wallet.withdraw", "risk.halt.modify",
    "risk.stop.modify", "risk.limits.modify"
})
PROTECTED = frozenset({"policy.modify", "identity.grant", "approval.issue", "secret.read"})

@dataclass(frozen=True)
class Principal:
    agent_id: str
    company_id: str
    role: str
    session_id: str
    active: bool
    expires_at: int

@dataclass(frozen=True)
class Task:
    task_id: str
    company_id: str
    assigned_agent_id: str
    allowed_operations: FrozenSet[str]
    allowed_resources: FrozenSet[str]
    expires_at: int
    policy_version: str

@dataclass(frozen=True)
class Request:
    operation: str
    resource: str
    now: int
    policy_version: str
    requires_owner_approval: bool = False
    approval_id: str = ""

@dataclass(frozen=True)
class Decision:
    outcome: str
    reason: str

class PolicyGateway:
    """All callbacks are trusted infrastructure interfaces, never model-supplied."""
    def __init__(self, *, identity_verifier: Callable, approval_consumer: Callable,
                 emergency_stop: Callable, current_policy_version: Callable,
                 trading_company_ids):
        ids=frozenset(trading_company_ids)
        if not ids or any(not isinstance(x,str) or not x.strip() for x in ids):
            raise ValueError("explicit_trading_company_ids_required")
        self.trading_company_ids=ids
        self.identity_verifier=identity_verifier
        self.approval_consumer=approval_consumer
        self.emergency_stop=emergency_stop
        self.current_policy_version=current_policy_version

    def authorize(self, principal: Principal, task: Task, request: Request) -> Decision:
        try:
            if not self.identity_verifier(principal): return Decision("deny","identity_unverified")
            if not principal.active or request.now >= principal.expires_at:
                return Decision("deny","principal_inactive_or_expired")
            if request.now >= task.expires_at: return Decision("deny","task_expired")
            if principal.company_id != task.company_id:
                return Decision("deny","principal_task_company_mismatch")
            if principal.agent_id != task.assigned_agent_id:
                return Decision("deny","agent_not_assigned_to_task")
            if request.policy_version != self.current_policy_version():
                return Decision("deny","stale_policy_version")
            if task.policy_version != request.policy_version:
                return Decision("deny","task_policy_version_mismatch")
            if self.emergency_stop(principal.company_id):
                return Decision("deny","company_emergency_stop_active")
            if request.operation in PROTECTED:
                return Decision("deny","protected_control_plane_operation")
            if principal.company_id in self.trading_company_ids and request.operation in TRADING_ALWAYS_DENY:
                return Decision("deny","trading_live_or_risk_control_action_prohibited")
            if request.operation not in task.allowed_operations:
                return Decision("deny","operation_outside_task_scope")
            if request.resource not in task.allowed_resources:
                return Decision("deny","resource_outside_task_scope")
            if request.requires_owner_approval:
                if not request.approval_id:
                    return Decision("deny","owner_approval_missing")
                if not self.approval_consumer(request.approval_id, principal, task, request):
                    return Decision("deny","owner_approval_invalid_or_unconsumed")
            return Decision("allow","all_deterministic_checks_passed")
        except Exception:
            return Decision("deny","policy_dependency_error_fail_closed")

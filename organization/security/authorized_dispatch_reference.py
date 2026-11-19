"""Composition reference: gateway authorization at the final outbox dispatch boundary.

No network calls. Injected resolver, gateway callbacks and sender are trusted
infrastructure/test doubles, not model-controlled values.
"""
import json

REQUIRED = ("company_id", "agent_id", "task_id", "operation", "resource",
            "policy_version", "requires_owner_approval", "approval_id")

def dispatch_authorized_one(*, store, worker, now, gateway, context_resolver,
                            sender, dispatch_fn, audit_fn=lambda *a, **k: None):
    """Claim one action; bind its immutable payload to trusted identity/task context;
    authorize once at final dispatch; then invoke sender with remote idempotency key.

    context_resolver(claim, payload, now) must load identity/task from trusted
    control-plane stores and return (principal, task, request). Never build
    principal/task from payload or model-supplied claims.
    """
    def final_policy_check(claim):
        try:
            payload = json.loads(claim.payload_json)
            if not isinstance(payload, dict) or any(k not in payload for k in REQUIRED):
                audit_fn("dispatch_denied", {"action_id": claim.action_id, "reason": "malformed_action_payload"})
                return False
            principal, task, request = context_resolver(claim, payload, now)
            bound = {
                "company_id": principal.company_id,
                "agent_id": principal.agent_id,
                "task_id": task.task_id,
                "operation": request.operation,
                "resource": request.resource,
                "policy_version": request.policy_version,
                "requires_owner_approval": request.requires_owner_approval,
                "approval_id": request.approval_id,
            }
            if any(payload.get(k) != v for k, v in bound.items()):
                audit_fn("dispatch_denied", {"action_id": claim.action_id, "reason": "payload_context_mismatch"})
                return False
            decision = gateway.authorize(principal, task, request)
            audit_fn("dispatch_authorization", {
                "action_id": claim.action_id, "company_id": principal.company_id,
                "agent_id": principal.agent_id, "task_id": task.task_id,
                "operation": request.operation, "resource": request.resource,
                "outcome": decision.outcome, "reason": decision.reason,
                "policy_version": request.policy_version
            })
            return decision.outcome == "allow"
        except Exception:
            audit_fn("dispatch_denied", {"action_id": claim.action_id, "reason": "context_or_audit_dependency_error"})
            return False
    return dispatch_fn(store, worker, now, final_policy_check, sender)

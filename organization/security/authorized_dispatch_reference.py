"""Composition reference: gateway authorization at the final outbox dispatch boundary.

No network calls. Injected resolver, gateway callbacks and sender are trusted
infrastructure/test doubles, not model-controlled values.
"""
import json

REQUIRED = ("company_id", "agent_id", "task_id", "operation", "resource",
            "policy_version", "requires_owner_approval", "approval_id")

def dispatch_authorized_one(*, store, worker, now, gateway, context_resolver,
                            sender, dispatch_fn, audit_fn=lambda *a, **k: None):
    """Claim one action and authorize once immediately before sender invocation.

    context_resolver must load principal/task from trusted control-plane stores;
    never construct them from model-supplied payload claims.
    """
    def emit(event, data):
        try:
            audit_fn(event, data)
            return True
        except Exception:
            return False

    def final_policy_check(claim):
        try:
            payload = json.loads(claim.payload_json)
            if not isinstance(payload, dict) or any(k not in payload for k in REQUIRED):
                emit("dispatch_denied", {"action_id": claim.action_id, "reason": "malformed_action_payload"})
                return False
            principal, task, request = context_resolver(claim, payload, now)
            bound = {
                "company_id": principal.company_id, "agent_id": principal.agent_id,
                "task_id": task.task_id, "operation": request.operation,
                "resource": request.resource, "policy_version": request.policy_version,
                "requires_owner_approval": request.requires_owner_approval,
                "approval_id": request.approval_id,
            }
            if any(payload.get(k) != v for k, v in bound.items()):
                emit("dispatch_denied", {"action_id": claim.action_id, "reason": "payload_context_mismatch"})
                return False
            decision = gateway.authorize(principal, task, request)
            audit_ok = emit("dispatch_authorization", {
                "action_id": claim.action_id, "company_id": principal.company_id,
                "agent_id": principal.agent_id, "task_id": task.task_id,
                "operation": request.operation, "resource": request.resource,
                "outcome": decision.outcome, "reason": decision.reason,
                "policy_version": request.policy_version
            })
            return audit_ok and decision.outcome == "allow"
        except Exception:
            # Do not attempt a second audit write when the audit dependency itself failed.
            return False
    return dispatch_fn(store, worker, now, final_policy_check, sender)

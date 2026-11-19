"""Offline recovery and reconciliation reference for outbox + approval ledger.

No network, broker, wallet, or external side effects. All evidence is supplied by
a trusted operator/reconciler and must be independently authenticated in production.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ReconciliationEvidence:
    action_id: str
    idempotency_key: str
    checked_at: int
    source: str
    outcome: str  # confirmed_not_applied | confirmed_applied | inconclusive
    evidence_digest: str
    authenticated: bool

@dataclass(frozen=True)
class RecoveryResult:
    status: str
    reason: str

def reconcile_unknown_action(*, store, action_id: str, evidence: ReconciliationEvidence,
                             now: int, max_evidence_age: int = 300) -> RecoveryResult:
    """Resolve outcome_unknown without ever blindly replaying an external action."""
    try:
        action=store.get(action_id)
        if action is None:
            return RecoveryResult("denied","action_not_found")
        if action["status"] != "outcome_unknown":
            return RecoveryResult("denied","action_not_in_unknown_state")
        if (not evidence.authenticated or evidence.action_id != action_id or
            evidence.idempotency_key != action["idempotency_key"]):
            return RecoveryResult("quarantined","evidence_identity_or_authentication_mismatch")
        if (not evidence.source or not evidence.evidence_digest or
            now < evidence.checked_at or now-evidence.checked_at > max_evidence_age):
            return RecoveryResult("quarantined","evidence_missing_or_stale")
        if evidence.outcome == "confirmed_applied":
            # Mark as completed only after authoritative receiver evidence.
            store.resolve_unknown(action_id, "confirmed_applied", evidence.evidence_digest, now)
            return RecoveryResult("resolved_applied","receiver_confirms_effect")
        if evidence.outcome == "confirmed_not_applied":
            # Never reset an action directly to pending. Require a new action intent
            # and fresh approval/policy decision in the production workflow.
            store.resolve_unknown(action_id, "confirmed_not_applied", evidence.evidence_digest, now)
            return RecoveryResult("resolved_not_applied_new_intent_required",
                                  "old_action_closed_fresh_authorization_required")
        return RecoveryResult("quarantined","inconclusive_receiver_state")
    except Exception:
        return RecoveryResult("quarantined","reconciliation_dependency_failure")

def verify_backup_restore(*, restored_ledger, expected_company: str,
                          expected_audit_valid: bool, expected_consumed_approval_ids):
    """Offline restore acceptance helper; caller supplies expected manifest."""
    try:
        if not expected_audit_valid or not restored_ledger.verify_audit(expected_company):
            return RecoveryResult("failed","audit_chain_invalid_after_restore")
        for approval_id in expected_consumed_approval_ids:
            if restored_ledger.count_consumptions(approval_id) != 1:
                return RecoveryResult("failed","consumption_state_missing_or_duplicated")
        return RecoveryResult("passed","manifest_and_audit_checks_passed")
    except Exception:
        return RecoveryResult("failed","restore_verification_error")

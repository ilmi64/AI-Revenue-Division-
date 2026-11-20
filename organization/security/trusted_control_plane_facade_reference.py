"""Trusted control-plane façade reference for identity/task resolution and approval issuance.

Offline interface prototype only. Cryptographic verification, trusted clock,
scheduler, revocation, and durable approval repository are trusted adapters
bound at service construction. No network or financial side effects occur.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, FrozenSet


class TrustedControlPlaneError(ValueError):
    pass


@dataclass(frozen=True)
class VerifiedPrincipal:
    agent_id: str
    company_id: str
    role: str
    session_id: str
    runtime_id: str
    identity_epoch: int
    expires_at: int


@dataclass(frozen=True)
class VerifiedTask:
    task_id: str
    company_id: str
    assigned_agent_id: str
    stream_id: str
    allowed_operations: FrozenSet[str]
    allowed_resources: FrozenSet[str]
    policy_version: str
    expires_at: int


@dataclass(frozen=True)
class VerifiedContext:
    principal: VerifiedPrincipal
    task: VerifiedTask
    resolved_at: int


@dataclass(frozen=True)
class ApprovalReceipt:
    approval_id: str
    company_id: str
    scope_digest: str
    expires_at: int
    audit_event_id: str


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _timestamp(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


class TrustedControlPlaneFacade:
    """Narrow company-scoped façade; dependencies are fixed at trusted startup."""

    def __init__(self, *, company_id: str, identity_audience: str,
                 approval_audience: str, trusted_owner_ids: set[str],
                 clock: Any, identity_verifier: Any, task_scheduler: Any,
                 owner_approval_verifier: Any, approval_repository: Any):
        if not all(_nonempty(x) for x in
                   (company_id, identity_audience, approval_audience)):
            raise TrustedControlPlaneError("company_and_audiences_required")
        if not isinstance(trusted_owner_ids, (set, frozenset)) or not trusted_owner_ids:
            raise TrustedControlPlaneError("trusted_owner_registry_required")
        if any(not _nonempty(x) for x in trusted_owner_ids):
            raise TrustedControlPlaneError("invalid_trusted_owner_registry")
        required = (
            (clock, "now"), (identity_verifier, "verify"),
            (task_scheduler, "resolve"),
            (owner_approval_verifier, "verify"),
            (approval_repository, "issue"),
        )
        if any(not callable(getattr(obj, method, None)) for obj, method in required):
            raise TrustedControlPlaneError("trusted_dependency_interface_missing")
        self.__company_id = company_id
        self.__identity_audience = identity_audience
        self.__approval_audience = approval_audience
        self.__trusted_owner_ids = frozenset(trusted_owner_ids)
        self.__clock = clock
        self.__identity_verifier = identity_verifier
        self.__task_scheduler = task_scheduler
        self.__owner_approval_verifier = owner_approval_verifier
        self.__approval_repository = approval_repository

    def _now(self) -> int:
        now = self.__clock.now()
        if not _timestamp(now):
            raise TrustedControlPlaneError("trusted_clock_invalid")
        return now

    @staticmethod
    def _verified_claims(result: Any, failure: str) -> dict[str, Any]:
        if not isinstance(result, dict) or result.get("verified") is not True:
            raise TrustedControlPlaneError(failure)
        claims = result.get("claims")
        if not isinstance(claims, dict):
            raise TrustedControlPlaneError("verified_claims_missing")
        return claims

    def resolve_principal_and_task(self, *, identity_assertion: Any,
                                   task_reference: str) -> VerifiedContext:
        if not _nonempty(task_reference):
            raise TrustedControlPlaneError("task_reference_required")
        now = self._now()
        try:
            identity_result = self.__identity_verifier.verify(
                identity_assertion,
                expected={"company_id": self.__company_id,
                          "audience": self.__identity_audience},
                now=now,
            )
        except Exception as exc:
            raise TrustedControlPlaneError("identity_verification_unavailable") from exc
        claims = self._verified_claims(identity_result, "identity_not_verified")
        required_strings = ("agent_id", "company_id", "role", "session_id", "runtime_id")
        if any(not _nonempty(claims.get(k)) for k in required_strings):
            raise TrustedControlPlaneError("identity_claims_incomplete")
        if claims["company_id"] != self.__company_id:
            raise TrustedControlPlaneError("identity_company_mismatch")
        issued, expiry, epoch = (claims.get("issued_at"), claims.get("expires_at"),
                                 claims.get("identity_epoch"))
        if not _timestamp(issued) or not _timestamp(expiry) or expiry <= now or issued > now:
            raise TrustedControlPlaneError("identity_expired_or_invalid")
        if not _timestamp(epoch):
            raise TrustedControlPlaneError("identity_epoch_invalid")
        principal = VerifiedPrincipal(
            agent_id=claims["agent_id"], company_id=claims["company_id"],
            role=claims["role"], session_id=claims["session_id"],
            runtime_id=claims["runtime_id"], identity_epoch=epoch,
            expires_at=expiry,
        )
        try:
            task_claims = self.__task_scheduler.resolve(
                task_reference=task_reference, principal=principal, now=now)
        except Exception as exc:
            raise TrustedControlPlaneError("trusted_task_resolution_unavailable") from exc
        if not isinstance(task_claims, dict):
            raise TrustedControlPlaneError("trusted_task_not_found")
        strings = ("task_id", "company_id", "assigned_agent_id", "stream_id", "policy_version")
        if any(not _nonempty(task_claims.get(k)) for k in strings):
            raise TrustedControlPlaneError("task_claims_incomplete")
        if (task_claims["company_id"] != self.__company_id or
                task_claims["assigned_agent_id"] != principal.agent_id):
            raise TrustedControlPlaneError("task_assignment_or_company_mismatch")
        task_expiry = task_claims.get("expires_at")
        if not _timestamp(task_expiry) or task_expiry <= now:
            raise TrustedControlPlaneError("task_expired_or_invalid")
        operations, resources = task_claims.get("allowed_operations"), task_claims.get("allowed_resources")
        if (not isinstance(operations, (set, frozenset, list, tuple)) or
                not isinstance(resources, (set, frozenset, list, tuple)) or
                not operations or not resources or
                any(not _nonempty(x) for x in operations) or
                any(not _nonempty(x) for x in resources)):
            raise TrustedControlPlaneError("task_scope_invalid")
        task = VerifiedTask(
            task_id=task_claims["task_id"], company_id=task_claims["company_id"],
            assigned_agent_id=task_claims["assigned_agent_id"],
            stream_id=task_claims["stream_id"],
            allowed_operations=frozenset(operations),
            allowed_resources=frozenset(resources),
            policy_version=task_claims["policy_version"], expires_at=task_expiry,
        )
        return VerifiedContext(principal=principal, task=task, resolved_at=now)

    def issue_owner_approval(self, *, owner_signed_envelope: Any) -> ApprovalReceipt:
        """Verify owner signature/scope, then persist via the trusted repository.

        This endpoint must be reachable only through the owner-approval service
        identity. A signed document alone does not authorize agent callers to
        invoke this method.
        """
        now = self._now()
        expected = {"company_id": self.__company_id,
                    "audience": self.__approval_audience,
                    "single_use": True}
        try:
            result = self.__owner_approval_verifier.verify(
                owner_signed_envelope, expected=expected, now=now)
        except Exception as exc:
            raise TrustedControlPlaneError("owner_approval_verification_unavailable") from exc
        claims = self._verified_claims(result, "owner_approval_not_verified")
        fields = ("owner_id", "company_id", "stream_id", "agent_id", "session_id",
                  "task_id", "operation", "resource", "policy_version", "nonce",
                  "audience", "approval_id", "scope_digest")
        if any(not _nonempty(claims.get(k)) for k in fields):
            raise TrustedControlPlaneError("owner_approval_scope_incomplete")
        if claims["owner_id"] not in self.__trusted_owner_ids:
            raise TrustedControlPlaneError("owner_not_in_trusted_registry")
        if claims["company_id"] != self.__company_id or claims["audience"] != self.__approval_audience:
            raise TrustedControlPlaneError("owner_approval_company_or_audience_mismatch")
        if claims.get("single_use") is not True:
            raise TrustedControlPlaneError("approval_must_be_single_use")
        issued, expiry = claims.get("issued_at"), claims.get("expires_at")
        if not _timestamp(issued) or not _timestamp(expiry) or issued > now or expiry <= now:
            raise TrustedControlPlaneError("owner_approval_expired_or_invalid")
        amount = claims.get("amount_minor")
        currency = claims.get("currency")
        if amount is not None:
            if not _timestamp(amount) or not _nonempty(currency):
                raise TrustedControlPlaneError("amount_requires_nonnegative_minor_units_and_currency")
        elif currency is not None and not _nonempty(currency):
            raise TrustedControlPlaneError("invalid_currency")
        try:
            receipt = self.__approval_repository.issue(claims=dict(claims), now=now)
        except Exception as exc:
            raise TrustedControlPlaneError("durable_approval_persistence_failed") from exc
        if not isinstance(receipt, dict) or any(
            not _nonempty(receipt.get(k)) for k in
            ("approval_id", "company_id", "scope_digest", "audit_event_id")
        ):
            raise TrustedControlPlaneError("approval_repository_receipt_invalid")
        if receipt["approval_id"] != claims["approval_id"] or receipt["company_id"] != self.__company_id:
            raise TrustedControlPlaneError("approval_repository_scope_mismatch")
        if receipt["scope_digest"] != claims["scope_digest"]:
            raise TrustedControlPlaneError("approval_repository_digest_mismatch")
        receipt_expiry = receipt.get("expires_at")
        if not _timestamp(receipt_expiry) or receipt_expiry != expiry:
            raise TrustedControlPlaneError("approval_repository_expiry_mismatch")
        return ApprovalReceipt(
            approval_id=receipt["approval_id"], company_id=receipt["company_id"],
            scope_digest=receipt["scope_digest"], expires_at=receipt_expiry,
            audit_event_id=receipt["audit_event_id"],
        )

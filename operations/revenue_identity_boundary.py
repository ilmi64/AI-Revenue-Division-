"""Offline identity trust-boundary checks; no identity authority is created here.

An external administrator must authenticate identities, keys and role grants.
A caller-supplied claim is never sufficient to authorize delivery or execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from revenue_evidence_custody import EvidenceReceipt
from revenue_review_separation import ReviewSeparation, assess_review


@dataclass(frozen=True)
class VerifiedPrincipal:
    principal_id: str
    role: str
    identity_verified: bool
    role_grant_verified: bool
    revoked: bool
    trust_domain: str


@dataclass(frozen=True)
class IdentityAssessment:
    task_id: str
    status: str
    blockers: tuple[str, ...]
    identity_verified: bool = False
    independent_custody_verified: bool = False
    execution_authorized: bool = False
    external_delivery_authorized: bool = False


def assess_identity(author: EvidenceReceipt, reviewer: EvidenceReceipt,
                    author_principal: VerifiedPrincipal,
                    reviewer_principal: VerifiedPrincipal,
                    *, trusted_registry_verified: bool = False) -> IdentityAssessment:
    if not isinstance(author_principal, VerifiedPrincipal) or not isinstance(reviewer_principal, VerifiedPrincipal):
        raise TypeError("principal evidence required")
    structural = assess_review(author, reviewer)
    blockers = list(structural.blockers)
    if trusted_registry_verified is not True:
        blockers.append("trusted_registry_not_verified")
    for receipt, principal, label in (
        (author, author_principal, "author"), (reviewer, reviewer_principal, "reviewer")
    ):
        if receipt.actor_id != principal.principal_id or receipt.actor_role != principal.role:
            blockers.append(label + "_identity_mismatch")
        if (principal.identity_verified is not True or principal.role_grant_verified is not True
                or principal.revoked is not False):
            blockers.append(label + "_trust_unverified")
        if not isinstance(principal.trust_domain, str) or not principal.trust_domain:
            blockers.append(label + "_domain_missing")
    if (author_principal.principal_id == reviewer_principal.principal_id
            or author_principal.trust_domain == reviewer_principal.trust_domain):
        blockers.append("independence_boundary_missing")
    return IdentityAssessment(author.task_id, "HOLD" if blockers else "IDENTITY_EVIDENCE_REPORTED",
                              tuple(blockers))

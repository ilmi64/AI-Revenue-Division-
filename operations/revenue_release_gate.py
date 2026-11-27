"""Aevora offline commissioning release gate: diagnostic only, never authorizes action."""
from __future__ import annotations
from dataclasses import dataclass
from revenue_identity_boundary import IdentityAssessment
from revenue_evidence_custody import LocalEvidenceCustody


@dataclass(frozen=True)
class ReleaseGate:
    status: str
    blockers: tuple[str, ...]
    execution_authorized: bool = False
    customer_contact_authorized: bool = False
    external_submission_authorized: bool = False
    spending_authorized: bool = False
    deployment_authorized: bool = False


def assess_release(identity: IdentityAssessment, custody: LocalEvidenceCustody,
                   *, anchor_sequence: int | None = None,
                   anchor_digest: str | None = None) -> ReleaseGate:
    """Caller-supplied anchors and identity claims do not constitute independent trust."""
    if not isinstance(identity, IdentityAssessment) or not isinstance(custody, LocalEvidenceCustody):
        raise TypeError("identity assessment and custody required")
    blockers = list(identity.blockers)
    if identity.status != "IDENTITY_EVIDENCE_REPORTED":
        blockers.append("identity_evidence_not_ready")
    if identity.identity_verified is not True:
        blockers.append("authenticated_identity_not_established")
    if identity.independent_custody_verified is not True:
        blockers.append("independent_custody_not_established")
    if anchor_sequence is None or anchor_digest is None:
        blockers.append("external_anchor_missing")
    elif not custody.verify_anchor(anchor_sequence, anchor_digest):
        blockers.append("external_anchor_mismatch")
    # No trusted authority integration: these flags are never elevated by this module.
    return ReleaseGate("BLOCKED", tuple(dict.fromkeys(blockers or ["release_authority_absent"])))

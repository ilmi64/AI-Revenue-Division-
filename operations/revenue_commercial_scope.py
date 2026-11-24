"""Closed internal commercial-review scope for the existing synthetic workflow."""
from dataclasses import dataclass
from types import MappingProxyType

from evidence_verifier import VerificationBlocked
from revenue_fixture_dispatch import PROFILES


_WORK_SCOPE = MappingProxyType({
    "app_build": "fixed_catalogue_preflight",
    "coding": "fixed_invoice_rounding",
    "ai_setup": "fixed_internal_review_routing",
    "authorized_bug_bounty": "static_fictional_program_terms_only",
})


@dataclass(frozen=True)
class CommercialReviewScope:
    service: str
    opportunity_reference: str
    work_scope: str
    company_id: str = "ai_revenue"
    recipient_scope: str = "ai_revenue"
    review_audience: str = "internal_owner_review_only"
    data_classification: str = "SYNTHETIC_FIXTURE_ONLY"
    upfront_cost_cap_cad: int = 0
    external_approval_granted: bool = False


def fixed_review_scope(service: str) -> CommercialReviewScope:
    if not isinstance(service, str) or service not in _WORK_SCOPE:
        raise VerificationBlocked("commercial_service_not_allowlisted")
    return CommercialReviewScope(service, PROFILES[service].reference, _WORK_SCOPE[service])


def validate_review_scope(request: CommercialReviewScope, service: str) -> None:
    if (
        not isinstance(request, CommercialReviewScope)
        or request != fixed_review_scope(service)
        or type(request.upfront_cost_cap_cad) is not int
        or request.external_approval_granted is not False
    ):
        raise VerificationBlocked("commercial_review_scope_mismatch")

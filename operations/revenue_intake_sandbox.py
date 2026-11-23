"""Offline opportunity intake for Aevora AI; no submissions, spending or execution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

KINDS = frozenset({"coding", "authorized_bug_bounty", "app_build", "ai_setup", "research"})
COUNTRIES = frozenset({"CA", "US", "GB", "EU", "OTHER"})
MAX_BUDGET_CAD = 1000000


@dataclass(frozen=True)
class Opportunity:
    reference: str
    kind: str
    country: str
    expected_revenue_cad: int
    upfront_cost_cad: int
    authorization_evidence: bool
    payout_confirmed: bool
    sanctions_reviewed: bool
    customer_contact_allowed: bool


@dataclass(frozen=True)
class Decision:
    reference: str
    status: Literal["REJECT", "HOLD", "REVIEW_READY"]
    reasons: tuple[str, ...]
    submission_authorized: bool = False
    spending_authorized: bool = False
    execution_authorized: bool = False


def qualify(item: Opportunity) -> Decision:
    if not isinstance(item, Opportunity):
        raise TypeError("Opportunity required")
    if not isinstance(item.reference, str) or not item.reference or len(item.reference) > 80 or not item.reference.isascii() or not all(c.isalnum() or c in "-_" for c in item.reference):
        raise ValueError("invalid reference")
    if item.kind not in KINDS or item.country not in COUNTRIES:
        return Decision(item.reference, "REJECT", ("unsupported_scope",))
    if any(type(v) is not int or v < 0 or v > MAX_BUDGET_CAD for v in (item.expected_revenue_cad, item.upfront_cost_cad)):
        return Decision(item.reference, "REJECT", ("invalid_financial_inputs",))
    if any(type(v) is not bool for v in (item.authorization_evidence, item.payout_confirmed, item.sanctions_reviewed, item.customer_contact_allowed)):
        return Decision(item.reference, "REJECT", ("invalid_evidence_flags",))
    if item.upfront_cost_cad:
        return Decision(item.reference, "REJECT", ("upfront_spend_forbidden",))
    reasons = []
    if not item.authorization_evidence:
        reasons.append("scope_authorization_unverified")
    if not item.payout_confirmed:
        reasons.append("payout_unverified")
    if not item.sanctions_reviewed:
        reasons.append("jurisdiction_review_pending")
    if not item.customer_contact_allowed:
        reasons.append("external_contact_not_approved")
    if item.expected_revenue_cad == 0:
        reasons.append("revenue_not_estimated")
    return Decision(item.reference, "HOLD" if reasons else "REVIEW_READY", tuple(reasons))

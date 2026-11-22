"""Offline R&I publication recipient-scope reference guard.

No publisher, network delivery, receipt persistence or authorization side effects.
A passing check is NOT approval to publish or act on intelligence.
"""
from dataclasses import dataclass
from enum import Enum


class Recipient(str, Enum):
    ORGANIZATION = "ORGANIZATION"
    AI_REVENUE = "AI_REVENUE"
    TRADING_TECHNOLOGY = "TRADING_TECHNOLOGY"


@dataclass(frozen=True)
class PublicationScope:
    publication_id: str
    recipient: Recipient
    audience: Recipient
    independently_reviewed: bool
    approved_for_publication: bool
    fresh: bool
    digest_verified: bool
    private_company_scopes: frozenset[Recipient]


def scope_blockers(item: PublicationScope, expected_recipient: Recipient) -> tuple[str, ...]:
    """Return blockers, never permission or a publication command."""
    if not isinstance(item, PublicationScope):
        return ("invalid_publication_scope",)
    if not isinstance(expected_recipient, Recipient):
        return ("invalid_expected_recipient",)
    reasons = []
    if not isinstance(item.recipient, Recipient) or not isinstance(item.audience, Recipient):
        reasons.append("invalid_recipient_type")
    if not isinstance(item.private_company_scopes, frozenset) or any(
        not isinstance(scope, Recipient) for scope in item.private_company_scopes
    ):
        reasons.append("invalid_private_scope")
        private_scopes = frozenset()
    else:
        private_scopes = item.private_company_scopes
    for name in ("independently_reviewed", "approved_for_publication", "fresh", "digest_verified"):
        if not isinstance(getattr(item, name), bool):
            reasons.append("invalid_" + name)
    if not isinstance(item.publication_id, str) or not item.publication_id.strip():
        reasons.append("missing_publication_id")
    if item.recipient != expected_recipient or item.audience != expected_recipient:
        reasons.append("wrong_recipient")
    if private_scopes - {expected_recipient}:
        reasons.append("cross_company_private_context")
    if expected_recipient == Recipient.ORGANIZATION and private_scopes:
        reasons.append("organization_private_context")
    if not item.independently_reviewed:
        reasons.append("independent_review_missing")
    if not item.approved_for_publication:
        reasons.append("publication_not_approved")
    if not item.fresh:
        reasons.append("stale")
    if not item.digest_verified:
        reasons.append("digest_unverified")
    return tuple(reasons)

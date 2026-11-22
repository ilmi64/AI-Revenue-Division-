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
    reasons = []
    if not isinstance(item.publication_id, str) or not item.publication_id.strip():
        reasons.append("missing_publication_id")
    valid_recipients = all(isinstance(value, Recipient) for value in (
        expected_recipient, item.recipient, item.audience
    ))
    if not valid_recipients:
        reasons.append("invalid_recipient_scope")
    elif item.recipient is not expected_recipient or item.audience is not expected_recipient:
        reasons.append("wrong_recipient")

    private_scopes = item.private_company_scopes
    if not isinstance(private_scopes, frozenset) or any(
        scope is not Recipient.AI_REVENUE and scope is not Recipient.TRADING_TECHNOLOGY
        for scope in private_scopes
    ):
        reasons.append("invalid_private_company_scopes")
    elif valid_recipients:
        if private_scopes - {expected_recipient}:
            reasons.append("cross_company_private_context")
        if expected_recipient is Recipient.ORGANIZATION and private_scopes:
            reasons.append("organization_private_context")
    if item.independently_reviewed is not True:
        reasons.append("independent_review_missing")
    if item.approved_for_publication is not True:
        reasons.append("publication_not_approved")
    if item.fresh is not True:
        reasons.append("stale")
    if item.digest_verified is not True:
        reasons.append("digest_unverified")
    return tuple(reasons)

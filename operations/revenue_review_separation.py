"""Offline reviewer-separation projection; identities are self-asserted until authenticated externally."""
from __future__ import annotations

from dataclasses import dataclass
from revenue_evidence_custody import EvidenceReceipt

REVIEW_ROLES = frozenset({"quality", "security", "compliance", "product", "research"})


@dataclass(frozen=True)
class ReviewSeparation:
    task_id: str
    status: str
    blockers: tuple[str, ...]
    identity_authenticated: bool = False
    independent_custody_verified: bool = False
    completion_verified: bool = False
    delivery_authorized: bool = False


def assess_review(author: EvidenceReceipt, reviewer: EvidenceReceipt) -> ReviewSeparation:
    if not isinstance(author, EvidenceReceipt) or not isinstance(reviewer, EvidenceReceipt):
        raise TypeError("two evidence receipts required")
    blockers = []
    if author.task_id != reviewer.task_id:
        blockers.append("task_mismatch")
    if author.actor_id == reviewer.actor_id:
        blockers.append("self_review")
    if reviewer.actor_role not in REVIEW_ROLES or reviewer.actor_role == author.actor_role:
        blockers.append("reviewer_role_invalid")
    if reviewer.sequence <= author.sequence:
        blockers.append("review_order_invalid")
    if reviewer.sequence == author.sequence + 1 and reviewer.previous_digest != author.record_digest:
        blockers.append("broken_adjacent_chain")
    if author.artifact_digest == reviewer.artifact_digest:
        blockers.append("review_artifact_not_distinct")
    return ReviewSeparation(author.task_id, "HOLD" if blockers else "STRUCTURALLY_SEPARATED",
                            tuple(blockers))

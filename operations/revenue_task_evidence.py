"""Offline Aevora task evidence review; no agent execution or customer delivery."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from revenue_agent_queue import QueueItem

DIGEST = re.compile(r"[0-9a-f]{64}\Z")
REVIEWERS = frozenset({"quality", "security", "compliance", "product", "research"})


@dataclass(frozen=True)
class TaskEvidence:
    task_id: str
    artifact_sha256: str
    artifact_bytes: bytes
    author_role: str
    reviewer_role: str
    reviewer_attested: bool


@dataclass(frozen=True)
class EvidenceDecision:
    task_id: str
    status: str
    reasons: tuple[str, ...]
    completion_verified: bool = False
    execution_authorized: bool = False
    external_delivery_authorized: bool = False
    spending_authorized: bool = False


def review_evidence(item: QueueItem, evidence: TaskEvidence) -> EvidenceDecision:
    if not isinstance(item, QueueItem) or not isinstance(evidence, TaskEvidence):
        raise TypeError("QueueItem and TaskEvidence required")
    reasons = []
    if item.state != "AWAITING_INTERNAL_REVIEW" or any((
        item.execution_authorized, item.external_delivery_authorized, item.spending_authorized
    )):
        reasons.append("queue_permissions_invalid")
    if evidence.task_id != item.task_id:
        reasons.append("task_identity_mismatch")
    if (not isinstance(evidence.artifact_bytes, bytes) or
            not evidence.artifact_bytes or len(evidence.artifact_bytes) > 1_000_000):
        reasons.append("artifact_invalid")
    if (not isinstance(evidence.artifact_sha256, str)
            or not DIGEST.fullmatch(evidence.artifact_sha256)
            or not isinstance(evidence.artifact_bytes, bytes)
            or hashlib.sha256(evidence.artifact_bytes).hexdigest() != evidence.artifact_sha256):
        reasons.append("artifact_digest_invalid")
    if evidence.author_role != item.role:
        reasons.append("author_role_mismatch")
    if (evidence.reviewer_role not in REVIEWERS
            or evidence.reviewer_role == evidence.author_role
            or evidence.reviewer_attested is not True):
        reasons.append("independent_review_unverified")
    return EvidenceDecision(item.task_id, "HOLD" if reasons else "EVIDENCE_REVIEWED", tuple(reasons))

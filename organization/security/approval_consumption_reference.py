"""Local simulation of one-time approval consumption; NOT durable/distributed."""
from __future__ import annotations
from dataclasses import dataclass
from threading import Lock
from typing import Optional

@dataclass(frozen=True)
class Approval:
    approval_id: str
    nonce: str
    company_id: str
    task_id: str
    operation: str
    resource: str
    expires_at: int
    owner_approved: bool = True

@dataclass(frozen=True)
class ConsumeResult:
    allowed: bool
    reason: str

class InMemoryApprovalConsumer:
    """Single-process demonstration. Lock/set do not prove cross-process atomicity."""
    def __init__(self):
        self._lock = Lock()
        self._consumed = set()
        self._revoked = set()
        self._cancelled_tasks = set()

    def revoke(self, approval_id: str) -> None:
        with self._lock: self._revoked.add(approval_id)

    def cancel_task(self, task_id: str) -> None:
        with self._lock: self._cancelled_tasks.add(task_id)

    def consume(self, approval: Approval, *, now: int, company_id: str,
                task_id: str, operation: str, resource: str) -> ConsumeResult:
        with self._lock:
            if not approval.owner_approved: return ConsumeResult(False, "owner_approval_missing")
            if not all((approval.approval_id, approval.nonce, approval.company_id,
                        approval.task_id, approval.operation, approval.resource)):
                return ConsumeResult(False, "malformed_approval")
            if approval.approval_id in self._revoked: return ConsumeResult(False, "approval_revoked")
            if task_id in self._cancelled_tasks: return ConsumeResult(False, "task_cancelled")
            if now >= approval.expires_at: return ConsumeResult(False, "approval_expired")
            if (approval.company_id, approval.task_id, approval.operation, approval.resource) != (
                company_id, task_id, operation, resource):
                return ConsumeResult(False, "scope_mismatch")
            if approval.approval_id in self._consumed or approval.nonce in self._consumed:
                return ConsumeResult(False, "replay_detected")
            self._consumed.add(approval.approval_id)
            self._consumed.add(approval.nonce)
            return ConsumeResult(True, "consumed_once")

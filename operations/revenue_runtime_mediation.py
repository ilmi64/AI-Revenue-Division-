"""Role-separated, offline mediation for an Aevora AI synthetic fixture run."""
from dataclasses import asdict, dataclass
import json
import sqlite3

from anchored_delivery_rehearsal import _verify_anchored_fixture
from evidence_verifier import VerificationBlocked
from revenue_agent_queue import QueueItem
from revenue_fixture_dispatch import (
    FixtureTicket, canonical, dispatch_fixture, validate_fixture_scope,
)
from revenue_task_evidence import EvidenceDecision, TaskEvidence, review_evidence
from synthetic_delivery_rehearsal import _sha


_MAX_WORKER_ATTEMPTS = 2
_RETRYABLE = "offline_worker_evidence_unavailable"


@dataclass(frozen=True)
class FixtureDelegation:
    ticket: FixtureTicket
    delegator_role: str = "ar_product_delivery"
    reviewer_role: str = "ar_qa_reviewer"
    supervisor_role: str = "ar_cto"
    runtime: str = "fixed_local_fixture"
    max_worker_attempts: int = _MAX_WORKER_ATTEMPTS


class FixtureMediation:
    """One in-process run. This fixture does not authenticate native adapters."""

    def __init__(self, delegation: FixtureDelegation, task: QueueItem):
        if (
            not isinstance(delegation, FixtureDelegation)
            or delegation != FixtureDelegation(delegation.ticket)
            or type(delegation.max_worker_attempts) is not int
        ):
            raise VerificationBlocked("fixture_delegation_scope_mismatch")
        validate_fixture_scope(delegation.ticket, task)
        self._delegation = delegation
        self._task = task
        self._state = "delegated"
        self._tested_bytes = None
        self._worker_log = None
        self._artifact = None
        self._log = None
        self.events = [{
            "stage": "fixture_delegated",
            "company_id": delegation.ticket.company_id,
            "recipient_scope": delegation.ticket.recipient_scope,
            "task_id": task.task_id,
            "delegator_role": delegation.delegator_role,
            "worker_role": delegation.ticket.role_id,
            "reviewer_role": delegation.reviewer_role,
            "runtime": delegation.runtime,
        }]

    def _expect(self, expected: str) -> None:
        if self._state != expected:
            raise VerificationBlocked("fixture_stage_precondition_failed")

    def run_worker(self) -> tuple[dict, str]:
        self._expect("delegated")
        self._state = "worker_pending"
        ticket = self._delegation.ticket
        for attempt in range(1, self._delegation.max_worker_attempts + 1):
            self.events.append({"stage": "worker_attempt", "attempt": attempt, "role": ticket.role_id})
            try:
                output, log, source_hash = dispatch_fixture(ticket, self._task)
            except VerificationBlocked as exc:
                retry = str(exc) == _RETRYABLE and attempt < self._delegation.max_worker_attempts
                self.events.append({
                    "stage": "worker_attempt_blocked", "attempt": attempt,
                    "reason": str(exc), "retrying_same_scope": retry,
                })
                if retry:
                    continue
                raise
            self._tested_bytes = canonical({"deliverable": output, "synthetic_source_sha256": source_hash})
            self._worker_log = canonical(log)
            self._state = "worker_checked"
            return output, source_hash
        raise VerificationBlocked("fixture_worker_attempts_exhausted")

    def review_artifact(self, artifact: bytes) -> EvidenceDecision:
        self._expect("worker_checked")
        self._state = "review_pending"
        try:
            record = json.loads(artifact)
            if not isinstance(artifact, bytes) or canonical(record) != artifact:
                raise VerificationBlocked("offline_task_artifact_invalid")
            tested_bytes = canonical({
                "deliverable": record["deliverable"],
                "synthetic_source_sha256": record["synthetic_source_sha256"],
            })
            matching_tasks = [
                assignment for assignment in record["assignments"]
                if isinstance(assignment, dict) and assignment.get("task_id") == self._task.task_id
            ]
        except (TypeError, ValueError, KeyError) as exc:
            raise VerificationBlocked("offline_task_artifact_invalid") from exc
        if (
            record.get("classification") != "SYNTHETIC_INTERNAL_ONLY"
            or record.get("reference") != self._task.opportunity_reference
            or tested_bytes != self._tested_bytes
            or len(matching_tasks) != 1
            or any(matching_tasks[0].get(field) != value for field, value in asdict(self._task).items())
            or matching_tasks[0].get("role_id") != self._delegation.ticket.role_id
        ):
            raise VerificationBlocked("offline_task_artifact_scope_mismatch")
        decision = review_evidence(self._task, TaskEvidence(
            task_id=self._task.task_id,
            artifact_sha256=_sha(artifact),
            artifact_bytes=artifact,
            author_role=self._task.role,
            reviewer_role="quality",
            reviewer_attested=True,
        ))
        if not isinstance(decision, EvidenceDecision):
            raise VerificationBlocked("offline_task_evidence_invalid")
        self.events.append({
            "stage": "independent_fixture_qa",
            "role": self._delegation.reviewer_role,
            "task_id": self._task.task_id,
            "status": decision.status,
            "artifact_sha256": _sha(artifact),
        })
        if (
            decision.task_id == self._task.task_id and decision.status == "EVIDENCE_REVIEWED"
            and decision.completion_verified is False and decision.execution_authorized is False
            and decision.external_delivery_authorized is False and decision.spending_authorized is False
        ):
            self._artifact = artifact
            self._log = canonical({
                **json.loads(self._worker_log),
                "task_evidence_review": asdict(decision),
                "fixture_runtime_events": self.events,
            })
            self._state = "review_checked"
        return decision

    @property
    def test_log(self) -> dict:
        self._expect("review_checked")
        return json.loads(self._log)

    def anchor(self, *, anchor_available: bool) -> dict:
        self._expect("review_checked")
        # The anchor is never retried. The verifier may have committed before
        # an error was observed, so the supervisor must review that outcome.
        self._state = "anchor_pending"
        try:
            result = _verify_anchored_fixture(
                "baseline" if anchor_available is True else "missing_anchor",
                self._artifact, self._log, self.events,
                opportunity_id=self._task.opportunity_reference,
                producer_id="fixture-engineering-builder",
            )
        except (OSError, sqlite3.Error) as exc:
            raise VerificationBlocked("offline_anchor_evidence_unavailable") from exc
        if not isinstance(result, dict) or result.get("status") != "verified_for_owner_review":
            raise VerificationBlocked("offline_receipt_invalid")
        if result.get("release_authorized") is not False:
            raise VerificationBlocked("offline_receipt_grants_release")
        self._state = "review_ready"
        return result

    def escalate(self, reason: str) -> dict:
        self._state = "supervisor_hold"
        escalation = {
            "status": "SUPERVISOR_REVIEW_REQUIRED",
            "role": self._delegation.supervisor_role,
            "task_id": self._task.task_id,
            "reason": reason,
            "automatic_resume_authorized": False,
        }
        self.events.append({"stage": "supervisor_escalation", **escalation})
        return escalation

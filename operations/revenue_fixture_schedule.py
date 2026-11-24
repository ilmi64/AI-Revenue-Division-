"""Company-local scheduling for fixed synthetic Aevora commissioning fixtures."""
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sqlite3
from typing import Callable

from evidence_verifier import VerificationBlocked
from revenue_commercial_scope import CommercialReviewScope, validate_review_scope
from revenue_fixture_dispatch import canonical
from revenue_workflow_demo import run_demo
from synthetic_delivery_rehearsal import _sha


_COMPANY = "ai_revenue"
_SUPERVISOR = "ar_cto"
_MAX_WINDOW_SECONDS = 300
_CLAIM_WINDOW_SECONDS = 30


@dataclass(frozen=True)
class ScheduledRequest:
    request_id: str
    scope: CommercialReviewScope
    expires_at: int


@dataclass(frozen=True)
class ScheduleStatus:
    request_id: str
    state: str
    reason: str | None
    result_sha256: str | None
    release_authorized: bool = False
    external_execution_authorized: bool = False


def _valid_id(request_id: str) -> bool:
    return isinstance(request_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", request_id) is not None


def _request_bytes(request: ScheduledRequest) -> bytes:
    if (
        not isinstance(request, ScheduledRequest) or not _valid_id(request.request_id)
        or not isinstance(request.scope, CommercialReviewScope)
        or type(request.expires_at) is not int or not 0 < request.expires_at <= 2**63 - 1
    ):
        raise VerificationBlocked("invalid_fixture_schedule_request")
    validate_review_scope(request.scope, request.scope.service)
    return canonical(asdict(request))


def _decode_request(raw: bytes) -> ScheduledRequest:
    try:
        item = json.loads(raw)
        request = ScheduledRequest(item["request_id"], CommercialReviewScope(**item["scope"]), item["expires_at"])
        if _request_bytes(request) != raw:
            raise VerificationBlocked("invalid_scheduled_payload")
        return request
    except (ValueError, KeyError, TypeError) as exc:
        raise VerificationBlocked("invalid_scheduled_payload") from exc


class FixtureScheduler:
    """Persist one-shot dispatch state. No scheduler daemon, external queue or runtime authority."""

    def __init__(self, *, database: Path, clock: Callable[[], int]):
        self._database = database
        self._clock = clock

    @contextmanager
    def _transaction(self):
        try:
            with closing(sqlite3.connect(
                self._database.resolve().as_uri() + "?mode=rw", uri=True, timeout=1,
            )) as db:
                db.row_factory = sqlite3.Row
                db.execute("PRAGMA synchronous=FULL")
                with db:
                    db.execute("BEGIN IMMEDIATE")
                    rows = db.execute("SELECT company_id, last_seen FROM fixture_scheduler_clock").fetchall()
                    if len(rows) != 1 or rows[0]["company_id"] != _COMPANY:
                        raise VerificationBlocked("fixture_scheduler_company_mismatch")
                    now = self._clock()
                    if type(now) is not int or not rows[0]["last_seen"] <= now <= 2**63 - 1:
                        raise VerificationBlocked("fixture_scheduler_clock_untrusted")
                    db.execute("UPDATE fixture_scheduler_clock SET last_seen=?", (now,))
                    yield db, now
        except (OSError, sqlite3.Error, RuntimeError) as exc:
            raise VerificationBlocked("fixture_scheduler_unavailable") from exc

    @staticmethod
    def _row(db, request_id: str):
        if not _valid_id(request_id):
            raise VerificationBlocked("invalid_fixture_schedule_request")
        row = db.execute("SELECT * FROM scheduled_fixture WHERE request_id=?", (request_id,)).fetchone()
        if row is None:
            raise VerificationBlocked("unknown_fixture_schedule_request")
        return row

    @staticmethod
    def _status(row) -> ScheduleStatus:
        return ScheduleStatus(row["request_id"], row["state"], row["reason"], row["result_sha256"])

    def schedule(self, request: ScheduledRequest) -> ScheduleStatus:
        data = _request_bytes(request)
        with self._transaction() as (db, now):
            row = db.execute(
                "SELECT * FROM scheduled_fixture WHERE request_id=?", (request.request_id,),
            ).fetchone()
            if row is not None:
                if row["request_bytes"] != data:
                    raise VerificationBlocked("fixture_schedule_idempotency_conflict")
                return self._status(row)
            if not 0 < request.expires_at - now <= _MAX_WINDOW_SECONDS:
                raise VerificationBlocked("fixture_schedule_expiry_not_allowed")
            db.execute(
                "INSERT INTO scheduled_fixture (request_id, request_bytes, expires_at, state) VALUES (?, ?, ?, 'QUEUED')",
                (request.request_id, data, request.expires_at),
            )
            return self._status(self._row(db, request.request_id))

    def status(self, request_id: str) -> ScheduleStatus:
        with self._transaction() as (db, _):
            return self._status(self._row(db, request_id))

    def _claim(self, request_id: str) -> tuple[ScheduledRequest | None, ScheduleStatus]:
        with self._transaction() as (db, now):
            row = self._row(db, request_id)
            if row["state"] != "QUEUED":
                return None, self._status(row)
            request = _decode_request(row["request_bytes"])
            if request.request_id != row["request_id"] or request.expires_at != row["expires_at"]:
                raise VerificationBlocked("invalid_scheduled_payload")
            if now >= request.expires_at:
                db.execute(
                    "UPDATE scheduled_fixture SET state='SUPERVISOR_HOLD', reason='expired_before_claim' WHERE request_id=?",
                    (request_id,),
                )
                return None, self._status(self._row(db, request_id))
            claim_until = min(request.expires_at, now + _CLAIM_WINDOW_SECONDS)
            changed = db.execute(
                "UPDATE scheduled_fixture SET state='RUNNING', claim_until=? WHERE request_id=? AND state='QUEUED'",
                (claim_until, request_id),
            )
            claimed = self._row(db, request_id)
            if (
                changed.rowcount != 1 or claimed["state"] != "RUNNING" or claimed["claim_until"] != claim_until
                or claimed["request_bytes"] != row["request_bytes"]
            ):
                raise VerificationBlocked("fixture_claim_not_persisted")
            return request, self._status(claimed)

    @staticmethod
    def _review_bytes(request: ScheduledRequest, result: dict) -> bytes:
        if (
            not isinstance(result, dict)
            or any(result.get(flag) is not False for flag in (
                "release_authorized", "external_actions_performed", "agent_execution_authorized",
                "customer_contact_authorized", "spending_authorized",
            ))
        ):
            raise VerificationBlocked("scheduled_fixture_outcome_not_review_only")
        receipt = result.get("receipt")
        if not isinstance(receipt, dict) or receipt.get("status") != "verified_for_owner_review":
            raise VerificationBlocked("scheduled_fixture_review_blocked")
        record = result.get("private_artifact")
        runtime = result.get("private_runtime")
        commercial = result.get("private_commercial_review")
        if (
            not isinstance(runtime, dict) or runtime.get("state") != "REVIEW_READY"
            or not isinstance(runtime.get("commissioning"), dict)
            or runtime["commissioning"].get("status") != "HOLD"
            or not isinstance(commercial, dict) or commercial.get("external_approval") != "NOT_GRANTED"
        ):
            raise VerificationBlocked("scheduled_fixture_outcome_not_review_only")
        if (
            not isinstance(record, dict) or not isinstance(record.get("contents"), dict)
            or receipt.get("release_authorized") is not False
            or not isinstance(receipt.get("manifest_sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", receipt["manifest_sha256"]) is None
            or record.get("sha256") != _sha(canonical(record["contents"]))
            or canonical(record["contents"].get("commercial_review_scope")) != canonical(asdict(request.scope))
        ):
            raise VerificationBlocked("scheduled_fixture_result_scope_mismatch")
        return canonical(result)

    def _finish(self, request_id: str, result: bytes | None, reason: str | None) -> ScheduleStatus:
        with self._transaction() as (db, now):
            row = self._row(db, request_id)
            if row["state"] != "RUNNING":
                return self._status(row)
            if now >= row["claim_until"]:
                result, reason = None, "expired_or_late_worker_result"
            state = "REVIEW_READY" if result is not None else "SUPERVISOR_HOLD"
            digest = _sha(result) if result is not None else None
            changed = db.execute(
                "UPDATE scheduled_fixture SET state=?, reason=?, result=?, result_sha256=? WHERE request_id=? AND state='RUNNING'",
                (state, reason, result, digest, request_id),
            )
            updated = self._row(db, request_id)
            if (
                changed.rowcount != 1 or updated["state"] != state or updated["reason"] != reason
                or updated["result"] != result or updated["result_sha256"] != digest
            ):
                raise VerificationBlocked("fixture_result_not_persisted")
            return self._status(updated)

    def run_one(self, request_id: str) -> ScheduleStatus:
        """Claim before executing the fixed demo. Repeated calls never reexecute a claim."""
        request, status = self._claim(request_id)
        if request is None:
            return status
        try:
            report = run_demo(mode="anchored", service=request.scope.service, commercial_scope=request.scope)
            reviewed = self._review_bytes(request, report)
        except VerificationBlocked as exc:
            return self._finish(request_id, None, str(exc))
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            return self._finish(request_id, None, "scheduled_fixture_execution_failed")
        return self._finish(request_id, reviewed, None)

    def recover_interrupted(self, request_id: str, *, supervisor_role: str) -> ScheduleStatus:
        """Record a terminal supervisor hold for an expired claim. No retry or release."""
        if supervisor_role != _SUPERVISOR:
            raise VerificationBlocked("fixture_recovery_role_mismatch")
        with self._transaction() as (db, now):
            row = self._row(db, request_id)
            if row["state"] == "RUNNING" and now >= row["claim_until"]:
                db.execute(
                    "UPDATE scheduled_fixture SET state='SUPERVISOR_HOLD', reason='interrupted_claim' WHERE request_id=?",
                    (request_id,),
                )
            return self._status(self._row(db, request_id))

    def private_result(self, request_id: str) -> bytes:
        """Read the exact private result bytes. These are never OCC input."""
        with self._transaction() as (db, _):
            row = self._row(db, request_id)
            data = row["result"]
            if row["state"] != "REVIEW_READY" or not isinstance(data, bytes) or _sha(data) != row["result_sha256"]:
                raise VerificationBlocked("scheduled_fixture_private_result_unavailable")
            request = _decode_request(row["request_bytes"])
            try:
                if self._review_bytes(request, json.loads(data)) != data:
                    raise VerificationBlocked("scheduled_fixture_private_result_invalid")
            except (ValueError, TypeError, KeyError) as exc:
                raise VerificationBlocked("scheduled_fixture_private_result_invalid") from exc
            return data

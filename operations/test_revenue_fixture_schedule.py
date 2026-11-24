"""Offline, SQLite-backed scheduling and supervisor recovery acceptance tests."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

from evidence_verifier import VerificationBlocked
from revenue_commercial_scope import fixed_review_scope
from revenue_fixture_schedule import FixtureScheduler, ScheduledRequest
from revenue_workflow_demo import run_demo


class RevenueFixtureScheduleTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / "aevora-fixture-schedule.sqlite"
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.executescript(Path(__file__).with_name("revenue_fixture_schedule.sql").read_text())
        self.now = 100
        self.request = ScheduledRequest("fixture-run-1", fixed_review_scope("coding"), 160)

    def scheduler(self):
        return FixtureScheduler(database=self.database, clock=lambda: self.now)

    def test_review_result_persists_exactly_and_replayed_request_does_not_run(self):
        schedule = self.scheduler()
        self.assertEqual(schedule.schedule(self.request).state, "QUEUED")
        self.assertEqual(schedule.schedule(self.request).state, "QUEUED")
        self.assertEqual(schedule.run_one(self.request.request_id).state, "REVIEW_READY")
        with patch("revenue_fixture_schedule.run_demo") as worker:
            restarted = self.scheduler()
            status = restarted.run_one(self.request.request_id)
            self.assertEqual(restarted.schedule(self.request), status)
            worker.assert_not_called()
        private = restarted.private_result(self.request.request_id)
        self.assertEqual(status.result_sha256, hashlib.sha256(private).hexdigest())
        self.assertEqual(json.loads(private)["private_runtime"]["commissioning"]["status"], "HOLD")
        self.assertIs(json.loads(private)["receipt"]["release_authorized"], False)
        self.assertIs(status.release_authorized, False)
        self.assertIs(status.external_execution_authorized, False)

    def test_request_id_cannot_change_scope_and_unapproved_scopes_never_queue(self):
        schedule = self.scheduler()
        schedule.schedule(self.request)
        with self.assertRaisesRegex(VerificationBlocked, "idempotency_conflict"):
            schedule.schedule(replace(self.request, scope=fixed_review_scope("ai_setup")))
        for field, value in (
            ("company_id", "trading_technology"), ("recipient_scope", "other"),
            ("work_scope", "arbitrary_command"), ("external_approval_granted", True),
            ("upfront_cost_cap_cad", 1), ("data_classification", "PRIVATE"),
        ):
            with self.subTest(field=field), self.assertRaisesRegex(VerificationBlocked, "scope_mismatch"):
                scope = replace(self.request.scope, **{field: value})
                schedule.schedule(replace(self.request, request_id="blocked", scope=scope))
        with self.assertRaisesRegex(VerificationBlocked, "unknown_fixture"):
            schedule.status("blocked")

    def test_concurrent_scheduler_instances_claim_once(self):
        self.scheduler().schedule(self.request)
        entered, continue_worker = Event(), Event()

        def run(*args, **kwargs):
            entered.set()
            if not continue_worker.wait(5):
                raise RuntimeError("test fixture worker timeout")
            return run_demo(*args, **kwargs)

        with patch("revenue_fixture_schedule.run_demo", side_effect=run) as worker:
            with ThreadPoolExecutor(max_workers=2) as threads:
                original = threads.submit(self.scheduler().run_one, self.request.request_id)
                try:
                    self.assertTrue(entered.wait(5))
                    competing = threads.submit(self.scheduler().run_one, self.request.request_id)
                    self.assertEqual(competing.result(timeout=5).state, "RUNNING")
                finally:
                    continue_worker.set()
                self.assertEqual(original.result(timeout=5).state, "REVIEW_READY")
            worker.assert_called_once()

    def test_expired_requests_and_clock_rollback_stop_before_worker(self):
        scheduler = self.scheduler()
        with self.assertRaisesRegex(VerificationBlocked, "expiry_not_allowed"):
            scheduler.schedule(replace(self.request, expires_at=401))
        scheduler.schedule(self.request)
        self.now = 90
        with patch("revenue_fixture_schedule.run_demo") as worker:
            with self.assertRaisesRegex(VerificationBlocked, "clock_untrusted"):
                scheduler.run_one(self.request.request_id)
            self.now = self.request.expires_at
            status = scheduler.run_one(self.request.request_id)
            self.assertEqual((status.state, status.reason), ("SUPERVISOR_HOLD", "expired_before_claim"))
            worker.assert_not_called()

    def test_process_exit_after_claim_remains_held_after_supervised_recovery(self):
        self.scheduler().schedule(self.request)
        script = """
import os
from pathlib import Path
import sys
from unittest.mock import patch
from revenue_fixture_schedule import FixtureScheduler
schedule = FixtureScheduler(database=Path(sys.argv[1]), clock=lambda: 100)
with patch('revenue_fixture_schedule.run_demo', side_effect=lambda **kwargs: os._exit(71)):
    schedule.run_one(sys.argv[2])
"""
        crashed = subprocess.run(
            [sys.executable, "-c", script, str(self.database), self.request.request_id],
            check=False, capture_output=True, timeout=10,
        )
        self.assertEqual(crashed.returncode, 71, crashed.stderr.decode())
        reopened = self.scheduler()
        self.assertEqual(reopened.status(self.request.request_id).state, "RUNNING")
        self.assertEqual(reopened.recover_interrupted(
            self.request.request_id, supervisor_role="ar_cto",
        ).state, "RUNNING")
        self.now = 130
        with self.assertRaisesRegex(VerificationBlocked, "recovery_role_mismatch"):
            reopened.recover_interrupted(self.request.request_id, supervisor_role="tt_cto")
        status = reopened.recover_interrupted(self.request.request_id, supervisor_role="ar_cto")
        self.assertEqual((status.state, status.reason), ("SUPERVISOR_HOLD", "interrupted_claim"))
        with patch("revenue_fixture_schedule.run_demo") as worker:
            self.assertEqual(reopened.run_one(self.request.request_id), status)
            worker.assert_not_called()

    def test_late_and_invalid_results_hold_and_do_not_persist_artifacts(self):
        scheduler = self.scheduler()
        scheduler.schedule(self.request)

        def late(**kwargs):
            self.now = 131
            return run_demo(**kwargs)

        with patch("revenue_fixture_schedule.run_demo", side_effect=late):
            status = scheduler.run_one(self.request.request_id)
        self.assertEqual((status.state, status.reason), ("SUPERVISOR_HOLD", "expired_or_late_worker_result"))
        with self.assertRaisesRegex(VerificationBlocked, "private_result_unavailable"):
            scheduler.private_result(self.request.request_id)
        next_request = replace(self.request, request_id="fixture-run-2")
        scheduler.schedule(next_request)
        attempted = run_demo(mode="anchored", service="coding")
        attempted["release_authorized"] = True
        with patch("revenue_fixture_schedule.run_demo", return_value=attempted):
            status = scheduler.run_one(next_request.request_id)
        self.assertEqual(status.reason, "scheduled_fixture_outcome_not_review_only")

    def test_supervisor_hold_cannot_be_resurrected_by_late_success(self):
        schedule = self.scheduler()
        schedule.schedule(self.request)

        def after_supervisor(**kwargs):
            self.now = 130
            status = self.scheduler().recover_interrupted(self.request.request_id, supervisor_role="ar_cto")
            self.assertEqual(status.state, "SUPERVISOR_HOLD")
            return run_demo(**kwargs)

        with patch("revenue_fixture_schedule.run_demo", side_effect=after_supervisor):
            status = schedule.run_one(self.request.request_id)
        self.assertEqual((status.state, status.reason), ("SUPERVISOR_HOLD", "interrupted_claim"))
        with self.assertRaisesRegex(VerificationBlocked, "private_result_unavailable"):
            schedule.private_result(self.request.request_id)

    def test_missing_database_and_corrupt_result_fail_closed(self):
        missing = self.database.with_name("missing-schedule.sqlite")
        with self.assertRaisesRegex(VerificationBlocked, "scheduler_unavailable"):
            FixtureScheduler(database=missing, clock=lambda: self.now).schedule(self.request)
        self.assertFalse(missing.exists())
        schedule = self.scheduler()
        schedule.schedule(self.request)
        schedule.run_one(self.request.request_id)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("UPDATE scheduled_fixture SET result=?", (b"{}",))
        with self.assertRaisesRegex(VerificationBlocked, "private_result_unavailable"):
            schedule.private_result(self.request.request_id)

    def test_wrong_company_or_uncommitted_claim_denies_dispatch(self):
        schedule = self.scheduler()
        schedule.schedule(self.request)
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER deny_claim BEFORE UPDATE ON scheduled_fixture "
                "WHEN new.state='RUNNING' BEGIN SELECT RAISE(IGNORE); END"
            )
        with patch("revenue_fixture_schedule.run_demo") as worker:
            with self.assertRaisesRegex(VerificationBlocked, "claim_not_persisted"):
                schedule.run_one(self.request.request_id)
            worker.assert_not_called()
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute("DELETE FROM fixture_scheduler_clock")
        with self.assertRaisesRegex(VerificationBlocked, "company_mismatch"):
            schedule.status(self.request.request_id)

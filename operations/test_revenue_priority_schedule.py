"""Deterministic ordering, v1 migration and worker-reservation tests."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict, replace
from pathlib import Path
import sqlite3
from threading import Event
import unittest
from unittest.mock import patch

from revenue_commercial_scope import fixed_review_scope
from revenue_fixture_dispatch import canonical
from revenue_fixture_schedule import FixtureScheduler, ScheduledRequest
from revenue_workflow_demo import run_demo
import test_revenue_fixture_schedule as base_schedule


class RevenuePriorityScheduleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = base_schedule.RevenueFixtureScheduleTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.database = self.fixture.database
        self.now = 100

    def scheduler(self):
        return FixtureScheduler(database=self.database, clock=lambda: self.now)

    @staticmethod
    def request(name, priority=5, expires_at=180):
        return ScheduledRequest(name, fixed_review_scope("coding"), expires_at, priority)

    def test_queue_order_uses_priority_expiry_and_request_identity(self):
        scheduler = self.scheduler()
        for request in (
            self.request("later-priority", 7, 120),
            self.request("same-deadline-z", 1, 160),
            self.request("later-deadline", 1, 170),
            self.request("same-deadline-a", 1, 160),
        ):
            scheduler.schedule(request)
        with patch("revenue_fixture_schedule.run_demo", wraps=run_demo) as worker:
            self.assertEqual(scheduler.run_one("later-priority").state, "QUEUED")
            worker.assert_not_called()
            self.assertEqual([scheduler.run_next().request_id for _ in range(4)], [
                "same-deadline-a", "same-deadline-z", "later-deadline", "later-priority",
            ])
            self.assertEqual(worker.call_count, 4)
        self.assertIsNone(scheduler.run_next())

    def test_priority_validation_idempotency_and_expired_high_priority_do_not_dispatch(self):
        scheduler = self.scheduler()
        for priority in (True, -1, 10, "urgent"):
            with self.subTest(priority=priority), self.assertRaisesRegex(ValueError, "invalid_fixture_schedule_request"):
                scheduler.schedule(self.request("denied", priority))
        request = self.request("same-request", 0, 110)
        scheduler.schedule(request)
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            scheduler.schedule(replace(request, priority=1))
        scheduler.schedule(self.request("eligible-later", 8))
        self.now = 110
        with patch("revenue_fixture_schedule.run_demo", wraps=run_demo) as worker:
            self.assertEqual(scheduler.run_next().request_id, "eligible-later")
            worker.assert_called_once()
        self.assertEqual(scheduler.status("same-request").reason, "expired_before_claim")

    def test_concurrent_distinct_requests_never_exceed_one_worker_reservation(self):
        self.scheduler().schedule(self.request("first", 0))
        self.scheduler().schedule(self.request("second", 1))
        entered, permission = Event(), Event()

        def report(**kwargs):
            entered.set()
            if not permission.wait(5):
                raise RuntimeError("fixture test timed out")
            return run_demo(**kwargs)

        with patch("revenue_fixture_schedule.run_demo", side_effect=report) as worker:
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(self.scheduler().run_next)
                try:
                    self.assertTrue(entered.wait(5))
                    self.assertTrue(self.scheduler().status("first").worker_reserved)
                    blocked = pool.submit(self.scheduler().run_next)
                    self.assertIsNone(blocked.result(timeout=5))
                    self.assertEqual(self.scheduler().run_one("second").state, "QUEUED")
                    worker.assert_called_once()
                finally:
                    permission.set()
                self.assertFalse(first.result(timeout=5).worker_reserved)
        self.assertEqual(self.scheduler().run_next().request_id, "second")

    def test_supervisor_hold_reserves_slot_until_actual_worker_returns(self):
        scheduler = self.scheduler()
        scheduler.schedule(self.request("first", 0))
        scheduler.schedule(self.request("second", 1))

        def resolve_after_hold(**kwargs):
            self.now = 130
            held = self.scheduler().recover_interrupted("first", supervisor_role="ar_cto")
            self.assertEqual(held.state, "SUPERVISOR_HOLD")
            self.assertTrue(held.worker_reserved)
            self.assertIsNone(self.scheduler().run_next())
            self.assertFalse(self.scheduler().status("second").worker_reserved)
            return run_demo(**kwargs)

        with patch("revenue_fixture_schedule.run_demo", side_effect=resolve_after_hold):
            held = scheduler.run_next()
        self.assertEqual(held.reason, "interrupted_claim")
        self.assertFalse(held.worker_reserved)
        self.assertIsNone(held.result_sha256)
        self.assertEqual(scheduler.run_next().state, "REVIEW_READY")

    @staticmethod
    def create_legacy(path, entries):
        with closing(sqlite3.connect(path)) as db, db:
            db.executescript("""
                CREATE TABLE fixture_scheduler_clock (company_id TEXT PRIMARY KEY, last_seen INTEGER NOT NULL);
                INSERT INTO fixture_scheduler_clock VALUES ('ai_revenue', 100);
                CREATE TABLE scheduled_fixture (
                    request_id TEXT PRIMARY KEY, request_bytes BLOB NOT NULL, expires_at INTEGER NOT NULL,
                    state TEXT NOT NULL, claim_until INTEGER, reason TEXT, result BLOB, result_sha256 TEXT
                );
            """)
            for request, state, deadline, reason in entries:
                body = asdict(request)
                del body["priority"]
                db.execute("INSERT INTO scheduled_fixture VALUES (?, ?, ?, ?, ?, ?, NULL, NULL)",
                           (request.request_id, canonical(body), request.expires_at, state, deadline, reason))
            db.executescript(Path(__file__).with_name("revenue_fixture_schedule_v2.sql").read_text())

    def test_v1_preserves_queued_scope_and_ambiguous_reservation(self):
        legacy_path = self.database.with_name("legacy.sqlite")
        legacy = self.request("legacy-queued")
        self.create_legacy(legacy_path, (
            (legacy, "QUEUED", None, None),
            (self.request("ambiguous-held", expires_at=140), "SUPERVISOR_HOLD", 130, "interrupted_claim"),
        ))
        scheduler = FixtureScheduler(database=legacy_path, clock=lambda: self.now)
        self.assertEqual(scheduler.schedule(legacy).state, "QUEUED")
        self.assertTrue(scheduler.status("ambiguous-held").worker_reserved)
        self.assertIsNone(scheduler.run_next())
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            scheduler.schedule(replace(legacy, priority=1))

    def test_unambiguous_v1_queued_request_runs_with_default_priority(self):
        path = self.database.with_name("legacy-clear.sqlite")
        request = self.request("legacy-default")
        self.create_legacy(path, ((request, "QUEUED", None, None),))
        scheduler = FixtureScheduler(database=path, clock=lambda: self.now)
        self.assertEqual(scheduler.run_next().state, "REVIEW_READY")
        self.assertIn(b'"release_authorized":false', scheduler.private_result(request.request_id))

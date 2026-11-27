"""Offline recovery trials with a real child claimant and synthetic Ed25519 signers."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest

from evidence_verifier import VerificationBlocked
from revenue_commercial_scope import fixed_review_scope
from revenue_fixture_reservation_recovery import (
    CurrentRecoveryTrust, RecoveryAuthorization, RecoverySignature, recovery_payload,
)
from revenue_fixture_schedule import FixtureScheduler, ScheduledRequest
from signed_audit_continuity import ContinuityKey
import test_revenue_fixture_schedule as scheduler_tests

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    Ed25519PrivateKey = None


class SyntheticRecoveryAuthority:
    """Fixture-only trust source, independent of the scheduler database."""

    def __init__(self, trust):
        self.trust = trust

    def current(self, company_id):
        if company_id != "ai_revenue":
            raise OSError("wrong synthetic trust partition")
        return self.trust


@unittest.skipUnless(sys.platform.startswith("linux") and Ed25519PrivateKey is not None, "Linux/Ed25519 fixture unavailable")
class RevenueReservationRecoveryTests(unittest.TestCase):
    def setUp(self):
        fixture = scheduler_tests.RevenueFixtureScheduleTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.database = fixture.database
        self.now = 100
        self.signers = {
            "supervisor": ("ar_cto", Ed25519PrivateKey.from_private_bytes(b"s" * 32)),
            "witness": ("sr_backup_recovery", Ed25519PrivateKey.from_private_bytes(b"w" * 32)),
        }
        keys = {
            key_id: ContinuityKey("ai_revenue", "fixture-" + key_id, role,
                                  secret.public_key().public_bytes_raw(), 220)
            for key_id, (role, secret) in self.signers.items()
        }
        self.authority = SyntheticRecoveryAuthority(CurrentRecoveryTrust("ai_revenue", 3, 129, 210, keys))

    def scheduler(self, authority=...):
        return FixtureScheduler(
            database=self.database, clock=lambda: self.now,
            recovery_authority=self.authority if authority is ... else authority,
        )

    def authorization(self, claim, **changes):
        unsigned = RecoveryAuthorization(
            claim, 3, self.now, 200, RecoverySignature("supervisor", b""), RecoverySignature("witness", b""),
        )
        unsigned = replace(unsigned, **changes)
        signed = {}
        for key_id, (role, secret) in self.signers.items():
            signed[key_id] = RecoverySignature(key_id, secret.sign(recovery_payload(unsigned, role, key_id)))
        return replace(unsigned, **signed)

    def claim_worker(self, *, service="coding", wait=False):
        request = ScheduledRequest("interrupted", fixed_review_scope(service), 180, priority=0)
        self.scheduler().schedule(request)
        script = """
import os
from pathlib import Path
import sys
from unittest.mock import patch
from revenue_fixture_schedule import FixtureScheduler

def abandon(**kwargs):
    if sys.argv[2] == "wait":
        print("claimed", flush=True)
        sys.stdin.buffer.read(1)
    os._exit(71)

with patch("revenue_fixture_schedule.run_demo", side_effect=abandon):
    FixtureScheduler(database=Path(sys.argv[1]), clock=lambda: 100).run_one("interrupted")
"""
        args = [sys.executable, "-c", script, str(self.database), "wait" if wait else "exit"]
        if wait:
            child = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.addCleanup(lambda: child.communicate(b" ", timeout=5) if child.poll() is None else None)
            self.assertEqual(child.stdout.readline(), b"claimed\n")
        else:
            child = subprocess.run(args, capture_output=True, timeout=10)
            self.assertEqual(child.returncode, 71, child.stderr.decode())
        self.now = 130
        held = self.scheduler().recover_interrupted(request.request_id, supervisor_role="ar_cto")
        self.assertEqual(held.state, "SUPERVISOR_HOLD")
        self.assertTrue(held.worker_reserved)
        return child

    def test_live_claimant_denied_and_only_reaped_worker_releases_slot(self):
        child = self.claim_worker(wait=True)
        scheduler = self.scheduler()
        claim = scheduler.reservation_claim("interrupted")
        self.assertEqual(claim.owner.pid, child.pid)
        with self.assertRaisesRegex(VerificationBlocked, "claimant_still_present"):
            scheduler.release_interrupted_reservation(self.authorization(claim))
        self.assertTrue(scheduler.status("interrupted").worker_reserved)
        child.communicate(b" ", timeout=5)
        self.assertEqual(child.returncode, 71)
        self.now = 131
        status = scheduler.release_interrupted_reservation(self.authorization(claim))
        self.assertEqual(status.state, "SUPERVISOR_HOLD")
        self.assertFalse(status.worker_reserved)
        self.assertIs(status.release_authorized, False)
        self.assertIs(status.external_execution_authorized, False)
        self.assertEqual(scheduler.run_one("interrupted"), status)
        scheduler.schedule(ScheduledRequest("next", fixed_review_scope("coding"), 180))
        self.assertEqual(scheduler.run_next().state, "REVIEW_READY")
        with closing(sqlite3.connect(self.database)) as db:
            raw = db.execute("SELECT recovery_custody FROM fixture_claim_owner WHERE request_id='interrupted'").fetchone()[0]
        self.assertIs(json.loads(raw)["release_authorized"], False)

    def test_missing_stale_revoked_or_compromised_authority_blocks(self):
        self.claim_worker()
        claim = self.scheduler().reservation_claim("interrupted")
        authorization = self.authorization(claim)
        original = self.authority.trust
        with self.assertRaisesRegex(VerificationBlocked, "authority_unavailable"):
            self.scheduler(None).release_interrupted_reservation(authorization)
        for trust, reason in (
            (replace(original, trust_epoch=4), "trust_stale"),
            (replace(original, observed_at=1, expires_at=122), "trust_stale"),
            (replace(original, company_id="trading_technology"), "trust_stale"),
            (replace(original, keys={**original.keys, "witness": replace(original.keys["witness"], revoked=True)}),
             "untrusted_fixture_recovery_signer"),
            (replace(original, keys={
                **original.keys, "witness": replace(original.keys["witness"], principal_id="fixture-supervisor"),
            }), "roles_not_independent"),
        ):
            with self.subTest(reason=reason), self.assertRaisesRegex(VerificationBlocked, reason):
                self.authority.trust = trust
                self.scheduler().release_interrupted_reservation(authorization)
        self.assertTrue(self.scheduler().status("interrupted").worker_reserved)

    def test_signatures_scope_and_expiry_are_exact(self):
        self.claim_worker()
        scheduler = self.scheduler()
        claim = scheduler.reservation_claim("interrupted")
        valid = self.authorization(claim)
        for invalid, reason in (
            (replace(valid, witness=replace(valid.witness, signature=b"x" * 64)), "invalid_continuity_signature"),
            (self.authorization(replace(claim, request_sha256="0" * 64)), "claim_mismatch"),
            (self.authorization(replace(claim, company_id="trading_technology")), "claim_mismatch"),
            (self.authorization(claim, expires_at=130), "trust_stale"),
            (self.authorization(claim, observed_at=129), "trust_stale"),
        ):
            with self.subTest(reason=reason), self.assertRaisesRegex(VerificationBlocked, reason):
                scheduler.release_interrupted_reservation(invalid)
        self.assertTrue(scheduler.status("interrupted").worker_reserved)

    def test_two_distinct_valid_signed_records_consume_reservation_once(self):
        self.claim_worker()
        claim = self.scheduler().reservation_claim("interrupted")
        attempts = (self.authorization(claim, expires_at=195), self.authorization(claim, expires_at=196))

        def resume(authorization):
            try:
                return self.scheduler().release_interrupted_reservation(authorization).worker_reserved
            except VerificationBlocked as exc:
                return str(exc)

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(pool.map(resume, attempts), (False, "fixture_held_reservation_not_recoverable"))
        with self.assertRaisesRegex(VerificationBlocked, "not_recoverable"):
            self.scheduler().release_interrupted_reservation(attempts[0])

    def test_failed_compare_and_set_rolls_back_custody_and_leaves_hold(self):
        self.claim_worker()
        scheduler = self.scheduler()
        authorization = self.authorization(scheduler.reservation_claim("interrupted"))
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute(
                "CREATE TRIGGER deny_release BEFORE UPDATE ON scheduled_fixture "
                "WHEN old.worker_reserved=1 AND new.worker_reserved=0 BEGIN SELECT RAISE(IGNORE); END"
            )
        with self.assertRaisesRegex(VerificationBlocked, "claim_changed"):
            scheduler.release_interrupted_reservation(authorization)
        self.assertTrue(scheduler.status("interrupted").worker_reserved)
        with closing(sqlite3.connect(self.database)) as db, db:
            self.assertIsNone(db.execute("SELECT recovery_custody FROM fixture_claim_owner").fetchone()[0])
            db.execute("DROP TRIGGER deny_release")
        self.assertFalse(scheduler.release_interrupted_reservation(authorization).worker_reserved)

    def test_changed_authority_or_expired_proof_at_record_leaves_reservation(self):
        self.claim_worker()
        scheduler = self.scheduler()
        claim = scheduler.reservation_claim("interrupted")
        original = self.authority.trust
        old_current = self.authority.current
        observations = iter((original, replace(original, trust_epoch=4)))
        self.authority.current = lambda company_id: next(observations)
        try:
            with self.assertRaisesRegex(VerificationBlocked, "authority_changed"):
                scheduler.release_interrupted_reservation(self.authorization(claim))
        finally:
            self.authority.current = old_current
        times = iter((130, 131))
        scoped = FixtureScheduler(
            database=self.database, clock=lambda: next(times), recovery_authority=self.authority,
        )
        with self.assertRaisesRegex(VerificationBlocked, "expired_before_record"):
            scoped.release_interrupted_reservation(self.authorization(claim, expires_at=131))
        self.assertTrue(scheduler.status("interrupted").worker_reserved)

    def test_app_parent_exit_does_not_establish_descendant_custody(self):
        self.claim_worker(service="app_build")
        with self.assertRaisesRegex(VerificationBlocked, "descendant_custody_required"):
            self.scheduler().reservation_claim("interrupted")
        self.assertTrue(self.scheduler().status("interrupted").worker_reserved)
        self.assertIsNone(self.scheduler().run_next())

    def test_untracked_historical_hold_cannot_release_reservation(self):
        self.claim_worker()
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("DROP TABLE fixture_claim_owner")
            db.executescript(Path(__file__).with_name("revenue_fixture_schedule_v3.sql").read_text())
        with self.assertRaisesRegex(VerificationBlocked, "claim_owner_untracked"):
            self.scheduler().reservation_claim("interrupted")
        self.assertTrue(self.scheduler().status("interrupted").worker_reserved)

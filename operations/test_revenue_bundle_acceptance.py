"""Exact scheduled package acceptance using independent synthetic Ed25519 review."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict, replace
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from evidence_verifier import VerificationBlocked
from revenue_bundle_acceptance import (
    BundleAcceptanceAuthorization, InternalBundleAcceptor, acceptance_payload,
)
from revenue_commercial_scope import fixed_review_scope
from revenue_fixture_reservation_recovery import CurrentRecoveryTrust
from revenue_fixture_schedule import FixtureScheduler, ScheduledRequest
from revenue_internal_review_bundle import build_internal_review_bundle
from signed_audit_continuity import ContinuityKey

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    Ed25519PrivateKey = None


class SyntheticAcceptanceAuthority:
    def __init__(self, trust):
        self.trust = trust

    def current(self, company_id):
        if company_id != "ai_revenue":
            raise OSError("fixture company authority unavailable")
        return self.trust


@unittest.skipIf(Ed25519PrivateKey is None, "Ed25519 fixture unavailable")
class RevenueBundleAcceptanceTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / "private-schedule.sqlite"
        with closing(sqlite3.connect(self.database)) as db, db:
            db.executescript(Path(__file__).with_name("revenue_fixture_schedule.sql").read_text())
        self.now = 100
        self.private_key = Ed25519PrivateKey.from_private_bytes(b"k" * 32)
        key = ContinuityKey(
            "ai_revenue", "fixture-independent-package-reviewer", "ar_engineering_reviewer",
            self.private_key.public_key().public_bytes_raw(), 150,
        )
        self.authority = SyntheticAcceptanceAuthority(CurrentRecoveryTrust("ai_revenue", 4, 95, 150, {"reviewer": key}))

    def scheduler(self, *, clock=None):
        return FixtureScheduler(database=self.database, clock=clock if clock is not None else lambda: self.now)

    def prepare(self, service="coding", request_id="review-package"):
        scheduler = self.scheduler()
        scheduler.schedule(ScheduledRequest(request_id, fixed_review_scope(service), 125))
        self.assertEqual(scheduler.run_one(request_id).state, "REVIEW_READY")
        acceptor = InternalBundleAcceptor(scheduler, authority=self.authority)
        claim = acceptor.claim(request_id)
        return acceptor, claim, build_internal_review_bundle(scheduler, request_id)

    def sign(self, claim, **changes):
        unsigned = BundleAcceptanceAuthorization(claim, 4, 100, 120, "reviewer", b"")
        unsigned = replace(unsigned, **changes)
        return replace(unsigned, signature=self.private_key.sign(acceptance_payload(unsigned)))

    def test_all_four_exact_packages_are_privately_accepted_without_release(self):
        for service in ("app_build", "coding", "ai_setup", "authorized_bug_bounty"):
            with self.subTest(service=service):
                acceptor, claim, bundle = self.prepare(service, service)
                authorization = self.sign(claim)
                receipt = acceptor.accept(service, bundle, authorization)
                self.assertEqual(receipt.status, "INTERNAL_EVIDENCE_ACCEPTED")
                self.assertEqual(receipt.commissioning_status, "HOLD")
                self.assertIs(receipt.release_authorized, False)
                with ZipFile(BytesIO(bundle)) as archive:
                    self.assertEqual(hashlib.sha256(archive.read("manifest.json")).hexdigest(), claim.manifest_sha256)
                reopened = InternalBundleAcceptor(self.scheduler(), authority=None)
                stored = json.loads(reopened.private_record(service))
                self.assertEqual(stored["receipt"], asdict(receipt))
                self.assertEqual(stored["acceptance_payload"], json.loads(acceptance_payload(authorization)))
                self.assertEqual(stored["signature"], authorization.signature.hex())
                with self.assertRaisesRegex(VerificationBlocked, "already_recorded"):
                    acceptor.accept(service, bundle, authorization)

    def test_altered_archive_signatures_scope_and_held_result_denied(self):
        acceptor, claim, bundle = self.prepare()
        valid = self.sign(claim)
        with self.assertRaisesRegex(VerificationBlocked, "exact_bytes_mismatch"):
            acceptor.accept(claim.request_id, bundle + b"appended", valid)
        for change in (
            {"manifest_sha256": "0" * 64}, {"result_sha256": "0" * 64}, {"request_sha256": "0" * 64},
            {"company_id": "trading_technology"}, {"recipient_scope": "shared_research"},
            {"request_id": "other-request"},
        ):
            with self.subTest(change=change), self.assertRaisesRegex(VerificationBlocked, "claim_mismatch"):
                acceptor.accept(claim.request_id, bundle, self.sign(replace(claim, **change)))
        with self.assertRaisesRegex(VerificationBlocked, "invalid_continuity_signature"):
            acceptor.accept(claim.request_id, bundle, replace(valid, signature=b"m" * 64))
        self.scheduler().schedule(ScheduledRequest("queued", fixed_review_scope("coding"), 125))
        with self.assertRaisesRegex(VerificationBlocked, "private_result_unavailable"):
            acceptor.claim("queued")

    def test_unauthorized_revoked_stale_or_conflicted_reviewer_cannot_accept(self):
        acceptor, claim, bundle = self.prepare()
        auth = self.sign(claim)
        original = self.authority.trust
        no_provider = InternalBundleAcceptor(self.scheduler(), authority=None)
        with self.assertRaisesRegex(VerificationBlocked, "authority_unavailable"):
            no_provider.accept(claim.request_id, bundle, auth)
        reviewer = original.keys["reviewer"]
        for trust, reason in (
            (replace(original, trust_epoch=5), "trust_stale"),
            (replace(original, expires_at=100), "trust_stale"),
            (replace(original, keys={"reviewer": replace(reviewer, revoked=True)}), "signer_untrusted"),
            (replace(original, keys={"reviewer": replace(reviewer, company_id="trading_technology")}), "signer_untrusted"),
            (replace(original, keys={"reviewer": replace(reviewer, purpose="ar_cto")}), "signer_untrusted"),
            (replace(original, keys={"reviewer": replace(reviewer, principal_id="fixture-engineering-builder")}),
             "reviewer_not_independent"),
            (replace(original, keys={"reviewer": replace(reviewer, principal_id="fixture-risk-reviewer")}),
             "reviewer_not_independent"),
        ):
            with self.subTest(reason=reason), self.assertRaisesRegex(VerificationBlocked, reason):
                self.authority.trust = trust
                acceptor.accept(claim.request_id, bundle, auth)

    def test_external_authority_change_or_expiry_before_record_is_denied(self):
        acceptor, claim, bundle = self.prepare()
        original = self.authority.trust
        old = self.authority.current
        observations = iter((original, replace(original, trust_epoch=5)))
        self.authority.current = lambda company_id: next(observations)
        try:
            with self.assertRaisesRegex(VerificationBlocked, "authority_changed"):
                acceptor.accept(claim.request_id, bundle, self.sign(claim))
        finally:
            self.authority.current = old
        ticks = iter((100, 100, 120))
        expiring = InternalBundleAcceptor(self.scheduler(clock=lambda: next(ticks)), authority=self.authority)
        with self.assertRaisesRegex(VerificationBlocked, "expired_before_record"):
            expiring.accept(claim.request_id, bundle, self.sign(claim))

    def test_concurrent_signed_records_consume_exact_package_once(self):
        acceptor, claim, bundle = self.prepare()
        attempts = (self.sign(claim, expires_at=119), self.sign(claim, expires_at=120))

        def accept(auth):
            try:
                return acceptor.accept(claim.request_id, bundle, auth).release_authorized
            except VerificationBlocked as exc:
                return str(exc)

        with ThreadPoolExecutor(max_workers=2) as workers:
            self.assertCountEqual(workers.map(accept, attempts), (False, "bundle_acceptance_already_recorded"))

    def test_result_changed_inside_transaction_rolls_back_acceptance(self):
        acceptor, claim, bundle = self.prepare()
        for field in ("result", "request_bytes"):
            with self.subTest(field=field):
                with closing(sqlite3.connect(self.database)) as db, db:
                    statement = (
                        "CREATE TRIGGER substitute_result AFTER INSERT ON fixture_bundle_acceptance BEGIN "
                        f"UPDATE scheduled_fixture SET {field}=x'7B7D' WHERE request_id=new.request_id; END"
                    )
                    db.execute(statement)
                with self.assertRaisesRegex(VerificationBlocked, "scheduled_result_changed"):
                    acceptor.accept(claim.request_id, bundle, self.sign(claim))
                with closing(sqlite3.connect(self.database)) as db, db:
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM fixture_bundle_acceptance").fetchone()[0], 0)
                    db.execute("DROP TRIGGER substitute_result")
        self.assertIs(acceptor.accept(claim.request_id, bundle, self.sign(claim)).release_authorized, False)

    def test_v4_migration_requires_explicit_registration_and_preserves_existing_result(self):
        acceptor, claim, bundle = self.prepare()
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute("DROP TABLE fixture_bundle_acceptance")
        with self.assertRaisesRegex(VerificationBlocked, "scheduler_unavailable"):
            acceptor.accept(claim.request_id, bundle, self.sign(claim))
        with closing(sqlite3.connect(self.database)) as db, db:
            db.executescript(Path(__file__).with_name("revenue_fixture_schedule_v4.sql").read_text())
        self.assertEqual(acceptor.claim(claim.request_id), claim)
        self.assertIs(acceptor.accept(claim.request_id, bundle, self.sign(claim)).release_authorized, False)

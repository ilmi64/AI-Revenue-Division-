"""Exercise packaging only through a real scheduled internal review."""

from contextlib import closing
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from evidence_verifier import VerificationBlocked
from revenue_commercial_scope import fixed_review_scope
from revenue_fixture_dispatch import canonical
from revenue_fixture_schedule import FixtureScheduler, ScheduledRequest
from revenue_internal_review_bundle import build_internal_review_bundle


class InternalReviewBundleTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "schedule.sqlite"
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executescript(Path(__file__).with_name("revenue_fixture_schedule.sql").read_text())
        self.scheduler = FixtureScheduler(database=self.path, clock=lambda: 100)

    def schedule(self, service):
        request = ScheduledRequest("fixture-" + service, fixed_review_scope(service), 130)
        self.scheduler.schedule(request)
        return request.request_id

    def test_reviewed_artifacts_and_evidence_are_preserved_for_all_four_services(self):
        for service in ("coding", "app_build", "ai_setup", "authorized_bug_bounty"):
            with self.subTest(service=service):
                request_id = self.schedule(service)
                self.assertEqual(self.scheduler.run_one(request_id).state, "REVIEW_READY")
                archive = build_internal_review_bundle(self.scheduler, request_id)
                persisted = json.loads(self.scheduler.private_result(request_id))
                with ZipFile(BytesIO(archive)) as zipped:
                    manifest = json.loads(zipped.read("manifest.json"))
                    self.assertFalse(manifest["release_authorized"])
                    self.assertEqual(manifest["commissioning_status"], "HOLD")
                    self.assertEqual(set(zipped.namelist()), {"manifest.json", *manifest["members_sha256"]})
                    for member, digest in manifest["members_sha256"].items():
                        self.assertEqual(sha256(zipped.read(member)).hexdigest(), digest)
                    self.assertEqual(zipped.read("reviewed-artifact.json"),
                                     canonical(persisted["private_artifact"]["contents"]))
                    self.assertEqual(zipped.read("review-evidence.json"), canonical(persisted["private_test_log"]))
                    self.assertEqual(zipped.read("anchored-review-receipt.json"), canonical(persisted["receipt"]))
                    self.assertEqual(manifest["commercial_review_scope"],
                                     persisted["private_artifact"]["contents"]["commercial_review_scope"])

    def test_package_is_byte_identical_after_scheduler_reopen(self):
        request_id = self.schedule("coding")
        self.scheduler.run_one(request_id)
        reopened = FixtureScheduler(database=self.path, clock=lambda: 100)
        self.assertEqual(
            build_internal_review_bundle(self.scheduler, request_id),
            build_internal_review_bundle(reopened, request_id),
        )

    def test_unrun_and_expired_requests_cannot_be_packaged(self):
        request_id = self.schedule("coding")
        with self.assertRaises(VerificationBlocked):
            build_internal_review_bundle(self.scheduler, request_id)
        expired = FixtureScheduler(database=self.path, clock=lambda: 131)
        self.assertNotEqual(expired.run_one(request_id).state, "REVIEW_READY")
        with self.assertRaises(VerificationBlocked):
            build_internal_review_bundle(expired, request_id)

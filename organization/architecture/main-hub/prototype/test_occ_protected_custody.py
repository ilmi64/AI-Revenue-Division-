"""Offline protected-file commissioning checks for already enrolled custody."""

from hashlib import sha256
import os
from pathlib import Path
import sqlite3
import unittest

import test_occ_publisher_enrollment as fixtures
from occ_durable_receipt_anchor import DurableReceiptAnchor
from occ_protected_custody import preflight_protected_custody
from occ_signed_visibility import ReceiptJournal


AI, NOW = fixtures.AI, fixtures.NOW


class ProtectedCustodyTests(unittest.TestCase):
    def setUp(self):
        fixtures.PublisherEnrollmentTests.setUp(self)
        self.authority_dir = self.path / "authority"
        self.journal_dir = self.path / "journal"
        self.authority_dir.mkdir(mode=0o700)
        self.journal_dir.mkdir(mode=0o700)
        self.enrollment_path = self.authority_dir / "enrollment.sqlite"
        self.anchor = self.initialize()
        self.journal = ReceiptJournal.initialize(self.journal_dir / "receipts.sqlite",
                                                 company_id=AI, anchor=self.anchor)
        self.options = dict(
            trust=self.trust[AI], now=NOW, expected_enrollment=self.anchor.enrollment_pins[AI],
            journal_uid=os.getuid(), authority_uid=os.getuid(),
        )

    sign = fixtures.PublisherEnrollmentTests.sign
    view = fixtures.PublisherEnrollmentTests.view
    prove = fixtures.PublisherEnrollmentTests.prove
    initialize = fixtures.PublisherEnrollmentTests.initialize

    def preflight(self, journal=None, **changes):
        return preflight_protected_custody(self.journal if journal is None else journal,
                                           **{**self.options, **changes})

    def digests(self):
        return [sha256(path.read_bytes()).hexdigest() for path in (self.journal.path, self.anchor.path)]

    def test_read_only_check_survives_prior_receipt_and_returns_no_private_metadata(self):
        self.view(ai_revenue_wire=self.sign(AI, 1), journal_by_company={AI: self.journal})
        before = self.digests()
        self.assertEqual(self.preflight(), {
            "company_id": AI, "checkpoints_aligned": True, "operational_claim": False,
            "witnessed_enrollment_verified": True, "local_file_protection_verified": True,
        })
        self.assertEqual(self.digests(), before)
        self.assertEqual(self.anchor.read(AI).count, 1)
        with self.assertRaisesRegex(ValueError, "independently retained enrollment"):
            self.preflight(expected_enrollment="0" * 64)

    def test_bad_owner_and_group_readable_file_or_directory_rejected(self):
        with self.assertRaisesRegex(ValueError, "owner-private|untrusted directory"):
            self.preflight(authority_uid=os.getuid() + 1)
        for path, rejected_mode, original_mode in (
            (Path(self.anchor.path), 0o640, 0o600),
            (self.journal_dir, 0o750, 0o700),
        ):
            path.chmod(rejected_mode)
            try:
                with self.assertRaisesRegex(ValueError, "owner-private|untrusted directory"):
                    self.preflight()
            finally:
                path.chmod(original_mode)
        self.assertTrue(self.preflight()["local_file_protection_verified"])

    def test_symlink_and_hardlink_rejected_even_when_content_is_identical(self):
        alternate = self.journal_dir / "aliased.sqlite"
        alternate.symlink_to(self.journal.path)
        with self.assertRaisesRegex(ValueError, "owner-private|untrusted directory"):
            self.preflight(ReceiptJournal(alternate, AI, self.anchor))
        alternate.unlink()
        os.link(self.journal.path, alternate)
        try:
            with self.assertRaisesRegex(ValueError, "unaliased"):
                self.preflight()
        finally:
            alternate.unlink()
        directory_alias = self.path / "alias"
        directory_alias.symlink_to(self.journal_dir, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "traverses|unaliased"):
            self.preflight(ReceiptJournal(directory_alias / self.journal.path.name, AI, self.anchor))

    def test_shared_directory_sidecar_and_wal_header_rejected(self):
        sibling = ReceiptJournal.initialize(self.authority_dir / "same-dir.sqlite",
                                              company_id=AI, anchor=self.anchor)
        with self.assertRaisesRegex(ValueError, "distinct directories"):
            self.preflight(sibling)
        sidecar = self.journal.path.with_name(self.journal.path.name + "-journal")
        sidecar.touch()
        try:
            with self.assertRaisesRegex(ValueError, "sidecar"):
                self.preflight()
        finally:
            sidecar.unlink()
        db = sqlite3.connect(self.journal.path)
        try:
            self.assertEqual(db.execute("PRAGMA journal_mode=WAL").fetchone(), ("wal",))
        finally:
            db.close()
        before = self.digests()
        with self.assertRaisesRegex(ValueError, "rollback journal format"):
            self.preflight()
        self.assertEqual(self.digests(), before)
        self.assertFalse(self.journal.path.with_name(self.journal.path.name + "-shm").exists())

    def test_authority_read_only_sqlite_open_blocks_write_pragma(self):
        reopened = DurableReceiptAnchor(self.anchor.path, self.approval_keys, self.anchor.enrollment_pins)
        with reopened._connect(read_only=True) as db:
            with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
                db.execute("DELETE FROM checkpoint")
        self.assertTrue(self.preflight()["local_file_protection_verified"])

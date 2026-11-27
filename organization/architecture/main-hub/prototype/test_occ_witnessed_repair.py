"""Witnessed single-receipt recovery without publishing a view."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
import sqlite3
import unittest

import test_occ_publisher_enrollment as enrollment
import test_occ_receipt_anchor as anchor_fixture
from occ_durable_receipt_anchor import (
    CustodyAuthorization, DurableReceiptAnchor, custody_transition_bytes, pending_repair_bytes,
)
from occ_signed_visibility import ReceiptJournal


AI, TRADING, NOW = enrollment.AI, enrollment.TRADING, enrollment.NOW


class StrippedWitness:
    def __init__(self, authority):
        self.authority = authority

    def read(self, company):
        return replace(self.authority.read(company), witnessed_enrollment_sha256=None)


class WitnessedRepairTests(unittest.TestCase):
    def setUp(self):
        enrollment.PublisherEnrollmentTests.setUp(self)
        self.anchor = self.initialize()
        self.journals = {
            company: ReceiptJournal.initialize(self.path / f"{company}-repair.sqlite",
                                                company_id=company, anchor=self.anchor)
            for company in self.scopes
        }

    sign = enrollment.PublisherEnrollmentTests.sign
    view = enrollment.PublisherEnrollmentTests.view
    prove = enrollment.PublisherEnrollmentTests.prove
    initialize = enrollment.PublisherEnrollmentTests.initialize

    def interrupt(self):
        wire = self.sign(AI, 1)
        interrupted = ReceiptJournal(self.journals[AI].path, AI,
                                     anchor_fixture.LostAcknowledgement(self.anchor))
        view = self.view(ai_revenue_wire=wire, trading_wire=self.sign(TRADING, 1),
                         journal_by_company={**self.journals, AI: interrupted})
        self.assertEqual(view[AI]["input_status"], "REJECTED")
        self.assertEqual(view[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")
        anchor = DurableReceiptAnchor(self.anchor.path, self.approval_keys, self.anchor.enrollment_pins)
        return wire, ReceiptJournal(interrupted.path, AI, anchor)

    def signature(self, checkpoints, *, signer=AI, expires=None):
        expires = NOW + timedelta(seconds=30) if expires is None else expires
        binding = pending_repair_bytes(*checkpoints, issued_at=NOW, expires_at=expires)
        return CustodyAuthorization(NOW, expires, self.custodians[signer].sign(binding))

    def count(self):
        with sqlite3.connect(self.journals[AI].path) as db:
            return db.execute("SELECT COUNT(*) FROM receipt").fetchone()[0]

    def test_missing_witness_does_not_repair_and_exact_witness_restores_only_local_row(self):
        wire, journal = self.interrupt()
        checkpoints = journal.pending_repair_checkpoints(wire, trust=self.trust[AI], now=NOW)
        self.assertEqual(checkpoints[-1], sha256(wire).hexdigest())
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.anchor.read(AI).count, 1)
        with self.assertRaisesRegex(ValueError, "witness is missing"):
            journal.reconcile_pending_receipt(wire, trust=self.trust[AI], now=NOW)
        self.assertEqual(self.count(), 0)
        approval = self.signature(checkpoints)
        self.assertIsNone(journal.reconcile_pending_receipt(
            wire, trust=self.trust[AI], now=NOW, authorization=approval,
        ))
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.anchor.read(AI).count, 1)
        with self.assertRaises(ValueError):
            journal.reconcile_pending_receipt(wire, trust=self.trust[AI], now=NOW, authorization=approval)
        self.assertEqual(self.view(ai_revenue_wire=wire)[AI]["input_status"], "REJECTED")
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 2))[AI]["authentication"],
                         "AUTHENTICATED_OFFLINE")

    def test_wrong_scope_digest_and_expired_witness_fail_without_mutating(self):
        wire, journal = self.interrupt()
        local, anchored, digest = journal.pending_repair_checkpoints(wire, trust=self.trust[AI], now=NOW)
        for scoped in (
            self.signature((local, anchored, digest), signer=TRADING),
            self.signature((local, anchored, "f" * 64)),
        ):
            with self.assertRaisesRegex(ValueError, "witness did not verify"):
                journal.reconcile_pending_receipt(wire, trust=self.trust[AI], now=NOW,
                                                  authorization=scoped)
        expiry = NOW + timedelta(seconds=1)
        with self.assertRaisesRegex(ValueError, "witness is missing or expired"):
            journal.reconcile_pending_receipt(
                wire, trust=self.trust[AI], now=expiry,
                authorization=self.signature((local, anchored, digest), expires=expiry),
            )
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.view(trading_wire=self.sign(TRADING, 2))[TRADING]["authentication"],
                         "AUTHENTICATED_OFFLINE")

    def test_unavailable_verifier_or_stripped_enrollment_cannot_downgrade_repair(self):
        wire, journal = self.interrupt()
        approval = self.signature(journal.pending_repair_checkpoints(wire, trust=self.trust[AI], now=NOW))
        for authority, error in (
            (anchor_fixture.LostAcknowledgement(self.anchor), "authority is unavailable"),
            (StrippedWitness(self.anchor), "witness binding does not match"),
        ):
            with self.assertRaisesRegex(ValueError, error):
                ReceiptJournal(journal.path, AI, authority).reconcile_pending_receipt(
                    wire, trust=self.trust[AI], now=NOW, authorization=approval,
                )
        self.assertEqual(self.count(), 0)

    def test_competing_recovery_consumes_exact_local_repair_once(self):
        wire, journal = self.interrupt()
        approval = self.signature(journal.pending_repair_checkpoints(wire, trust=self.trust[AI], now=NOW))

        def attempt(_):
            try:
                journal.reconcile_pending_receipt(wire, trust=self.trust[AI], now=NOW,
                                                  authorization=approval)
            except ValueError:
                return False
            return True

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(pool.map(attempt, range(2)), (True, False))
        self.assertEqual(self.count(), 1)
        self.assertEqual(self.anchor.read(AI).count, 1)

    def test_retained_pin_refuses_repair_when_both_presentations_lose_the_witness(self):
        wire, journal = self.interrupt()
        with sqlite3.connect(journal.path) as db:
            db.execute("DROP TABLE receipt_witness_binding")
        stripped = ReceiptJournal(journal.path, AI, StrippedWitness(self.anchor))
        for operation in (stripped.pending_repair_checkpoints, stripped.reconcile_pending_receipt):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(ValueError, "independently retained enrollment"):
                    operation(wire, trust=self.trust[AI], now=NOW,
                              expected_enrollment=self.anchor.enrollment_pins[AI])
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.anchor.read(AI).count, 1)
        self.assertEqual(self.view(trading_wire=self.sign(TRADING, 2))[TRADING]["authentication"],
                         "AUTHENTICATED_OFFLINE")

    def test_rotation_rejects_peer_pin_and_keeps_exact_pin_on_valid_transition(self):
        current = self.anchor.read(AI)
        peer = self.anchor.read(TRADING)
        replacement = replace(self.trust[AI], source_revision="e" * 40)
        expires = NOW + timedelta(seconds=30)
        binding = custody_transition_bytes(current, replacement, issued_at=NOW, expires_at=expires)
        approval = CustodyAuthorization(NOW, expires, self.custodians[AI].sign(binding))
        for pin in (True, self.anchor.enrollment_pins[TRADING]):
            with self.subTest(pin=pin), self.assertRaisesRegex(ValueError, "independently retained enrollment"):
                self.journals[AI].transition_custody(self.trust[AI], replacement, approval, now=NOW,
                                                    expected_enrollment=pin)
        self.assertEqual(self.anchor.read(AI), current)
        self.journals[AI].transition_custody(self.trust[AI], replacement, approval, now=NOW,
                                            expected_enrollment=self.anchor.enrollment_pins[AI])
        self.assertNotEqual(self.anchor.read(AI).custody_sha256, current.custody_sha256)
        self.assertEqual(self.anchor.read(AI).witnessed_enrollment_sha256, current.witnessed_enrollment_sha256)
        self.assertEqual(self.anchor.read(TRADING), peer)

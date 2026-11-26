"""Witnessed offline publisher enrollment keeps company custody separate."""

from dataclasses import replace
from datetime import timedelta
import sqlite3
import unittest

import test_occ_durable_receipt_anchor as fixture
from occ_durable_receipt_anchor import DurableReceiptAnchor
from occ_publisher_enrollment import (
    PublisherEnrollment, publisher_enrollment_bytes, witness_enrollment_bytes,
)
from occ_signed_visibility import ReceiptJournal


AI, TRADING, NOW = fixture.AI, fixture.TRADING, fixture.NOW


class PublisherEnrollmentTests(unittest.TestCase):
    def setUp(self):
        fixture.DurableReceiptAnchorTests.setUp(self)
        self.scopes = {company: (f"{company}-enrollment", trust) for company, trust in self.trust.items()}
        self.challenges = {AI: "a1" * 32, TRADING: "b2" * 32}
        self.proofs = {company: (challenge, self.prove(company))
                       for company, challenge in self.challenges.items()}
        self.enrollment_path = self.path / "witnessed.sqlite"

    sign = fixture.DurableReceiptAnchorTests.sign
    view = fixture.DurableReceiptAnchorTests.view

    def prove(self, company, *, signing_company=None, witness_company=None):
        journal_id, trust = self.scopes[company]
        expires = NOW + timedelta(seconds=60)
        challenge = self.challenges[company]
        binding = publisher_enrollment_bytes(
            trust, journal_id, self.approval_keys[company], challenge=challenge,
            issued_at=NOW, expires_at=expires,
        )
        signature = self.keys[signing_company or company].sign(binding)
        witness = self.custodians[witness_company or company].sign(witness_enrollment_bytes(binding, signature))
        return PublisherEnrollment(challenge, NOW, expires, signature, witness)

    def initialize(self, **changes):
        options = dict(authority_public_keys=self.approval_keys, enrollments=self.proofs, now=NOW)
        return DurableReceiptAnchor.initialize(self.enrollment_path, self.scopes, **{**options, **changes})

    def test_witnessed_publishers_verify_independently_after_authority_reopen(self):
        provisioned = self.initialize()
        self.assertEqual(set(provisioned.enrollment_pins), {AI, TRADING})
        self.assertNotEqual(provisioned.enrollment_pins[AI], provisioned.enrollment_pins[TRADING])
        reopened = DurableReceiptAnchor(provisioned.path, self.approval_keys, provisioned.enrollment_pins)
        journals = {
            company: ReceiptJournal.initialize(self.path / f"{company}-witnessed.sqlite",
                                                company_id=company, anchor=reopened)
            for company in self.scopes
        }
        result = self.view(ai_revenue_wire=self.sign(AI, 1), trading_wire=self.sign(TRADING, 1),
                           journal_by_company=journals)
        self.assertEqual(result[AI]["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertEqual(result[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertNotIn("enrollment", result[AI])
        self.assertEqual(reopened.read(AI).count, 1)
        self.assertEqual(reopened.read(TRADING).count, 1)

    def test_wrong_signer_or_witness_leaves_authority_unprovisioned(self):
        for proof in (self.prove(AI, signing_company=TRADING),
                      self.prove(AI, witness_company=TRADING),
                      replace(self.proofs[AI][1], publisher_signature=b"x" * 64)):
            with self.subTest(proof=proof), self.assertRaisesRegex(ValueError, "possession or independent witness"):
                self.initialize(enrollments={**self.proofs, AI: (self.challenges[AI], proof)})
            self.assertFalse(self.enrollment_path.exists())

    def test_challenge_expiry_and_required_peer_evidence_fail_before_write(self):
        for changes in (
            {"enrollments": {AI: self.proofs[AI]}},
            {"now": NOW + timedelta(seconds=60)},
            {"enrollments": {**self.proofs, AI: ("e1" * 32, self.proofs[AI][1])}},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.initialize(**changes)
            self.assertFalse(self.enrollment_path.exists())

    def test_publisher_proof_binds_journal_identity_and_exact_custody(self):
        old = self.scopes[AI]
        for journal, trust in (("another-journal", old[1]),
                               (old[0], replace(old[1], source_revision="c" * 40)),
                               (old[0], replace(old[1], divisional_telemetry=True))):
            self.scopes[AI] = journal, trust
            with self.subTest(journal=journal, trust=trust), self.assertRaisesRegex(ValueError, "possession"):
                self.initialize()
            self.assertFalse(self.enrollment_path.exists())

    def test_missing_pin_fails_and_persisted_proof_tampering_holds_only_affected_scope(self):
        provisioned = self.initialize()
        with self.assertRaisesRegex(ValueError, "binding mode"):
            DurableReceiptAnchor(provisioned.path, self.approval_keys).read(AI)
        journals = {
            company: ReceiptJournal.initialize(self.path / f"tamper-{company}.sqlite",
                                                company_id=company, anchor=provisioned)
            for company in self.scopes
        }
        with sqlite3.connect(provisioned.path) as db:
            db.execute("UPDATE publisher_enrollment SET proof_sha256=? WHERE company_id=?", ("0" * 64, AI))
        result = self.view(ai_revenue_wire=self.sign(AI, 1), trading_wire=self.sign(TRADING, 1),
                           journal_by_company=journals)
        self.assertEqual(result[AI]["input_status"], "REJECTED")
        self.assertEqual(result[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")

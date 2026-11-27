"""Witnessed offline publisher enrollment keeps company custody separate."""

from dataclasses import replace
from datetime import timedelta
import sqlite3
import unittest

import test_occ_durable_receipt_anchor as fixture
from occ_durable_receipt_anchor import DurableReceiptAnchor
from occ_mobile_visibility import render_mobile_visibility
from occ_publisher_enrollment import (
    PublisherEnrollment, publisher_enrollment_bytes, witness_enrollment_bytes,
)
from occ_signed_visibility import ReceiptJournal, build_authenticated_visibility, sign_fixture


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

    def test_custody_preflight_is_read_only_and_detects_rollback_without_consuming_receipt(self):
        anchor = self.initialize()
        journal_path = self.path / "preflight.sqlite"
        journal = ReceiptJournal.initialize(journal_path, company_id=AI, anchor=anchor)
        anchor_before, journal_before = anchor.path.read_bytes(), journal_path.read_bytes()
        options = {"trust": self.trust[AI], "now": NOW, "expected_enrollment": anchor.enrollment_pins[AI]}
        self.assertEqual(journal.preflight_witnessed_custody(**options), {
            "company_id": AI, "checkpoints_aligned": True,
            "witnessed_enrollment_verified": True, "operational_claim": False,
        })
        for wrong in (None, anchor.enrollment_pins[TRADING], True):
            with self.subTest(wrong=wrong), self.assertRaisesRegex(ValueError, "independently retained enrollment"):
                journal.preflight_witnessed_custody(**{**options, "expected_enrollment": wrong})
        self.assertEqual(anchor.path.read_bytes(), anchor_before)
        self.assertEqual(journal_path.read_bytes(), journal_before)
        report = build_authenticated_visibility(
            ai_revenue_wire=self.sign(AI, 1), trust_by_company=self.trust,
            journal_by_company={AI: journal}, witnessed_enrollment_pins=anchor.enrollment_pins, now=NOW,
        )
        self.assertEqual(report["companies"][AI]["authentication"], "AUTHENTICATED_OFFLINE")
        rolled_path = self.path / "rolled.sqlite"
        rolled_path.write_bytes(journal_before)
        rolled = ReceiptJournal(rolled_path, AI, anchor)
        with self.assertRaisesRegex(ValueError, "does not match the independent checkpoint"):
            rolled.preflight_witnessed_custody(**options)
        self.assertEqual(rolled_path.read_bytes(), journal_before)
        self.assertEqual(anchor.read(TRADING).count, 0)

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

    def test_missing_local_witness_binding_rejects_even_with_correct_independent_pin(self):
        anchor = self.initialize()
        journals = {
            company: ReceiptJournal.initialize(self.path / f"{company}-binding.sqlite",
                                                company_id=company, anchor=anchor)
            for company in self.scopes
        }
        with sqlite3.connect(journals[AI].path) as db:
            db.execute("DROP TABLE receipt_witness_binding")
        view = self.view(ai_revenue_wire=self.sign(AI, 1), trading_wire=self.sign(TRADING, 1),
                         journal_by_company=journals, witnessed_enrollment_pins=anchor.enrollment_pins)
        self.assertEqual(view[AI]["input_status"], "REJECTED")
        self.assertEqual(anchor.read(AI).count, 0)
        self.assertTrue(view[TRADING]["verified_witnessed_enrollment"])
        self.assertEqual(anchor.read(TRADING).count, 1)

    def test_witnessed_reporting_rejects_downgraded_journal_and_missing_or_wrong_pin(self):
        anchor = self.initialize()
        journals = {
            company: ReceiptJournal.initialize(self.path / f"{company}-strict.sqlite",
                                                company_id=company, anchor=anchor)
            for company in self.scopes
        }
        fallback = ReceiptJournal.initialize(self.path / "fallback.sqlite", company_id=AI)
        for journal, pins in (
            (fallback, anchor.enrollment_pins),
            (journals[AI], {TRADING: anchor.enrollment_pins[TRADING]}),
            (journals[AI], {**anchor.enrollment_pins, AI: "0" * 64}),
        ):
            with self.subTest(journal=journal.path.name, pins=pins):
                view = self.view(ai_revenue_wire=self.sign(AI, 1),
                                 journal_by_company={**journals, AI: journal},
                                 witnessed_enrollment_pins=pins)
                self.assertEqual(view[AI]["input_status"], "REJECTED")
        self.assertEqual(anchor.read(AI).count, 0)
        report = build_authenticated_visibility(
            ai_revenue_wire=self.sign(AI, 1), trading_wire=self.sign(TRADING, 1),
            trust_by_company=self.trust, journal_by_company=journals,
            witnessed_enrollment_pins=anchor.enrollment_pins, now=NOW,
        )
        self.assertFalse(report["operational_claim"])
        html = render_mobile_visibility(report, assessed_at=NOW)
        self.assertEqual(html.count("Witnessed enrollment matched"), 2)
        for pin in anchor.enrollment_pins.values():
            self.assertNotIn(pin, html)

    def test_company_resource_qualification_requires_witnessed_enrollment_and_stays_scoped(self):
        self.trust = {company: replace(trust, divisional_telemetry=True) for company, trust in self.trust.items()}
        self.scopes = {company: (journal_id, self.trust[company])
                       for company, (journal_id, _) in self.scopes.items()}
        proofs = {company: (challenge, self.prove(company)) for company, challenge in self.challenges.items()}
        anchor = self.initialize(enrollments=proofs)
        journals = {
            company: ReceiptJournal.initialize(self.path / f"{company}-resource.sqlite",
                                                company_id=company, anchor=anchor)
            for company in self.scopes
        }

        def wire(company, resources):
            incidents = {"open_incident_count": 0, "pending_approval_count": 1,
                         "blocker_count": 0 if company == AI else len(self.trading["blockers"])}
            payload = {"report": self.ai if company == AI else self.trading, "divisional_telemetry": {
                "company_totals": incidents, "divisions": {}, "resource_qualification": resources,
            }}
            return sign_fixture(payload, trust=self.trust[company], sequence=1, issued_at=NOW,
                                expires_at=NOW + timedelta(seconds=30), private_key=self.keys[company])

        ai_wire = wire(AI, {"native_workforce": "BLOCKED"})
        trading_wire = wire(TRADING, {"historical_data": "STAGED_FOR_REVIEW"})
        common = {"trust_by_company": self.trust, "journal_by_company": journals, "now": NOW}
        missing_pin = build_authenticated_visibility(ai_revenue_wire=ai_wire, **common)
        self.assertEqual(missing_pin["companies"][AI]["input_status"], "REJECTED")

        strict = {**common, "witnessed_enrollment_pins": anchor.enrollment_pins}
        for bad in ({"historical_data": "BLOCKED"}, {"native_workforce": "RELEASED"},
                    {"native_workforce": {"secret_path": "private"}}, {}):
            with self.subTest(bad=bad):
                rejected = build_authenticated_visibility(ai_revenue_wire=wire(AI, bad), **strict)
                self.assertEqual(rejected["companies"][AI]["input_status"], "REJECTED")
                self.assertEqual(anchor.read(AI).count, 0)
        result = build_authenticated_visibility(ai_revenue_wire=ai_wire, trading_wire=trading_wire, **strict)
        ai_card, trading_card = render_mobile_visibility(result).split('<article aria-labelledby="trading_technology">')
        self.assertIn("Native workforce</dt><dd>Blocked", ai_card)
        self.assertNotIn("Historical data", ai_card)
        self.assertIn("Historical data</dt><dd>Staged for review", trading_card)
        self.assertNotIn("Native workforce", trading_card)
        self.assertFalse(result["operational_claim"])
        self.assertEqual(anchor.read(AI).count, 1)
        self.assertEqual(anchor.read(TRADING).count, 1)

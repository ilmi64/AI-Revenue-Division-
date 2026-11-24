"""Deterministic synthetic trust and isolated offline receipt tests."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from occ_readonly import EXPECTED, read_fixture
from occ_signed_visibility import PublisherTrust, ReceiptJournal, build_authenticated_visibility, sign_fixture


AI, TRADING = "ai_revenue", "trading_technology"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
NOW = datetime(2026, 11, 20, 12, 0, 2, tzinfo=timezone.utc)


class SignedVisibilityTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.journal = ReceiptJournal.initialize(Path(tmp.name) / "receipts.sqlite")
        self.ai_key = Ed25519PrivateKey.from_private_bytes(b"\x01" * 32)
        self.trading_key = Ed25519PrivateKey.from_private_bytes(b"\x02" * 32)
        self.trust = {
            AI: PublisherTrust(AI, "aevora", "ai-fixture", self.ai_key.public_key().public_bytes_raw(),
                               "a" * 40, NOW - timedelta(hours=1), NOW + timedelta(hours=1)),
            TRADING: PublisherTrust(TRADING, "polybot", "tt-fixture", self.trading_key.public_key().public_bytes_raw(),
                                    "b" * 40, NOW - timedelta(hours=1), NOW + timedelta(hours=1)),
        }
        self.ai = {
            "organization": "Daivora Group", "source_company": "Aevora AI", "recipient": "Main Hub/OCC",
            "mode": "read_only_aggregate", "execution_authorized": False,
            "external_actions_performed": False, "total": 1,
            "counts": {"blocked": 0, "checklist_complete_unverified": 1,
                       "hold": 0, "rejected": 0, "review_ready": 0},
        }
        self.trading = read_fixture(FIXTURES / EXPECTED[TRADING])
        self.trading["source_revision"] = "b" * 40
        self.trading["gates"][0]["status"] = "BLOCKED"

    def signed(self, company, payload=None, **changes):
        options = {
            "trust": self.trust[company], "sequence": 1, "issued_at": NOW,
            "expires_at": NOW + timedelta(seconds=30),
            "private_key": self.ai_key if company == AI else self.trading_key,
        }
        if payload is None:
            payload = self.ai if company == AI else self.trading
        return sign_fixture(payload, **{**options, **changes})

    def report(self, **changes):
        options = {"trust_by_company": self.trust, "journal": self.journal, "now": NOW}
        return build_authenticated_visibility(**{**options, **changes})

    def test_authenticated_statuses_are_independent_and_private_text_redacted(self):
        self.trading["blockers"][0]["summary"] = "PRIVATE TEXT"
        report = self.report(ai_revenue_wire=self.signed(AI), trading_wire=self.signed(TRADING))
        ai, trading = (report["companies"][company] for company in (AI, TRADING))
        self.assertEqual(ai["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertEqual(ai["reported_total"], 1)
        self.assertEqual(trading["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertEqual(trading["reported_gate_counts"]["BLOCKED"], 1)
        self.assertFalse(report["operational_claim"])
        self.assertNotIn("PRIVATE TEXT", json.dumps(report))

    def test_authenticated_quarantined_snapshot_exposes_no_counts(self):
        self.trading["incident_summary"] = {
            "open_count": 1, "highest_severity": "high", "quarantined": True,
        }
        report = self.report(ai_revenue_wire=self.signed(AI), trading_wire=self.signed(TRADING))
        self.assertEqual(report["companies"][TRADING], {
            "input_status": "QUARANTINED",
            "display_status": "UNKNOWN",
            "authentication": "AUTHENTICATED_OFFLINE",
        })
        self.assertEqual(report["companies"][AI]["reported_total"], 1)

    def test_tampered_or_wrong_key_does_not_suppress_peer(self):
        ai_wire = self.signed(AI).replace(b'"total":1', b'"total":0')
        report = self.report(ai_revenue_wire=ai_wire, trading_wire=self.signed(TRADING))
        self.assertEqual(report["companies"][AI]["input_status"], "REJECTED")
        self.assertEqual(report["companies"][TRADING]["authentication"], "AUTHENTICATED_OFFLINE")
        forged = self.signed(AI, private_key=self.trading_key)
        self.assertEqual(self.report(ai_revenue_wire=forged)["companies"][AI]["input_status"], "REJECTED")
        self.assertEqual(self.report(ai_revenue_wire=self.signed(TRADING))["companies"][AI]["input_status"], "REJECTED")
        result = self.report(ai_revenue_wire=self.signed(AI))
        self.assertEqual(result["companies"][AI]["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertEqual(result["companies"][TRADING]["input_status"], "MISSING")

    def test_noncanonical_duplicate_oversized_and_float_inputs_are_rejected(self):
        wire = self.signed(AI)
        for malformed in (wire + b" ", wire.replace(b'"total":1', b'"total":1.0'),
                          wire.replace(b'"total":1', b'"total":1,"total":1'), b"x" * 65537):
            with self.subTest(wire_size=len(malformed)):
                self.assertEqual(self.report(ai_revenue_wire=malformed)["companies"][AI]["input_status"], "REJECTED")

    def test_wrong_pin_invalid_body_revoked_expired_and_shared_key_rejected(self):
        for change in ({"execution_authorized": True}, {"recipient": "other"}, {"raw_record": "private"}):
            wire = self.signed(AI, {**self.ai, **change})
            self.assertEqual(self.report(ai_revenue_wire=wire)["companies"][AI]["input_status"], "REJECTED")
        for trust in ({}, {**self.trust, AI: replace(self.trust[AI], revoked=True)},
                      {**self.trust, AI: replace(self.trust[AI], source_revision="c" * 40)},
                      {**self.trust, AI: replace(self.trust[AI], valid_until=NOW)},
                      {**self.trust, TRADING: replace(self.trust[TRADING], public_key=self.trust[AI].public_key)}):
            result = self.report(ai_revenue_wire=self.signed(AI), trust_by_company=trust)
            self.assertEqual(result["companies"][AI]["input_status"], "REJECTED")
        body = {**self.trading, "source_revision": "c" * 40}
        self.assertEqual(self.report(trading_wire=self.signed(TRADING, body))["companies"][TRADING]["input_status"], "REJECTED")

    def test_freshness_is_checked_against_a_separate_clock(self):
        for wire in (self.signed(AI, issued_at=NOW + timedelta(seconds=1)),
                     self.signed(AI, expires_at=NOW),
                     self.signed(AI, expires_at=NOW + timedelta(seconds=301))):
            with self.subTest(wire=wire[:50]):
                self.assertEqual(self.report(ai_revenue_wire=wire)["companies"][AI]["input_status"], "REJECTED")

    def test_replay_snapshot_id_reuse_and_missing_journal_fail_closed(self):
        wire = self.signed(TRADING, sequence=2)
        self.assertEqual(self.report(trading_wire=wire)["companies"][TRADING]["authentication"], "AUTHENTICATED_OFFLINE")
        restarted = ReceiptJournal(self.journal.path)
        for attempt in (wire, self.signed(TRADING, sequence=1), self.signed(TRADING, sequence=3)):
            result = self.report(trading_wire=attempt, journal=restarted)
            self.assertEqual(result["companies"][TRADING]["input_status"], "REJECTED")
        missing = ReceiptJournal(self.journal.path.with_name("missing.sqlite"))
        result = self.report(ai_revenue_wire=self.signed(AI), journal=missing)
        self.assertEqual(result["companies"][AI]["input_status"], "REJECTED")
        self.assertFalse(missing.path.exists())

    def test_single_acceptance_for_concurrent_delivery(self):
        wire = self.signed(AI)
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(
                lambda journal: self.report(ai_revenue_wire=wire, journal=journal)["companies"][AI]["authentication"],
                [ReceiptJournal(self.journal.path), ReceiptJournal(self.journal.path)],
            ))
        self.assertCountEqual(outcomes, ["AUTHENTICATED_OFFLINE", "UNVERIFIED"])

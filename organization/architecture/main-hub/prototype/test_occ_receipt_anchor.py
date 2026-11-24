"""Offline independent authority tests, with separate synthetic publisher keys."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from shutil import copyfile
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from occ_readonly import EXPECTED, read_fixture
from occ_receipt_anchor import FixtureReceiptAnchor
from occ_signed_visibility import (
    PublisherTrust, ReceiptJournal, build_authenticated_visibility, sign_fixture,
)


AI, TRADING = "ai_revenue", "trading_technology"
NOW = datetime(2026, 11, 20, 12, 0, 2, tzinfo=timezone.utc)
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class LostAcknowledgement:
    def __init__(self, authority):
        self.authority = authority

    def read(self, company):
        return self.authority.read(company)

    def advance(self, expected, successor):
        self.authority.advance(expected, successor)
        if expected.company_id == AI:
            raise OSError("simulated acknowledgement loss after independent commit")


class MissingCompanyCheckpoint:
    def __init__(self, authority):
        self.authority = authority

    def read(self, company):
        if company == AI:
            raise OSError("independent authority unavailable")
        return self.authority.read(company)

    def advance(self, expected, successor):
        self.authority.advance(expected, successor)


class ReceiptAnchorTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)
        self.keys = {
            AI: Ed25519PrivateKey.from_private_bytes(b"\x1a" * 32),
            TRADING: Ed25519PrivateKey.from_private_bytes(b"\x1b" * 32),
        }
        self.trust = {
            company: PublisherTrust(company, publisher, f"{publisher}-key",
                self.keys[company].public_key().public_bytes_raw(), revision * 40,
                NOW - timedelta(hours=1), NOW + timedelta(hours=1))
            for company, publisher, revision in ((AI, "aevora", "a"), (TRADING, "polybot", "b"))
        }
        self.anchor = FixtureReceiptAnchor({
            company: (f"{company}-journal", trust) for company, trust in self.trust.items()
        })
        self.journals = {
            company: ReceiptJournal.initialize(self.path / f"{company}.sqlite",
                                                company_id=company, anchor=self.anchor)
            for company in self.trust
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

    def sign(self, company, sequence, *, trust=None):
        if company == AI:
            body = self.ai
        else:
            body = {**self.trading, "snapshot_id": f"SYN-polybot-{sequence}"}
        return sign_fixture(body, trust=self.trust[company] if trust is None else trust,
                            sequence=sequence, issued_at=NOW, expires_at=NOW + timedelta(seconds=30),
                            private_key=self.keys[company])

    def view(self, **changes):
        options = {"trust_by_company": self.trust, "journal_by_company": self.journals, "now": NOW}
        result = build_authenticated_visibility(**{**options, **changes})
        self.assertFalse(result["operational_claim"])
        return result["companies"]

    def test_exact_checkpoint_restores_and_stale_backup_blocks_only_its_company(self):
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 1))[AI]["authentication"],
                         "AUTHENTICATED_OFFLINE")
        backup = self.path / "older.sqlite"
        copyfile(self.journals[AI].path, backup)
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 2))[AI]["authentication"],
                         "AUTHENTICATED_OFFLINE")
        latest = self.path / "latest.sqlite"
        copyfile(self.journals[AI].path, latest)
        older_journals = {**self.journals, AI: ReceiptJournal(backup, AI, self.anchor)}
        held = self.view(ai_revenue_wire=self.sign(AI, 2), trading_wire=self.sign(TRADING, 1),
                         journal_by_company=older_journals)
        self.assertEqual(held[AI], {"input_status": "REJECTED", "authentication": "UNVERIFIED"})
        self.assertEqual(held[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")
        restored = {**self.journals, AI: ReceiptJournal(latest, AI, self.anchor)}
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 2), journal_by_company=restored)
                         [AI]["input_status"], "REJECTED")
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 3), journal_by_company=restored)
                         [AI]["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertEqual(self.anchor.read(AI).count, 3)
        self.assertEqual(self.anchor.read(TRADING).count, 1)

    def test_advanced_but_uncertain_acceptance_rejects_after_reopen(self):
        fault = LostAcknowledgement(self.anchor)
        journals = {**self.journals, AI: ReceiptJournal(self.journals[AI].path, AI, fault)}
        result = self.view(ai_revenue_wire=self.sign(AI, 1), trading_wire=self.sign(TRADING, 1),
                           journal_by_company=journals)
        self.assertEqual(result[AI]["input_status"], "REJECTED")
        self.assertEqual(result[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertEqual(self.anchor.read(AI).count, 1)
        with sqlite3.connect(self.journals[AI].path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM receipt").fetchone(), (0,))
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 2))[AI]["input_status"], "REJECTED")
        missing = self.path / "replacement.sqlite"
        with self.assertRaisesRegex(ValueError, "cannot reprovision"):
            ReceiptJournal.initialize(missing, company_id=AI, anchor=self.anchor)
        self.assertFalse(missing.exists())

    def test_tampered_local_record_and_missing_anchor_fail_closed(self):
        self.view(ai_revenue_wire=self.sign(AI, 1))
        path = self.journals[AI].path
        with sqlite3.connect(path) as db:
            db.execute("UPDATE receipt SET digest=?", ("0" * 64,))
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 2))[AI]["input_status"], "REJECTED")
        for compromised in (ReceiptJournal(path, AI),
                            ReceiptJournal(path, AI, MissingCompanyCheckpoint(self.anchor))):
            result = self.view(ai_revenue_wire=self.sign(AI, 2),
                               journal_by_company={**self.journals, AI: compromised})
            self.assertEqual(result[AI]["input_status"], "REJECTED")

    def test_locally_reassigned_publisher_custody_cannot_override_anchor(self):
        original = self.trust[AI]
        for new in (replace(original, source_revision="c" * 40),
                    replace(original, key_id="reissued-key"),
                    replace(original, valid_until=NOW + timedelta(hours=2))):
            result = self.view(ai_revenue_wire=self.sign(AI, 1, trust=new),
                               trust_by_company={**self.trust, AI: new})
            self.assertEqual(result[AI]["input_status"], "REJECTED")
        self.assertEqual(self.anchor.read(AI).count, 0)
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 1))[AI]["authentication"],
                         "AUTHENTICATED_OFFLINE")

    def test_independent_compare_and_advance_rejects_second_clone(self):
        other_path = self.path / "other.sqlite"
        copyfile(self.journals[AI].path, other_path)
        other = ReceiptJournal(other_path, AI, self.anchor)
        wire = self.sign(AI, 1)
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(
                lambda journal: self.view(ai_revenue_wire=wire,
                    journal_by_company={**self.journals, AI: journal})[AI]["authentication"],
                (self.journals[AI], other),
            ))
        self.assertCountEqual(results, ["AUTHENTICATED_OFFLINE", "UNVERIFIED"])

    def test_peer_cannot_relabel_or_reuse_company_bound_anchor(self):
        trading_path = self.journals[TRADING].path
        outcomes = self.view(ai_revenue_wire=self.sign(AI, 1), trading_wire=self.sign(TRADING, 1),
            journal_by_company={**self.journals, AI: ReceiptJournal(trading_path, AI, self.anchor)})
        self.assertEqual(outcomes[AI]["input_status"], "REJECTED")
        self.assertEqual(outcomes[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")

"""Durable checkpoint, explicit custody approval and bounded journal repair."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from shutil import copyfile
import subprocess
import sys
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import test_occ_receipt_anchor as fixtures
from occ_durable_receipt_anchor import (
    CustodyAuthorization, DurableReceiptAnchor, custody_transition_bytes,
)
from occ_signed_visibility import ReceiptJournal


AI, TRADING, NOW = fixtures.AI, fixtures.TRADING, fixtures.NOW


class DurableReceiptAnchorTests(unittest.TestCase):
    def setUp(self):
        # Use the existing publisher fixtures; durable authority gets a distinct store and keys.
        fixtures.ReceiptAnchorTests.setUp(self)
        self.custodians = {
            company: Ed25519PrivateKey.from_private_bytes(bytes([index]) * 32)
            for index, company in enumerate((AI, TRADING), start=30)
        }
        self.approval_keys = {
            name: key.public_key().public_bytes_raw() for name, key in self.custodians.items()
        }
        self.anchor = DurableReceiptAnchor.initialize(
            self.path / "authority.sqlite",
            {company: (f"{company}-durable", trust) for company, trust in self.trust.items()},
            authority_public_keys=self.approval_keys,
        )
        self.journals = {
            company: ReceiptJournal.initialize(self.path / f"{company}-durable.sqlite",
                                                company_id=company, anchor=self.anchor)
            for company in self.trust
        }

    sign = fixtures.ReceiptAnchorTests.sign
    view = fixtures.ReceiptAnchorTests.view

    def reopen(self, *, keys=None):
        return DurableReceiptAnchor(self.anchor.path, self.approval_keys if keys is None else keys)

    def authorize(self, replacement, *, signer=AI, current=None, expires=None):
        checkpoint = self.anchor.read(AI) if current is None else current
        expires = NOW + timedelta(seconds=60) if expires is None else expires
        body = custody_transition_bytes(checkpoint, replacement, issued_at=NOW, expires_at=expires)
        return CustodyAuthorization(NOW, expires, self.custodians[signer].sign(body))

    def test_authority_reopens_in_fresh_process_and_rejects_receipt_rollback(self):
        older = self.path / "older.sqlite"
        copyfile(self.journals[AI].path, older)
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 1))[AI]["authentication"],
                         "AUTHENTICATED_OFFLINE")
        subprocess.run([
            sys.executable, "-c",
            "from occ_durable_receipt_anchor import DurableReceiptAnchor; import sys; "
            "assert DurableReceiptAnchor(sys.argv[1], {'ai_revenue': bytes.fromhex(sys.argv[2])})"
            ".read('ai_revenue').count == 1",
            str(self.anchor.path), self.approval_keys[AI].hex(),
        ], cwd=Path(__file__).parent, check=True)
        journals = {**self.journals, AI: ReceiptJournal(older, AI, self.reopen())}
        view = self.view(ai_revenue_wire=self.sign(AI, 1), trading_wire=self.sign(TRADING, 1),
                         journal_by_company=journals)
        self.assertEqual(view[AI]["input_status"], "REJECTED")
        self.assertEqual(view[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")

    def test_replacement_custodian_config_fails_only_its_scope(self):
        wrong = self.reopen(keys={**self.approval_keys, AI: self.approval_keys[TRADING]})
        journals = {
            company: ReceiptJournal(journal.path, company, wrong)
            for company, journal in self.journals.items()
        }
        view = self.view(ai_revenue_wire=self.sign(AI, 1), trading_wire=self.sign(TRADING, 1),
                         journal_by_company=journals)
        self.assertEqual(view[AI]["input_status"], "REJECTED")
        self.assertEqual(view[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")

    def test_uncertain_commit_repairs_only_exact_single_signed_receipt(self):
        interrupted = ReceiptJournal(self.journals[AI].path, AI,
                                     fixtures.LostAcknowledgement(self.reopen()))
        wire = self.sign(AI, 1)
        report = self.view(ai_revenue_wire=wire,
                           journal_by_company={**self.journals, AI: interrupted})
        self.assertEqual(report[AI]["input_status"], "REJECTED")
        self.assertEqual(self.reopen().read(AI).count, 1)
        journal = ReceiptJournal(self.journals[AI].path, AI, self.reopen())
        with self.assertRaisesRegex(ValueError, "single anchored interruption"):
            journal.reconcile_pending_receipt(self.sign(AI, 2), trust=self.trust[AI], now=NOW)
        journal.reconcile_pending_receipt(wire, trust=self.trust[AI], now=NOW)
        self.assertEqual(self.reopen().read(AI).count, 1)
        self.assertEqual(self.view(ai_revenue_wire=wire)[AI]["input_status"], "REJECTED")
        with self.assertRaises(ValueError):
            journal.reconcile_pending_receipt(wire, trust=self.trust[AI], now=NOW)
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 2))[AI]["authentication"],
                         "AUTHENTICATED_OFFLINE")

    def test_new_custody_needs_exact_independent_approval_and_survives_reopen(self):
        previous = self.trust[AI]
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 1))[AI]["authentication"],
                         "AUTHENTICATED_OFFLINE")
        self.keys[AI] = Ed25519PrivateKey.from_private_bytes(b"\x40" * 32)
        replacement = replace(previous, key_id="next-key",
                              public_key=self.keys[AI].public_key().public_bytes_raw())
        journal = self.journals[AI]
        with self.assertRaisesRegex(ValueError, "approval signature"):
            journal.transition_custody(previous, replacement, self.authorize(replacement, signer=TRADING), now=NOW)
        with self.assertRaisesRegex(ValueError, "approval signature"):
            journal.transition_custody(previous, replace(replacement, key_id="tampered"),
                                       self.authorize(replacement), now=NOW)
        approval = self.authorize(replacement)
        journal.transition_custody(previous, replacement, approval, now=NOW)
        reopened = ReceiptJournal(journal.path, AI, self.reopen())
        with self.assertRaises(ValueError):
            reopened.transition_custody(previous, replacement, approval, now=NOW)
        self.assertEqual(self.view(ai_revenue_wire=self.sign(AI, 2, trust=replacement),
                                   trust_by_company={**self.trust, AI: replacement},
                                   journal_by_company={**self.journals, AI: reopened})
                         [AI]["authentication"], "AUTHENTICATED_OFFLINE")
        with self.assertRaisesRegex(ValueError, "already been used"):
            reopened.transition_custody(replacement, previous, self.authorize(previous), now=NOW)

    def test_stale_checkpoint_expired_approval_and_unaligned_history_fail(self):
        previous = self.trust[AI]
        replacement = replace(previous, source_revision="c" * 40)
        journal = self.journals[AI]
        stale = self.authorize(replacement)
        self.view(ai_revenue_wire=self.sign(AI, 1))
        with self.assertRaisesRegex(ValueError, "approval signature"):
            journal.transition_custody(previous, replacement, stale, now=NOW)
        expiry = NOW + timedelta(seconds=1)
        with self.assertRaisesRegex(ValueError, "freshness"):
            journal.transition_custody(previous, replacement, self.authorize(replacement, expires=expiry),
                                       now=expiry)
        interrupted = ReceiptJournal(journal.path, AI, fixtures.LostAcknowledgement(self.reopen()))
        self.view(ai_revenue_wire=self.sign(AI, 2), journal_by_company={**self.journals, AI: interrupted})
        with self.assertRaisesRegex(ValueError, "does not match the independent checkpoint"):
            journal.transition_custody(previous, replacement, self.authorize(replacement), now=NOW)

    def test_concurrent_receipt_clones_share_independent_durable_cas(self):
        other = self.path / "other-ai.sqlite"
        copyfile(self.journals[AI].path, other)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(
                lambda path: self.view(ai_revenue_wire=self.sign(AI, 1),
                    journal_by_company={**self.journals, AI: ReceiptJournal(path, AI, self.reopen())})
                    [AI]["authentication"],
                (self.journals[AI].path, other),
            ))
        self.assertCountEqual(outcomes, ["AUTHENTICATED_OFFLINE", "UNVERIFIED"])
        self.assertEqual(self.reopen().read(AI).count, 1)

    def test_separate_authority_file_outage_keeps_peer_available(self):
        trading_authority = DurableReceiptAnchor.initialize(
            self.path / "isolated-trading-authority.sqlite",
            {TRADING: ("trading-isolated", self.trust[TRADING])},
            authority_public_keys={TRADING: self.approval_keys[TRADING]},
        )
        trading_journal = ReceiptJournal.initialize(
            self.path / "isolated-trading.sqlite", company_id=TRADING, anchor=trading_authority,
        )
        self.anchor.path.unlink()
        result = self.view(ai_revenue_wire=self.sign(AI, 1), trading_wire=self.sign(TRADING, 1),
                           journal_by_company={AI: self.journals[AI], TRADING: trading_journal})
        self.assertEqual(result[AI]["input_status"], "REJECTED")
        self.assertEqual(result[TRADING]["authentication"], "AUTHENTICATED_OFFLINE")
        self.assertFalse(self.anchor.path.exists())

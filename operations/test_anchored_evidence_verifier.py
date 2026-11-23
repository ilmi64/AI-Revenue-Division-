"""Synthetic adversarial verification against separated anchor and ledger fixtures."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
import hashlib
import hmac
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest

from anchored_evidence_verifier import (
    AnchoredEvidenceVerifier, advance_trust, trust_fingerprint, verify_anchored_receipt,
)
from evidence_verifier import (
    Attestation, EvidenceManifest, ReviewScope, TrustedKey, VerificationBlocked, attestation_payload,
)


class AnchoredEvidenceVerifierTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.anchor = self.root / "anchor.sqlite"
        self.audit = self.root / "audit.sqlite"
        self.scope = ReviewScope(
            "aevora-ai", "synthetic-opportunity", "b" * 40, "synthetic-recipient",
            "fixture-channel", "policy-v2", "producer",
        )
        self.artifact = b"private synthetic artifact"
        self.test_log = b"synthetic test evidence"
        self.manifest = EvidenceManifest(
            self.scope, hashlib.sha256(self.artifact).hexdigest(),
            hashlib.sha256(self.test_log).hexdigest(), "nonce-fixture", 200,
        )
        self.registry = {
            "qa": TrustedKey(self.scope.company_id, "qa", "independent_qa", 250, b"q" * 32),
            "owner": TrustedKey(self.scope.company_id, "owner", "owner_review", 250, b"o" * 32),
        }
        self.provision(self.anchor, "review_anchor.sql", (
            "INSERT INTO review_anchor VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.scope.company_id, "fixture-store", 2,
             trust_fingerprint(self.scope.company_id, self.registry), "policy-v2", 0, "0" * 64),
        ))
        self.provision(self.audit, "review_audit.sql", (
            "INSERT INTO audit_identity VALUES (?, ?)", (self.scope.company_id, "fixture-store"),
        ))

    @staticmethod
    def provision(path, schema, statement):
        with closing(sqlite3.connect(path)) as db, db:
            db.executescript(Path(__file__).with_name(schema).read_text())
            db.execute(*statement)

    @staticmethod
    def change(path, statement, params=()):
        with closing(sqlite3.connect(path)) as db, db:
            db.execute(statement, params)

    def verify(self, *, manifest=None, registry=None, **overrides):
        manifest = self.manifest if manifest is None else manifest
        registry = self.registry if registry is None else registry
        inputs = dict(
            anchor_path=self.anchor, audit_path=self.audit, registry=registry,
            scope=self.scope, trust_epoch=2, clock=lambda: 100,
        )
        inputs.update(overrides)
        def sign(key_id):
            key = registry[key_id]
            payload = attestation_payload(manifest.digest(), key_id, key.role, 175)
            return Attestation(key_id, 175, hmac.digest(key.secret, payload, "sha256").hex())
        return AnchoredEvidenceVerifier(**inputs).verify(
            manifest, deliverable=self.artifact, test_log=self.test_log, qa=sign("qa"), owner=sign("owner"),
        )

    def test_reopened_store_checks_continuity_and_replay(self):
        first = self.verify()
        self.assertEqual(first.audit_sequence, 1)
        self.assertEqual(first.status, "verified_for_owner_review")
        self.assertIs(first.release_authorized, False)
        with self.assertRaisesRegex(VerificationBlocked, "replay_conflict"):
            self.verify()
        second = self.verify(manifest=replace(self.manifest, nonce="fresh-nonce"))
        self.assertEqual(second.audit_sequence, 2)
        self.assertIs(second.release_authorized, False)
        for receipt in (first, second):
            verify_anchored_receipt(self.anchor, self.audit, self.scope.company_id, receipt)
        with self.assertRaisesRegex(VerificationBlocked, "receipt_not_anchored"):
            verify_anchored_receipt(
                self.anchor, self.audit, self.scope.company_id, replace(first, audit_sha256="a" * 64),
            )

    def test_concurrent_handles_yield_one_receipt(self):
        barrier = Barrier(2, timeout=5)
        def attempt():
            barrier.wait()
            try:
                return self.verify().release_authorized
            except VerificationBlocked as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = pool.submit(attempt), pool.submit(attempt)
            self.assertCountEqual((a.result(), b.result()), (False, "replay_conflict"))

    def test_stale_clone_and_identity_substitution_are_blocked(self):
        clone = self.root / "pre-claim-clone.sqlite"
        shutil.copyfile(self.audit, clone)
        self.verify()
        with self.assertRaisesRegex(VerificationBlocked, "audit_anchor_divergence"):
            self.verify(audit_path=clone)
        self.change(clone, "UPDATE audit_identity SET store_id='independent-store'")
        with self.assertRaisesRegex(VerificationBlocked, "audit_identity_mismatch"):
            self.verify(audit_path=clone)

    def test_epoch_pin_blocks_rollback_and_same_epoch_snapshot_substitution(self):
        revoked = {**self.registry, "qa": replace(self.registry["qa"], revoked=True)}
        advance_trust(self.anchor, self.scope.company_id, expected_epoch=2, new_epoch=3,
                      policy="policy-v2", registry=revoked)
        for arguments in ({}, {"trust_epoch": 3}):
            with self.subTest(arguments=arguments), self.assertRaisesRegex(
                VerificationBlocked, "stale_trust_or_policy",
            ):
                self.verify(**arguments)
        with self.assertRaisesRegex(VerificationBlocked, "untrusted_attestation_key"):
            self.verify(registry=revoked, trust_epoch=3)
        with self.assertRaisesRegex(VerificationBlocked, "trust_epoch_not_monotonic"):
            advance_trust(self.anchor, self.scope.company_id, expected_epoch=3, new_epoch=2,
                          policy="policy-v2", registry=self.registry)
        with self.assertRaisesRegex(VerificationBlocked, "trust_epoch_changed_or_missing"):
            advance_trust(self.anchor, self.scope.company_id, expected_epoch=2, new_epoch=4,
                          policy="policy-v2", registry=self.registry)

    def test_corrupted_audit_rejected_by_verifier_and_independent_reader(self):
        first = self.verify()
        self.verify(manifest=replace(self.manifest, nonce="second"))
        self.change(self.audit, "UPDATE review_audit SET nonce='edited' WHERE sequence=1")
        with self.assertRaisesRegex(VerificationBlocked, "audit_chain_invalid"):
            self.verify(manifest=replace(self.manifest, nonce="third"))
        with self.assertRaisesRegex(VerificationBlocked, "audit_chain_invalid"):
            verify_anchored_receipt(self.anchor, self.audit, self.scope.company_id, first)

    def test_missing_audit_anchor_or_same_file_fail_closed(self):
        self.verify()
        with self.assertRaisesRegex(VerificationBlocked, "anchor_must_be_separate"):
            self.verify(audit_path=self.anchor)
        for missing in ("anchor_path", "audit_path"):
            with self.subTest(missing=missing), self.assertRaisesRegex(
                VerificationBlocked, "anchor_or_audit_unavailable",
            ):
                self.verify(**{missing: self.root / "missing.sqlite"})
        self.assertFalse((self.root / "missing.sqlite").exists())
        self.change(self.audit, "DELETE FROM review_audit")
        with self.assertRaisesRegex(VerificationBlocked, "audit_anchor_divergence"):
            self.verify(manifest=replace(self.manifest, nonce="fresh"))

    def test_process_exit_between_commits_blocks_resume(self):
        script = """
import os
from pathlib import Path
import sqlite3
import sys
from test_anchored_evidence_verifier import AnchoredEvidenceVerifierTests

fixture = AnchoredEvidenceVerifierTests()
fixture.setUp()
fixture.anchor, fixture.audit = map(Path, sys.argv[1:])

class ExitBeforeAnchorCommit(sqlite3.Connection):
    def execute(self, sql, params=()):
        if sql == "COMMIT" and self.is_anchor:
            os._exit(71)
        return super().execute(sql, params)

original = sqlite3.connect
def connect(database, **kwargs):
    db = original(database, **kwargs, factory=ExitBeforeAnchorCommit)
    db.is_anchor = database == fixture.anchor.as_uri() + "?mode=rw"
    return db

sqlite3.connect = connect
fixture.verify()
"""
        child = subprocess.run(
            [sys.executable, "-c", script, str(self.anchor), str(self.audit)],
            check=False, capture_output=True, timeout=10, env=dict(os.environ, TMPDIR=str(self.root)),
        )
        self.assertEqual(child.returncode, 71, child.stderr.decode())
        with self.assertRaisesRegex(VerificationBlocked, "audit_anchor_divergence"):
            self.verify(manifest=replace(self.manifest, nonce="different"))

    def test_clock_rollback_and_attestation_expiry_at_claim_block(self):
        for observed_at in (99, 175):
            with self.subTest(observed_at=observed_at), self.assertRaisesRegex(
                VerificationBlocked, "clock_or_attestation_expired_at_claim",
            ):
                readings = iter((100, observed_at))
                self.verify(clock=lambda: next(readings))
        self.assertEqual(self.verify().audit_sequence, 1)

    def test_company_recipient_and_policy_downgrade_remain_blocked(self):
        for change in ({"company_id": "other-company"}, {"recipient": "other-recipient"}):
            with self.subTest(change=change), self.assertRaisesRegex(VerificationBlocked, "scope"):
                self.verify(manifest=replace(self.manifest, scope=replace(self.scope, **change)))
        stale_scope = replace(self.scope, policy_version="policy-v1")
        with self.assertRaisesRegex(VerificationBlocked, "stale_trust_or_policy"):
            self.verify(manifest=replace(self.manifest, scope=stale_scope), scope=stale_scope)

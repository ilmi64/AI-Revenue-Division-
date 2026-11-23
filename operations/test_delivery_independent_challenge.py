"""Independent offline challenge using fresh fictional artifacts, keys and stores."""
from contextlib import closing
from dataclasses import asdict, replace
import hashlib
import hmac
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from evidence_verifier import (
    Attestation, EvidenceManifest, EvidenceVerifier, ReviewScope, SQLiteReviewReplayStore,
    TrustedKey, VerificationBlocked, attestation_payload,
)
from occ_summary import summarize
from synthetic_delivery_rehearsal import run_rehearsal


class DeliveryIndependentChallenge(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.store = self.root / "replay.sqlite"
        with closing(sqlite3.connect(self.store)) as db:
            db.executescript(Path(__file__).with_name("evidence_verifier_replay.sql").read_text())
        self.scope = ReviewScope(
            "challenge-aevora", "offline-opp", "b" * 40, "fictional-recipient",
            "local-fixture", "policy-v2", "producer",
        )
        self.artifact = b"challenge fixture report"
        self.log = b"challenge fixture test bytes"
        self.manifest = EvidenceManifest(
            self.scope, hashlib.sha256(self.artifact).hexdigest(),
            hashlib.sha256(self.log).hexdigest(), "challenge-nonce", 200,
        )
        self.keys = {
            "qa": TrustedKey(self.scope.company_id, "reviewer", "independent_qa", 250, b"a" * 32),
            "owner": TrustedKey(self.scope.company_id, "owner", "owner_review", 250, b"b" * 32),
        }

    def verify(self, *, manifest=None, path=None, registry=..., signing_keys=None, artifact=None):
        manifest = self.manifest if manifest is None else manifest
        path = self.store if path is None else path
        registry = self.keys if registry is ... else registry
        signing_keys = self.keys if signing_keys is None else signing_keys

        def sign(key_id):
            key = signing_keys[key_id]
            message = attestation_payload(manifest.digest(), key_id, key.role, 180)
            return Attestation(key_id, 180, hmac.digest(key.secret, message, "sha256").hex())

        verifier = EvidenceVerifier(
            expected_scope=self.scope, registry=registry,
            replay_store=SQLiteReviewReplayStore(path), clock=lambda: 100,
        )
        return verifier.verify(
            manifest, deliverable=self.artifact if artifact is None else artifact, test_log=self.log,
            qa=sign("qa"), owner=sign("owner"),
        )

    def assert_review_only(self, receipt):
        self.assertEqual(receipt.status, "verified_for_owner_review")
        self.assertIs(receipt.release_authorized, False)

    def assert_rehearsal_denies_release(self, report):
        self.assertIs(report["release_authorized"], False)
        self.assertIs(report["external_actions_performed"], False)
        self.assertIs(report["occ"]["execution_authorized"], False)
        self.assertEqual(report["private_audit"][-1]["status"], "denied")

    def crash_writer(self, *, commit):
        # Kill a separate process while its transaction is open or immediately
        # after COMMIT. The parent then opens a fresh verifier connection.
        script = """
import os, sqlite3, sys
db = sqlite3.connect(sys.argv[1], isolation_level=None)
db.execute("PRAGMA synchronous=FULL")
db.execute("BEGIN IMMEDIATE")
db.execute("INSERT INTO evidence_review_replay VALUES (?, ?, ?, ?)", (*sys.argv[2:5], 100))
if sys.argv[5] == "commit":
    db.execute("COMMIT")
os._exit(71)
"""
        subprocess.run(
            [sys.executable, "-c", script, str(self.store), self.scope.company_id,
             self.manifest.nonce, self.manifest.digest(), "commit" if commit else "pending"],
            check=False, timeout=10, capture_output=True,
        ).check_returncode()

    def test_crash_before_commit_drops_unfinished_nonce_claim(self):
        with self.assertRaises(subprocess.CalledProcessError) as error:
            self.crash_writer(commit=False)
        self.assertEqual(error.exception.returncode, 71)
        self.assert_review_only(self.verify())

    def test_crash_after_commit_preserves_nonce_claim_on_reopen(self):
        with self.assertRaises(subprocess.CalledProcessError) as error:
            self.crash_writer(commit=True)
        self.assertEqual(error.exception.returncode, 71)
        with self.assertRaisesRegex(VerificationBlocked, "replay_conflict"):
            self.verify()

    def test_stale_trust_snapshot_can_reinstate_revoked_signer_without_granting_release(self):
        current = {**self.keys, "qa": replace(self.keys["qa"], revoked=True)}
        with self.assertRaisesRegex(VerificationBlocked, "untrusted_attestation_key"):
            self.verify(registry=current)
        # An old but internally consistent registry is indistinguishable to
        # this prototype without a trusted monotonic registry version.
        self.assert_review_only(self.verify(registry=self.keys))

    def test_stale_store_clone_allows_repeat_review_without_granting_release(self):
        clone = self.root / "stale-clone.sqlite"
        shutil.copyfile(self.store, clone)
        initial = self.verify()
        with self.assertRaisesRegex(VerificationBlocked, "replay_conflict"):
            self.verify()
        repeated = self.verify(path=clone)
        self.assert_review_only(initial)
        self.assert_review_only(repeated)
        self.assertEqual(initial.manifest_sha256, repeated.manifest_sha256)
        # #38 catches in-run rollback via an external-to-the-database checkpoint.
        self.assert_rehearsal_denies_release(run_rehearsal("snapshot_rollback"))

    def test_unavailable_revoked_expired_or_compromised_review_authority(self):
        with self.assertRaisesRegex(VerificationBlocked, "trust_registry_unavailable"):
            self.verify(registry=None)
        for key_id, change in (
            ("qa", {"revoked": True}), ("owner", {"expires_at": 100}),
            ("qa", {"principal_id": "owner"}), ("owner", {"secret": self.keys["qa"].secret}),
        ):
            with self.subTest(key_id=key_id, change=tuple(change)), self.assertRaises(VerificationBlocked):
                altered = {**self.keys, key_id: replace(self.keys[key_id], **change)}
                self.verify(registry=altered, signing_keys=altered)
        with self.assertRaisesRegex(VerificationBlocked, "replay_store_unavailable"):
            self.verify(path=self.root / "missing.sqlite")

    def test_manifest_artifact_recipient_and_policy_substitution_are_blocked(self):
        with self.assertRaisesRegex(VerificationBlocked, "deliverable_digest_mismatch"):
            self.verify(artifact=b"altered report")
        for field, value in (
            ("recipient", "wrong-recipient"), ("company_id", "other-company"),
            ("policy_version", "policy-v1"), ("source_commit", "c" * 40),
        ):
            with self.subTest(field=field), self.assertRaisesRegex(VerificationBlocked, "scope"):
                changed = replace(self.scope, **{field: value})
                self.verify(manifest=replace(self.manifest, scope=changed))
        self.assert_review_only(self.verify())

    def test_corrupted_or_missing_rehearsal_audit_is_outside_verifier_trust(self):
        rehearsal = run_rehearsal()
        events = rehearsal["private_audit"]
        for nonce, challenged_audit in (
            ("audit-missing", None),
            ("audit-corrupt", [*events[:-1], {"stage": "external_delivery", "status": "allowed"}]),
        ):
            with self.subTest(nonce=nonce):
                audit_path = self.root / "local-audit.json"
                if challenged_audit is None:
                    self.assertFalse(audit_path.exists())
                else:
                    audit_path.write_text(json.dumps(challenged_audit))
                # A rehearsal event list has no independently sealed chain.
                # Local file absence or mutation is invisible to this verifier.
                self.assert_review_only(self.verify(manifest=replace(self.manifest, nonce=nonce)))
        self.assert_rehearsal_denies_release(rehearsal)

    def test_occ_rejects_receipt_status_and_drops_contaminating_fields(self):
        receipt = self.verify()
        with self.assertRaisesRegex(ValueError, "unsupported decision status"):
            summarize([asdict(receipt)])
        public = summarize([{
            "status": "checklist_complete_unverified",
            "manifest_sha256": receipt.manifest_sha256,
            "company_id": self.scope.company_id,
            "recipient": self.scope.recipient,
            "private": {"audit": "sensitive-fictional-payload"},
            "release_authorized": True,
        }])
        encoded = json.dumps(public)
        for value in (
            receipt.manifest_sha256, self.scope.company_id, self.scope.recipient,
            "sensitive-fictional-payload", "release_authorized",
        ):
            self.assertNotIn(value, encoded)
        self.assertIs(public["execution_authorized"], False)
        self.assertIs(public["external_actions_performed"], False)

"""Offline verification fixtures. All IDs, artifacts and HMAC keys are fictional."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict, replace
import hashlib
import hmac
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest

from evidence_verifier import (
    Attestation, EvidenceManifest, EvidenceVerifier, ReviewScope, SQLiteReviewReplayStore,
    TrustedKey, VerificationBlocked, attestation_payload,
)


class EvidenceVerifierTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "replay.sqlite"
        with closing(sqlite3.connect(self.path)) as db:
            db.executescript(Path(__file__).with_name("evidence_verifier_replay.sql").read_text())
        self.scope = ReviewScope(
            "aevora_ai", "fixture-opportunity", "a" * 40, "fixture-recipient",
            "fixture-channel", "policy-1", "producer",
        )
        self.deliverable = b"synthetic deliverable"
        self.test_log = b"synthetic test evidence"
        self.manifest = EvidenceManifest(
            self.scope, hashlib.sha256(self.deliverable).hexdigest(),
            hashlib.sha256(self.test_log).hexdigest(), "fixture-nonce", 150,
        )
        self.registry = {
            "reviewer-key": TrustedKey("aevora_ai", "reviewer", "independent_qa", 200, b"q" * 32),
            "owner-key": TrustedKey("aevora_ai", "owner", "owner_review", 200, b"o" * 32),
        }

    def signed(self, key_id, manifest, expiry=140):
        key = self.registry[key_id]
        payload = attestation_payload(manifest.digest(), key_id, key.role, expiry)
        return Attestation(key_id, expiry, hmac.digest(key.secret, payload, "sha256").hex())

    def verifier(self, **overrides):
        settings = dict(
            expected_scope=self.scope, registry=self.registry,
            replay_store=SQLiteReviewReplayStore(self.path), clock=lambda: 110,
        )
        settings.update(overrides)
        return EvidenceVerifier(**settings)

    def verify(self, *, verifier=None, manifest=None, **overrides):
        manifest = self.manifest if manifest is None else manifest
        settings = dict(
            deliverable=self.deliverable, test_log=self.test_log,
            qa=self.signed("reviewer-key", manifest), owner=self.signed("owner-key", manifest),
        )
        settings.update(overrides)
        return (self.verifier() if verifier is None else verifier).verify(manifest, **settings)

    def test_receipt_never_authorizes_release(self):
        self.assertEqual(asdict(self.verify()), {
            "manifest_sha256": self.manifest.digest(),
            "status": "verified_for_owner_review",
            "release_authorized": False,
        })

    def test_artifact_substitution_does_not_consume_nonce(self):
        for field in ("deliverable", "test_log"):
            with self.subTest(field=field), self.assertRaisesRegex(VerificationBlocked, field):
                self.verify(**{field: b"substitution"})
        self.verify()

    def test_valid_signatures_cannot_override_expected_scope(self):
        for field, value in (
            ("company_id", "trading_technology"), ("recipient", "other"), ("channel", "other"),
            ("policy_version", "v2"), ("opportunity_id", "changed"), ("source_commit", "b" * 40),
        ):
            with self.subTest(field=field), self.assertRaisesRegex(VerificationBlocked, "scope"):
                self.verify(manifest=replace(self.manifest, scope=replace(self.scope, **{field: value})))

    def test_self_review_shared_principal_and_shared_credentials_fail(self):
        original = self.registry["reviewer-key"]
        for changed in (
            replace(original, principal_id="Producer"), replace(original, principal_id="owner"),
            replace(original, secret=self.registry["owner-key"].secret),
        ):
            with self.subTest(changed=changed), self.assertRaisesRegex(
                VerificationBlocked, "non_independent|shared_review",
            ):
                self.registry["reviewer-key"] = changed
                self.verify()

    def test_unknown_revoked_or_wrong_company_key_fails(self):
        qa = self.signed("reviewer-key", self.manifest)
        for changed in (
            None, replace(self.registry["reviewer-key"], revoked=True),
            replace(self.registry["reviewer-key"], expires_at=110),
            replace(self.registry["reviewer-key"], company_id="trading_technology"),
        ):
            with self.subTest(changed=changed), self.assertRaisesRegex(VerificationBlocked, "untrusted"):
                self.verify(verifier=self.verifier(registry={**self.registry, "reviewer-key": changed}), qa=qa)

    def test_unavailable_registry_and_replay_store_fail_closed(self):
        for name in ("registry", "replay_store"):
            with self.subTest(name=name), self.assertRaisesRegex(VerificationBlocked, "unavailable"):
                self.verify(verifier=self.verifier(**{name: None}))
        self.path.unlink()
        with self.assertRaisesRegex(VerificationBlocked, "replay_store_unavailable"):
            self.verify()
        self.assertFalse(self.path.exists())

    def test_store_with_no_uniqueness_constraint_fails_closed(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DROP TABLE evidence_review_replay")
            db.execute(
                "CREATE TABLE evidence_review_replay "
                "(company_id TEXT, nonce TEXT, manifest_sha256 TEXT, verified_at INTEGER)"
            )
        with self.assertRaisesRegex(VerificationBlocked, "replay_store_unavailable"):
            self.verify()

    def test_expiry_and_wrong_purpose_are_rejected(self):
        with self.assertRaisesRegex(VerificationBlocked, "expired_manifest"):
            self.verify(verifier=self.verifier(clock=lambda: 150))
        with self.assertRaisesRegex(VerificationBlocked, "attestation_expiry"):
            self.verify(owner=self.signed("owner-key", self.manifest, expiry=110))
        with self.assertRaisesRegex(VerificationBlocked, "attestation_expiry"):
            self.verify(owner=self.signed("owner-key", self.manifest, expiry=151))
        key = self.registry["owner-key"]
        wrong_role = attestation_payload(self.manifest.digest(), "owner-key", "release", 140)
        with self.assertRaisesRegex(VerificationBlocked, "signature"):
            self.verify(owner=Attestation("owner-key", 140, hmac.digest(key.secret, wrong_role, "sha256").hex()))

    def test_cross_manifest_attestation_and_invalid_signature_are_rejected(self):
        other = replace(self.manifest, nonce="other-nonce")
        with self.assertRaisesRegex(VerificationBlocked, "signature"):
            self.verify(owner=self.signed("owner-key", other))
        with self.assertRaisesRegex(VerificationBlocked, "signature"):
            self.verify(qa=Attestation("reviewer-key", 140, "a" * 64))

    def test_replay_persists_across_handles_even_if_manifest_changes(self):
        self.verify()
        with self.assertRaisesRegex(VerificationBlocked, "replay_conflict"):
            self.verify(manifest=replace(self.manifest, expires_at=151))

    def test_concurrent_handles_produce_at_most_one_receipt(self):
        barrier = Barrier(2, timeout=5)

        def attempt():
            verifier = self.verifier()
            barrier.wait()
            try:
                return self.verify(verifier=verifier).status
            except VerificationBlocked as exc:
                return str(exc)

        with ThreadPoolExecutor(max_workers=2) as workers:
            results = [workers.submit(attempt), workers.submit(attempt)]
            self.assertCountEqual([result.result() for result in results], (
                "verified_for_owner_review", "replay_conflict",
            ))

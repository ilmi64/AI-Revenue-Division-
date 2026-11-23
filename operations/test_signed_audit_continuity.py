"""Synthetic Ed25519 continuity challenge against the pinned anchored rehearsal."""
from dataclasses import replace
import json
import unittest
from unittest.mock import patch

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    Ed25519PrivateKey = None

from anchored_evidence_verifier import advance_trust, read_anchored_checkpoint
from evidence_verifier import VerificationBlocked
from occ_summary import summarize
from signed_audit_continuity import (
    ContinuityCheckpoint, ContinuityKey, CurrentAuthority, SignedAuditReceipt,
    SignedCheckpoint, SignedContinuityVerifier, audit_receipt_payload,
    checkpoint_fingerprint, checkpoint_payload,
)
import test_anchored_evidence_verifier as anchored_fixtures


class FixtureAuthority:
    """Independent in-process pin for this run, outside both SQLite files."""

    def __init__(self, state):
        self.state = state

    def current(self, company_id):
        if company_id != self.state.company_id:
            raise OSError("authority partition unavailable")
        return self.state


@unittest.skipIf(Ed25519PrivateKey is None, "Ed25519 fixture dependency unavailable")
class SignedAuditContinuityTests(unittest.TestCase):
    def setUp(self):
        fixture = anchored_fixtures.AnchoredEvidenceVerifierTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.company = fixture.scope.company_id
        self.checkpoint_private = Ed25519PrivateKey.from_private_bytes(b"c" * 32)
        self.audit_private = Ed25519PrivateKey.from_private_bytes(b"a" * 32)
        self.keys = {
            "checkpoint": ContinuityKey(
                self.company, "checkpoint-operator", "checkpoint",
                self.checkpoint_private.public_key().public_bytes_raw(), 300,
            ),
            "audit": ContinuityKey(
                self.company, "independent-auditor", "audit",
                self.audit_private.public_key().public_bytes_raw(), 300,
            ),
        }

    def provision_proof(self, review, *, expires_at=200):
        state = read_anchored_checkpoint(self.fixture.anchor, self.fixture.audit, self.company, review)
        checkpoint = ContinuityCheckpoint(self.company, state, 95, expires_at)
        key_id = "checkpoint"
        pin = checkpoint_fingerprint(checkpoint, key_id)
        signature = self.checkpoint_private.sign(checkpoint_payload(checkpoint, key_id))
        unsigned = SignedAuditReceipt(self.company, pin, review, "audit", b"")
        receipt = replace(unsigned, signature=self.audit_private.sign(audit_receipt_payload(unsigned)))
        return SignedCheckpoint(checkpoint, key_id, signature), receipt, FixtureAuthority(
            CurrentAuthority(self.company, pin, self.keys),
        )

    def verifier(self, authority, *, now=100, company=None):
        return SignedContinuityVerifier(
            company_id=self.company if company is None else company,
            anchor_path=self.fixture.anchor, audit_path=self.fixture.audit,
            authority=authority, clock=lambda: now,
        )

    def test_valid_proof_is_private_review_only(self):
        checkpoint, receipt, authority = self.provision_proof(self.fixture.verify())
        self.assertIsNone(self.verifier(authority).verify(checkpoint, receipt))
        self.assertIs(receipt.release_authorized, False)
        self.assertIs(receipt.review.release_authorized, False)

    def test_release_claim_and_occ_private_proof_contamination_are_denied(self):
        checkpoint, receipt, authority = self.provision_proof(self.fixture.verify())
        forged = replace(receipt)
        object.__setattr__(forged, "release_authorized", True)
        object.__setattr__(forged, "signature", self.audit_private.sign(audit_receipt_payload(forged)))
        with self.assertRaisesRegex(VerificationBlocked, "invalid_continuity_scope"):
            self.verifier(authority).verify(checkpoint, forged)
        with self.assertRaisesRegex(ValueError, "unsupported decision status"):
            summarize([{"status": receipt.review.status}])
        summary = summarize([{
            "status": "checklist_complete_unverified", "proof": receipt,
            "company_id": receipt.company_id, "release_authorized": True,
        }])
        self.assertIs(summary["execution_authorized"], False)
        self.assertNotIn(receipt.checkpoint_sha256, json.dumps(summary))
        self.assertNotIn("proof", summary)

    def test_signatures_and_role_domain_cannot_be_substituted(self):
        checkpoint, receipt, authority = self.provision_proof(self.fixture.verify())
        verifier = self.verifier(authority)
        for altered_checkpoint, altered_receipt in (
            (replace(checkpoint, signature=b"x" * 64), receipt),
            (checkpoint, replace(receipt, signature=checkpoint.signature)),
            (checkpoint, replace(receipt, signature=self.audit_private.sign(
                checkpoint_payload(checkpoint.checkpoint, checkpoint.key_id),
            ))),
            (checkpoint, replace(receipt, review=replace(receipt.review, audit_sha256="e" * 64))),
        ):
            with self.subTest(), self.assertRaisesRegex(VerificationBlocked, "invalid_continuity_signature"):
                verifier.verify(altered_checkpoint, altered_receipt)

    def test_expiry_missing_authority_and_unavailable_signature_backend_block(self):
        checkpoint, receipt, authority = self.provision_proof(self.fixture.verify())
        with self.assertRaisesRegex(VerificationBlocked, "checkpoint_time"):
            self.verifier(authority, now=200).verify(checkpoint, receipt)
        with self.assertRaisesRegex(VerificationBlocked, "authority_unavailable"):
            self.verifier(None).verify(checkpoint, receipt)
        with patch.dict("sys.modules", {"cryptography.hazmat.primitives.asymmetric.ed25519": None}):
            with self.assertRaisesRegex(VerificationBlocked, "ed25519_backend_unavailable"):
                self.verifier(authority).verify(checkpoint, receipt)

    def test_revoked_keys_and_collapsed_principals_block(self):
        checkpoint, receipt, authority = self.provision_proof(self.fixture.verify())
        for key_id in self.keys:
            state = replace(authority.state, keys={**self.keys, key_id: replace(self.keys[key_id], revoked=True)})
            with self.subTest(key_id=key_id), self.assertRaisesRegex(VerificationBlocked, "untrusted_continuity_key"):
                self.verifier(FixtureAuthority(state)).verify(checkpoint, receipt)
        collapsed = replace(self.keys["audit"], principal_id=self.keys["checkpoint"].principal_id)
        state = replace(authority.state, keys={**self.keys, "audit": collapsed})
        with self.assertRaisesRegex(VerificationBlocked, "non_independent"):
            self.verifier(FixtureAuthority(state)).verify(checkpoint, receipt)

    def test_old_signed_epoch_does_not_match_local_trust_after_advancement(self):
        checkpoint, receipt, authority = self.provision_proof(self.fixture.verify())
        advance_trust(
            self.fixture.anchor, self.company, expected_epoch=2, new_epoch=3,
            policy=self.fixture.scope.policy_version, registry=self.fixture.registry,
        )
        with self.assertRaisesRegex(VerificationBlocked, "local_checkpoint_divergence"):
            self.verifier(authority).verify(checkpoint, receipt)

    def test_coordinated_local_rollback_cannot_reinstate_old_signed_checkpoint(self):
        old = self.provision_proof(self.fixture.verify())
        old_anchor = self.fixture.anchor.read_bytes()
        old_audit = self.fixture.audit.read_bytes()
        second = self.fixture.verify(manifest=replace(self.fixture.manifest, nonce="second"))
        current_checkpoint, current_receipt, authority = self.provision_proof(second)

        self.fixture.anchor.write_bytes(old_anchor)
        self.fixture.audit.write_bytes(old_audit)
        verifier = self.verifier(authority)
        with self.assertRaisesRegex(VerificationBlocked, "checkpoint_not_current"):
            verifier.verify(old[0], old[1])
        with self.assertRaisesRegex(VerificationBlocked, "audit_receipt_not_anchored"):
            verifier.verify(current_checkpoint, current_receipt)

    def test_torn_pair_and_recovery_check_preserve_replay_denial(self):
        earlier = self.fixture.anchor.read_bytes()
        checkpoint, receipt, authority = self.provision_proof(self.fixture.verify())
        approved_backup = self.fixture.anchor.read_bytes()
        # Reproduce the persisted pair left by the real process-exit fixture
        # test in test_anchored_evidence_verifier.
        self.fixture.anchor.write_bytes(earlier)
        verifier = self.verifier(authority)
        with self.assertRaisesRegex(VerificationBlocked, "audit_anchor_divergence"):
            verifier.verify(checkpoint, receipt)
        # Restoring known matching bytes simulates independently reviewed
        # recovery. The verifier does not repair or reseed either store.
        self.fixture.anchor.write_bytes(approved_backup)
        verifier.verify(checkpoint, receipt)
        with self.assertRaisesRegex(VerificationBlocked, "replay_conflict"):
            self.fixture.verify()

    def test_cross_company_and_corrupted_history_fail_closed(self):
        checkpoint, receipt, authority = self.provision_proof(self.fixture.verify())
        with self.assertRaisesRegex(VerificationBlocked, "authority_or_clock_unavailable"):
            self.verifier(authority, company="other-company").verify(checkpoint, receipt)
        with self.assertRaisesRegex(VerificationBlocked, "invalid_continuity_scope"):
            self.verifier(authority).verify(checkpoint, replace(receipt, company_id="other-company"))
        self.fixture.change(self.fixture.audit, "UPDATE review_audit SET nonce='modified'")
        with self.assertRaisesRegex(VerificationBlocked, "audit_chain_invalid"):
            self.verifier(authority).verify(checkpoint, receipt)

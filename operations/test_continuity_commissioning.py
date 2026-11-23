"""Synthetic in-process commissioning custody, lifecycle and recovery evidence."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from threading import Barrier, Lock
import unittest

from continuity_commissioning import (
    CommissioningRequest, CommissioningReviewer, CustodyObservation,
    ExternalReview, review_payload,
)
from evidence_verifier import VerificationBlocked
from occ_summary import summarize
from signed_audit_continuity import ContinuityKey, CurrentAuthority
import test_signed_audit_continuity as signed_fixtures


class SyntheticCommissioningAuthority:
    """Lock-backed test double. It provides no production custody or durability."""

    def __init__(self, observation):
        self.current = observation
        self.records = {}
        self.seen_bundles = set()
        self.lock = Lock()
        self.barrier = None
        self.sink_clock = 100
        self.replace_before_record = None

    def observe(self, company_id):
        with self.lock:
            if self.current.authority.company_id != company_id:
                raise OSError("synthetic company compartment unavailable")
            return self.current

    def record_if_current(self, observation, evidence):
        if self.barrier is not None:
            self.barrier.wait()
        with self.lock:
            self.seen_bundles.add(evidence.approval_bundle_sha256)
            if self.replace_before_record is not None:
                self.current = self.replace_before_record
            request = evidence.request
            key = (request.company_id, request.checkpoint_sha256, request.request_id)
            if (
                observation != self.current or key in self.records
                or not evidence.checked_at <= self.sink_clock < evidence.valid_until
                or not observation.observed_at <= self.sink_clock < observation.expires_at
            ):
                return False
            self.records[key] = evidence
            return True


@unittest.skipIf(signed_fixtures.Ed25519PrivateKey is None, "Ed25519 fixture dependency unavailable")
class ContinuityCommissioningTests(unittest.TestCase):
    def setUp(self):
        fixture = signed_fixtures.SignedAuditContinuityTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.company = fixture.company
        backend = signed_fixtures.Ed25519PrivateKey
        self.external_private = {
            "external-audit": backend.from_private_bytes(b"d" * 32),
            "external-recovery": backend.from_private_bytes(b"r" * 32),
        }
        self.checkpoint, self.proof, observation = self.commission_fixture(fixture.fixture.verify())
        self.authority = SyntheticCommissioningAuthority(observation)

    def commission_fixture(self, receipt, *, custody_revision=11, signer_revision=23):
        checkpoint, proof, continuity = self.fixture.provision_proof(receipt)
        keys = {
            **continuity.state.keys,
            **{
                key_id: ContinuityKey(
                    self.company, key_id, key_id.replace("-", "_"),
                    secret.public_key().public_bytes_raw(), 300,
                )
                for key_id, secret in self.external_private.items()
            },
        }
        observation = CustodyObservation(
            "independent-custodian", "signer-registrar", custody_revision, signer_revision, 95, 130,
            CurrentAuthority(self.company, proof.checkpoint_sha256, keys),
        )
        return checkpoint, proof, observation

    def reviewer(self, authority, **overrides):
        local = self.fixture.fixture
        settings = dict(
            company_id=self.company, custodian_id="independent-custodian",
            signer_operator_id="signer-registrar", anchor_path=local.anchor, audit_path=local.audit,
            authority=authority, clock=lambda: 100, maximum_observation_age=10,
        )
        settings.update(overrides)
        return CommissioningReviewer(**settings)

    def request(self, observation=None, proof=None):
        observation = self.authority.current if observation is None else observation
        proof = self.proof if proof is None else proof
        return CommissioningRequest(
            self.company, "recovery-review-fixture", proof.checkpoint_sha256, proof.review.manifest_sha256,
            observation.custody_revision, observation.signer_revision,
        )

    def signed_review(self, request, key_id, *, evidence="a" * 64, expiry=125, disposition="accepted"):
        unsigned = ExternalReview(key_id, key_id.replace("-", "_"), evidence, disposition, expiry, b"")
        sig = self.external_private[key_id].sign(review_payload(request, unsigned))
        return replace(unsigned, signature=sig)

    def record(self, *, proof=None, checkpoint=None, request=None, audit=None, recovery=None,
               reviewer=None, evidence="a" * 64):
        request = self.request() if request is None else request
        checkpoint = self.checkpoint if checkpoint is None else checkpoint
        proof = self.proof if proof is None else proof
        return (self.reviewer(self.authority) if reviewer is None else reviewer).record(
            request, checkpoint, proof,
            audit=self.signed_review(request, "external-audit", evidence=evidence) if audit is None else audit,
            recovery=self.signed_review(request, "external-recovery") if recovery is None else recovery,
        )

    def test_private_review_records_once_and_cannot_authorize_delivery_or_occ(self):
        receipt = self.record()
        self.assertEqual(receipt.status, "synthetic_commissioning_evidence_recorded")
        self.assertIs(receipt.release_authorized, False)
        with self.assertRaisesRegex(VerificationBlocked, "already_recorded"):
            self.record()
        with self.assertRaisesRegex(ValueError, "unsupported decision"):
            summarize([{"status": receipt.status}])
        aggregate = summarize([{"status": "checklist_complete_unverified", "private": receipt}])
        self.assertNotIn(receipt.approval_bundle_sha256, json.dumps(aggregate))
        self.assertIs(aggregate["execution_authorized"], False)

    def test_missing_unavailable_wrong_or_stale_custody_blocks(self):
        with self.assertRaisesRegex(VerificationBlocked, "custody_unavailable"):
            self.record(reviewer=self.reviewer(None))
        original = self.authority.current
        for current, reason in (
            (replace(original, authority=replace(original.authority, company_id="other-company")), "custody_unavailable"),
            (replace(original, custodian_id="unprovisioned"), "scope_mismatch"),
            (replace(original, signer_operator_id="unprovisioned"), "scope_mismatch"),
            (replace(original, observed_at=89), "stale_commissioning_custody"),
            (replace(original, expires_at=100), "stale_commissioning_custody"),
        ):
            with self.subTest(reason=reason), self.assertRaisesRegex(VerificationBlocked, reason):
                self.authority.current = current
                self.record()
        self.assertFalse(self.authority.records)

    def test_revoked_or_stale_keys_and_role_collapse_block(self):
        original = self.authority.current
        for change, reason in (
            ({"revoked": True}, "untrusted_continuity_key"),
            ({"expires_at": 100}, "untrusted_continuity_key"),
            ({"principal_id": original.custodian_id}, "roles_not_independent"),
        ):
            changed = replace(original.authority.keys["external-audit"], **change)
            self.authority.current = replace(
                original, authority=replace(original.authority, keys={**original.authority.keys, "external-audit": changed}),
            )
            with self.subTest(change=change), self.assertRaisesRegex(VerificationBlocked, reason):
                self.record()

    def test_competing_distinct_signed_approvals_record_at_most_once(self):
        self.authority.barrier = Barrier(2, timeout=5)

        def attempt(evidence_sha256):
            try:
                return self.record(evidence=evidence_sha256).release_authorized
            except VerificationBlocked as exc:
                return str(exc)

        with ThreadPoolExecutor(max_workers=2) as pool:
            attempts = [pool.submit(attempt, digest * 64) for digest in ("a", "b")]
            self.assertCountEqual([x.result() for x in attempts], (
                False, "commissioning_state_changed_or_already_recorded",
            ))
        self.assertEqual(len(self.authority.seen_bundles), 2)
        self.assertEqual(len(self.authority.records), 1)

    def test_state_changes_or_review_expires_before_atomic_record(self):
        current = self.authority.current
        self.authority.replace_before_record = replace(current, signer_revision=current.signer_revision + 1)
        with self.assertRaisesRegex(VerificationBlocked, "state_changed"):
            self.record(request=self.request(current))
        self.authority.current = current
        self.authority.replace_before_record = None
        self.authority.sink_clock = 105
        short = self.signed_review(self.request(), "external-recovery", expiry=105)
        with self.assertRaisesRegex(VerificationBlocked, "state_changed"):
            self.record(recovery=short)
        self.assertFalse(self.authority.records)

    def test_scope_substitution_and_missing_or_rejected_recovery_review(self):
        for field, value in (
            ("company_id", "other-company"), ("manifest_sha256", "e" * 64),
            ("checkpoint_sha256", "e" * 64), ("custody_revision", 10), ("signer_revision", 22),
        ):
            with self.subTest(field=field), self.assertRaisesRegex(VerificationBlocked, "request_scope_mismatch"):
                self.record(request=replace(self.request(), **{field: value}))
        prior = self.signed_review(self.request(), "external-recovery")
        with self.assertRaisesRegex(VerificationBlocked, "invalid_continuity_signature"):
            self.record(request=replace(self.request(), request_id="another-request"), recovery=prior)
        with self.assertRaisesRegex(VerificationBlocked, "external_review_missing_or_expired"):
            self.reviewer(self.authority).record(
                self.request(), self.checkpoint, self.proof,
                audit=self.signed_review(self.request(), "external-audit"), recovery=None,
            )
        rejected = self.signed_review(self.request(), "external-recovery", disposition="rejected")
        with self.assertRaisesRegex(VerificationBlocked, "external_review_missing_or_expired"):
            self.record(recovery=rejected)

    def test_coordinated_local_rollback_refused_with_current_custody(self):
        local = self.fixture.fixture
        old_anchor, old_audit = local.anchor.read_bytes(), local.audit.read_bytes()
        old_request = self.request()
        review = local.verify(manifest=replace(local.manifest, nonce="second"))
        current_checkpoint, current_proof, current = self.commission_fixture(review, custody_revision=12)
        self.authority.current = current
        local.anchor.write_bytes(old_anchor)
        local.audit.write_bytes(old_audit)
        with self.assertRaisesRegex(VerificationBlocked, "commissioning_request_scope_mismatch"):
            self.record(request=old_request)
        with self.assertRaisesRegex(VerificationBlocked, "audit_receipt_not_anchored"):
            self.record(
                checkpoint=current_checkpoint, proof=current_proof, request=self.request(current, current_proof),
            )
        self.assertFalse(self.authority.records)

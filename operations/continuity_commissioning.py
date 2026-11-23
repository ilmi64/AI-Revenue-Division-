"""Offline commissioning evidence boundary for private Aevora continuity."""
from dataclasses import asdict, dataclass, field
import hashlib
from pathlib import Path
import re
from types import MappingProxyType
from typing import Callable, Protocol

from evidence_verifier import VerificationBlocked
from signed_audit_continuity import (
    CurrentAuthority, SignedAuditReceipt, SignedCheckpoint, SignedContinuityVerifier,
    _canonical, _key, _verify_signature,
)


@dataclass(frozen=True)
class CustodyObservation:
    custodian_id: str
    signer_operator_id: str
    custody_revision: int
    signer_revision: int
    observed_at: int
    expires_at: int
    authority: CurrentAuthority


@dataclass(frozen=True)
class CommissioningRequest:
    company_id: str
    request_id: str
    checkpoint_sha256: str
    manifest_sha256: str
    custody_revision: int
    signer_revision: int


@dataclass(frozen=True)
class ExternalReview:
    key_id: str
    purpose: str
    evidence_sha256: str
    disposition: str
    expires_at: int
    signature: bytes


@dataclass(frozen=True)
class CommissioningEvidence:
    request: CommissioningRequest
    approval_bundle_sha256: str
    checked_at: int
    valid_until: int
    status: str = field(default="synthetic_commissioning_evidence_recorded", init=False)
    release_authorized: bool = field(default=False, init=False)


class CommissioningAuthority(Protocol):
    """Deployment-controlled custody, signer lifecycle and evidence sink.

    observe must return the current company-local pin and independently
    administered signer lifecycle, with authenticated identity, monotonic
    revisions and bounded freshness. There is no production implementation.

    record_if_current must atomically verify both current revisions and the
    entire observation and evidence validity under its own trusted clock, then
    write at most one evidence record per company/checkpoint/request.
    A timeout, stale observation, outage or duplicate cannot report success.
    """

    def observe(self, company_id: str) -> CustodyObservation: ...

    def record_if_current(self, observation: CustodyObservation, evidence: CommissioningEvidence) -> bool: ...


def review_payload(request: CommissioningRequest, review: ExternalReview) -> bytes:
    return _canonical({
        "purpose": "aevora-external-commissioning-review-v1",
        "request": asdict(request),
        "key_id": review.key_id,
        "review_purpose": review.purpose,
        "evidence_sha256": review.evidence_sha256,
        "disposition": review.disposition,
        "expires_at": review.expires_at,
    })


def _sha(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


@dataclass(frozen=True)
class _BoundAuthority:
    snapshot: CurrentAuthority

    def current(self, company_id: str) -> CurrentAuthority:
        if company_id != self.snapshot.company_id:
            raise VerificationBlocked("commissioning_authority_company_mismatch")
        return self.snapshot


class CommissioningReviewer:
    """Record a synthetic evidence bundle, with no operational approval."""

    def __init__(
        self, *, company_id: str, custodian_id: str, signer_operator_id: str,
        anchor_path: Path, audit_path: Path, authority: CommissioningAuthority | None,
        clock: Callable[[], int], maximum_observation_age: int,
    ):
        self.company_id = company_id
        self.custodian_id = custodian_id
        self.signer_operator_id = signer_operator_id
        self.anchor_path = anchor_path
        self.audit_path = audit_path
        self.authority = authority
        self.clock = clock
        self.maximum_observation_age = maximum_observation_age

    def _current(self, now: int) -> CustodyObservation:
        if self.authority is None:
            raise VerificationBlocked("commissioning_custody_unavailable")
        try:
            observed = self.authority.observe(self.company_id)
        except (OSError, RuntimeError) as exc:
            raise VerificationBlocked("commissioning_custody_unavailable") from exc
        if (
            not isinstance(observed, CustodyObservation) or not isinstance(observed.authority, CurrentAuthority)
            or observed.authority.company_id != self.company_id
            or observed.custodian_id != self.custodian_id or observed.signer_operator_id != self.signer_operator_id
            or not isinstance(observed.custodian_id, str) or not observed.custodian_id.strip()
            or not isinstance(observed.signer_operator_id, str) or not observed.signer_operator_id.strip()
            or observed.custodian_id.casefold() == observed.signer_operator_id.casefold()
            or not _sha(observed.authority.checkpoint_sha256)
        ):
            raise VerificationBlocked("commissioning_custody_scope_mismatch")
        if (
            type(self.maximum_observation_age) is not int or self.maximum_observation_age <= 0
            or type(observed.observed_at) is not int or type(observed.expires_at) is not int
            or not 0 <= observed.observed_at <= now < observed.expires_at
            or now - observed.observed_at > self.maximum_observation_age
            or type(observed.custody_revision) is not int or observed.custody_revision <= 0
            or type(observed.signer_revision) is not int or observed.signer_revision <= 0
        ):
            raise VerificationBlocked("stale_commissioning_custody")
        try:
            keys = MappingProxyType(dict(observed.authority.keys))
        except (TypeError, ValueError, OSError, RuntimeError) as exc:
            raise VerificationBlocked("commissioning_signer_lifecycle_unavailable") from exc
        return CustodyObservation(
            observed.custodian_id, observed.signer_operator_id,
            observed.custody_revision, observed.signer_revision, observed.observed_at, observed.expires_at,
            CurrentAuthority(observed.authority.company_id, observed.authority.checkpoint_sha256, keys),
        )

    def _now(self) -> int:
        try:
            now = self.clock()
        except (OSError, RuntimeError) as exc:
            raise VerificationBlocked("commissioning_clock_unavailable") from exc
        if type(now) is not int or now < 0:
            raise VerificationBlocked("invalid_commissioning_time")
        return now

    def record(
        self, request: CommissioningRequest, checkpoint: SignedCheckpoint, proof: SignedAuditReceipt,
        *, audit: ExternalReview, recovery: ExternalReview,
    ) -> CommissioningEvidence:
        now = self._now()
        observation = self._current(now)
        current = observation.authority
        if (
            not isinstance(request, CommissioningRequest) or request.company_id != self.company_id
            or not isinstance(request.request_id, str) or not request.request_id.strip()
            or not isinstance(proof, SignedAuditReceipt)
            or request.checkpoint_sha256 != current.checkpoint_sha256
            or request.checkpoint_sha256 != proof.checkpoint_sha256 or not _sha(request.manifest_sha256)
            or type(request.custody_revision) is not int or type(request.signer_revision) is not int
            or request.custody_revision != observation.custody_revision
            or request.signer_revision != observation.signer_revision
        ):
            raise VerificationBlocked("commissioning_request_scope_mismatch")

        SignedContinuityVerifier(
            company_id=self.company_id, anchor_path=self.anchor_path, audit_path=self.audit_path,
            authority=_BoundAuthority(current), clock=lambda: now,
        ).verify(checkpoint, proof)
        if request.manifest_sha256 != proof.review.manifest_sha256:
            raise VerificationBlocked("commissioning_request_scope_mismatch")

        signers = [_key(current, checkpoint.key_id, "checkpoint", now), _key(current, proof.key_id, "audit", now)]
        signatures = []
        expiries = [observation.expires_at, checkpoint.checkpoint.expires_at]
        for purpose, review in (("external_audit", audit), ("external_recovery", recovery)):
            if (
                not isinstance(review, ExternalReview) or review.purpose != purpose
                or review.disposition != "accepted" or not _sha(review.evidence_sha256)
                or type(review.expires_at) is not int or now >= review.expires_at
            ):
                raise VerificationBlocked("external_review_missing_or_expired")
            key = _key(current, review.key_id, purpose, now)
            if review.expires_at > key.expires_at:
                raise VerificationBlocked("external_review_exceeds_key_lifetime")
            payload = review_payload(request, review)
            _verify_signature(key.public_key, review.signature, payload)
            signers.append(key)
            signatures.append({
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "signature_hex": review.signature.hex(),
            })
            expiries.append(review.expires_at)

        principals = {
            *(signer.principal_id.strip().casefold() for signer in signers),
            observation.custodian_id.strip().casefold(), observation.signer_operator_id.strip().casefold(),
        }
        if len(principals) != 6 or len({signer.public_key for signer in signers}) != 4:
            raise VerificationBlocked("commissioning_review_roles_not_independent")
        expiries.extend(signer.expires_at for signer in signers)
        checked_at = self._now()
        if (
            not now <= checked_at < min(expiries)
            or checked_at - observation.observed_at > self.maximum_observation_age
        ):
            raise VerificationBlocked("commissioning_authority_expired_during_review")
        expiries.append(observation.observed_at + self.maximum_observation_age + 1)
        evidence = CommissioningEvidence(
            request, hashlib.sha256(_canonical({"reviews": signatures})).hexdigest(),
            checked_at, min(expiries),
        )
        try:
            recorded = self.authority.record_if_current(observation, evidence)
        except (OSError, RuntimeError) as exc:
            raise VerificationBlocked("commissioning_evidence_sink_unavailable") from exc
        if recorded is not True:
            raise VerificationBlocked("commissioning_state_changed_or_already_recorded")
        return evidence

"""Offline Ed25519 proof for a private Aevora audit receipt and checkpoint."""
from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Callable, Mapping, Protocol

from anchored_evidence_verifier import AnchoredCheckpoint, AnchoredReviewReceipt, read_anchored_checkpoint
from evidence_verifier import VerificationBlocked


@dataclass(frozen=True)
class ContinuityCheckpoint:
    company_id: str
    state: AnchoredCheckpoint
    issued_at: int
    expires_at: int


@dataclass(frozen=True)
class SignedCheckpoint:
    checkpoint: ContinuityCheckpoint
    key_id: str
    signature: bytes


@dataclass(frozen=True)
class SignedAuditReceipt:
    company_id: str
    checkpoint_sha256: str
    review: AnchoredReviewReceipt
    key_id: str
    signature: bytes
    release_authorized: bool = field(default=False, init=False)


@dataclass(frozen=True)
class ContinuityKey:
    company_id: str
    principal_id: str
    purpose: str
    public_key: bytes
    expires_at: int
    revoked: bool = False


@dataclass(frozen=True)
class CurrentAuthority:
    company_id: str
    checkpoint_sha256: str
    keys: Mapping[str, ContinuityKey]


class ContinuityAuthority(Protocol):
    """Out-of-band source of current pins and revocation for a company.

    Provision current state independently of the applicant and both review
    databases. The implementation must protect it from rollback and report
    missing, stale or uncertain authority as unavailable.
    """

    def current(self, company_id: str) -> CurrentAuthority: ...


def _canonical(data: dict) -> bytes:
    return json.dumps(
        data, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"),
    ).encode("ascii")


def checkpoint_payload(checkpoint: ContinuityCheckpoint, key_id: str) -> bytes:
    return _canonical({
        "purpose": "aevora-independent-checkpoint-v1",
        "key_id": key_id,
        "checkpoint": asdict(checkpoint),
    })


def checkpoint_fingerprint(checkpoint: ContinuityCheckpoint, key_id: str) -> str:
    return hashlib.sha256(checkpoint_payload(checkpoint, key_id)).hexdigest()


def audit_receipt_payload(receipt: SignedAuditReceipt) -> bytes:
    return _canonical({
        "purpose": "aevora-private-audit-receipt-v1",
        "company_id": receipt.company_id,
        "checkpoint_sha256": receipt.checkpoint_sha256,
        "review": asdict(receipt.review),
        "key_id": receipt.key_id,
        "release_authorized": receipt.release_authorized,
    })


def _verify_signature(key: bytes, signature: bytes, payload: bytes) -> None:
    try:
        from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise VerificationBlocked("ed25519_backend_unavailable") from exc
    try:
        Ed25519PublicKey.from_public_bytes(key).verify(signature, payload)
    except UnsupportedAlgorithm as exc:
        raise VerificationBlocked("ed25519_backend_unavailable") from exc
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise VerificationBlocked("invalid_continuity_signature") from exc


def _key(authority: CurrentAuthority, key_id: str, purpose: str, now: int) -> ContinuityKey:
    if not isinstance(authority.keys, Mapping) or not isinstance(key_id, str):
        raise VerificationBlocked("invalid_continuity_authority")
    key = authority.keys.get(key_id)
    if (
        not isinstance(key, ContinuityKey) or key.company_id != authority.company_id
        or key.purpose != purpose or key.revoked is not False
        or not isinstance(key.principal_id, str) or not key.principal_id.strip()
        or type(key.expires_at) is not int or now >= key.expires_at
        or not isinstance(key.public_key, bytes) or len(key.public_key) != 32
    ):
        raise VerificationBlocked("untrusted_continuity_key")
    return key


class SignedContinuityVerifier:
    """Validate a read-only proof without issuing or authorizing delivery."""

    def __init__(
        self, *, company_id: str, anchor_path: Path, audit_path: Path,
        authority: ContinuityAuthority | None, clock: Callable[[], int],
    ):
        self.company_id = company_id
        self.anchor_path = anchor_path
        self.audit_path = audit_path
        self.authority = authority
        self.clock = clock

    def verify(self, signed: SignedCheckpoint, receipt: SignedAuditReceipt) -> None:
        if self.authority is None:
            raise VerificationBlocked("continuity_authority_unavailable")
        try:
            current = self.authority.current(self.company_id)
            now = self.clock()
        except (OSError, RuntimeError) as exc:
            raise VerificationBlocked("continuity_authority_or_clock_unavailable") from exc
        if not isinstance(current, CurrentAuthority) or current.company_id != self.company_id:
            raise VerificationBlocked("invalid_continuity_authority")
        if not isinstance(signed, SignedCheckpoint) or not isinstance(signed.checkpoint, ContinuityCheckpoint):
            raise VerificationBlocked("invalid_signed_checkpoint")
        checkpoint = signed.checkpoint
        if (
            not isinstance(receipt, SignedAuditReceipt) or not isinstance(receipt.review, AnchoredReviewReceipt)
            or not isinstance(checkpoint.state, AnchoredCheckpoint)
            or checkpoint.company_id != self.company_id or receipt.company_id != self.company_id
            or receipt.release_authorized is not False or receipt.review.release_authorized is not False
            or receipt.review.status != "verified_for_owner_review"
        ):
            raise VerificationBlocked("invalid_continuity_scope")
        if (
            type(now) is not int or type(checkpoint.issued_at) is not int or type(checkpoint.expires_at) is not int
            or not 0 <= checkpoint.issued_at <= now < checkpoint.expires_at
        ):
            raise VerificationBlocked("stale_or_invalid_checkpoint_time")

        state = checkpoint.state
        for value in (
            state.trust_fingerprint, state.audit_sha256, receipt.review.manifest_sha256,
            receipt.review.audit_sha256, receipt.checkpoint_sha256,
        ):
            if not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None:
                raise VerificationBlocked("invalid_continuity_digest")
        if (
            not isinstance(state.store_id, str) or not state.store_id.strip()
            or not isinstance(state.policy_version, str) or not state.policy_version.strip()
            or type(state.trust_epoch) is not int or state.trust_epoch <= 0
            or type(state.audit_sequence) is not int or state.audit_sequence <= 0
            or type(receipt.review.audit_sequence) is not int
            or not 1 <= receipt.review.audit_sequence <= state.audit_sequence
        ):
            raise VerificationBlocked("invalid_continuity_state")

        checkpoint_key = _key(current, signed.key_id, "checkpoint", now)
        audit_key = _key(current, receipt.key_id, "audit", now)
        if (
            checkpoint_key.principal_id.casefold() == audit_key.principal_id.casefold()
            or checkpoint_key.public_key == audit_key.public_key
        ):
            raise VerificationBlocked("non_independent_continuity_principals")

        payload = checkpoint_payload(checkpoint, signed.key_id)
        pin = hashlib.sha256(payload).hexdigest()
        if pin != current.checkpoint_sha256 or pin != receipt.checkpoint_sha256:
            raise VerificationBlocked("checkpoint_not_current")
        _verify_signature(checkpoint_key.public_key, signed.signature, payload)
        _verify_signature(audit_key.public_key, receipt.signature, audit_receipt_payload(receipt))
        local = read_anchored_checkpoint(self.anchor_path, self.audit_path, self.company_id, receipt.review)
        if local != checkpoint.state:
            raise VerificationBlocked("local_checkpoint_divergence")

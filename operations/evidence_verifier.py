"""Synthetic offline delivery-evidence verifier with no release authority."""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass, field
import hashlib
import hmac
import json
from pathlib import Path
import re
import sqlite3
from typing import Callable, Mapping


class VerificationBlocked(ValueError):
    """Verification could not establish all required conditions."""


@dataclass(frozen=True)
class ReviewScope:
    company_id: str
    opportunity_id: str
    source_commit: str
    recipient: str
    channel: str
    policy_version: str
    producer_id: str


@dataclass(frozen=True)
class EvidenceManifest:
    scope: ReviewScope
    deliverable_sha256: str
    test_log_sha256: str
    nonce: str
    expires_at: int

    def digest(self) -> str:
        return hashlib.sha256(_canonical(asdict(self))).hexdigest()


@dataclass(frozen=True)
class Attestation:
    key_id: str
    expires_at: int
    signature: str


@dataclass(frozen=True)
class TrustedKey:
    company_id: str
    principal_id: str
    role: str
    expires_at: int
    secret: bytes = field(repr=False)
    revoked: bool = False


@dataclass(frozen=True)
class VerificationReceipt:
    manifest_sha256: str
    status: str = field(default="verified_for_owner_review", init=False)
    release_authorized: bool = field(default=False, init=False)


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def attestation_payload(digest: str, key_id: str, role: str, expires_at: int) -> bytes:
    """Versioned bytes authenticated by the synthetic fixture signer."""
    return _canonical({
        "purpose": "aevora_delivery_evidence_review_v1",
        "manifest_sha256": digest,
        "key_id": key_id,
        "role": role,
        "expires_at": expires_at,
    })


def _token(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[!-~]{1,256}", value))


def _live_expiry(value: object, now: int) -> bool:
    return type(value) is int and now < value <= 2 ** 63 - 1


class SQLiteReviewReplayStore:
    """Atomically consume a company-scoped nonce in a pre-provisioned store."""

    def __init__(self, path: Path):
        self.uri = path.resolve().as_uri() + "?mode=rw"

    def claim(self, company_id: str, nonce: str, digest: str, now: int) -> None:
        try:
            with closing(sqlite3.connect(self.uri, uri=True, timeout=1)) as db:
                db.execute("PRAGMA synchronous=FULL")
                with db:
                    claim = db.execute(
                        "INSERT INTO evidence_review_replay "
                        "(company_id, nonce, manifest_sha256, verified_at) VALUES (?, ?, ?, ?) "
                        "ON CONFLICT(company_id, nonce) DO NOTHING",
                        (company_id, nonce, digest, now),
                    )
                    if claim.rowcount != 1:
                        raise VerificationBlocked("replay_conflict")
        except sqlite3.IntegrityError as exc:
            raise VerificationBlocked("replay_conflict_or_store_integrity_error") from exc
        except sqlite3.Error as exc:
            raise VerificationBlocked("replay_store_unavailable") from exc


class EvidenceVerifier:
    """Use only an independently supplied scope, key registry, store and clock.

    HMAC here uses synthetic keys for offline verification. It does not
    establish production signer identity or asymmetric key custody.
    """

    def __init__(
        self, *, expected_scope: ReviewScope, registry: Mapping[str, TrustedKey] | None,
        replay_store: SQLiteReviewReplayStore | None, clock: Callable[[], int],
    ):
        self.expected_scope = expected_scope
        self.registry = registry
        self.replay_store = replay_store
        self.clock = clock

    def _trusted_attestation(
        self, attestation: Attestation, role: str, digest: str, expires_at: int, now: int,
    ) -> TrustedKey:
        if not isinstance(attestation, Attestation) or not _token(attestation.key_id):
            raise VerificationBlocked("invalid_attestation")
        if self.registry is None:
            raise VerificationBlocked("trust_registry_unavailable")
        try:
            key = self.registry.get(attestation.key_id)
        except (OSError, RuntimeError) as exc:
            raise VerificationBlocked("trust_registry_unavailable") from exc
        if (
            not isinstance(key, TrustedKey) or key.revoked is not False
            or key.company_id != self.expected_scope.company_id or key.role != role
            or not _token(key.principal_id)
            or not _live_expiry(key.expires_at, now)
            or not isinstance(key.secret, bytes) or len(key.secret) < 32
        ):
            raise VerificationBlocked("untrusted_attestation_key")
        if (
            not _live_expiry(attestation.expires_at, now)
            or attestation.expires_at > min(key.expires_at, expires_at)
        ):
            raise VerificationBlocked("invalid_attestation_expiry")
        expected = hmac.new(
            key.secret, attestation_payload(digest, attestation.key_id, role, attestation.expires_at),
            hashlib.sha256,
        ).hexdigest()
        if (
            not isinstance(attestation.signature, str)
            or re.fullmatch(r"[a-f0-9]{64}", attestation.signature) is None
            or not hmac.compare_digest(expected, attestation.signature)
        ):
            raise VerificationBlocked("invalid_attestation_signature")
        return key

    def verify(
        self, manifest: EvidenceManifest, *, deliverable: bytes, test_log: bytes,
        qa: Attestation, owner: Attestation,
    ) -> VerificationReceipt:
        if (
            not isinstance(manifest, EvidenceManifest) or not isinstance(manifest.scope, ReviewScope)
            or manifest.scope != self.expected_scope
            or not all(_token(value) for value in asdict(manifest.scope).values())
            or re.fullmatch(r"[a-f0-9]{40}", manifest.scope.source_commit) is None
            or not _token(manifest.nonce)
        ):
            raise VerificationBlocked("invalid_or_mismatched_manifest_scope")
        try:
            now = self.clock()
        except (OSError, RuntimeError) as exc:
            raise VerificationBlocked("trusted_clock_unavailable") from exc
        if type(now) is not int or now < 0 or not _live_expiry(manifest.expires_at, now):
            raise VerificationBlocked("invalid_clock_or_expired_manifest")

        for label, artifact, expected in (
            ("deliverable", deliverable, manifest.deliverable_sha256),
            ("test_log", test_log, manifest.test_log_sha256),
        ):
            if (
                not isinstance(artifact, bytes) or not artifact
                or hashlib.sha256(artifact).hexdigest() != expected
            ):
                raise VerificationBlocked(f"{label}_digest_mismatch")

        digest = manifest.digest()
        reviewer = self._trusted_attestation(qa, "independent_qa", digest, manifest.expires_at, now)
        approver = self._trusted_attestation(owner, "owner_review", digest, manifest.expires_at, now)
        principals = (manifest.scope.producer_id, reviewer.principal_id, approver.principal_id)
        if len({principal.casefold() for principal in principals}) != 3:
            raise VerificationBlocked("non_independent_review_principals")
        if hmac.compare_digest(reviewer.secret, approver.secret):
            raise VerificationBlocked("shared_review_credentials")
        if self.replay_store is None:
            raise VerificationBlocked("replay_store_unavailable")
        self.replay_store.claim(manifest.scope.company_id, manifest.nonce, digest, now)
        return VerificationReceipt(digest)

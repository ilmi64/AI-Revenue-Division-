"""Offline, company-local delivery review with an independently held fixture anchor."""
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import sqlite3
from types import MappingProxyType
from typing import Mapping

from evidence_verifier import EvidenceVerifier, ReviewScope, TrustedKey, VerificationBlocked


_ZERO_HEAD = "0" * 64


def _digest(data: object) -> str:
    encoded = json.dumps(
        data, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _epoch(epoch: int) -> int:
    if type(epoch) is not int or not 0 < epoch < 2**63:
        raise VerificationBlocked("invalid_trust_epoch")
    return epoch


def trust_fingerprint(company_id: str, registry: Mapping[str, TrustedKey]) -> str:
    """Pin the complete company-scoped trust snapshot, including revocation."""
    if not isinstance(registry, Mapping):
        raise VerificationBlocked("trust_registry_unavailable")
    keys = {}
    for key_id, key in registry.items():
        if (
            not isinstance(key_id, str) or not isinstance(key, TrustedKey)
            or key.company_id != company_id or not isinstance(key.secret, bytes)
            or type(key.revoked) is not bool
        ):
            raise VerificationBlocked("invalid_company_trust_snapshot")
        metadata = asdict(key)
        del metadata["secret"]
        keys[key_id] = {**metadata, "fixture_key_sha256": hashlib.sha256(key.secret).hexdigest()}
    return _digest({"purpose": "aevora-trust-v1", "company": company_id, "keys": keys})


@contextmanager
def _existing_db(path: Path):
    try:
        uri = path.resolve().as_uri() + "?mode=rw"
        with closing(sqlite3.connect(uri, uri=True, isolation_level=None, timeout=1)) as db:
            db.execute("PRAGMA synchronous=FULL")
            yield db
    except (OSError, sqlite3.Error) as exc:
        raise VerificationBlocked("anchor_or_audit_unavailable") from exc


def advance_trust(
    anchor_path: Path, company_id: str, *, expected_epoch: int, new_epoch: int,
    policy: str, registry: Mapping[str, TrustedKey],
) -> None:
    """Trusted offline provisioning operation, separate from verify inputs."""
    expected_epoch = _epoch(expected_epoch)
    new_epoch = _epoch(new_epoch)
    if new_epoch <= expected_epoch:
        raise VerificationBlocked("trust_epoch_not_monotonic")
    fingerprint = trust_fingerprint(company_id, registry)
    with _existing_db(anchor_path) as anchor:
        anchor.execute("BEGIN IMMEDIATE")
        changed = anchor.execute(
            "UPDATE review_anchor SET epoch=?, trust_fingerprint=?, policy=? "
            "WHERE company_id=? AND epoch=?",
            (new_epoch, fingerprint, policy, company_id, expected_epoch),
        )
        if changed.rowcount != 1:
            raise VerificationBlocked("trust_epoch_changed_or_missing")
        anchor.execute("COMMIT")


@dataclass(frozen=True)
class AnchoredReviewReceipt:
    manifest_sha256: str
    audit_sequence: int
    audit_sha256: str
    status: str = field(default="verified_for_owner_review", init=False)
    release_authorized: bool = field(default=False, init=False)


class _AnchorLedger:
    def __init__(self, anchor_path: Path, audit_path: Path, company_id: str):
        self.anchor_path = anchor_path
        self.audit_path = audit_path
        self.company_id = company_id

    @contextmanager
    def locked(self):
        try:
            if self.anchor_path.samefile(self.audit_path):
                raise VerificationBlocked("anchor_must_be_separate")
        except OSError as exc:
            raise VerificationBlocked("anchor_or_audit_unavailable") from exc
        # Serialize by the independent anchor, including across verifier instances.
        with _existing_db(self.anchor_path) as anchor, _existing_db(self.audit_path) as audit:
            anchor.execute("BEGIN IMMEDIATE")
            audit.execute("BEGIN IMMEDIATE")
            yield anchor, audit

    def validated_state(self, anchor: sqlite3.Connection, audit: sqlite3.Connection):
        state = anchor.execute(
            "SELECT store_id, epoch, trust_fingerprint, policy, sequence, head "
            "FROM review_anchor WHERE company_id=?", (self.company_id,),
        ).fetchone()
        if state is None:
            raise VerificationBlocked("anchor_company_unavailable")
        store_id, _, _, _, sequence, anchor_head = state
        identity = audit.execute("SELECT company_id, store_id FROM audit_identity").fetchall()
        if identity != [(self.company_id, store_id)]:
            raise VerificationBlocked("audit_identity_mismatch")

        rows = audit.execute(
            "SELECT sequence, previous, epoch, nonce, manifest, observed_at, digest "
            "FROM review_audit ORDER BY sequence",
        ).fetchall()
        head = _ZERO_HEAD
        for index, row in enumerate(rows, 1):
            row_sequence, previous, epoch, nonce, manifest, observed_at, digest = row
            if row_sequence != index or previous != head or digest != self.event_digest(
                store_id, row_sequence, previous, epoch, nonce, manifest, observed_at,
            ):
                raise VerificationBlocked("audit_chain_invalid")
            head = digest
        if len(rows) != sequence or head != anchor_head:
            raise VerificationBlocked("audit_anchor_divergence")
        return state

    def event_digest(self, store_id, sequence, previous, epoch, nonce, manifest, observed_at):
        return _digest({
            "purpose": "aevora-review-audit-v1",
            "company": self.company_id,
            "store": store_id,
            "sequence": sequence,
            "previous": previous,
            "epoch": epoch,
            "nonce": nonce,
            "manifest": manifest,
            "observed_at": observed_at,
        })

    def verify_receipt(self, receipt: AnchoredReviewReceipt) -> None:
        """Independently check continuity and the private receipt's anchored row."""
        if not isinstance(receipt, AnchoredReviewReceipt):
            raise VerificationBlocked("invalid_audit_receipt")
        with self.locked() as (anchor, audit):
            self.validated_state(anchor, audit)
            found = audit.execute(
                "SELECT manifest, digest FROM review_audit WHERE sequence=?",
                (receipt.audit_sequence,),
            ).fetchone()
            if found != (receipt.manifest_sha256, receipt.audit_sha256):
                raise VerificationBlocked("audit_receipt_not_anchored")


def verify_anchored_receipt(
    anchor_path: Path, audit_path: Path, company_id: str, receipt: AnchoredReviewReceipt,
) -> None:
    """Check an existing receipt without issuing an authority decision."""
    _AnchorLedger(anchor_path, audit_path, company_id).verify_receipt(receipt)


class _PendingClaim:
    def __init__(self, ledger: _AnchorLedger, epoch: int, fingerprint: str, policy: str, clock, expiries):
        self.ledger = ledger
        self.epoch = epoch
        self.fingerprint = fingerprint
        self.policy = policy
        self.clock = clock
        self.expiries = expiries
        self.receipt = None

    def claim(self, company_id: str, nonce: str, manifest: str, now: int) -> None:
        if company_id != self.ledger.company_id:
            raise VerificationBlocked("audit_company_mismatch")
        with self.ledger.locked() as (anchor, audit):
            state = self.ledger.validated_state(anchor, audit)
            store_id, epoch, trust, policy, sequence, head = state
            if (epoch, trust, policy) != (self.epoch, self.fingerprint, self.policy):
                raise VerificationBlocked("stale_trust_or_policy")
            try:
                observed_at = self.clock()
            except (OSError, RuntimeError) as exc:
                raise VerificationBlocked("trusted_clock_unavailable") from exc
            if type(observed_at) is not int or not now <= observed_at < min(self.expiries):
                raise VerificationBlocked("clock_or_attestation_expired_at_claim")
            digest = self.ledger.event_digest(
                store_id, sequence + 1, head, epoch, nonce, manifest, observed_at,
            )
            changed = audit.execute(
                "INSERT INTO review_audit VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(nonce) DO NOTHING",
                (sequence + 1, head, epoch, nonce, manifest, observed_at, digest),
            )
            if changed.rowcount != 1:
                raise VerificationBlocked("replay_conflict")
            moved = anchor.execute(
                "UPDATE review_anchor SET sequence=?, head=? WHERE company_id=? AND sequence=? AND head=?",
                (sequence + 1, digest, company_id, sequence, head),
            )
            if moved.rowcount != 1:
                raise VerificationBlocked("anchor_checkpoint_compare_failed")
            # Check the uncommitted pair before either write becomes durable.
            self.ledger.validated_state(anchor, audit)
            # A process exit between commits leaves a detectable mismatch.
            # Do not retry ambiguously committed work or silently reseed.
            audit.execute("COMMIT")
            anchor.execute("COMMIT")
            self.receipt = AnchoredReviewReceipt(manifest, sequence + 1, digest)


class AnchoredEvidenceVerifier:
    def __init__(
        self, *, anchor_path: Path, audit_path: Path, scope: ReviewScope,
        registry: Mapping[str, TrustedKey], trust_epoch: int, clock,
    ):
        if not isinstance(registry, Mapping):
            raise VerificationBlocked("trust_registry_unavailable")
        self.registry = MappingProxyType(dict(registry))
        self.ledger = _AnchorLedger(anchor_path, audit_path, scope.company_id)
        self.fingerprint = trust_fingerprint(scope.company_id, self.registry)
        self.epoch = _epoch(trust_epoch)
        self.scope = scope
        self.clock = clock

    def verify(self, manifest, *, deliverable, test_log, qa, owner) -> AnchoredReviewReceipt:
        claim = _PendingClaim(
            self.ledger, self.epoch, self.fingerprint, self.scope.policy_version, self.clock,
            (getattr(manifest, "expires_at", None), getattr(qa, "expires_at", None),
             getattr(owner, "expires_at", None)),
        )
        verifier = EvidenceVerifier(
            expected_scope=self.scope, registry=self.registry, replay_store=claim, clock=self.clock,
        )
        verifier.verify(manifest, deliverable=deliverable, test_log=test_log, qa=qa, owner=owner)
        if claim.receipt is None:
            raise VerificationBlocked("missing_anchored_receipt")
        return claim.receipt

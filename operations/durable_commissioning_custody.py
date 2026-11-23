"""Synthetic durable company custody with a separately retained checkpoint pin."""
from collections.abc import Mapping
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re
from pathlib import Path
import sqlite3
from typing import Callable, Protocol

from continuity_commissioning import (
    CommissioningEvidence, CustodyObservation, ExternalReview, review_bundle_fingerprint, review_payload,
)
from evidence_verifier import VerificationBlocked
from occ_summary import summarize
from signed_audit_continuity import ContinuityKey, CurrentAuthority, _canonical, _key, _verify_signature


@dataclass(frozen=True)
class CustodyPin:
    company_id: str
    store_id: str
    sequence: int
    head: str


class ExternalCustodyPin(Protocol):
    """Independent authenticated pin custody with durable monotonic CAS.

    Provision identity and genesis outside the custody database. Never
    reconstruct a pin from an untrusted database after outage or restore.
    A write must advance exactly one sequence for the same company/store.
    Report ambiguous writes and unavailable authority as failures.
    """

    def current(self, company_id: str, store_id: str) -> CustodyPin: ...

    def advance(self, current: CustodyPin, replacement: CustodyPin) -> bool: ...


def _snapshot_data(observation: CustodyObservation) -> dict:
    return {
        "custodian_id": observation.custodian_id,
        "signer_operator_id": observation.signer_operator_id,
        "custody_revision": observation.custody_revision,
        "signer_revision": observation.signer_revision,
        "observed_at": observation.observed_at,
        "expires_at": observation.expires_at,
        "company_id": observation.authority.company_id,
        "checkpoint_sha256": observation.authority.checkpoint_sha256,
        "keys": {
            key_id: {**asdict(key), "public_key": key.public_key.hex()}
            for key_id, key in observation.authority.keys.items()
        },
    }


def _observation(data: dict) -> CustodyObservation:
    keys = {
        key_id: ContinuityKey(**{**meta, "public_key": bytes.fromhex(meta["public_key"])})
        for key_id, meta in data["keys"].items()
    }
    return CustodyObservation(
        data["custodian_id"], data["signer_operator_id"], data["custody_revision"],
        data["signer_revision"], data["observed_at"], data["expires_at"],
        CurrentAuthority(data["company_id"], data["checkpoint_sha256"], keys),
    )


def _private_evidence(evidence: CommissioningEvidence) -> dict:
    payload = asdict(evidence)
    payload["reviews"] = [
        {**asdict(review), "signature": review.signature.hex()} for review in evidence.reviews
    ]
    return payload


def _validate_rotation(current: CustodyObservation, updated: CustodyObservation) -> None:
    old, new = current.authority, updated.authority
    if (
        current.custodian_id != updated.custodian_id or current.signer_operator_id != updated.signer_operator_id
        or updated.custody_revision < current.custody_revision
        or updated.signer_revision < current.signer_revision or updated.observed_at < current.observed_at
        or (updated.expires_at > current.expires_at and updated.observed_at == current.observed_at)
        or (new.checkpoint_sha256 != old.checkpoint_sha256 and updated.custody_revision == current.custody_revision)
        or (new.keys != old.keys and updated.signer_revision == current.signer_revision)
    ):
        raise VerificationBlocked("custody_or_signer_lifecycle_regression")
    for key_id, key in old.keys.items():
        successor = new.keys.get(key_id)
        if (
            successor is None or (key.revoked and not successor.revoked)
            or replace(successor, revoked=key.revoked) != key
        ):
            raise VerificationBlocked("signer_id_mutation_or_revocation_rollback")


class SyntheticDurableCustody:
    """SQLite fixture plus an independently provisioned pin, never production authority."""

    def __init__(self, *, path: Path, company_id: str, store_id: str, pin: ExternalCustodyPin | None,
                 clock: Callable[[], int]):
        self.path = path
        self.company_id = company_id
        self.store_id = store_id
        self.pin = pin
        self.clock = clock

    @contextmanager
    def _open(self):
        if self.pin is None:
            raise VerificationBlocked("external_custody_pin_unavailable")
        try:
            with closing(sqlite3.connect(self.path.resolve().as_uri() + "?mode=rw", uri=True,
                                         isolation_level=None, timeout=1)) as db:
                db.execute("PRAGMA synchronous=FULL")
                db.execute("BEGIN IMMEDIATE")
                identity = db.execute("SELECT company_id, store_id FROM custody_identity").fetchall()
                if identity != [(self.company_id, self.store_id)]:
                    raise VerificationBlocked("custody_store_identity_mismatch")
                state = self._state(db)
                if self.pin.current(self.company_id, self.store_id) != state[0]:
                    raise VerificationBlocked("external_custody_pin_divergence")
                yield db, state
        except (OSError, sqlite3.Error, TypeError, ValueError, KeyError, RuntimeError) as exc:
            if isinstance(exc, VerificationBlocked):
                raise
            raise VerificationBlocked("durable_custody_unavailable_or_corrupt") from exc

    def _head(self, prior: CustodyPin, payload: str) -> str:
        return hashlib.sha256(_canonical({
            "purpose": "aevora-durable-custody-v1", **asdict(prior), "payload": payload,
        })).hexdigest()

    def _state(self, db):
        pin = CustodyPin(self.company_id, self.store_id, 0, "0" * 64)
        observation = None
        records = {}
        for sequence, previous, payload, head in db.execute(
            "SELECT sequence, previous, payload, head FROM custody_event ORDER BY sequence",
        ):
            if sequence != pin.sequence + 1 or previous != pin.head or head != self._head(pin, payload):
                raise VerificationBlocked("custody_audit_chain_invalid")
            event = json.loads(payload)
            if event["kind"] == "observation":
                observation = _observation(event["value"])
            elif event["kind"] == "commissioning_evidence":
                record = event["value"]
                request = record["request"]
                key = (request["company_id"], request["checkpoint_sha256"], request["request_id"])
                if request["company_id"] != self.company_id or record["release_authorized"] is not False or key in records:
                    raise VerificationBlocked("custody_audit_evidence_invalid")
                records[key] = record
            else:
                raise VerificationBlocked("custody_audit_event_invalid")
            pin = CustodyPin(self.company_id, self.store_id, sequence, head)
        return pin, observation, records

    def _append(self, db, current: CustodyPin, kind: str, value: dict) -> None:
        payload = _canonical({"kind": kind, "value": value}).decode("ascii")
        updated = replace(current, sequence=current.sequence + 1, head=self._head(current, payload))
        db.execute("INSERT INTO custody_event VALUES (?, ?, ?, ?)",
                   (updated.sequence, current.head, payload, updated.head))
        if self._state(db)[0] != updated:
            raise VerificationBlocked("custody_write_readback_mismatch")
        if self.pin.advance(current, updated) is not True:
            raise VerificationBlocked("external_custody_pin_changed")
        # A crash or ambiguous commit after pin advance leaves a detectable
        # mismatch. Recovery requires independent review, never reseeding.
        db.execute("COMMIT")

    def provision_observation(self, updated: CustodyObservation) -> None:
        """Trusted synthetic lifecycle administration, not applicant input."""
        with self._open() as (db, (pin, previous, _)):
            if (
                not isinstance(updated, CustodyObservation)
                or not isinstance(updated.authority, CurrentAuthority)
                or updated.authority.company_id != self.company_id
                or not isinstance(updated.authority.checkpoint_sha256, str)
                or re.fullmatch(r"[0-9a-f]{64}", updated.authority.checkpoint_sha256) is None
                or type(updated.custody_revision) is not int or updated.custody_revision < 1
                or type(updated.signer_revision) is not int or updated.signer_revision < 1
                or type(updated.observed_at) is not int or type(updated.expires_at) is not int
                or not 0 <= updated.observed_at < updated.expires_at
                or not isinstance(updated.authority.keys, Mapping) or not updated.authority.keys
                or any(
                    not isinstance(key_id, str) or not key_id.strip()
                    or not isinstance(key, ContinuityKey) or key.company_id != self.company_id
                    or not isinstance(key.public_key, bytes) or len(key.public_key) != 32
                    or not isinstance(key.principal_id, str) or not key.principal_id.strip()
                    or key.purpose not in ("checkpoint", "audit", "external_audit", "external_recovery")
                    or type(key.expires_at) is not int or key.expires_at <= 0
                    or type(key.revoked) is not bool
                    for key_id, key in updated.authority.keys.items()
                )
                or len({key.public_key for key in updated.authority.keys.values()}) != len(updated.authority.keys)
            ):
                raise VerificationBlocked("invalid_custody_snapshot")
            if previous is not None:
                _validate_rotation(previous, updated)
            self._append(db, pin, "observation", _snapshot_data(updated))

    def observe(self, company_id: str) -> CustodyObservation:
        if company_id != self.company_id:
            raise VerificationBlocked("custody_company_scope_mismatch")
        with self._open() as (_, (_, observed, _)):
            if observed is None:
                raise VerificationBlocked("custody_observation_missing")
            return observed

    def record_if_current(self, observation: CustodyObservation, evidence: CommissioningEvidence) -> bool:
        """Trusted reviewer port; recheck review signatures and atomic custody state."""
        with self._open() as (db, (pin, current, records)):
            if not isinstance(evidence, CommissioningEvidence):
                return False
            request = evidence.request
            key = (request.company_id, request.checkpoint_sha256, request.request_id)
            now = self.clock()
            if (
                current is None or current != observation or key in records
                or request.company_id != self.company_id or request.checkpoint_sha256 != current.authority.checkpoint_sha256
                or request.custody_revision != current.custody_revision or request.signer_revision != current.signer_revision
                or evidence.release_authorized is not False or type(now) is not int
                or not evidence.checked_at <= now < min(evidence.valid_until, current.expires_at)
                or not current.observed_at <= now or len(evidence.reviews) != 2
            ):
                return False
            for review, purpose in zip(evidence.reviews, ("external_audit", "external_recovery"), strict=True):
                if (
                    not isinstance(review, ExternalReview) or review.purpose != purpose
                    or review.disposition != "accepted" or type(review.expires_at) is not int
                    or not now < review.expires_at or evidence.valid_until > review.expires_at
                ):
                    return False
                signer = _key(current.authority, review.key_id, purpose, now)
                if review.expires_at > signer.expires_at:
                    return False
                _verify_signature(signer.public_key, review.signature, review_payload(request, review))
            if review_bundle_fingerprint(request, evidence.reviews) != evidence.approval_bundle_sha256:
                return False
            self._append(db, pin, "commissioning_evidence", _private_evidence(evidence))
            return True

    def private_manifest(self) -> dict:
        """Canonicalizable private evidence index. Do not publish it to OCC."""
        with self._open() as (_, (pin, observed, records)):
            if observed is None:
                raise VerificationBlocked("custody_observation_missing")
            return {
                "schema": "aevora-synthetic-commissioning-evidence-v1",
                "classification": "SYNTHETIC_PRIVATE",
                "custody_pin": asdict(pin),
                "checkpoint_sha256": observed.authority.checkpoint_sha256,
                "signer_revision": observed.signer_revision,
                "custody_revision": observed.custody_revision,
                "records": list(records.values()),
                "release_authorized": False,
                "external_actions_performed": False,
                "owner_approval": "NOT_GRANTED",
            }

    def occ_projection(self) -> dict:
        """Expose an allowlisted aggregate via the existing read-only contract."""
        with self._open() as (_, (_, observed, records)):
            if observed is None:
                raise VerificationBlocked("custody_observation_missing")
            return summarize([{"status": "checklist_complete_unverified"} for _ in records])

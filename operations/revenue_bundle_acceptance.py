"""Signed company-private acceptance of an exact scheduled internal bundle."""
from dataclasses import asdict, dataclass, field
from io import BytesIO
import json
from zipfile import ZipFile

from evidence_verifier import VerificationBlocked
from revenue_fixture_dispatch import canonical
from revenue_fixture_reservation_recovery import RecoveryAuthority, _fresh_window, _read_authority
from revenue_fixture_schedule import FixtureScheduler
from revenue_internal_review_bundle import _bundle_from_verified_result
from signed_audit_continuity import ContinuityKey, _verify_signature
from synthetic_delivery_rehearsal import _sha


_COMPANY = "ai_revenue"
_REVIEWER_ROLE = "ar_engineering_reviewer"


@dataclass(frozen=True)
class BundleAcceptanceClaim:
    company_id: str
    recipient_scope: str
    request_id: str
    request_sha256: str
    result_sha256: str
    bundle_sha256: str
    manifest_sha256: str


@dataclass(frozen=True)
class BundleAcceptanceAuthorization:
    claim: BundleAcceptanceClaim
    trust_epoch: int
    observed_at: int
    expires_at: int
    key_id: str
    signature: bytes


@dataclass(frozen=True)
class BundleAcceptanceReceipt:
    claim: BundleAcceptanceClaim
    reviewer_id: str
    trust_epoch: int
    accepted_at: int
    status: str = field(default="INTERNAL_EVIDENCE_ACCEPTED", init=False)
    commissioning_status: str = field(default="HOLD", init=False)
    release_authorized: bool = field(default=False, init=False)


def acceptance_payload(authorization: BundleAcceptanceAuthorization) -> bytes:
    return canonical({
        "purpose": "aevora-private-bundle-acceptance-v1",
        "reviewer_role": _REVIEWER_ROLE,
        "claim": asdict(authorization.claim),
        "trust_epoch": authorization.trust_epoch,
        "observed_at": authorization.observed_at,
        "expires_at": authorization.expires_at,
        "key_id": authorization.key_id,
        "release_authorized": False,
    })


class InternalBundleAcceptor:
    """Use only an independently provisioned current authority at local bootstrap."""

    def __init__(self, scheduler: FixtureScheduler, *, authority: RecoveryAuthority | None):
        if not isinstance(scheduler, FixtureScheduler):
            raise TypeError("a company-local fixture scheduler is required")
        self._scheduler = scheduler
        self._authority = authority

    def _evidence(self, request_id: str):
        with self._scheduler._transaction() as (db, _):
            row = self._scheduler._row(db, request_id)
            result = self._scheduler._verified_private_result(row)
            request_sha256 = _sha(row["request_bytes"])
        review = json.loads(result)
        artifact = review["private_artifact"]["contents"]
        scope = artifact["commercial_review_scope"]
        if (
            scope["company_id"] != _COMPANY or scope["recipient_scope"] != _COMPANY
            or scope["review_audience"] != "internal_owner_review_only"
            or scope["external_approval_granted"] is not False
        ):
            raise VerificationBlocked("bundle_internal_scope_mismatch")
        participants = set()
        assignments = artifact.get("assignments")
        if not isinstance(assignments, list):
            raise VerificationBlocked("bundle_fixture_participant_invalid")
        for assignment in assignments:
            actor = assignment.get("proposed_owner") if isinstance(assignment, dict) else None
            if not isinstance(actor, str) or not actor.strip():
                raise VerificationBlocked("bundle_fixture_participant_invalid")
            participants.add(actor.strip().casefold())
        if not participants:
            raise VerificationBlocked("bundle_fixture_participant_invalid")
        expected_bundle = _bundle_from_verified_result(review)
        with ZipFile(BytesIO(expected_bundle)) as zipped:
            manifest_sha256 = _sha(zipped.read("manifest.json"))
        claim = BundleAcceptanceClaim(
            _COMPANY, scope["recipient_scope"], request_id,
            request_sha256, _sha(result), _sha(expected_bundle), manifest_sha256,
        )
        return claim, expected_bundle, result, participants

    def claim(self, request_id: str) -> BundleAcceptanceClaim:
        """Company-private locally generated claim for an independent reviewer."""
        return self._evidence(request_id)[0]

    def accept(self, request_id: str, bundle: bytes, authorization: BundleAcceptanceAuthorization) -> BundleAcceptanceReceipt:
        if self._authority is None:
            raise VerificationBlocked("bundle_acceptance_authority_unavailable")
        claim, expected_bundle, result, participants = self._evidence(request_id)
        # Compare against the trusted local pack, without parsing supplied ZIPs.
        if not isinstance(bundle, bytes) or bundle != expected_bundle:
            raise VerificationBlocked("bundle_acceptance_exact_bytes_mismatch")
        if not isinstance(authorization, BundleAcceptanceAuthorization) or authorization.claim != claim:
            raise VerificationBlocked("bundle_acceptance_claim_mismatch")
        with self._scheduler._transaction() as (db, now):
            self._require_same_result(db, claim, result)
            if db.execute(
                "SELECT 1 FROM fixture_bundle_acceptance WHERE request_id=?", (request_id,),
            ).fetchone() is not None:
                raise VerificationBlocked("bundle_acceptance_already_recorded")
            current = _read_authority(self._authority)
            if (
                current.company_id != _COMPANY or type(current.trust_epoch) is not int or current.trust_epoch <= 0
                or type(authorization.trust_epoch) is not int or authorization.trust_epoch != current.trust_epoch
                or not _fresh_window(current.observed_at, current.expires_at, now)
                or not _fresh_window(authorization.observed_at, authorization.expires_at, now)
                or not isinstance(authorization.key_id, str) or not authorization.key_id
            ):
                raise VerificationBlocked("bundle_acceptance_trust_stale_or_out_of_scope")
            key = current.keys.get(authorization.key_id)
            if (
                not isinstance(key, ContinuityKey) or key.company_id != _COMPANY or key.purpose != _REVIEWER_ROLE
                or not isinstance(key.principal_id, str) or not key.principal_id.strip()
                or key.revoked is not False or type(key.expires_at) is not int
                or authorization.expires_at > min(key.expires_at, current.expires_at)
            ):
                raise VerificationBlocked("bundle_acceptance_signer_untrusted")
            if key.principal_id.strip().casefold() in participants:
                raise VerificationBlocked("bundle_acceptance_reviewer_not_independent")
            payload = acceptance_payload(authorization)
            _verify_signature(key.public_key, authorization.signature, payload)
            if _read_authority(self._authority) != current:
                raise VerificationBlocked("bundle_acceptance_authority_changed")
            accepted_at = self._scheduler._clock()
            if type(accepted_at) is not int or not now <= accepted_at < authorization.expires_at:
                raise VerificationBlocked("bundle_acceptance_expired_before_record")
            db.execute("UPDATE fixture_scheduler_clock SET last_seen=?", (accepted_at,))
            receipt = BundleAcceptanceReceipt(claim, key.principal_id, authorization.trust_epoch, accepted_at)
            raw = canonical({
                "receipt": asdict(receipt),
                "acceptance_payload": json.loads(payload),
                "acceptance_payload_sha256": _sha(payload),
                "key_id": authorization.key_id,
                "signature": authorization.signature.hex(),
            })
            written = db.execute(
                "INSERT INTO fixture_bundle_acceptance VALUES (?, ?, ?) ON CONFLICT(request_id) DO NOTHING",
                (request_id, raw, _sha(raw)),
            )
            self._require_same_result(db, claim, result)
            row = db.execute(
                "SELECT receipt, receipt_sha256 FROM fixture_bundle_acceptance WHERE request_id=?", (request_id,),
            ).fetchone()
            if (
                written.rowcount != 1 or row is None
                or row["receipt"] != raw or row["receipt_sha256"] != _sha(raw)
            ):
                raise VerificationBlocked("bundle_acceptance_record_changed")
            return receipt

    def private_record(self, request_id: str) -> bytes:
        claim, _, result, _ = self._evidence(request_id)
        with self._scheduler._transaction() as (db, _):
            self._require_same_result(db, claim, result)
            record = db.execute(
                "SELECT receipt, receipt_sha256 FROM fixture_bundle_acceptance WHERE request_id=?", (request_id,),
            ).fetchone()
            if record is None or not isinstance(record["receipt"], bytes) or _sha(record["receipt"]) != record["receipt_sha256"]:
                raise VerificationBlocked("bundle_acceptance_record_unavailable")
            raw = record["receipt"]
            try:
                decoded = json.loads(raw)
                receipt = decoded["receipt"]
                payload = decoded["acceptance_payload"]
                if (
                    canonical(decoded) != raw or receipt["claim"] != asdict(claim)
                    or receipt["status"] != "INTERNAL_EVIDENCE_ACCEPTED" or receipt["commissioning_status"] != "HOLD"
                    or receipt["release_authorized"] is not False
                    or payload["purpose"] != "aevora-private-bundle-acceptance-v1"
                    or payload["reviewer_role"] != _REVIEWER_ROLE or payload["claim"] != asdict(claim)
                    or payload["release_authorized"] is not False
                    or payload["trust_epoch"] != receipt["trust_epoch"]
                    or payload["key_id"] != decoded["key_id"]
                    or not _fresh_window(payload["observed_at"], payload["expires_at"], receipt["accepted_at"])
                    or _sha(canonical(payload)) != decoded["acceptance_payload_sha256"]
                ):
                    raise VerificationBlocked("bundle_acceptance_record_invalid")
            except (KeyError, TypeError, ValueError) as exc:
                raise VerificationBlocked("bundle_acceptance_record_invalid") from exc
            return raw

    def _require_same_result(self, db, claim: BundleAcceptanceClaim, result: bytes) -> None:
        row = self._scheduler._row(db, claim.request_id)
        if (
            row["state"] != "REVIEW_READY" or row["result"] != result
            or row["result_sha256"] != claim.result_sha256 or not isinstance(row["request_bytes"], bytes)
            or _sha(row["request_bytes"]) != claim.request_sha256
        ):
            raise VerificationBlocked("bundle_acceptance_scheduled_result_changed")

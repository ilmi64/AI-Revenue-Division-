"""Synthetic publisher proof of possession and independent custodial witness."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import json
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from occ_receipt_anchor import custody_digest


_PUBLISHER_DOMAIN = b"daivora.occ.publisher-enrollment/synthetic-v1\x00"
_WITNESS_DOMAIN = b"daivora.occ.publisher-enrollment-witness/synthetic-v1\x00"
_MAX_WINDOW = timedelta(minutes=5)


@dataclass(frozen=True)
class PublisherEnrollment:
    challenge: str
    issued_at: datetime
    expires_at: datetime
    publisher_signature: bytes
    witness_signature: bytes


def _time(value):
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0) or value.microsecond:
        raise ValueError("enrollment requires UTC whole-second timestamps")
    return value


def publisher_enrollment_bytes(trust, journal_id, custodian_public_key, *,
                               challenge, issued_at, expires_at):
    issued, expires = _time(issued_at), _time(expires_at)
    if (
        not isinstance(challenge, str) or not re.fullmatch(r"[0-9a-f]{64}", challenge)
        or not isinstance(journal_id, str) or not re.fullmatch(r"[a-zA-Z0-9._-]{1,80}", journal_id)
        or not isinstance(custodian_public_key, bytes) or len(custodian_public_key) != 32
        or not timedelta(0) < expires - issued <= _MAX_WINDOW
    ):
        raise ValueError("invalid witnessed enrollment binding")
    record = [
        trust.company_id, journal_id, custody_digest(trust), custodian_public_key.hex(),
        challenge, issued.isoformat(), expires.isoformat(),
    ]
    return _PUBLISHER_DOMAIN + json.dumps(record, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def witness_enrollment_bytes(binding, publisher_signature):
    if not isinstance(publisher_signature, bytes) or len(publisher_signature) != 64:
        raise ValueError("publisher enrollment signature is malformed")
    return _WITNESS_DOMAIN + sha256(binding).digest() + publisher_signature


def verify_publisher_enrollment(trust, journal_id, custodian_public_key, *,
                                expected_challenge, enrollment, now):
    """Return a proof digest after checking both configured offline principals."""
    from occ_signed_visibility import _trust_matches_company

    now = _time(now)
    _trust_matches_company(trust, trust.company_id, now)
    if (
        not isinstance(enrollment, PublisherEnrollment)
        or enrollment.challenge != expected_challenge
        or not trust.valid_from <= _time(enrollment.issued_at) <= now
        < _time(enrollment.expires_at) <= trust.valid_until
        or not isinstance(enrollment.witness_signature, bytes)
        or len(enrollment.witness_signature) != 64
    ):
        raise ValueError("publisher enrollment challenge or freshness is invalid")
    binding = publisher_enrollment_bytes(
        trust, journal_id, custodian_public_key, challenge=expected_challenge,
        issued_at=enrollment.issued_at, expires_at=enrollment.expires_at,
    )
    witness = witness_enrollment_bytes(binding, enrollment.publisher_signature)
    try:
        Ed25519PublicKey.from_public_bytes(trust.public_key).verify(enrollment.publisher_signature, binding)
        Ed25519PublicKey.from_public_bytes(custodian_public_key).verify(enrollment.witness_signature, witness)
    except InvalidSignature as exc:
        raise ValueError("publisher possession or independent witness did not verify") from exc
    return sha256(witness + enrollment.witness_signature).hexdigest()

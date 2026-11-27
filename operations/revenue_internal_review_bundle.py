"""Package exact, company-private output from a completed fixture schedule.

The archive includes the reviewed artifact and its original evidence. The
manifest locates each member by digest and preserves the release denial.
"""

from hashlib import sha256
from io import BytesIO
import json
from zipfile import ZIP_STORED, ZipFile, ZipInfo

from evidence_verifier import VerificationBlocked
from revenue_fixture_dispatch import canonical
from revenue_fixture_schedule import FixtureScheduler


def build_internal_review_bundle(scheduler: FixtureScheduler, request_id: str) -> bytes:
    """Return a deterministic ZIP after the scheduler's scope and digest checks."""
    if not isinstance(scheduler, FixtureScheduler):
        raise TypeError("a company-local fixture scheduler is required")
    return _bundle_from_verified_result(json.loads(scheduler.private_result(request_id)))


def _bundle_from_verified_result(reviewed: dict) -> bytes:
    """Package only an already verified company-local scheduler result."""
    try:
        artifact = reviewed["private_artifact"]["contents"]
        evidence = reviewed["private_test_log"]
        receipt = reviewed["receipt"]
        scope = artifact["commercial_review_scope"]
        if not isinstance(evidence, dict) or not isinstance(scope, dict):
            raise VerificationBlocked("internal_review_bundle_missing_evidence")
        members = {
            "reviewed-artifact.json": canonical(artifact),
            "review-evidence.json": canonical(evidence),
            "anchored-review-receipt.json": canonical(receipt),
        }
        manifest = canonical({
            "schema_version": 1,
            "classification": "SYNTHETIC_INTERNAL_REVIEW_ONLY",
            "commissioning_status": "HOLD",
            "release_authorized": False,
            "commercial_review_scope": scope,
            "members_sha256": {name: sha256(data).hexdigest() for name, data in members.items()},
        })
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, VerificationBlocked):
            raise
        raise VerificationBlocked("internal_review_bundle_invalid") from error

    output = BytesIO()
    with ZipFile(output, mode="w", compression=ZIP_STORED) as archive:
        for name, data in {"manifest.json": manifest, **members}.items():
            member = ZipInfo(name)
            member.create_system = 3
            member.external_attr = 0o100600 << 16
            archive.writestr(member, data)
    return output.getvalue()

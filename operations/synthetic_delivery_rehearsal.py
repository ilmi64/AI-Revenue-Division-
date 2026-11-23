"""Run a closed, fictional Aevora AI delivery-review rehearsal."""
from contextlib import closing
from dataclasses import asdict, replace
import hashlib
import hmac
import json
import argparse
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from delivery_gate import decide
from evidence_verifier import (
    Attestation, EvidenceManifest, EvidenceVerifier, ReviewScope, SQLiteReviewReplayStore,
    TrustedKey, VerificationBlocked, attestation_payload,
)
from occ_summary import summarize
from opportunity_intake import assess


_SCENARIOS = (
    "baseline", "missing_registry", "revoked_reviewer", "wrong_recipient", "wrong_company",
    "stale_policy", "replay", "snapshot_rollback", "unavailable_store", "aborted_transaction",
)
_FIXTURE_SCOPE = ReviewScope(
    "aevora_ai", "fictional-opp-1", "a" * 40, "fictional-recipient",
    "fictional-local-channel", "fixture-policy-v2", "fixture-producer",
)
_FIXTURE_NOW = 1800000000


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _artifact_and_test_log() -> tuple[bytes, bytes]:
    artifact = json.dumps(
        {"label": "SYNTHETIC", "monthly_minutes": 12 * 5, "workflow": "fictional-intake"},
        sort_keys=True, separators=(",", ":"),
    ).encode("ascii")
    value = json.loads(artifact)
    if value["label"] != "SYNTHETIC" or value["monthly_minutes"] != 60:
        raise RuntimeError("fixture checks failed")
    return artifact, b"SYNTHETIC: fixture label and monthly minute calculation checked\n"


def _attest(key_id: str, key: TrustedKey, manifest: EvidenceManifest) -> Attestation:
    expiry = manifest.expires_at - 1
    message = attestation_payload(manifest.digest(), key_id, key.role, expiry)
    return Attestation(key_id, expiry, hmac.digest(key.secret, message, "sha256").hex())


def _checkpoint_present(path: Path, manifest: EvidenceManifest, digest: str) -> bool:
    """Compare a restored fixture with a checkpoint held outside it in this run."""
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            row = db.execute(
                "SELECT manifest_sha256 FROM evidence_review_replay WHERE company_id=? AND nonce=?",
                (manifest.scope.company_id, manifest.nonce),
            ).fetchone()
    except sqlite3.Error:
        return False
    return row == (digest,)


def run_unanchored_fixture_rehearsal(scenario: str = "baseline") -> dict:
    """Historical characterization fixture for the pinned unanchored review."""
    if scenario not in _SCENARIOS:
        raise ValueError("unknown synthetic scenario")
    return _run_rehearsal(scenario, _verify_fixture)


def _run_rehearsal(scenario, verify_fixture):
    """Share the stages and redaction without changing verifier selection."""
    audit = []
    opportunity = {
        "id": _FIXTURE_SCOPE.opportunity_id, "title": "Fictional workflow material", "kind": "coding",
        "source_url": "https://example.invalid/fictional", "scope_authorized": True,
        "cost_cad": 0, "requires_credentials": False, "external_action": False, "deadline_utc": None,
    }
    intake = assess(opportunity)
    audit.append({"stage": "intake", "status": intake["status"]})
    artifact, test_log = _artifact_and_test_log()
    audit.append({"stage": "fixture_checks", "deliverable_sha256": _sha(artifact), "test_log_sha256": _sha(test_log)})
    checklist = decide({
        "opportunity": opportunity,
        "evidence": {
            "task_owner": _FIXTURE_SCOPE.producer_id, "source_commit": _FIXTURE_SCOPE.source_commit,
            "tests_passed": True, "test_command": "synthetic fixture checks",
            "test_log_ref": "in-memory:synthetic-fixture-checks",
        },
        "approvals": {"delivery_authorized": True, "scope_reviewed": True},
    })
    audit.append({"stage": "checklist", "status": checklist["status"], "release_authorized": False})

    public_status = "blocked"
    receipt = None
    if intake["status"] == "review_ready" and checklist["status"] == "checklist_complete_unverified":
        try:
            receipt = verify_fixture(scenario, artifact, test_log, audit)
            audit.append({"stage": "verification", "status": receipt["status"]})
            # The OCC vocabulary deliberately exposes only the existing checklist state.
            public_status = checklist["status"]
        except VerificationBlocked as exc:
            audit.append({"stage": "verification", "status": "blocked", "reason": str(exc)})

    audit.append({"stage": "external_delivery", "status": "denied", "release_authorized": False})
    return {
        "classification": "SYNTHETIC",
        "scenario": scenario,
        "private_audit": audit,
        "receipt": receipt,
        "occ": summarize([{"status": public_status}]),
        "release_authorized": False,
        "external_actions_performed": False,
    }


def _verify_fixture(scenario: str, artifact: bytes, test_log: bytes, audit: list) -> dict:
    changes = {
        "wrong_recipient": {"recipient": "wrong-fixture-recipient"},
        "wrong_company": {"company_id": "fictional-other-company"},
        "stale_policy": {"policy_version": "fixture-policy-v1"},
    }
    scope = replace(_FIXTURE_SCOPE, **changes.get(scenario, {}))
    manifest = EvidenceManifest(scope, _sha(artifact), _sha(test_log), "fixture-nonce", _FIXTURE_NOW + 60)
    registry = {
        "fixture-qa": TrustedKey("aevora_ai", "fixture-qa", "independent_qa", _FIXTURE_NOW + 120, b"q" * 32),
        "fixture-owner": TrustedKey("aevora_ai", "fixture-owner", "owner_review", _FIXTURE_NOW + 120, b"o" * 32),
    }
    qa = _attest("fixture-qa", registry["fixture-qa"], manifest)
    owner = _attest("fixture-owner", registry["fixture-owner"], manifest)
    if scenario == "revoked_reviewer":
        registry["fixture-qa"] = replace(registry["fixture-qa"], revoked=True)

    with TemporaryDirectory() as directory:
        path = Path(directory).resolve() / "replay.sqlite"
        with closing(sqlite3.connect(path)) as db:
            db.executescript(Path(__file__).with_name("evidence_verifier_replay.sql").read_text(encoding="utf-8"))
            if scenario == "aborted_transaction":
                db.executescript(
                    "CREATE TRIGGER fixture_abort AFTER INSERT ON evidence_review_replay "
                    "BEGIN SELECT RAISE(ABORT, 'synthetic write abort'); END;"
                )
        old_snapshot = path.read_bytes() if scenario == "snapshot_rollback" else None
        if scenario == "unavailable_store":
            path.unlink()
        verifier = EvidenceVerifier(
            expected_scope=_FIXTURE_SCOPE,
            registry=None if scenario == "missing_registry" else registry,
            replay_store=SQLiteReviewReplayStore(path),
            clock=lambda: _FIXTURE_NOW,
        )

        def verify():
            return verifier.verify(manifest, deliverable=artifact, test_log=test_log, qa=qa, owner=owner)

        try:
            receipt = verify()
        except VerificationBlocked:
            if scenario == "aborted_transaction":
                with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
                    count = db.execute("SELECT COUNT(*) FROM evidence_review_replay").fetchone()[0]
                audit.append({"stage": "transaction_rollback", "nonce_claims": count})
            raise
        if not _checkpoint_present(path, manifest, receipt.manifest_sha256):
            raise VerificationBlocked("nonce_claim_readback_failed")
        audit.append({"stage": "nonce_claim", "manifest_sha256": receipt.manifest_sha256})
        if scenario == "replay":
            verify()
            raise RuntimeError("synthetic replay unexpectedly verified")
        if old_snapshot is not None:
            path.write_bytes(old_snapshot)
            if not _checkpoint_present(path, manifest, receipt.manifest_sha256):
                audit.append({"stage": "snapshot_checkpoint", "status": "mismatch"})
                raise VerificationBlocked("replay_snapshot_checkpoint_mismatch")
            raise RuntimeError("synthetic rollback unexpectedly preserved the checkpoint")
        return asdict(receipt)


def run_rehearsal(*, mode: str, scenario: str = "baseline") -> dict:
    """Run the synthetic delivery workflow with an explicitly selected anchor."""
    from anchored_delivery_rehearsal import run_anchored_rehearsal

    return run_anchored_rehearsal(mode=mode, scenario=scenario)


def main() -> None:
    from anchored_delivery_rehearsal import SCENARIOS

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("anchored",))
    args = parser.parse_args()
    print(json.dumps(
        [run_rehearsal(mode=args.mode, scenario=scenario) for scenario in SCENARIOS],
        indent=2, sort_keys=True,
    ))


if __name__ == "__main__":
    main()

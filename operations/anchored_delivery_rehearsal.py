"""Explicitly select anchored verification for a fictional Aevora AI rehearsal."""
from contextlib import closing
from dataclasses import asdict, replace
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from anchored_evidence_verifier import (
    AnchoredEvidenceVerifier, advance_trust, trust_fingerprint, verify_anchored_receipt,
)
from evidence_verifier import EvidenceManifest, TrustedKey, VerificationBlocked
from synthetic_delivery_rehearsal import _FIXTURE_NOW, _FIXTURE_SCOPE, _attest, _run_rehearsal, _sha


SCENARIOS = (
    "baseline", "stale_trust", "missing_anchor", "missing_audit", "corrupted_audit",
    "interrupted_commit", "nonce_replay", "wrong_company", "wrong_recipient", "stale_policy",
    "coordinated_rollback",
)
_FIXTURE_EPOCH = 2
_FIXTURE_STORE_ID = "anchored-rehearsal-store"


def _provision(path: Path, schema: str, insert: str, values: tuple) -> None:
    with closing(sqlite3.connect(path)) as db, db:
        db.executescript(Path(__file__).with_name(schema).read_text(encoding="utf-8"))
        db.execute(insert, values)


def _verify_anchored_fixture(scenario, artifact, test_log, events):
    scope = _FIXTURE_SCOPE
    manifest_scope = replace(scope, **{
        "wrong_company": {"company_id": "wrong-fixture-company"},
        "wrong_recipient": {"recipient": "wrong-fixture-recipient"},
        "stale_policy": {"policy_version": "fixture-policy-v1"},
    }.get(scenario, {}))
    # A stale expected-scope policy must still fail against the current anchor.
    expected_scope = manifest_scope if scenario == "stale_policy" else scope
    manifest = EvidenceManifest(
        manifest_scope, _sha(artifact), _sha(test_log), "anchored-fixture-nonce", _FIXTURE_NOW + 60,
    )
    keys = {
        "qa": TrustedKey(scope.company_id, "fixture-qa", "independent_qa", _FIXTURE_NOW + 120, b"q" * 32),
        "owner": TrustedKey(scope.company_id, "fixture-owner", "owner_review", _FIXTURE_NOW + 120, b"o" * 32),
    }
    attested = {
        "qa": _attest("qa", keys["qa"], manifest), "owner": _attest("owner", keys["owner"], manifest),
    }

    with TemporaryDirectory() as directory:
        anchor = Path(directory).resolve() / "anchor.sqlite"
        audit = anchor.with_name("audit.sqlite")
        _provision(anchor, "review_anchor.sql", "INSERT INTO review_anchor VALUES (?, ?, ?, ?, ?, ?, ?)", (
            scope.company_id, _FIXTURE_STORE_ID, _FIXTURE_EPOCH,
            trust_fingerprint(scope.company_id, keys), scope.policy_version, 0, "0" * 64,
        ))
        _provision(audit, "review_audit.sql", "INSERT INTO audit_identity VALUES (?, ?)",
                   (scope.company_id, _FIXTURE_STORE_ID))
        prior_anchor = anchor.read_bytes() if scenario in ("interrupted_commit", "coordinated_rollback") else None
        prior_audit = audit.read_bytes() if scenario == "coordinated_rollback" else None
        if scenario == "missing_anchor":
            anchor.unlink()
        if scenario == "missing_audit":
            audit.unlink()
        if scenario == "stale_trust":
            current = {**keys, "qa": replace(keys["qa"], revoked=True)}
            advance_trust(anchor, scope.company_id, expected_epoch=_FIXTURE_EPOCH,
                          new_epoch=_FIXTURE_EPOCH + 1, policy=scope.policy_version, registry=current)

        def verify():
            # Reopen from the selected anchor on each attempt. There is no
            # unanchored verification branch, including on authority outage.
            verifier = AnchoredEvidenceVerifier(
                anchor_path=anchor, audit_path=audit, scope=expected_scope, registry=keys,
                trust_epoch=_FIXTURE_EPOCH, clock=lambda: _FIXTURE_NOW,
            )
            return verifier.verify(manifest, deliverable=artifact, test_log=test_log, **attested)

        receipt = verify()
        verify_anchored_receipt(anchor, audit, scope.company_id, receipt)
        if receipt.release_authorized is not False:
            raise VerificationBlocked("synthetic_receipt_grants_release")
        events.append({
            "stage": "anchored_receipt_readback",
            "audit_sequence": receipt.audit_sequence,
            "audit_sha256": receipt.audit_sha256,
            "manifest_sha256": receipt.manifest_sha256,
            "trust_epoch": _FIXTURE_EPOCH,
            "release_authorized": False,
        })
        if scenario == "nonce_replay":
            verify()
            raise RuntimeError("replay_rehearsal_safety_invariant")
        if scenario == "corrupted_audit":
            with closing(sqlite3.connect(audit)) as db, db:
                db.execute("UPDATE review_audit SET nonce='corrupted-fixture-row'")
            verify_anchored_receipt(anchor, audit, scope.company_id, receipt)
            raise RuntimeError("audit_corruption_rehearsal_safety_invariant")
        if scenario == "interrupted_commit":
            # Reproduce on disk the persisted pair left by an exit between
            # commits. The pinned verifier suite also tests a real child exit.
            anchor.write_bytes(prior_anchor)
            events.append({"stage": "fault_injection", "state": "audit_ahead_of_anchor"})
            verify()
            raise RuntimeError("interrupted_commit_rehearsal_safety_invariant")
        if scenario == "coordinated_rollback":
            anchor.write_bytes(prior_anchor)
            audit.write_bytes(prior_audit)
            events.append({"stage": "fault_injection", "state": "both_files_restored_prior_receipt_retained"})
            # The prior receipt is an independent continuity reference for
            # this run only. The matching local pair cannot detect this alone.
            verify_anchored_receipt(anchor, audit, scope.company_id, receipt)
            raise RuntimeError("coordinated_rollback_rehearsal_safety_invariant")
        return asdict(receipt)


def run_anchored_rehearsal(*, mode: str, scenario: str = "baseline") -> dict:
    """Produce offline evidence only when anchored mode is explicitly selected."""
    if mode != "anchored":
        raise ValueError("explicit anchored mode required")
    if scenario not in SCENARIOS:
        raise ValueError("unknown anchored scenario")
    report = _run_rehearsal(scenario, _verify_anchored_fixture)
    report["verification_mode"] = "anchored"
    return report


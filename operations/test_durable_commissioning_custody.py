"""Offline SQLite durability and separately retained custody pin fixtures."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict, replace
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from threading import Barrier, Lock
import unittest

from continuity_commissioning import ExternalReview, review_payload
from durable_commissioning_custody import CustodyPin, SyntheticDurableCustody
from evidence_verifier import VerificationBlocked
from signed_audit_continuity import ContinuityKey
import test_continuity_commissioning as commissioning_fixtures


class SyntheticIndependentPin:
    """Test-only in-memory monotonic pin, external to the case's SQLite files."""

    def __init__(self, pin):
        self.pin = pin
        self.lock = Lock()
        self.unavailable = False
        self.ambiguous = False

    def current(self, company_id, store_id):
        with self.lock:
            if self.unavailable or (company_id, store_id) != (self.pin.company_id, self.pin.store_id):
                raise OSError("pin unavailable")
            return self.pin

    def advance(self, current, replacement):
        with self.lock:
            if (
                self.unavailable or current != self.pin or replacement.sequence != current.sequence + 1
                or (current.company_id, current.store_id) != (replacement.company_id, replacement.store_id)
            ):
                return False
            self.pin = replacement
            if self.ambiguous:
                raise TimeoutError("pin advanced but acknowledgement was not returned")
            return True


@unittest.skipIf(commissioning_fixtures.signed_fixtures.Ed25519PrivateKey is None, "Ed25519 fixture dependency unavailable")
class DurableCommissioningCustodyTests(unittest.TestCase):
    def setUp(self):
        fixture = commissioning_fixtures.ContinuityCommissioningTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.company = fixture.company
        self.path = fixture.fixture.fixture.root / "commissioning-custody.sqlite"
        schema = Path(__file__).with_name("durable_commissioning_custody.sql").read_text(encoding="utf-8")
        self.pin = SyntheticIndependentPin(CustodyPin(self.company, "synthetic-independent-store", 0, "0" * 64))
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executescript(schema)
            db.execute("INSERT INTO custody_identity VALUES (?, ?)", (self.company, self.pin.pin.store_id))
        self.store().provision_observation(fixture.authority.current)

    def store(self, *, path=None, **overrides):
        settings = dict(
            path=self.path if path is None else path, pin=self.pin, company_id=self.company,
            store_id="synthetic-independent-store", clock=lambda: 100,
        )
        settings.update(overrides)
        return SyntheticDurableCustody(**settings)

    def record(self, *, custody=None, request=None, recovery=None, evidence="a" * 64):
        custody = self.store() if custody is None else custody
        request = self.fixture.request(custody.observe(self.company)) if request is None else request
        return self.fixture.record(
            reviewer=self.fixture.reviewer(custody), request=request, recovery=recovery, evidence=evidence,
        )

    def test_restart_persists_signed_lifecycle_and_duplicate_history(self):
        first = self.record()
        store = self.store()
        manifest = store.private_manifest()
        self.assertEqual(manifest["custody_pin"]["sequence"], 2)
        self.assertEqual(manifest["records"][0]["approval_bundle_sha256"], first.approval_bundle_sha256)
        self.assertEqual(len(manifest["records"][0]["reviews"]), 2)
        for review in manifest["records"][0]["reviews"]:
            self.assertEqual(len(bytes.fromhex(review["signature"])), 64)
        self.assertEqual(manifest["owner_approval"], "NOT_GRANTED")
        self.assertIs(manifest["release_authorized"], False)
        self.assertEqual(manifest, self.store().private_manifest())
        check = """
import json
from pathlib import Path
import sys
from durable_commissioning_custody import CustodyPin, SyntheticDurableCustody
from test_durable_commissioning_custody import SyntheticIndependentPin

pin = CustodyPin(**json.loads(sys.argv[2]))
custody = SyntheticDurableCustody(
    path=Path(sys.argv[1]), company_id=pin.company_id, store_id=pin.store_id,
    pin=SyntheticIndependentPin(pin), clock=lambda: 100,
)
print(json.dumps(custody.private_manifest(), sort_keys=True))
"""
        restarted = subprocess.run(
            [sys.executable, "-c", check, str(self.path), json.dumps(asdict(self.pin.pin))],
            check=True, capture_output=True, timeout=10,
        )
        self.assertEqual(json.loads(restarted.stdout), manifest)
        with self.assertRaisesRegex(VerificationBlocked, "already_recorded"):
            self.record(custody=store)

    def test_independent_pin_blocks_rollback_clone_and_corruption(self):
        clone = self.path.with_name("stale.sqlite")
        shutil.copyfile(self.path, clone)
        self.record()
        with self.assertRaisesRegex(VerificationBlocked, "pin_divergence"):
            self.store(path=clone).private_manifest()
        old = clone.read_bytes()
        full = self.path.read_bytes()
        self.path.write_bytes(old)
        with self.assertRaisesRegex(VerificationBlocked, "pin_divergence"):
            self.store().observe(self.company)
        self.path.write_bytes(full)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE custody_event SET payload='{}' WHERE sequence=1")
        with self.assertRaisesRegex(VerificationBlocked, "audit_chain_invalid"):
            self.store().private_manifest()

    def test_revocation_with_rotation_survives_reopen_and_rejects_stale_keys(self):
        before = self.store().observe(self.company)
        old = before.authority.keys["external-recovery"]
        backend = commissioning_fixtures.signed_fixtures.Ed25519PrivateKey
        replacement = backend.from_private_bytes(b"n" * 32)
        keys = {
            **before.authority.keys,
            "external-recovery": replace(old, revoked=True),
            "external-recovery-v2": ContinuityKey(
                self.company, old.principal_id, old.purpose, replacement.public_key().public_bytes_raw(), 300,
            ),
        }
        after = replace(before, signer_revision=before.signer_revision + 1,
                        authority=replace(before.authority, keys=keys))
        self.store().provision_observation(after)
        with self.assertRaisesRegex(VerificationBlocked, "untrusted_continuity_key"):
            self.record()
        with self.assertRaisesRegex(VerificationBlocked, "lifecycle_regression"):
            self.store().provision_observation(before)
        with self.assertRaisesRegex(VerificationBlocked, "revocation_rollback"):
            self.store().provision_observation(replace(before, signer_revision=after.signer_revision + 1))
        alias = {**keys, "compromised-alias": replace(old, revoked=False)}
        with self.assertRaisesRegex(VerificationBlocked, "invalid_custody_snapshot"):
            self.store().provision_observation(replace(
                after, signer_revision=after.signer_revision + 1, authority=replace(after.authority, keys=alias),
            ))
        self.assertTrue(self.store().observe(self.company).authority.keys["external-recovery"].revoked)
        request = self.fixture.request(after)
        note = ExternalReview("external-recovery-v2", "external_recovery", "f" * 64, "accepted", 125, b"")
        note = replace(note, signature=replacement.sign(review_payload(request, note)))
        self.assertIs(self.record(request=request, recovery=note).release_authorized, False)

    def test_wrong_company_and_unavailable_custody_block(self):
        with self.assertRaisesRegex(VerificationBlocked, "scope_mismatch"):
            self.record(request=replace(self.fixture.request(), company_id="other-company"))
        with self.assertRaisesRegex(VerificationBlocked, "scope_mismatch"):
            self.store().observe("other-company")
        with self.assertRaisesRegex(VerificationBlocked, "identity_mismatch"):
            self.store(company_id="other-company").private_manifest()
        with self.assertRaisesRegex(VerificationBlocked, "pin_unavailable"):
            self.store(pin=None).private_manifest()
        self.pin.unavailable = True
        with self.assertRaisesRegex(VerificationBlocked, "durable_custody_unavailable"):
            self.store().private_manifest()

    def test_pin_advanced_then_ambiguous_ack_blocks_further_operations(self):
        self.pin.ambiguous = True
        with self.assertRaisesRegex(VerificationBlocked, "durable_custody_unavailable"):
            self.record()
        self.pin.ambiguous = False
        with self.assertRaisesRegex(VerificationBlocked, "pin_divergence"):
            self.store().private_manifest()

    def test_committed_synthetic_manifest_and_occ_fixture_are_reproducible(self):
        self.record()
        directory = Path(__file__).with_name("fixtures")
        for name, result in (
            ("commissioning-evidence.synthetic.json", self.store().private_manifest()),
            ("commissioning-occ.synthetic.json", self.store().occ_projection()),
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    (directory / name).read_text(encoding="utf-8"),
                    json.dumps(result, indent=2, sort_keys=True) + "\n",
                )

    def test_competing_requests_across_handles_and_occ_redaction(self):
        barrier = Barrier(2, timeout=5)
        def compete(digest):
            barrier.wait()
            try:
                return self.record(evidence=digest).release_authorized
            except VerificationBlocked as exc:
                return str(exc)

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(pool.map(compete, ("a" * 64, "b" * 64)),
                                  (False, "commissioning_state_changed_or_already_recorded"))
        public = self.store().occ_projection()
        private = self.store().private_manifest()
        self.assertEqual(public["counts"]["checklist_complete_unverified"], 1)
        serialized = json.dumps(public)
        for field in ("custody_pin", "manifest_sha256", "signature", "approval_bundle_sha256", self.company):
            self.assertNotIn(field, serialized)
        self.assertIs(public["execution_authorized"], False)
        self.assertEqual(len(private["records"]), 1)

"""Tests for OCC signed snapshot production and monotonic sequencing."""
import hashlib
import hmac
import json
import tempfile
import unittest
from pathlib import Path

from occ_snapshot_publisher import (
    SnapshotPublisherError,
    SnapshotSequenceStore,
    canonical_snapshot_bytes,
    policy_file_sha256,
    sign_snapshot,
    write_envelope_atomic,
)


SECRET = b"test-only-secret-material-at-least-32-bytes"
POLICY = "a" * 64


class SnapshotPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SnapshotSequenceStore(Path(self.temp.name) / "sequence.sqlite3")

    def issue_clear(self, now=1000.0, version=7):
        return self.store.issue(
            status="CLEAR",
            stop_conditions=[],
            evidence_refs=[],
            policy_sha256=POLICY,
            portfolio_version=version,
            now_epoch=now,
            ttl_seconds=120,
            secret=SECRET,
        )

    def test_shared_polybot_interoperability_vector(self):
        fixture_path = Path(__file__).parent / "fixtures" / "occ-control-envelope.test.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        secret = bytes.fromhex(fixture["secret_hex"])
        snapshot = fixture["envelope"]["snapshot"]
        expected = fixture["envelope"]["signature_hex"]
        self.assertEqual(sign_snapshot(snapshot, secret), expected)
        self.assertEqual(sign_snapshot(dict(reversed(tuple(snapshot.items()))), secret), expected)

        for field in ("generated_at_epoch", "expires_at_epoch"):
            with self.subTest(timestamp=field):
                self.assertIs(type(snapshot[field]), float)
                tampered = {**snapshot, field: int(snapshot[field])}
                self.assertNotEqual(canonical_snapshot_bytes(tampered), canonical_snapshot_bytes(snapshot))
                self.assertNotEqual(sign_snapshot(tampered, secret), expected)
        tampered = {**snapshot, "evidence_refs": ["occ:test-vector:altered"]}
        self.assertNotEqual(sign_snapshot(tampered, secret), expected)

    def test_policy_file_digest_uses_exact_file_bytes(self):
        policy_path = Path(self.temp.name) / "policy.json"
        policy_path.write_bytes(b'{"approved":true}\n')
        self.assertEqual(
            policy_file_sha256(policy_path),
            hashlib.sha256(b'{"approved":true}\n').hexdigest(),
        )

    def test_clear_snapshot_is_canonical_and_hmac_signed(self):
        envelope = self.issue_clear()
        snapshot = envelope["snapshot"]
        expected = hmac.new(
            SECRET, canonical_snapshot_bytes(snapshot), hashlib.sha256
        ).hexdigest()
        self.assertEqual(envelope["signature_hex"], expected)
        self.assertEqual(snapshot["schema_version"], 1)
        self.assertEqual(snapshot["source_system"], "OCC")
        self.assertEqual(snapshot["status"], "CLEAR")
        self.assertEqual(snapshot["stop_conditions"], [])
        self.assertEqual(snapshot["evidence_refs"], [])
        self.assertEqual(snapshot["expires_at_epoch"], 1120.0)

    def test_halt_requires_condition_and_evidence(self):
        envelope = self.store.issue(
            status="HALT",
            stop_conditions=["position_or_order_state_uncertain"],
            evidence_refs=["occ:incident:INC-1"],
            policy_sha256=POLICY,
            portfolio_version=3,
            now_epoch=1000,
            ttl_seconds=60,
            secret=SECRET,
        )
        self.assertEqual(envelope["snapshot"]["status"], "HALT")
        self.assertTrue(envelope["signature_hex"])

    def test_clear_with_stop_condition_is_rejected(self):
        with self.assertRaises(SnapshotPublisherError):
            self.store.issue(
                status="CLEAR",
                stop_conditions=["incident_severity_critical"],
                evidence_refs=["occ:incident:1"],
                policy_sha256=POLICY,
                portfolio_version=0,
                now_epoch=1000,
                ttl_seconds=60,
                secret=SECRET,
            )

    def test_unknown_stop_condition_is_rejected(self):
        with self.assertRaises(SnapshotPublisherError):
            self.store.issue(
                status="HALT",
                stop_conditions=["trade_anyway"],
                evidence_refs=["occ:incident:1"],
                policy_sha256=POLICY,
                portfolio_version=0,
                now_epoch=1000,
                ttl_seconds=60,
                secret=SECRET,
            )

    def test_ttl_above_receiver_limit_is_rejected(self):
        with self.assertRaises(SnapshotPublisherError):
            self.store.issue(
                status="CLEAR", stop_conditions=[], evidence_refs=[],
                policy_sha256=POLICY, portfolio_version=0,
                now_epoch=1000, ttl_seconds=301, secret=SECRET,
            )

    def test_clock_rollback_and_duplicate_timestamp_are_rejected(self):
        self.issue_clear(now=1000)
        for stamp in (999.0, 1000.0):
            with self.subTest(stamp=stamp):
                with self.assertRaises(SnapshotPublisherError):
                    self.issue_clear(now=stamp)

    def test_sequence_state_survives_restart(self):
        self.issue_clear(now=1000)
        restarted = SnapshotSequenceStore(Path(self.temp.name) / "sequence.sqlite3")
        for timestamp in (999, 1000):
            with self.subTest(timestamp=timestamp), self.assertRaises(SnapshotPublisherError):
                restarted.issue(
                    status="CLEAR", stop_conditions=[], evidence_refs=[],
                    policy_sha256=POLICY, portfolio_version=0,
                    now_epoch=timestamp, ttl_seconds=60, secret=SECRET,
                )
        envelope = restarted.issue(
            status="CLEAR", stop_conditions=[], evidence_refs=[],
            policy_sha256=POLICY, portfolio_version=0,
            now_epoch=1001, ttl_seconds=60, secret=SECRET,
        )
        self.assertEqual(envelope["snapshot"]["generated_at_epoch"], 1001.0)

    def test_envelope_is_atomically_written_without_secret(self):
        envelope = self.issue_clear()
        destination = Path(self.temp.name) / "shared" / "occ-control-envelope.json"
        written = write_envelope_atomic(envelope, destination)
        self.assertEqual(written, destination)
        decoded = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(decoded, envelope)
        self.assertNotIn(SECRET.decode("utf-8"), destination.read_text(encoding="utf-8"))
        self.assertEqual(destination.stat().st_mode & 0o777, 0o600)

    def test_boolean_version_and_timestamp_are_rejected(self):
        with self.assertRaises(SnapshotPublisherError):
            self.store.issue(
                status="CLEAR", stop_conditions=[], evidence_refs=[],
                policy_sha256=POLICY, portfolio_version=True,
                now_epoch=1000, ttl_seconds=60, secret=SECRET,
            )
        with self.assertRaises(SnapshotPublisherError):
            self.store.issue(
                status="CLEAR", stop_conditions=[], evidence_refs=[],
                policy_sha256=POLICY, portfolio_version=0,
                now_epoch=True, ttl_seconds=60, secret=SECRET,
            )


if __name__ == "__main__":
    unittest.main()

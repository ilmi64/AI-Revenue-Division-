"""Tests for the conservative OCC draft-baseline publisher."""
import json
import tempfile
import unittest
from pathlib import Path

from occ_snapshot_publisher import SnapshotPublisherError
from occ_fail_closed_publisher import (
    FailClosedPublicationError,
    publish_draft_baseline_halt,
)


SECRET = b"test-only-secret-material-at-least-32-bytes"


class FailClosedPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = self.root / "risk-control-policy.json"
        self.policy.write_text(
            json.dumps({
                "schema_version": "1.0.0",
                "status": "draft_control_baseline",
                "authority": {"trade_authority": "not_granted"},
            }),
            encoding="utf-8",
        )

    def publish(self, policy_path=None, **kwargs):
        return publish_draft_baseline_halt(
            policy_path=policy_path or self.policy,
            sequence_db_path=self.root / "sequence.sqlite3",
            inbox_path=self.root / "shared" / "envelope.json",
            portfolio_version=7,
            secret=SECRET,
            now_epoch=1000.0,
            **kwargs,
        )

    def test_draft_baseline_publishes_only_short_lived_halt(self):
        envelope = self.publish()
        snapshot = envelope["snapshot"]
        self.assertEqual(snapshot["status"], "HALT")
        self.assertEqual(
            snapshot["stop_conditions"], ["required_owner_approval_missing"]
        )
        self.assertEqual(snapshot["portfolio_version"], 7)
        self.assertEqual(snapshot["expires_at_epoch"], 1060.0)
        self.assertIn("draft_control_baseline", snapshot["evidence_refs"][0])

    def test_no_policy_status_can_produce_clear(self):
        policy = json.loads(self.policy.read_text(encoding="utf-8"))
        policy["status"] = "approved"
        self.policy.write_text(json.dumps(policy), encoding="utf-8")
        envelope = self.publish()
        self.assertEqual(envelope["snapshot"]["status"], "HALT")

    def test_published_envelope_contains_no_secret(self):
        self.publish()
        raw = (self.root / "shared" / "envelope.json").read_text(encoding="utf-8")
        self.assertNotIn(SECRET.decode("utf-8"), raw)
        self.assertNotIn(SECRET.hex(), raw)

    def test_missing_policy_refuses_publication(self):
        with self.assertRaises(FailClosedPublicationError):
            self.publish(policy_path=self.root / "missing.json")

    def test_invalid_portfolio_version_refuses_publication(self):
        with self.assertRaises(SnapshotPublisherError):
            publish_draft_baseline_halt(
                policy_path=self.policy,
                sequence_db_path=self.root / "sequence.sqlite3",
                inbox_path=self.root / "shared" / "envelope.json",
                portfolio_version=True,
                secret=SECRET,
                now_epoch=1000.0,
            )


if __name__ == "__main__":
    unittest.main()

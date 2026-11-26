"""Tests use only disposable staged bytes."""
import base64
from hashlib import sha256, sha512
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from check_revenue_native_artifacts import _MANIFEST, verify_staged


class NativeArtifactPreflightTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.stage = Path(folder.name)

    def test_known_manifest_reports_every_absent_artifact(self):
        manifest = json.loads(_MANIFEST.read_bytes())
        result = verify_staged(self.stage, manifest)
        self.assertEqual(len(result["artifact_checks"]), len(manifest["artifacts"]))
        self.assertEqual(set(result["artifact_checks"].values()), {"MISSING"})
        self.assertFalse(result["all_candidate_bytes_match"])

    def test_sha256_and_npm_sri_match_without_conferring_authority(self):
        raw = b"not a real executable or package"
        (self.stage / "cpu.tar.gz").write_bytes(raw)
        (self.stage / "npm.tgz").write_bytes(raw)
        result = verify_staged(self.stage, {"artifacts": [
            {"file": "cpu.tar.gz", "integrity": "sha256:" + sha256(raw).hexdigest(), "size_bytes": len(raw)},
            {"file": "npm.tgz", "integrity": "sha512-" + base64.b64encode(sha512(raw).digest()).decode("ascii")},
        ]})
        self.assertTrue(result["all_candidate_bytes_match"])
        for field in ("installation_authorized", "native_execution_verified", "release_authorized"):
            self.assertIs(result[field], False)

    def test_mismatched_bytes_size_and_links_are_rejected(self):
        path = self.stage / "weights.gguf"
        path.write_bytes(b"other")
        pin = "sha256:" + sha256(b"known").hexdigest()
        (self.stage / "link.gguf").symlink_to(path)
        checks = verify_staged(self.stage, {"artifacts": [
            {"file": "weights.gguf", "integrity": pin},
            {"file": "link.gguf", "integrity": pin},
        ]})["artifact_checks"]
        self.assertEqual(checks, {"weights.gguf": "DIGEST_MISMATCH", "link.gguf": "UNREADABLE"})
        sized = verify_staged(self.stage, {"artifacts": [
            {"file": "weights.gguf", "integrity": pin, "size_bytes": 123},
        ]})["artifact_checks"]
        self.assertEqual(sized["weights.gguf"], "SIZE_MISMATCH")
        with self.assertRaisesRegex(ValueError, "basename"):
            verify_staged(self.stage, {"artifacts": [{"file": "../weights.gguf", "integrity": pin}]})

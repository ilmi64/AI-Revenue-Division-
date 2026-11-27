"""Offline checks for the exact launcher capability and cleanup gates."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

_PROBE = Path(__file__).parent / "revenue_isolation_probe"
_ID = "c" * 64
_CAPABILITY = 'systemd 2 true true true true ["name=rootless","name=cgroupns"]'


class PilotSupervisionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name)
        self.calls = self.path / "calls"
        docker = self.path / "docker"
        docker.write_text("""#!/bin/bash
printf '%s\\n' "$*" >> "$DAIVORA_TEST_CALLS"
[[ "$1" == --host=unix:///var/run/docker.sock ]] || exit 91
case "$2" in
  info) printf '%s\\n' "$DAIVORA_TEST_CAPABILITY";;
  rm) exit "${DAIVORA_TEST_REMOVE_STATUS:-0}";;
  ps) printf '%s' "${DAIVORA_TEST_REMAINING:-}";;
  *) exit 92;;
esac
""")
        docker.chmod(0o700)
        self.env = {
            **os.environ,
            "PATH": f"{self.path}:{os.environ['PATH']}",
            "DAIVORA_TEST_CALLS": str(self.calls),
            "DAIVORA_TEST_CAPABILITY": _CAPABILITY,
        }

    def launch(self, *args):
        return subprocess.run(["bash", *args], env=self.env, capture_output=True,
                              text=True, check=False, timeout=5)

    def test_each_missing_controller_denies_before_create(self):
        for capability in (
            'none 2 false false false false ["name=rootless"]',
            _CAPABILITY.replace("systemd 2", "systemd 1"),
            _CAPABILITY.replace("name=rootless", "name=seccomp"),
            *(" ".join(_CAPABILITY.split()[:i] + ["false"] + _CAPABILITY.split()[i + 1:])
              for i in range(2, 6)),
        ):
            with self.subTest(capability=capability):
                self.env["DAIVORA_TEST_CAPABILITY"] = capability
                result = self.launch(_PROBE / "run-approved-native-pilot.sh",
                                     f"sha256:{_ID}", "/unavailable-stage", str(self.path))
                self.assertEqual(result.returncode, 125)
        self.assertTrue(all(" info " in line for line in self.calls.read_text().splitlines()))

    def test_qualified_capability_preflight_remains_read_only(self):
        result = self.launch(_PROBE / "run-approved-native-pilot.sh", "--preflight")
        self.assertEqual(result.returncode, 0)
        self.assertIn(" info ", self.calls.read_text())

    def test_cleanup_requires_daemon_acknowledgment_and_absence(self):
        command = 'source "$1"; remove_capsule "$2"'
        args = ("-c", command, "supervision", _PROBE / "capsule-supervision.sh", _ID)
        first = self.launch(*args)
        self.assertEqual(first.returncode, 0)
        self.assertIn(f"--filter id={_ID}", self.calls.read_text())
        self.env["DAIVORA_TEST_REMAINING"] = _ID
        self.assertNotEqual(self.launch(*args).returncode, 0)
        self.env["DAIVORA_TEST_REMOVE_STATUS"] = "7"
        self.assertNotEqual(self.launch(*args).returncode, 0)

    def test_cleanup_does_not_accept_other_identifiers(self):
        result = self.launch("-c", 'source "$1"; remove_capsule "$2"', "supervision",
                             _PROBE / "capsule-supervision.sh", "production")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.calls.exists())

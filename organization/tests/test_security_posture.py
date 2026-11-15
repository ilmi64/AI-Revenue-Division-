import tempfile
import unittest
from pathlib import Path

from organization.tools.validate_security_posture import (
    build_report, inspect_action_pins, validate_workflow_permissions
)


class SecurityPostureTests(unittest.TestCase):
    def test_only_contents_read_permission_is_accepted(self):
        self.assertEqual(validate_workflow_permissions("permissions:\n  contents: read\n"), [])
        self.assertTrue(validate_workflow_permissions("permissions:\n  contents: write\n"))
        self.assertTrue(validate_workflow_permissions("permissions:\n  write-all\n"))

    def test_unpinned_actions_are_reported_without_secret_output(self):
        warnings = inspect_action_pins("      uses: actions/checkout@v4\n")
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["action"], "actions/checkout")

    def test_verified_full_commit_sha_pins_are_accepted(self):
        workflow = (
            "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1\\n"
            "uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0\\n"
        )
        self.assertEqual(inspect_action_pins(workflow), [])

    def test_secret_scan_flags_credential_shape_and_redacts_value(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/org-control-centre-checks.yml").write_text(
                "permissions:\n  contents: read\n", encoding="utf-8"
            )
            fake_token = "ghp_" + ("A" * 36)
            (root / "sample.py").write_text(
                f'token = "{fake_token}"\n', encoding="utf-8"
            )
            report = build_report(root)
            self.assertEqual(report["secret_scan"]["finding_count"], 1)
            self.assertEqual(report["secret_scan"]["findings_redacted"][0]["rule_id"], "GITHUB_TOKEN")
            self.assertNotIn("ghp_", str(report))

    def test_placeholders_and_non_secret_hashes_are_not_flagged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/org-control-centre-checks.yml").write_text(
                "permissions:\n  contents: read\n", encoding="utf-8"
            )
            (root / "example.md").write_text(
                "Use YOUR_API_KEY_HERE; SHA256: " + "a" * 64, encoding="utf-8"
            )
            report = build_report(root)
            self.assertEqual(report["secret_scan"]["finding_count"], 0)
            self.assertEqual(report["status"], "checks_passed")


if __name__ == "__main__":
    unittest.main()

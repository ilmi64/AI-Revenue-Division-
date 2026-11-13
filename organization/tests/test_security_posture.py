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

    def test_secret_scan_flags_credential_shape_and_redacts_value(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/org-control-centre-checks.yml").write_text(
                "permissions:\n  contents: read\n", encoding="utf-8"
            )
            (root / "sample.py").write_text(
                'token = "ghp_" + "A" * 36\n', encoding="utf-8"
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

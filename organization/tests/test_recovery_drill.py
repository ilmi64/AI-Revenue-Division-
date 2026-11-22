import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from run_recovery_drill import run_drill

class RecoveryDrillTests(unittest.TestCase):
    def test_fixture_backup_restore_rollback_and_health_checks_pass(self):
        report = run_drill()
        self.assertTrue(report["passed"])
        self.assertEqual([item["id"] for item in report["checks"]], [
            "backup_integrity", "restore_integrity", "rollback_integrity", "restart_health_check"
        ])
        self.assertTrue(all(item["passed"] for item in report["checks"]))
    def test_drill_never_claims_production_recovery_or_touches_external_systems(self):
        report = run_drill()
        self.assertFalse(report["production_recovery_verified"])
        self.assertFalse(report["external_systems_touched"])
        self.assertFalse(report["credentials_used"])
        self.assertEqual(report["scope"], "isolated_temporary_fixture_only")
        self.assertGreaterEqual(len(report["limitations"]), 4)

if __name__ == "__main__":
    unittest.main()

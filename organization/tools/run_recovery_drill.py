#!/usr/bin/env python3
"""Run a non-destructive file-level recovery drill in an isolated temporary directory.

This validates the drill harness only. It does not back up or restore production data,
invoke service commands, access credentials, or change external systems.
"""
from __future__ import annotations
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_drill() -> dict:
    checks = []
    with tempfile.TemporaryDirectory(prefix="org-recovery-drill-") as temp:
        root = Path(temp)
        live = root / "fixture-live"
        backup = root / "fixture-backup"
        live.mkdir()
        (live / "service-config.txt").write_text("mode=known-good\n", encoding="utf-8")
        (live / "health-marker.txt").write_text("health=ready\n", encoding="utf-8")
        baseline = {p.name: digest(p) for p in sorted(live.iterdir()) if p.is_file()}

        shutil.copytree(live, backup)
        backup_manifest = {p.name: digest(p) for p in sorted(backup.iterdir()) if p.is_file()}
        backup_ok = baseline == backup_manifest
        checks.append({"id": "backup_integrity", "passed": backup_ok,
                       "detail": "Temporary fixture backup hashes match the source."})

        (live / "service-config.txt").write_text("mode=deliberately-corrupted\n", encoding="utf-8")
        shutil.copy2(backup / "service-config.txt", live / "service-config.txt")
        restore_ok = {p.name: digest(p) for p in sorted(live.iterdir()) if p.is_file()} == baseline
        checks.append({"id": "restore_integrity", "passed": restore_ok,
                       "detail": "Restored temporary fixture hashes match the known-good baseline."})

        pre_change = root / "pre-change-snapshot"
        shutil.copytree(live, pre_change)
        (live / "service-config.txt").write_text("mode=rollback-test-change\n", encoding="utf-8")
        shutil.copy2(pre_change / "service-config.txt", live / "service-config.txt")
        rollback_ok = {p.name: digest(p) for p in sorted(live.iterdir()) if p.is_file()} == baseline
        checks.append({"id": "rollback_integrity", "passed": rollback_ok,
                       "detail": "Rollback returns the temporary fixture to its pre-change hashes."})

        marker = live / "health-marker.txt"
        restart_check_ok = marker.is_file() and marker.read_text(encoding="utf-8").strip() == "health=ready"
        checks.append({"id": "restart_health_check", "passed": restart_check_ok,
                       "detail": "Synthetic service health marker is present and ready; no service was started."})

    return {
        "scope": "isolated_temporary_fixture_only",
        "production_recovery_verified": False,
        "external_systems_touched": False,
        "credentials_used": False,
        "checks": checks,
        "passed": all(item["passed"] for item in checks),
        "limitations": [
            "No production backup source or destination was accessed.",
            "No real application, database, host, container or cloud service was stopped or restarted.",
            "No production rollback, RTO or RPO was measured.",
            "A successful drill validates this harness only, not operational readiness."
        ]
    }

if __name__ == "__main__":
    report = run_drill()
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)

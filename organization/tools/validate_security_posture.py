#!/usr/bin/env python3
"""Static, read-only repository security posture checks; no network or secret values emitted."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

SECRET_RULES = [
    ("PRIVATE_KEY_BLOCK", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    ("AWS_ACCESS_KEY_ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("SLACK_TOKEN", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b")),
    ("STRIPE_SECRET_KEY", re.compile(r"\bsk_(?:live|test)_[0-9A-Za-z]{20,}\b")),
]
TEXT_SUFFIXES = {".py", ".json", ".md", ".csv", ".yml", ".yaml", ".toml", ".txt", ".sh", ".cfg", ".ini"}
EXCLUDED_PARTS = {".git", "__pycache__", ".venv", "venv", "node_modules"}


def tracked_files(root: Path) -> list[Path]:
    try:
        git_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        ).stdout.strip()
        if Path(git_root).resolve() != root.resolve():
            raise subprocess.CalledProcessError(1, "git rev-parse --show-toplevel")
        result = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        names = [name for name in result.stdout.decode("utf-8", "replace").split("\0") if name]
        return [root / name for name in names if (root / name).is_file()]
    except (OSError, subprocess.CalledProcessError):
        return [
            path for path in root.rglob("*")
            if path.is_file() and not any(part in EXCLUDED_PARTS for part in path.parts)
        ]


def scan_secrets(root: Path) -> list[dict]:
    findings = []
    for path in tracked_files(root):
        if path.suffix.lower() not in TEXT_SUFFIXES or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for rule_id, pattern in SECRET_RULES:
            if pattern.search(content):
                findings.append({"file": path.relative_to(root).as_posix(), "rule_id": rule_id})
    return findings


def validate_workflow_permissions(workflow_text: str) -> list[str]:
    matches = re.findall(r"(?ms)^permissions:[ \t]*\n((?:[ \t]+[^\n]*\n)+)", workflow_text)
    if len(matches) != 1:
        return ["Workflow must declare exactly one explicit top-level permissions block."]
    entries = [line.strip() for line in matches[0].splitlines() if line.strip()]
    if entries != ["contents: read"]:
        return ["Workflow permissions must be restricted to exactly contents: read."]
    return []


def inspect_action_pins(workflow_text: str) -> list[dict]:
    warnings = []
    for line_number, line in enumerate(workflow_text.splitlines(), 1):
        match = re.search(r"\buses:\s*([^\s#]+)", line)
        if match and not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-fA-F]{40}", match.group(1)):
            warnings.append({
                "line": line_number,
                "action": match.group(1).split("@", 1)[0],
                "issue": "action reference is not pinned to a full immutable commit SHA"
            })
    return warnings


def build_report(root: Path) -> dict:
    workflow_path = root / ".github/workflows/org-control-centre-checks.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""
    permission_errors = validate_workflow_permissions(workflow_text)
    findings = scan_secrets(root)
    dependency_manifests = [
        path.relative_to(root).as_posix()
        for path in tracked_files(root)
        if path.name.lower() in {"requirements.txt", "pyproject.toml", "poetry.lock", "pipfile", "pipfile.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}
    ]
    pin_warnings = inspect_action_pins(workflow_text)
    errors = permission_errors + [
        f"Potential credential pattern {item['rule_id']} in {item['file']}."
        for item in findings
    ]
    return {
        "scope": "static_tracked_text_and_workflow_policy_checks",
        "status": "failed" if errors else ("review_required" if pin_warnings else "checks_passed"),
        "secret_scan": {
            "files_scanned": len(tracked_files(root)),
            "finding_count": len(findings),
            "findings_redacted": findings
        },
        "workflow_permissions": {
            "expected": {"contents": "read"},
            "errors": permission_errors,
            "least_privilege_check_passed": not permission_errors
        },
        "action_dependency_integrity": {
            "dependency_manifests_detected": dependency_manifests,
            "unpinned_action_warnings": pin_warnings,
            "note": "Action tags are mutable; pin each action to a verified full commit SHA before treating supply-chain pinning as complete."
        },
        "recovery_access_policy": {
            "production_restore_or_rollback": "explicit_owner_approval_and_independent_second_review_required",
            "approved_operator_scope": "named_owner_approved_operators_only",
            "credential_storage": "never_in_repository_logs_or_drill_artifacts",
            "automated_drill": "isolated_temporary_fixture_only"
        },
        "errors": errors,
        "limitations": [
            "Static pattern scanning is not a complete secret detector and cannot establish that credentials were never exposed in repository history.",
            "Workflow YAML is checked for declared permissions, not actual repository, organisation, app, or account permissions.",
            "Dependency inventory is informational; no vulnerability database, lockfile resolution, malware scan, or third-party action review is performed.",
            "Passing checks are not a penetration test, security certification, production hardening assessment, or proof of system security."
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report = build_report(args.root.resolve())
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

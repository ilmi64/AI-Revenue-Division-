"""Validate canonical OCC risk/incident records and the supplemental evidence index."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ORG = Path(__file__).resolve().parents[1]
RISK_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ORG / "tools"))
from validate_incident_register import validate as validate_incidents

PATHS = {
    "incidents": ORG / "incident-register.json",
    "risks": ORG / "risk-register.json",
    "decisions": ORG / "decision-register.json",
    "queue": ORG / "work-queue.json",
    "registry": ORG / "division-registry.json",
    "evidence": RISK_DIR / "evidence-register.json",
}
EVIDENCE_REQUIRED = {
    "evidence_id", "recorded_at_utc", "source_division", "evidence_type",
    "description", "source_reference", "captured_at_utc", "integrity_status",
    "review_status", "related_incident_ids", "access_classification",
    "retention_review_at_utc",
}
SECRET_KEYS = {
    "password", "passwd", "mfa", "mfa_code", "seed", "seed_phrase",
    "private_key", "secret", "api_key", "api_secret", "access_token",
}


def _secret_key_paths(value, path="$"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in SECRET_KEYS:
                found.append(f"{path}.{key}")
            found.extend(_secret_key_paths(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_secret_key_paths(child, f"{path}[{index}]"))
    return found


def validate_evidence_register(evidence, incidents, registry):
    errors = []
    if not isinstance(evidence, dict):
        return ["Evidence register root must be an object."]
    if evidence.get("schema_version") != "1.0.0":
        errors.append("Evidence register schema_version must be 1.0.0.")
    rows = evidence.get("records")
    if not isinstance(rows, list):
        return errors + ["Evidence register records must be an array."]
    division_ids = {
        row.get("id") for row in registry.get("divisions", [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    incident_ids = {
        row.get("id") for row in incidents.get("records", [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"Evidence record at index {index} must be an object.")
            continue
        evidence_id = row.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            errors.append(f"Evidence record at index {index} requires a non-empty evidence_id.")
            continue
        if evidence_id in seen:
            errors.append(f"Evidence IDs must be unique: {evidence_id}.")
        seen.add(evidence_id)
        missing = EVIDENCE_REQUIRED - set(row)
        if missing:
            errors.append(f"Evidence {evidence_id} missing fields: {sorted(missing)}.")
        if row.get("source_division") not in division_ids:
            errors.append(f"Evidence {evidence_id} references an unknown source division.")
        if row.get("integrity_status") not in {"not_checked", "hash_recorded", "verified", "integrity_failed"}:
            errors.append(f"Evidence {evidence_id} has invalid integrity_status.")
        if row.get("review_status") not in {"unreviewed", "accepted", "rejected", "superseded"}:
            errors.append(f"Evidence {evidence_id} has invalid review_status.")
        if row.get("access_classification") not in {"internal", "restricted", "confidential"}:
            errors.append(f"Evidence {evidence_id} has invalid access_classification.")
        related = row.get("related_incident_ids", [])
        if not isinstance(related, list) or any(value not in incident_ids for value in related):
            errors.append(f"Evidence {evidence_id} contains an invalid incident reference.")
    for path in _secret_key_paths(evidence):
        errors.append(f"Evidence register contains prohibited secret field: {path}.")
    return errors


def validate_all(incidents, risks, decisions, queue, registry, evidence):
    errors = validate_incidents(incidents, risks, decisions, queue, registry)
    errors.extend(validate_evidence_register(evidence, incidents, registry))
    if not isinstance(risks, dict) or risks.get("schema_version") != 1:
        errors.append("Canonical OCC risk register schema_version must be 1.")
    risk_rows = risks.get("records", []) if isinstance(risks, dict) else []
    if not isinstance(risk_rows, list):
        errors.append("Canonical OCC risk register records must be an array.")
        risk_rows = []
    seen = set()
    task_ids = {
        row.get("id") for row in queue.get("tasks", [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    division_ids = {
        row.get("id") for row in registry.get("divisions", [])
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    for index, row in enumerate(risk_rows):
        if not isinstance(row, dict):
            errors.append(f"Risk record at index {index} must be an object.")
            continue
        risk_id = row.get("id")
        if not isinstance(risk_id, str) or not risk_id.strip():
            errors.append(f"Risk record at index {index} requires a non-empty id.")
            continue
        if risk_id in seen:
            errors.append(f"Risk IDs must be unique: {risk_id}.")
        seen.add(risk_id)
        for field in ("severity", "status", "description", "division_id", "mitigation", "owner_assignment"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"Risk {risk_id} requires non-empty {field}.")
        if row.get("severity") not in {"critical", "high", "medium", "low", "unassessed"}:
            errors.append(f"Risk {risk_id} has invalid severity.")
        if row.get("status") not in {"open", "mitigating", "accepted_pending_owner_approval", "closed", "unassessed"}:
            errors.append(f"Risk {risk_id} has invalid status.")
        if row.get("division_id") not in division_ids:
            errors.append(f"Risk {risk_id} references an unknown division.")
        related_tasks = row.get("related_task_ids", [])
        if not isinstance(related_tasks, list) or any(value not in task_ids for value in related_tasks):
            errors.append(f"Risk {risk_id} contains an invalid task reference.")
    return errors


def main():
    loaded = {
        key: json.loads(path.read_text(encoding="utf-8"))
        for key, path in PATHS.items()
    }
    errors = validate_all(
        loaded["incidents"], loaded["risks"], loaded["decisions"],
        loaded["queue"], loaded["registry"], loaded["evidence"]
    )
    if errors:
        print("\n".join(errors))
        return 1
    print(
        "OCC risk/evidence validation passed: "
        f"{len(loaded['risks']['records'])} risk records, "
        f"{len(loaded['incidents']['records'])} incidents, "
        f"{len(loaded['evidence']['records'])} evidence records. "
        "This is structural validation, not operational readiness."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

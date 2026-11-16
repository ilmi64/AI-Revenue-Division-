"""Validate draft risk, incident and evidence registers without external side effects."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INCIDENT_PATH = ROOT / "incident-register.json"
EVIDENCE_PATH = ROOT / "evidence-register.json"
RISK_PATH = ROOT / "risk-register.json"
DIVISION_IDS = {
    "executive", "ai-revenue", "technology", "research", "finance", "risk",
    "crypto", "ecommerce", "animora", "tisrd", "business-commercial",
}
SECRET_KEYS = {
    "password", "passwd", "mfa", "mfa_code", "seed", "seed_phrase",
    "private_key", "secret", "api_key", "api_secret", "access_token",
}
INCIDENT_REQUIRED = {
    "incident_id", "detected_at_utc", "reporting_division", "affected_divisions",
    "category", "severity", "status", "facts", "hypotheses",
    "evidence_references", "containment", "owner_status",
    "next_review_at_utc", "created_at_utc", "last_updated_at_utc",
}
EVIDENCE_REQUIRED = {
    "evidence_id", "recorded_at_utc", "source_division", "evidence_type",
    "description", "source_reference", "captured_at_utc", "integrity_status",
    "review_status", "related_incident_ids", "access_classification",
    "retention_review_at_utc",
}
RISK_REQUIRED = {
    "risk_id", "division_id", "title", "description", "likelihood", "impact",
    "status", "existing_controls", "required_actions", "owner_status",
    "evidence_references", "review_due_at_utc",
}


def _secret_key_paths(value, path="$"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_norm = str(key).lower()
            if key_norm in SECRET_KEYS:
                found.append(f"{path}.{key}")
            found.extend(_secret_key_paths(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_secret_key_paths(child, f"{path}[{index}]"))
    return found


def validate_registers(incidents: dict, evidence: dict, risks: dict) -> list[str]:
    errors = []
    for name, data in (("incident", incidents), ("evidence", evidence), ("risk", risks)):
        if data.get("schema_version") != "1.0.0":
            errors.append(f"{name} register schema_version must be 1.0.0")
        if not isinstance(data.get("records"), list):
            errors.append(f"{name} register records must be a list")
        for path in _secret_key_paths(data):
            errors.append(f"{name} register contains prohibited secret field: {path}")

    incident_rows = incidents.get("records", [])
    evidence_rows = evidence.get("records", [])
    risk_rows = risks.get("records", [])
    if not all(isinstance(row, dict) for row in incident_rows + evidence_rows + risk_rows):
        return errors + ["all register records must be objects"]

    def unique_ids(rows, key, label):
        values = [row.get(key) for row in rows]
        if any(not isinstance(value, str) or not value.strip() for value in values):
            errors.append(f"{label} records require non-empty {key}")
        if len(values) != len(set(values)):
            errors.append(f"{label} record IDs must be unique")

    unique_ids(incident_rows, "incident_id", "incident")
    unique_ids(evidence_rows, "evidence_id", "evidence")
    unique_ids(risk_rows, "risk_id", "risk")

    evidence_ids = {row.get("evidence_id") for row in evidence_rows}
    incident_ids = {row.get("incident_id") for row in incident_rows}
    for row in incident_rows:
        missing = INCIDENT_REQUIRED - set(row)
        if missing:
            errors.append(f"{row.get('incident_id', '<unknown>')}: missing incident fields {sorted(missing)}")
        if row.get("reporting_division") not in DIVISION_IDS:
            errors.append(f"{row.get('incident_id', '<unknown>')}: unknown reporting division")
        if not set(row.get("affected_divisions", [])).issubset(DIVISION_IDS):
            errors.append(f"{row.get('incident_id', '<unknown>')}: unknown affected division")
        if row.get("severity") not in {"SEV1", "SEV2", "SEV3", "SEV4"}:
            errors.append(f"{row.get('incident_id', '<unknown>')}: invalid severity")
        if row.get("status") not in {"detected", "triaging", "contained", "investigating", "recovering", "validating", "closed"}:
            errors.append(f"{row.get('incident_id', '<unknown>')}: invalid status")
        if not isinstance(row.get("facts"), list) or not isinstance(row.get("hypotheses"), list):
            errors.append(f"{row.get('incident_id', '<unknown>')}: facts and hypotheses must be separate lists")
        if not set(row.get("evidence_references", [])).issubset(evidence_ids):
            errors.append(f"{row.get('incident_id', '<unknown>')}: unknown evidence reference")

    for row in evidence_rows:
        missing = EVIDENCE_REQUIRED - set(row)
        if missing:
            errors.append(f"{row.get('evidence_id', '<unknown>')}: missing evidence fields {sorted(missing)}")
        if row.get("source_division") not in DIVISION_IDS:
            errors.append(f"{row.get('evidence_id', '<unknown>')}: unknown source division")
        if row.get("integrity_status") not in {"not_checked", "hash_recorded", "verified", "integrity_failed"}:
            errors.append(f"{row.get('evidence_id', '<unknown>')}: invalid integrity status")
        if row.get("review_status") not in {"unreviewed", "accepted", "rejected", "superseded"}:
            errors.append(f"{row.get('evidence_id', '<unknown>')}: invalid review status")
        if row.get("access_classification") not in {"internal", "restricted", "confidential"}:
            errors.append(f"{row.get('evidence_id', '<unknown>')}: invalid access classification")
        if not set(row.get("related_incident_ids", [])).issubset(incident_ids):
            errors.append(f"{row.get('evidence_id', '<unknown>')}: unknown incident reference")

    for row in risk_rows:
        missing = RISK_REQUIRED - set(row)
        if missing:
            errors.append(f"{row.get('risk_id', '<unknown>')}: missing risk fields {sorted(missing)}")
        if row.get("division_id") not in DIVISION_IDS:
            errors.append(f"{row.get('risk_id', '<unknown>')}: unknown division")
        if row.get("likelihood") not in {"low", "medium", "high", "unknown"}:
            errors.append(f"{row.get('risk_id', '<unknown>')}: invalid likelihood")
        if row.get("impact") not in {"low", "medium", "high", "critical", "unknown"}:
            errors.append(f"{row.get('risk_id', '<unknown>')}: invalid impact")
        if row.get("status") not in {"open", "mitigating", "accepted_by_owner", "closed", "blocked_pending_evidence"}:
            errors.append(f"{row.get('risk_id', '<unknown>')}: invalid status")
        if not set(row.get("evidence_references", [])).issubset(evidence_ids):
            errors.append(f"{row.get('risk_id', '<unknown>')}: unknown evidence reference")
    return errors


def main() -> int:
    incidents = json.loads(INCIDENT_PATH.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    risks = json.loads(RISK_PATH.read_text(encoding="utf-8"))
    errors = validate_registers(incidents, evidence, risks)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        "Register structure passed: "
        f"{len(incident_rows := incidents['records'])} incidents, "
        f"{len(evidence['records'])} evidence items, "
        f"{len(risks['records'])} risks. "
        "Structural validation is not operational readiness evidence."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

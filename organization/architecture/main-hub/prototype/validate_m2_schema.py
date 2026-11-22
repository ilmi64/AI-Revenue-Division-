#!/usr/bin/env python3
"""Offline Draft 2020-12 and exact-source validator for the M2 OCC fixtures.

This is a validation utility, not a test suite or an operational OCC service.
It reads only the committed local schema and synthetic fixture files. It makes
no network requests and performs no external actions.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from m2_envelope_semantics import check_m2_envelope_semantics, check_snapshot_fixture_agreement
from occ_readonly import assess_snapshot

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "records.schema.json"
ENVELOPE_PATH = ROOT / "fixtures" / "main-hub-envelope.example.json"

# GitHub Git-blob SHA-1 values for the exact reviewed source revisions.
# Update these pins only after reviewing and intentionally accepting new blobs.
EXPECTED_BLOB_SHAS = {
    "schema/records.schema.json": "5b2dd53a7d5a72b8eed7ab647fcdb54d21edf3a0",
    "fixtures/main-hub-envelope.example.json": "9f3d7d83ee0d87f7cba1fbda7002c5b9b7d856d0",
    "fixtures/ai-revenue.snapshot.example.json": "e2a1019ae9327dd4bed56f1bf8a1801b49aaae33",
    "fixtures/trading-technology.snapshot.example.json": "ecc536031e115eadc71493a3da81ec3c8839e3ac",
    "fixtures/registry-and-workstreams.example.json": "d001e4ee87544ab6628ad6b95d1ddb9e5c87ea98",
    "fixtures/decisions.example.json": "a6ebb6a7596248568f0c26888b2984e66b48c9e0",
}


def github_blob_sha1(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def strict_json_load(path: Path) -> tuple[Any, bytes]:
    raw = path.read_bytes()

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key!r}")
            result[key] = value
        return result

    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-standard JSON constant: {value}")
        ),
    )
    return value, raw


def unique_values(records: list[dict[str, Any]], key: str, label: str) -> list[str]:
    values = [record.get(key) for record in records]
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"{label}: missing or invalid {key}")
    if len(values) != len(set(values)):
        raise ValueError(f"{label}: duplicate {key}")
    return values


def main() -> int:
    print("M2 offline source and schema validation")
    print("No network access or external actions are performed.")

    loaded: dict[str, Any] = {}
    for relative, expected_sha in EXPECTED_BLOB_SHAS.items():
        path = ROOT / relative
        value, raw = strict_json_load(path)
        actual_sha = github_blob_sha1(raw)
        if actual_sha != expected_sha:
            raise ValueError(
                f"source pin mismatch for {relative}: "
                f"expected {expected_sha}, got {actual_sha}"
            )
        loaded[relative] = value
        print(f"PASS exact source pin: {relative} ({actual_sha})")

    schema = loaded["schema/records.schema.json"]
    envelope = loaded["fixtures/main-hub-envelope.example.json"]

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(envelope),
        key=lambda error: (list(map(str, error.absolute_path)), error.message),
    )
    if errors:
        for error in errors:
            location = "/" + "/".join(map(str, error.absolute_path))
            print(f"FAIL schema validation {location}: {error.message}")
        return 1
    print("PASS Draft 2020-12 schema and asserted format validation")

    # Semantic referential-integrity validation complements, never replaces, schema checks.
    check_m2_envelope_semantics(envelope)
    print("PASS offline M2 envelope referential-integrity checks")

    # The independently pinned company fixture and the combined envelope must
    # describe the same synthetic snapshot. A divergence is a source-integrity
    # failure even when both JSON documents separately satisfy their schemas.
    standalone = {
        "ai_revenue": loaded["fixtures/ai-revenue.snapshot.example.json"],
        "trading_technology": loaded["fixtures/trading-technology.snapshot.example.json"],
    }
    check_snapshot_fixture_agreement(envelope, standalone)
    print("PASS exact semantic agreement between envelope and pinned company fixtures")

    # The envelope and the standalone reader must agree on the snapshot contract.
    # This checks nested gate/evidence semantics, not publisher authenticity.
    for snapshot in envelope["status_snapshots"]:
        assessed = assess_snapshot(snapshot, snapshot["company_id"])
        if assessed["display_status"] not in {"UNKNOWN", "STALE"}:
            raise ValueError("unauthenticated snapshot was promoted to trusted status")
        if assessed["trust"] not in {"SYNTHETIC_UNTRUSTED", "UNAUTHENTICATED"}:
            raise ValueError("snapshot trust classification is unexpectedly elevated")
    print("PASS conservative standalone snapshot semantics (untrusted only)")

    company_ids = unique_values(
        envelope["company_registry"], "company_id", "company_registry"
    )
    if set(company_ids) != {"ai_revenue", "trading_technology"}:
        raise ValueError(f"unexpected company registry: {company_ids}")

    snapshot_ids = unique_values(
        envelope["status_snapshots"], "company_id", "status_snapshots"
    )
    if set(snapshot_ids) != {"ai_revenue", "trading_technology"}:
        raise ValueError(f"unexpected snapshot company set: {snapshot_ids}")

    unique_values(envelope["workstreams"], "workstream_id", "workstreams")
    unique_values(envelope["decisions"], "decision_id", "decisions")
    print("PASS semantic identity and record-uniqueness checks")
    print("PASS exactly two operating companies; shared divisions remain outside company registry")
    print("LIMIT: schema validity and source pins do not authenticate a publisher or prove readiness.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)

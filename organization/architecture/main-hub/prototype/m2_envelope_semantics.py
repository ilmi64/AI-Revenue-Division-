"""Offline M2 envelope semantic checks beyond JSON Schema.

No authentication, publisher trust, execution or operational readiness claim.
"""
from collections.abc import Mapping


class EnvelopeSemanticError(ValueError):
    pass


COMPANIES = frozenset({"ai_revenue", "trading_technology"})


def _ids(records, field, label):
    if not isinstance(records, list):
        raise EnvelopeSemanticError(f"{label} must be an array")
    values = []
    for record in records:
        if not isinstance(record, Mapping):
            raise EnvelopeSemanticError(f"{label} item must be an object")
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EnvelopeSemanticError(f"{label} has missing {field}")
        values.append(value)
    if len(values) != len(set(values)):
        raise EnvelopeSemanticError(f"{label} has duplicate {field}")
    return set(values)


def check_m2_envelope_semantics(envelope):
    """Require isolated company identities and valid internal workstream references.

    Intended to run *after* Draft 2020-12 validation, never instead of it.
    """
    if not isinstance(envelope, Mapping):
        raise EnvelopeSemanticError("envelope must be an object")
    company_ids = _ids(envelope.get("company_registry"), "company_id", "company_registry")
    snapshot_ids = _ids(envelope.get("status_snapshots"), "company_id", "status_snapshots")
    if company_ids != COMPANIES or snapshot_ids != COMPANIES:
        raise EnvelopeSemanticError("company registry and snapshots must contain exactly both companies")
    workstream_ids = _ids(envelope.get("workstreams"), "workstream_id", "workstreams")
    _ids(envelope.get("decisions"), "decision_id", "decisions")
    for record in envelope["workstreams"]:
        dependencies = record.get("depends_on", [])
        if not isinstance(dependencies, list) or any(
            not isinstance(value, str) for value in dependencies
        ):
            raise EnvelopeSemanticError("workstream dependencies must be string IDs")
        if len(dependencies) != len(set(dependencies)):
            raise EnvelopeSemanticError("duplicate workstream dependency")
        if record["workstream_id"] in dependencies:
            raise EnvelopeSemanticError("self-dependent workstream")
        if set(dependencies) - workstream_ids:
            raise EnvelopeSemanticError("unknown workstream dependency")
    # Detect cycles as well as direct self-references; a cyclic dependency
    # cannot be treated as a valid readiness chain.
    graph = {
        record["workstream_id"]: tuple(record.get("depends_on", []))
        for record in envelope["workstreams"]
    }
    visiting = set()
    visited = set()
    for root in graph:
        if root in visited:
            continue
        stack = [(root, False)]
        while stack:
            node, leaving = stack.pop()
            if leaving:
                visiting.remove(node)
                visited.add(node)
                continue
            if node in visited:
                continue
            if node in visiting:
                raise EnvelopeSemanticError("cyclic workstream dependency")
            visiting.add(node)
            stack.append((node, True))
            for dependency in reversed(graph[node]):
                stack.append((dependency, False))
    for decision in envelope["decisions"]:
        references = decision.get("workstream_ids", [])
        if not isinstance(references, list) or any(
            not isinstance(value, str) for value in references
        ):
            raise EnvelopeSemanticError("decision workstream references must be string IDs")
        if set(references) - workstream_ids:
            raise EnvelopeSemanticError("decision references unknown workstream")
    return None


def check_snapshot_fixture_agreement(envelope, standalone):
    """Reject drift between the envelope and separately pinned company snapshots."""
    if not isinstance(envelope, Mapping) or not isinstance(standalone, Mapping):
        raise EnvelopeSemanticError("snapshot comparison requires objects")
    snapshots = envelope.get("status_snapshots")
    ids = _ids(snapshots, "company_id", "status_snapshots")
    if ids != COMPANIES or set(standalone) != COMPANIES:
        raise EnvelopeSemanticError("snapshot fixture company set mismatch")
    for snapshot in snapshots:
        company_id = snapshot["company_id"]
        pinned = standalone[company_id]
        if not isinstance(pinned, Mapping) or pinned.get("company_id") != company_id:
            raise EnvelopeSemanticError(f"pinned fixture identity mismatch: {company_id}")
        if snapshot != pinned:
            raise EnvelopeSemanticError(
                f"envelope snapshot differs from pinned company fixture: {company_id}"
            )

def check_companion_fixture_agreement(envelope, registry_and_workstreams, decisions):
    """Require each independently pinned companion to match the full envelope."""
    for label, companion, fields in (
        ("registry/workstreams", registry_and_workstreams, ("company_registry", "workstreams")),
        ("decisions", decisions, ("decisions",)),
    ):
        keys = ("schema_version", *fields)
        if not isinstance(companion, Mapping) or set(companion) != set(keys):
            raise EnvelopeSemanticError(f"{label} companion has unexpected fields")
        for key in keys:
            if key not in envelope or companion[key] != envelope[key]:
                raise EnvelopeSemanticError(f"{label} companion differs from envelope: {key}")

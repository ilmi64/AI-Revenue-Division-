#!/usr/bin/env python3
"""Validate that declared division dependencies have provider links and operating handoffs."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def build_report(registry, dependency_map, framework):
    errors, edges = [], []
    if not all(isinstance(x, dict) for x in (registry, dependency_map, framework)):
        return {"schema_version": 1, "validated": False,
                "errors": ["registry, dependency_map and framework must be JSON objects"], "edges": []}
    registry_rows = registry.get("divisions", [])
    dependency_rows = dependency_map.get("divisions", [])
    framework_rows = framework.get("divisions", [])
    if not all(isinstance(x, list) for x in (registry_rows, dependency_rows, framework_rows)):
        return {"schema_version": 1, "validated": False,
                "errors": ["division collections must be lists"], "edges": []}
    known = {x.get("id") for x in registry_rows if isinstance(x, dict) and isinstance(x.get("id"), str)}
    providers = {x.get("division_id"): x for x in dependency_rows if isinstance(x, dict)}
    operators = {x.get("id"): x for x in framework_rows if isinstance(x, dict)}
    for consumer in dependency_rows:
        if not isinstance(consumer, dict):
            errors.append("Every dependency-map division must be an object")
            continue
        consumer_id = consumer.get("division_id")
        if consumer_id not in known:
            errors.append(f"Unknown dependency-map consumer {consumer_id!r}")
            continue
        targets = consumer.get("depends_on", [])
        if not isinstance(targets, list):
            errors.append(f"{consumer_id}: depends_on must be a list")
            continue
        handoffs = operators.get(consumer_id, {}).get("handoffs", [])
        if not isinstance(handoffs, list):
            errors.append(f"{consumer_id}: framework handoffs must be a list")
            handoffs = []
        for dependency in targets:
            if not isinstance(dependency, dict):
                errors.append(f"{consumer_id}: dependency entries must be objects")
                continue
            provider_id = dependency.get("division_id")
            if provider_id not in known or provider_id == consumer_id:
                errors.append(f"{consumer_id}: invalid provider {provider_id!r}")
                continue
            provider = providers.get(provider_id, {})
            provided_to = provider.get("provides_to", [])
            provider_linked = isinstance(provided_to, list) and (
                "all" in provided_to or consumer_id in provided_to
            )
            handoff_linked = any(
                isinstance(h, dict) and h.get("to") in {provider_id, "all"}
                and isinstance(h.get("artifact"), str) and bool(h.get("artifact").strip())
                and isinstance(h.get("trigger"), str) and bool(h.get("trigger").strip())
                for h in handoffs
            )
            edge = {
                "consumer_division": consumer_id,
                "provider_division": provider_id,
                "dependency_type": dependency.get("type", "unspecified"),
                "capability": dependency.get("capability", ""),
                "provider_linked": provider_linked,
                "handoff_linked": handoff_linked,
                "connected": provider_linked and handoff_linked
            }
            edges.append(edge)
            if not provider_linked:
                errors.append(f"{consumer_id} depends on {provider_id}, but provider provides_to does not include the consumer")
            if not handoff_linked:
                errors.append(f"{consumer_id} depends on {provider_id}, but no triggered artifact handoff is defined")
    return {
        "schema_version": 1,
        "validated": not errors,
        "dependency_edge_count": len(edges),
        "connected_edge_count": sum(edge["connected"] for edge in edges),
        "disconnected_edge_count": sum(not edge["connected"] for edge in edges),
        "edges": edges,
        "errors": errors
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("organization/division-registry.json"))
    parser.add_argument("--dependencies", type=Path, default=Path("organization/dependency-map.json"))
    parser.add_argument("--framework", type=Path, default=Path("organization/operating-framework.json"))
    args = parser.parse_args()
    try:
        values = [json.loads(path.read_text(encoding="utf-8")) for path in
                  (args.registry, args.dependencies, args.framework)]
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = build_report(*values)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["validated"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

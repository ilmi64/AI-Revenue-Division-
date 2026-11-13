#!/usr/bin/env python3
"""Normalize approved read-only opportunity feeds from multiple revenue divisions.

Each division may place a JSON file in division-inputs/. This is a connector contract,
not an assertion that external platforms or accounts are already connected.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from datetime import datetime, timezone

LANES = {
    "ai_development": "AI agent and automation development",
    "freelance_services": "Freelance software and technical services",
    "ai_evaluation": "AI training, evaluation and data annotation",
    "digital_products": "Reusable software and digital products",
    "grants_sponsorships": "Open-source grants and sponsorships",
    "security_testing": "Security testing and responsible disclosure",
    "research_tasks": "Paid research and technical research tasks",
    "github_bounties": "Public GitHub bounty and issue leads",
    "remote_employment": "Remote employment listings from public job feeds",
}
REQUIRED = ("title", "url", "source_name", "lane")

def normalize(item: dict, lane: str) -> dict:
    missing = [key for key in REQUIRED if not str(item.get(key, "")).strip()]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))
    url = str(item["url"]).strip()
    if not url.startswith("https://"):
        raise ValueError("Only HTTPS source URLs are accepted")
    if lane not in LANES:
        raise ValueError(f"Unsupported revenue lane: {lane}")
    if item["lane"] != lane:
        raise ValueError("Record lane must match its input feed lane")
    return {
        "id": str(item.get("id") or url),
        "title": str(item["title"]).strip(),
        "url": url,
        "source_name": str(item["source_name"]).strip(),
        "source_type": str(item.get("source_type") or "human_curated"),
        "company": str(item.get("company") or ""),
        "location_text": str(item.get("location_text") or ""),
        "eligibility_hint": str(item.get("eligibility_hint") or "unknown"),
        "source_attribution": str(item.get("source_attribution") or ""),
        "reward_amount": item.get("reward_amount"),
        "reward_currency": item.get("reward_currency"),
        "lane": lane,
        "lane_description": LANES[lane],
        "summary": str(item.get("summary") or ""),
        "discovered_at": str(item.get("discovered_at") or ""),
        "signals": [str(x) for x in item.get("signals", []) if isinstance(x, str)],
        "commercial_status": "unverified_lead",
        "funding_verified": False,
        "eligibility_verified": False,
        "payout_verified": False,
        "human_review_required": True,
        "prohibited_automatic_actions": [
            "apply", "claim", "contact", "submit", "publish", "invoice", "pay", "trade"
        ],
    }

def ingest(directory: str, github_payload: dict | None = None) -> tuple[list[dict], list[str]]:
    root = Path(directory)
    results, errors = [], []
    for lane in LANES:
        path = root / f"{lane}.json"
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            records = payload if isinstance(payload, list) else payload.get("results", [])
            if not isinstance(records, list):
                raise ValueError("Feed must be a list or an object with a results list")
            for record in records:
                if isinstance(record, dict):
                    results.append(normalize(record, lane))
                else:
                    errors.append(f"{path}: ignored non-object record")
        except Exception as exc:
            errors.append(f"{path}: {type(exc).__name__}: {exc}")
    if github_payload:
        for record in github_payload.get("results", []):
            try:
                mapped = {
                    "title": record.get("title"), "url": record.get("url"),
                    "source_name": "GitHub", "source_type": "public_issue_search",
                    "lane": "github_bounties", "summary": record.get("note", ""),
                    "signals": record.get("signals", []),
                }
                results.append(normalize(mapped, "github_bounties"))
            except Exception as exc:
                errors.append(f"GitHub lead: {type(exc).__name__}: {exc}")
    deduped = {}
    for record in results:
        deduped[record["url"]] = record
    return sorted(deduped.values(), key=lambda x: (x["lane"], x["title"].lower())), errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="division-inputs")
    parser.add_argument("--github-input", default="opportunity-output/github-opportunities.json")
    parser.add_argument("--output", default="opportunity-output/all-opportunities.json")
    args = parser.parse_args()
    github = None
    try:
        github = json.loads(Path(args.github_input).read_text(encoding="utf-8"))
    except FileNotFoundError:
        pass
    records, errors = ingest(args.input_dir, github)
    report = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "lanes": LANES, "record_count": len(records), "results": records, "errors": errors,
        "disclaimer": "Unified unverified leads only. External services are not connected unless their feed is explicitly configured.",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Unified {len(records)} leads across {len(set(x['lane'] for x in records))} active lanes; {len(errors)} feed errors.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

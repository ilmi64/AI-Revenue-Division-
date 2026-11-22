"""Offline, approval-gated opportunity intake for Aevora AI. No network or submissions."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

KINDS = {"coding", "coding_bounty", "bug_bounty", "automation", "creative", "research"}
STATES = {"hold", "review_ready", "rejected"}
REQUIRED = {"id", "kind", "title", "source_url", "scope_authorized", "cost_cad",
            "requires_credentials", "external_action", "deadline_utc"}

def assess(item, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(item, dict):
        return {"status": "rejected", "reasons": ["not_an_object"]}
    missing = sorted(REQUIRED - item.keys())
    if missing:
        return {"status": "rejected", "reasons": ["missing:" + ",".join(missing)]}
    reasons = []
    if not isinstance(item["id"], str) or not item["id"].strip():
        reasons.append("invalid_id")
    if not isinstance(item["kind"], str) or item["kind"] not in KINDS:
        reasons.append("unsupported_kind")
    if not isinstance(item["title"], str) or not item["title"].strip():
        reasons.append("invalid_title")
    url = item["source_url"]
    try:
        parsed_url = urlsplit(url) if isinstance(url, str) else None
        valid_url = (parsed_url is not None and parsed_url.scheme == "https"
                     and bool(parsed_url.hostname) and not parsed_url.username
                     and not parsed_url.password and not any(ord(char) < 32 or ord(char) == 127 or char.isspace() for char in url))
        if valid_url:
            _ = parsed_url.port
    except (ValueError, TypeError):
        valid_url = False
    if not valid_url:
        reasons.append("unverified_source_url")
    if item["scope_authorized"] is not True:
        reasons.append("authorization_unverified")
    cost = item["cost_cad"]
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost != 0:
        reasons.append("upfront_cost_or_invalid_cost")
    for flag in ("requires_credentials", "external_action"):
        if not isinstance(item[flag], bool):
            reasons.append("invalid_" + flag)
        elif item[flag]:
            reasons.append(flag + "_requires_approval")
    deadline = item["deadline_utc"]
    if deadline is not None:
        try:
            if not isinstance(deadline, str):
                raise ValueError("not string")
            parsed = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("timezone missing")
            if parsed <= now:
                reasons.append("expired")
        except (ValueError, TypeError, OverflowError):
            reasons.append("invalid_deadline")
    return {"status": "hold" if reasons else "review_ready", "reasons": reasons,
            "next_action": "human_review_only"}

def evaluate(items, now=None):
    if not isinstance(items, list):
        raise ValueError("Input must be a JSON array")
    seen = set()
    results = []
    for item in items:
        result = assess(item, now)
        raw_id = item.get("id") if isinstance(item, dict) else None
        key = raw_id if isinstance(raw_id, str) else None
        if isinstance(key, str) and key in seen:
            result = {"status": "rejected", "reasons": ["duplicate_id"],
                      "next_action": "human_review_only"}
        if isinstance(key, str):
            seen.add(key)
        results.append({"id": key, **result})
    return results

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Local JSON array, no fetching")
    parser.add_argument("--output", type=Path, help="Optional local JSON report")
    args = parser.parse_args()
    results = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    payload = json.dumps({"company": "Aevora AI", "mode": "offline_review_only",
                          "results": results}, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

if __name__ == "__main__":
    main()

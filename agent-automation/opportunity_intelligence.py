#!/usr/bin/env python3
"""Read-only GitHub opportunity discovery. Never claims, comments on, or submits work."""
from __future__ import annotations
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com/search/issues"
QUERIES = (
    'is:issue is:open label:bounty',
    'is:issue is:open "bounty"',
    'is:issue is:open "paid" "good first issue"',
)
LIMIT = 20

def search_issues(query: str, timeout: int = 20) -> list[dict]:
    url = API + "?" + urllib.parse.urlencode({"q": query, "per_page": LIMIT, "sort": "updated", "order": "desc"})
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-Revenue-Division-Opportunity-Intelligence",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("Unexpected GitHub issue-search response")
    return payload["items"]

def normalize(item: dict) -> dict:
    labels = [x.get("name", "") for x in item.get("labels", []) if isinstance(x, dict)]
    title = str(item.get("title", ""))
    text = (title + " " + " ".join(labels)).lower()
    signals = []
    if "bounty" in text: signals.append("bounty_keyword")
    if any(word in text for word in ("paid", "reward", "prize", "funded")): signals.append("payment_keyword")
    if any(word in text for word in ("good first issue", "beginner", "easy")): signals.append("accessibility_keyword")
    return {
        "title": title,
        "url": item.get("html_url", ""),
        "repository": (item.get("repository_url", "").rsplit("/", 1)[-1]),
        "state": item.get("state", ""),
        "created_at": item.get("created_at", ""),
        "updated_at": item.get("updated_at", ""),
        "labels": labels,
        "signals": signals,
        "funding_verified": False,
        "eligibility_verified": False,
        "competition_verified": False,
        "note": "Discovery lead only. Confirm sponsor, amount, escrow, eligibility, deadline and claim rules at the source.",
    }

def collect(search_fn=search_issues) -> tuple[list[dict], list[str]]:
    found, errors = {}, []
    for query in QUERIES:
        try:
            for item in search_fn(query):
                url = item.get("html_url")
                if url:
                    found[url] = normalize(item)
        except Exception as exc:
            errors.append(f"{query}: {type(exc).__name__}: {exc}")
    results = sorted(found.values(), key=lambda x: (bool(x["signals"]), x["updated_at"]), reverse=True)
    return results, errors

def render_markdown(results: list[dict], generated_at: str, errors: list[str]) -> str:
    lines = [
        "# GitHub Revenue Opportunity Radar", "",
        f"Generated: {generated_at}", "",
        "> Read-only discovery leads, not verified paid work. Search keywords are not proof of funding or eligibility.",
        "", "| Opportunity | Repository | Signals | Updated |",
        "|---|---|---|---|",
    ]
    for item in results:
        title = item["title"].replace("|", "\\|")
        signals = ", ".join(item["signals"]) or "none"
        lines.append(f"| [{title}]({item['url']}) | {item['repository']} | {signals} | {item['updated_at']} |")
    if not results:
        lines.append("| No leads returned | — | — | — |")
    lines.extend(["", "## Mandatory verification before investing time", "",
        "- Confirm a named sponsor and an explicit payout amount or funding mechanism.",
        "- Confirm the bounty is still open, unclaimed, and the acceptance criteria are achievable.",
        "- Verify Canadian eligibility, payout method, fees, deadline, escrow and dispute rules.",
        "- Check existing pull requests, assignees, comments and competition.",
        "- Estimate effort and required skills; reject tasks with unclear scope or unverifiable payment.",
        "- Never submit, comment, claim, contact a sponsor, or publish code automatically.", "",
        "## Collection errors", ""])
    lines.extend([f"- {error}" for error in errors] or ["- None"])
    return "\n".join(lines) + "\n"

def main() -> int:
    output = Path(os.environ.get("OPPORTUNITY_OUTPUT_DIR", "opportunity-output"))
    output.mkdir(parents=True, exist_ok=True)
    results, errors = collect()
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {"generated_at": generated, "results": results, "errors": errors,
               "disclaimer": "Unverified discovery leads; no external actions performed."}
    (output / "github-opportunities.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (output / "github-opportunities.md").write_text(render_markdown(results, generated, errors), encoding="utf-8")
    print(f"Collected {len(results)} unique GitHub discovery leads; {len(errors)} query errors.")
    return 0 if results or not errors else 1

if __name__ == "__main__":
    sys.exit(main())

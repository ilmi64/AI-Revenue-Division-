#!/usr/bin/env python3
"""Read-only discovery of GitHub issues carrying BOSS bounty markers.

This deliberately does not call BOSS private endpoints, log in, claim work, or
treat a badge/summary comment as proof that a bounty is currently payable.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
QUERIES = (
    'is:issue is:open "api.boss.dev/badge/bounty" in:body',
    'is:issue is:open "boss.dev/issue/github" in:body',
)
MAX_ISSUES = 15
TIMEOUT = 20
WARNING_TERMS = (
    "likely be invalid", "disabled the integration", "not claimable",
    "doesn't work", "does not work", "bounty link is broken",
    "will never get paid", "payment error", "invalid due to issues with boss",
)

def api_get(url: str, timeout: int = TIMEOUT):
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-Revenue-Division-BOSS-Research/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"GitHub API returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))

def search_issues(query: str) -> list[dict]:
    url = API + "/search/issues?" + urllib.parse.urlencode({
        "q": query, "per_page": MAX_ISSUES, "sort": "updated", "order": "desc",
    })
    payload = api_get(url)
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("Unexpected GitHub issue-search response")
    return payload["items"]

def inspect_comments(comments: list[dict]) -> dict:
    bot_notes, warnings, claim_activity = [], [], 0
    for comment in comments:
        body = str(comment.get("body") or "")
        author = str((comment.get("user") or {}).get("login") or "")
        lower = body.lower()
        if author == "boss-bounty[bot]" or "total bounty:" in lower:
            bot_notes.append({
                "author": author,
                "url": comment.get("html_url", ""),
                "excerpt": body[:1200],
            })
        if any(term in lower for term in WARNING_TERMS):
            warnings.append({
                "author": author,
                "url": comment.get("html_url", ""),
                "excerpt": body[:700],
            })
        if re.search(r"(?im)^\s*/(?:claim|attempt|champion|onit|volunteer)\b", body):
            claim_activity += 1
    return {
        "boss_summary_comments": bot_notes[:3],
        "platform_warnings": warnings[:3],
        "claim_or_champion_comment_count": claim_activity,
        "platform_status": "warning_detected_review_required" if warnings else (
            "summary_seen_not_payment_verified" if bot_notes else "not_verified"
        ),
    }

def normalize_issue(issue: dict, comments: list[dict] | None = None) -> dict:
    body = str(issue.get("body") or "")
    marker = re.search(r"https://www\.boss\.dev/issue/github/[^\s\"'<>]+", body)
    badge = re.search(r"https://api\.boss\.dev/badge/bounty[^\s\"'<>]+", body)
    if not marker and not badge:
        raise ValueError("Issue does not contain a recognized BOSS bounty marker")
    inspected = inspect_comments(comments or [])
    return {
        "id": f"boss-github:{issue.get('node_id') or issue.get('html_url')}",
        "title": str(issue.get("title") or "Untitled BOSS-marked issue"),
        "url": str(issue.get("html_url") or ""),
        "source_name": "BOSS-marked GitHub issue",
        "source_type": "public_github_issue_boss_marker",
        "lane": "github_bounties",
        "company": str((issue.get("repository_url") or "").rsplit("/", 1)[-1]),
        "summary": "BOSS marker detected. Funding, payout status, sponsor reliability, scope and eligibility require current human verification.",
        "discovered_at": str(issue.get("updated_at") or ""),
        "eligibility_hint": "Canada is listed in BOSS documentation; this exact bounty and payout eligibility remain unverified.",
        "reward_amount": None,
        "reward_currency": None,
        "signals": ["boss_bounty_marker", "public_github_issue"],
        "commercial_status": "unverified_lead",
        "funding_verified": False,
        "eligibility_verified": False,
        "payout_verified": False,
        "human_review_required": True,
        "boss_issue_url": marker.group(0) if marker else "",
        "boss_badge_url": badge.group(0) if badge else "",
        "issue_state": str(issue.get("state") or ""),
        "issue_updated_at": str(issue.get("updated_at") or ""),
        **inspected,
        "source_attribution": "Public GitHub issue and comments; BOSS marker is a discovery signal only. Confirm current status on the original issue and official BOSS account before investing effort.",
        "prohibited_automatic_actions": ["claim", "comment", "contact", "submit", "publish", "invoice", "pay"],
    }

def collect(search_fn=search_issues, api_fn=api_get):
    found, errors = {}, []
    for query in QUERIES:
        try:
            for issue in search_fn(query):
                url = issue.get("html_url")
                if url:
                    found[url] = issue
        except Exception as exc:
            errors.append(f"search: {type(exc).__name__}: {exc}")
    results = []
    for issue in sorted(found.values(), key=lambda x: x.get("updated_at", ""), reverse=True)[:MAX_ISSUES]:
        try:
            comments_url = issue.get("comments_url")
            comments = api_fn(comments_url) if comments_url and int(issue.get("comments", 0) or 0) else []
            results.append(normalize_issue(issue, comments if isinstance(comments, list) else []))
        except Exception as exc:
            errors.append(f"{issue.get('html_url','unknown')}: {type(exc).__name__}: {exc}")
    return results, errors

def main() -> int:
    output = Path("division-inputs/github_bounties.json")
    report_path = Path("external-source-output/boss-source-report.json")
    records, errors = collect()
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "GitHub public issue search for BOSS bounty markers",
        "records_found": len(records),
        "warning_detected": sum(x["platform_status"] == "warning_detected_review_required" for x in records),
        "errors": errors,
        "funding_verified": 0,
        "payout_verified": 0,
        "note": "Discovery only. BOSS markers and bot summaries do not prove that a bounty is active or payable. No BOSS API, login, claim, or external action is performed.",
    }, indent=2), encoding="utf-8")
    print(f"BOSS-marked issues: {len(records)}; collection errors: {len(errors)}.")
    return 0 if records or not errors else 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Read-only research radar for official AI/automation platform releases."""
from __future__ import annotations
import json, os, sys, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCES = (
    ("Activepieces", "activepieces/activepieces"),
    ("Dify", "langgenius/dify"),
    ("n8n", "n8n-io/n8n"),
    ("Ollama", "ollama/ollama"),
)

def fetch_latest_release(owner_repo: str, timeout: int = 20) -> dict:
    url = f"https://api.github.com/repos/{owner_repo}/releases?per_page=5"
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-Revenue-Division-Research-Radar",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Unexpected GitHub releases response")
    stable = [item for item in payload if not item.get("draft") and not item.get("prerelease")]
    if not stable:
        return {"repository": owner_repo, "status": "no_stable_release"}
    item = stable[0]
    return {
        "repository": owner_repo, "status": "ok",
        "tag": item.get("tag_name", ""),
        "name": item.get("name") or item.get("tag_name", ""),
        "published_at": item.get("published_at", ""),
        "url": item.get("html_url", f"https://github.com/{owner_repo}/releases"),
        "summary": (item.get("body") or "").strip()[:1200],
    }

def render_markdown(results: list[dict], generated_at: str) -> str:
    lines = [
        "# AI & Automation Research Radar", "",
        f"Generated: {generated_at}", "",
        "> Read-only snapshot of latest stable releases from official project repositories. This is a source monitor, not an AI assessment or endorsement.",
        "", "| Project | Latest stable release | Published | Status |",
        "|---|---|---|---|",
    ]
    for item in results:
        if item["status"] == "ok":
            name = item["name"].replace("|", "\\|")
            tag = item["tag"].replace("|", "\\|")
            lines.append(f"| [{name}]({item['url']}) | {tag} | {item['published_at'] or 'not provided'} | OK |")
        else:
            lines.append(f"| {item['repository']} | — | — | No stable release found |")
    lines.extend(["", "## Review notes", ""])
    for item in results:
        lines.append(f"### {item['repository']}")
        if item["status"] == "ok":
            lines.append(item["summary"] or "No release notes supplied.")
            lines.append(f"Source: {item['url']}")
        else:
            lines.append("No stable release was returned by the official releases endpoint.")
        lines.append("")
    lines.extend([
        "## Required human review", "",
        "- Check release notes, licensing, security advisories, hosting requirements, and model costs.",
        "- Do not deploy, connect accounts, or change production systems based on this report alone.",
        "- This collector does not call an LLM and makes no claims about product quality or suitability.", "",
    ])
    return "\n".join(lines)

def main() -> int:
    output_dir = Path(os.environ.get("RADAR_OUTPUT_DIR", "radar-output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    results, errors = [], []
    for label, owner_repo in SOURCES:
        try:
            result = fetch_latest_release(owner_repo)
            result["project"] = label
            results.append(result)
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            results.append({"project": label, "repository": owner_repo, "status": "error"})
            errors.append(f"{owner_repo}: {type(exc).__name__}: {exc}")
    (output_dir / "research-radar.json").write_text(
        json.dumps({"generated_at": generated_at, "results": results, "errors": errors}, indent=2), encoding="utf-8")
    (output_dir / "research-radar.md").write_text(render_markdown(results, generated_at), encoding="utf-8")
    print(f"Research radar generated for {len(results)} projects.")
    if errors:
        print("Some sources could not be reached:")
        for error in errors:
            print(f"- {error}")
    return 0 if len(errors) < len(SOURCES) else 1

if __name__ == "__main__":
    sys.exit(main())

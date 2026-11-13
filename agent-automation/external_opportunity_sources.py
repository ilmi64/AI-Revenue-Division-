#!/usr/bin/env python3
"""Read-only connectors for public remote-work feeds (stdlib only).

Sources are fetched without login, API keys, cookies or scraping. Records retain the
source name and original listing URL. This is discovery, not proof of Canadian eligibility,
payment, contract availability or suitability.
"""
from __future__ import annotations
import argparse, json, re, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone
from html import unescape

SOURCES = {
    "jobicy": "https://jobicy.com/api/v2/remote-jobs?count=100",
    "remoteok": "https://remoteok.com/api",
    "himalayas": "https://himalayas.app/jobs/api?limit=100",
}
USER_AGENT = "AI-Revenue-Division-Opportunity-Research/1.0 (read-only; source-attributed)"
MATCH_TERMS = (
    "python", "software", "developer", "engineer", "automation", "ai ", "artificial intelligence",
    "machine learning", "data annot", "ai trainer", "evaluator", "evaluation", "qa ", "quality assurance",
    "testing", "research", "technical writer", "api", "integration", "security", "cyber",
    "freelance", "contract", "part-time", "prompt", "llm", "agent",
)

def fetch_json(url: str, timeout: int = 25):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))

def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", unescape(value)).strip()

def classify(text: str) -> str:
    t = text.lower()
    if any(x in t for x in ("data annot", "ai trainer", "model evaluator", "ai evaluator", "llm evaluator")):
        return "ai_evaluation"
    if any(x in t for x in ("penetration test", "security researcher", "security engineer", "cybersecurity", "vulnerability")):
        return "security_testing"
    if any(x in t for x in ("research engineer", "research scientist", "research assistant", "technical research")):
        return "research_tasks"
    if any(x in t for x in ("automation", "ai agent", "machine learning", "artificial intelligence", "llm", "python developer")):
        return "ai_development"
    if any(x in t for x in ("freelance", "contractor", "contract role", "independent contractor")):
        return "freelance_services"
    return "remote_employment"

def relevant(text: str) -> bool:
    t = text.lower()
    return any(term in t for term in MATCH_TERMS)

def country_hint(value) -> str:
    if isinstance(value, list):
        values = [str(x) for x in value]
        if any(x.lower() in ("canada", "canadian", "worldwide", "anywhere", "global") for x in values):
            return "canada_or_worldwide_listed_check_full_terms"
        if values:
            return "country_restrictions_listed_check_full_terms"
    elif isinstance(value, str):
        v = value.lower()
        if any(x in v for x in ("canada", "worldwide", "anywhere", "global")):
            return "canada_or_worldwide_listed_check_full_terms"
        if value.strip():
            return "location_text_present_check_full_terms"
    return "unknown"

def base_record(source: str, title: str, company: str, url: str, location,
                description: str, posted: str, tags, source_id: str) -> dict | None:
    if not url.startswith("https://"):
        return None
    excerpt = strip_html(description)[:700]
    tag_text = " ".join(str(x) for x in (tags or []))
    combined = " ".join((title, company, str(location or ""), tag_text, excerpt))
    if not relevant(combined):
        return None
    lane = classify(combined)
    return {
        "id": f"{source}:{source_id or url}",
        "title": title.strip() or "Untitled listing",
        "url": url,
        "source_name": {"jobicy": "Jobicy", "remoteok": "Remote OK", "himalayas": "Himalayas"}[source],
        "source_type": "public_unauthenticated_job_feed",
        "lane": lane,
        "summary": excerpt,
        "discovered_at": posted or "",
        "company": company or "Not supplied",
        "location_text": location if isinstance(location, str) else ", ".join(map(str, location or [])),
        "eligibility_hint": country_hint(location),
        "reward_amount": None,
        "reward_currency": None,
        "commercial_status": "unverified_lead",
        "funding_verified": False,
        "eligibility_verified": False,
        "payout_verified": False,
        "source_attribution": f"Listing supplied by { {'jobicy':'Jobicy','remoteok':'Remote OK','himalayas':'Himalayas'}[source]}; follow the original listing for current details.",
        "human_review_required": True,
        "prohibited_automatic_actions": ["apply", "claim", "contact", "submit", "publish", "invoice", "pay", "trade"],
    }

def parse_jobicy(payload: dict) -> list[dict]:
    rows, out = payload.get("jobs", []), []
    for j in rows:
        rec = base_record("jobicy", str(j.get("jobTitle","")), str(j.get("companyName","")),
            str(j.get("url","")), j.get("jobGeo",""), str(j.get("jobExcerpt","")),
            str(j.get("pubDate","")), j.get("jobIndustry",[]), str(j.get("id","")))
        if rec: out.append(rec)
    return out

def parse_remoteok(payload) -> list[dict]:
    if not isinstance(payload, list): raise ValueError("Remote OK response must be a list")
    out=[]
    for j in payload:
        if not isinstance(j, dict) or "position" not in j: continue  # first array item is legal notice
        rec=base_record("remoteok", str(j.get("position","")), str(j.get("company","")),
            str(j.get("url") or j.get("apply_url") or ""), j.get("location",""),
            str(j.get("description","")), str(j.get("date","")), j.get("tags",[]), str(j.get("id","")))
        if rec: out.append(rec)
    return out

def parse_himalayas(payload: dict) -> list[dict]:
    out=[]
    for j in payload.get("jobs", []):
        loc=j.get("locationRestrictions", [])
        rec=base_record("himalayas", str(j.get("title","")), str(j.get("companyName","")),
            str(j.get("applicationLink") or j.get("guid") or ""), loc,
            str(j.get("excerpt","")), str(j.get("pubDate","")), j.get("categories",[]), str(j.get("guid","")))
        if rec: out.append(rec)
    return out

PARSERS = {"jobicy": parse_jobicy, "remoteok": parse_remoteok, "himalayas": parse_himalayas}

def collect(fetcher=fetch_json, sleep=time.sleep) -> tuple[list[dict], list[str]]:
    records, errors = {}, []
    for name, url in SOURCES.items():
        try:
            payload = fetcher(url)
            for item in PARSERS[name](payload):
                # Deduplicate identical original URLs while retaining one attributed source record.
                records.setdefault(item["url"], item)
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
        if name != "himalayas":
            sleep(1.0)
    return sorted(records.values(), key=lambda x: (x["lane"], x["title"].lower())), errors

def write_lane_feeds(records: list[dict], output_dir: str) -> dict:
    root=Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    groups={}
    for item in records: groups.setdefault(item["lane"], []).append(item)
    for lane, rows in groups.items():
        (root / f"{lane}.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return {lane: len(rows) for lane, rows in groups.items()}

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="division-inputs")
    parser.add_argument("--report", default="external-source-output/source-report.json")
    args=parser.parse_args()
    records, errors=collect()
    lane_counts=write_lane_feeds(records,args.output_dir)
    report={
        "generated_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sources_configured":list(SOURCES), "records_found":len(records),
        "lane_counts":lane_counts, "errors":errors,
        "eligibility_verified":0, "payout_verified":0,
        "note":"Read-only public-feed discovery. Listings may be stale, unsuitable or unavailable to Canadian residents. Check the original listing and provider terms.",
    }
    p=Path(args.report); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"External feeds: {len(records)} relevant leads; {len(errors)} source errors.")
    return 0 if records or not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only connectors for configured public Greenhouse, Lever and Ashby boards."""
from __future__ import annotations
import argparse, json, re, time
from pathlib import Path
from urllib.request import Request, urlopen
from external_opportunity_sources import classify, relevant, country_hint, strip_html

USER_AGENT = "AI-Revenue-Division-Opportunity-Research/1.0 (read-only; source-attributed)"
SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{board}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true",
}

def fetch_json(url: str, timeout: int = 25):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))

def validate_config(config: dict) -> list[dict]:
    boards = config.get("boards", [])
    if not isinstance(boards, list):
        raise ValueError("config.boards must be a list")
    clean = []
    for entry in boards:
        if not isinstance(entry, dict):
            raise ValueError("Each board entry must be an object")
        provider, board = entry.get("provider"), entry.get("board")
        if provider not in ENDPOINTS or not isinstance(board, str) or not SLUG.fullmatch(board):
            raise ValueError("Each board needs a supported provider and safe board slug")
        region = entry.get("region", "global")
        if provider == "lever" and region not in ("global", "eu"):
            raise ValueError("Lever region must be global or eu")
        clean.append({"provider": provider, "board": board, "company": str(entry.get("company") or board),
                      "region": region})
    return clean

def endpoint(entry: dict) -> str:
    if entry["provider"] == "lever" and entry["region"] == "eu":
        return "https://api.eu.lever.co/v0/postings/" + entry["board"] + "?mode=json"
    return ENDPOINTS[entry["provider"]].format(board=entry["board"], region=entry["region"])

def _record(entry: dict, job: dict) -> dict | None:
    provider = entry["provider"]
    if provider == "greenhouse":
        title = str(job.get("title") or "")
        location = (job.get("location") or {}).get("name", "")
        url = str(job.get("absolute_url") or "")
        posted = str(job.get("first_published") or job.get("updated_at") or "")
        description = str(job.get("content") or "")
        department = ", ".join(x.get("name", "") for x in job.get("departments", []) if isinstance(x, dict))
        application_url = url
        employment_type = ""
        workplace = ""
        source_id = job.get("id", url)
    elif provider == "lever":
        title = str(job.get("text") or "")
        cats = job.get("categories") or {}
        location = str(cats.get("location") or "")
        url = str(job.get("hostedUrl") or job.get("applyUrl") or "")
        posted = str(job.get("createdAt") or "")
        description = str(job.get("descriptionPlain") or job.get("description") or "")
        department = str(cats.get("department") or cats.get("team") or "")
        application_url = str(job.get("applyUrl") or url)
        employment_type = str(cats.get("commitment") or "")
        workplace = str(job.get("workplaceType") or "")
        source_id = job.get("id", url)
    else:
        if job.get("isListed") is False:
            return None
        title = str(job.get("title") or "")
        location = str(job.get("location") or "")
        url = str(job.get("jobUrl") or job.get("applyUrl") or "")
        posted = str(job.get("publishedAt") or "")
        description = str(job.get("descriptionPlain") or job.get("descriptionHtml") or "")
        department = str(job.get("department") or job.get("team") or "")
        application_url = str(job.get("applyUrl") or url)
        employment_type = str(job.get("employmentType") or "")
        workplace = str(job.get("workplaceType") or "")
        source_id = job.get("id") or url
    if not url.startswith("https://") or not application_url.startswith("https://"):
        return None
    searchable = " ".join((title, entry["company"], str(location), department, description))
    if not relevant(searchable):
        return None
    excerpt = strip_html(description)[:700]
    source_name = {"greenhouse":"Greenhouse","lever":"Lever","ashby":"Ashby"}[provider]
    return {
        "id": f"{provider}:{entry['board']}:{source_id}",
        "title": title.strip() or "Untitled listing", "url": url, "application_url": application_url,
        "source_name": source_name, "source_type": "public_unauthenticated_employer_job_board",
        "lane": classify(searchable), "summary": excerpt, "discovered_at": posted,
        "company": entry["company"], "location_text": str(location),
        "eligibility_hint": country_hint(str(location)), "department": department,
        "employment_type": employment_type, "workplace_type": workplace,
        "reward_amount": None, "reward_currency": None,
        "signals": ["employer_ats_public_listing", "source_relevance_keyword"],
        "commercial_status": "unverified_lead", "funding_verified": False,
        "eligibility_verified": False, "payout_verified": False,
        "source_attribution": f"Public job listing supplied by {source_name}; use the employer's original listing and application link.",
        "human_review_required": True,
        "prohibited_automatic_actions": ["apply","claim","contact","submit","publish","invoice","pay","trade"],
    }

def parse_board(entry: dict, payload) -> list[dict]:
    provider = entry["provider"]
    if provider == "lever":
        jobs = payload if isinstance(payload, list) else None
    else:
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if not isinstance(jobs, list):
        raise ValueError(f"Unexpected {provider} response shape")
    rows = []
    for job in jobs:
        if isinstance(job, dict):
            row = _record(entry, job)
            if row:
                rows.append(row)
    return rows

def collect(config: dict, fetcher=fetch_json, sleep=time.sleep):
    records, errors, health = {}, [], []
    boards = validate_config(config)
    for index, entry in enumerate(boards):
        try:
            rows = parse_board(entry, fetcher(endpoint(entry)))
            for row in rows:
                records.setdefault(row["url"], row)
            health.append({"provider":entry["provider"],"board":entry["board"],"status":"ok","relevant_leads":len(rows)})
        except Exception as exc:
            errors.append(f"{entry['provider']}:{entry['board']}: {type(exc).__name__}: {exc}")
            health.append({"provider":entry["provider"],"board":entry["board"],"status":"error"})
        if index < len(boards)-1:
            sleep(1.0)
    return sorted(records.values(), key=lambda x:(x["lane"],x["title"].lower())), errors, health

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",default="agent-automation/ats-boards.json")
    parser.add_argument("--output-dir",default="division-inputs")
    parser.add_argument("--report",default="external-source-output/ats-source-report.json")
    args=parser.parse_args()
    config_path=Path(args.config)
    if not config_path.exists():
        config={"boards":[]}
    else:
        config=json.loads(config_path.read_text(encoding="utf-8"))
    records,errors,health=collect(config)
    root=Path(args.output_dir); root.mkdir(parents=True,exist_ok=True)
    groups={}
    for row in records: groups.setdefault(row["lane"],[]).append(row)
    for lane,rows in groups.items():
        path=root/f"{lane}.json"
        existing=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        if not isinstance(existing,list): existing=[]
        by_url={x.get("url"):x for x in existing if isinstance(x,dict)}
        for row in rows: by_url[row["url"]]=row
        path.write_text(json.dumps(list(by_url.values()),indent=2),encoding="utf-8")
    report={"boards_configured":len(validate_config(config)),"records_found":len(records),
            "lane_counts":{k:len(v) for k,v in groups.items()},"board_health":health,"errors":errors,
            "note":"Read-only public employer-board discovery. Canadian eligibility, compensation, role availability and suitability require human verification."}
    out=Path(args.report); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"ATS boards: {len(records)} relevant leads; {len(errors)} board errors; {len(health)} boards checked.")
    return 1 if errors and not records else 0

if __name__ == "__main__":
    raise SystemExit(main())

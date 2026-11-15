#!/usr/bin/env python3
"""Validate review-only employer ATS candidates; never activate or apply to jobs."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from ats_job_board_sources import collect

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidates",default="agent-automation/ats-board-candidates.json")
    parser.add_argument("--report",default="external-source-output/ats-candidate-validation.json")
    args=parser.parse_args()
    data=json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    candidates=data.get("candidates",[])
    config={"boards":[{"provider":x["provider"],"board":x["board"],"company":x["company"]} for x in candidates]}
    records,errors,health=collect(config)
    report={
      "candidate_count":len(candidates),
      "api_validated_count":sum(1 for x in health if x["status"]=="ok"),
      "api_error_count":sum(1 for x in health if x["status"]!="ok"),
      "relevant_public_listings_found":len(records),
      "boards":health,
      "errors":errors,
      "activation":"not_activated",
      "approval_required":True,
      "note":"This is a review-only validation pass. It does not write candidate jobs into division intake, alter ats-boards.json, apply, contact employers or verify Canadian eligibility."
    }
    out=Path(args.report); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"ATS candidate boards: {report['api_validated_count']}/{len(candidates)} API responses validated; {len(records)} relevant listings; {len(errors)} errors. No candidates activated.")
    return 0
if __name__=="__main__":
    raise SystemExit(main())

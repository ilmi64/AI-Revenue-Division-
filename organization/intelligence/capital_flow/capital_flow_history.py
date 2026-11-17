"""Build a read-only event-history projection from normalized events and review ledger."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from capital_flow_review import LedgerError, load_ledger


class HistoryError(ValueError):
    pass


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise HistoryError(f"{path}: line {line_number}: invalid JSON") from exc
            if not isinstance(item, dict):
                raise HistoryError(f"{path}: line {line_number}: expected object")
            records.append(item)
    return records


def project_history(events: list[dict[str, Any]], reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for index, event in enumerate(events, 1):
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise HistoryError(f"event record {index}: event_id required")
        if event_id in by_id:
            raise HistoryError(f"duplicate event_id in normalized event input: {event_id}")
        by_id[event_id] = event

    grouped: dict[str, list[dict[str, Any]]] = {event_id: [] for event_id in by_id}
    for review in reviews:
        event_id = review.get("event_id")
        if event_id not in by_id:
            raise HistoryError(f"review references unknown event_id: {event_id}")
        grouped[event_id].append(review)

    output = []
    for event_id, event in by_id.items():
        timeline = grouped[event_id]
        current_status = event.get("review_status", "unverified")
        latest = None
        for review in timeline:
            if review.get("review_status") is not None:
                current_status = review["review_status"]
            latest = review
        output.append({
            "event_id": event_id,
            "event": event,
            "review_history": timeline,
            "review_count": len(timeline),
            "current_review_status": current_status,
            "latest_review": latest,
            "projection_authority": "read_only_research_summary_no_execution_authority"
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Project read-only capital-flow event histories")
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--reviews", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        events = load_jsonl(args.events)
        reviews = load_ledger(args.reviews)
        projected = project_history(events, reviews)
        with args.output.open("w", encoding="utf-8") as handle:
            for record in projected:
                handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        print(json.dumps({"status": "projected", "event_count": len(projected),
                          "review_count": len(reviews),
                          "authority": "read_only_research_summary_no_execution_authority"}, indent=2))
        return 0
    except (HistoryError, LedgerError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

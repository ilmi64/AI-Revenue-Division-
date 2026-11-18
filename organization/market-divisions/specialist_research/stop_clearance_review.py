"""Read-only independent review of stop-clearance evidence.

This module assesses whether a latched stop has enough linked recovery evidence
and two distinct independent reviews to be presented for a separate OCC decision.
It never clears, downgrades, or deactivates a stop.
"""
from __future__ import annotations

from typing import Any

try:
    from .incident_event_ledger import verify_events
except ImportError:
    from incident_event_ledger import verify_events

AUTHORITY = "research_only_no_execution_authority"
REQUIRED_REVIEW_ROLES = {"independent_risk", "occ"}


def assess_stop_clearance(event_records: list[dict[str, Any]]) -> dict[str, Any]:
    ledger = verify_events(event_records)
    errors: list[str] = []
    if not ledger["valid"]:
        return {
            "valid": False, "status": "HALT_REVIEW",
            "errors": ["event ledger integrity failed; clearance evidence cannot be assessed"],
            "stops": [], "global_stop_active": True,
            "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
        }

    events = [row["event"] for row in event_records]
    by_id = {event["event_id"]: event for event in events}
    stops: dict[str, dict[str, Any]] = {}
    for event in events:
        if event["event_type"] != "stop_raised":
            continue
        stop_id = event["details"].get("stop_id")
        if not isinstance(stop_id, str) or not stop_id.strip():
            errors.append(f"stop_raised event {event['event_id']} has no stop_id; clearance cannot be correlated")
            continue
        stops.setdefault(stop_id, {"stop_id": stop_id, "raise_event_id": event["event_id"],
                                   "incident_id": event["subject_id"], "requests": []})

    for event in events:
        if event["event_type"] != "stop_clearance_requested":
            continue
        details = event["details"]
        stop_id = details.get("stop_id")
        stop = stops.get(stop_id) if isinstance(stop_id, str) else None
        request_errors: list[str] = []
        if stop is None:
            request_errors.append("request references no known latched stop")
            errors.append(f"clearance request {event['event_id']} references unknown stop_id {stop_id!r}")
        else:
            if details.get("incident_id") != stop["incident_id"]:
                request_errors.append("request incident_id does not match the stop incident")
        recovery_ids = details.get("recovery_evidence_event_ids")
        corrective_ids = details.get("corrective_action_event_ids")
        if not isinstance(recovery_ids, list) or not recovery_ids:
            request_errors.append("at least one recovery_evidence_added event is required")
            recovery_ids = []
        if not isinstance(corrective_ids, list) or not corrective_ids:
            request_errors.append("at least one corrective_action_verified event is required")
            corrective_ids = []
        for event_id, expected_type in (
            *((x, "recovery_evidence_added") for x in recovery_ids),
            *((x, "corrective_action_verified") for x in corrective_ids),
        ):
            linked = by_id.get(event_id) if isinstance(event_id, str) else None
            if (linked is None or linked["event_type"] != expected_type
                    or linked["details"].get("stop_id") != stop_id
                    or linked["subject_id"] != details.get("incident_id")):
                request_errors.append(f"linked {expected_type} event {event_id!r} is missing or mismatched")
        if details.get("requestor_id") != event["actor_id"]:
            request_errors.append("requestor_id must match the request event actor_id")
        request = {
            "request_event_id": event["event_id"], "stop_id": stop_id,
            "requestor_id": event["actor_id"], "request_errors": request_errors,
            "reviews": [],
        }
        if stop is not None:
            stop["requests"].append(request)

    requests = {
        request["request_event_id"]: request
        for stop in stops.values() for request in stop["requests"]
    }
    for event in events:
        if event["event_type"] != "stop_clearance_reviewed":
            continue
        details = event["details"]
        request = requests.get(details.get("request_event_id"))
        if request is None:
            errors.append(f"review {event['event_id']} references an unknown clearance request")
            continue
        if details.get("stop_id") != request["stop_id"]:
            request["request_errors"].append(f"review {event['event_id']} stop_id mismatch")
        if event["actor_id"] == request["requestor_id"]:
            request["request_errors"].append(f"review {event['event_id']} is not independent of the requestor")
        if details.get("reviewer_id") != event["actor_id"]:
            request["request_errors"].append(f"review {event['event_id']} reviewer_id mismatch")
        request["reviews"].append({
            "event_id": event["event_id"], "reviewer_id": event["actor_id"],
            "reviewer_role": details.get("reviewer_role"), "decision": details.get("decision"),
        })

    results = []
    for stop in stops.values():
        request_results = []
        for request in stop["requests"]:
            reviews = request["reviews"]
            roles = {r["reviewer_role"] for r in reviews if r["decision"] == "eligible"}
            reviewers = {r["reviewer_id"] for r in reviews if r["decision"] == "eligible"}
            rejected = any(r["decision"] == "rejected" for r in reviews)
            request_errors = list(request["request_errors"])
            if len(reviewers) != len([r for r in reviews if r["decision"] == "eligible"]):
                request_errors.append("duplicate reviewer identity; independent review requires distinct people")
            if not REQUIRED_REVIEW_ROLES.issubset(roles):
                request_errors.append("both independent_risk and occ eligible reviews are required")
            eligible = not request_errors and not rejected and REQUIRED_REVIEW_ROLES.issubset(roles) and len(reviewers) >= 2
            request_results.append({
                "request_event_id": request["request_event_id"],
                "status": "eligible_for_separate_occ_decision" if eligible else
                          "rejected" if rejected else "pending_or_incomplete",
                "review_count": len(reviews), "review_roles": sorted(roles),
                "errors": request_errors,
            })
        results.append({
            "stop_id": stop["stop_id"], "raise_event_id": stop["raise_event_id"],
            "incident_id": stop["incident_id"], "requests": request_results,
            "status": ("eligible_for_separate_occ_decision"
                       if any(x["status"] == "eligible_for_separate_occ_decision" for x in request_results)
                       else "review_pending_or_incomplete"),
            "stop_remains_active": True,
        })

    return {
        "valid": not errors, "status": "HALT_REVIEW" if errors else "REVIEW_ONLY",
        "errors": errors, "stops": results,
        "global_stop_active": ledger["global_stop_active"],
        "clearance_performed": False,
        "trade_authority": False, "live_readiness": False, "authority": AUTHORITY,
        "limitations": [
            "Two distinct independent_risk and occ reviewers are evidence requirements, not cryptographic identity proof",
            "Reviewer attestations and evidence references are caller-supplied and not independently authenticated",
            "Eligibility is not clearance; all stops remain active pending a separate authorised OCC process",
        ],
    }

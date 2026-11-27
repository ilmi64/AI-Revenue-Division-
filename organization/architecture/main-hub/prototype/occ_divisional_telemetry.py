"""Strict projection of company-published divisional counters for OCC."""

from occ_company_visibility import COMMON_SUBSYSTEMS, COMPANY_SUBSYSTEMS


COUNTER_FIELDS = ("open_incident_count", "pending_approval_count", "blocker_count")
DIVISIONS = {
    company: tuple(name for name in COMMON_SUBSYSTEMS if name != "main_hub") + subsystems
    for company, subsystems in COMPANY_SUBSYSTEMS.items()
}
_MAX_COUNT = (1 << 53) - 1
RESOURCE_FIELDS = {
    "ai_revenue": ("native_workforce", "coding_service", "publisher_custody"),
    "trading_technology": ("historical_data", "paper_operations", "publisher_custody"),
}
RESOURCE_STATUSES = frozenset({"BLOCKED", "STAGED_FOR_REVIEW", "APPROVAL_REQUIRED", "NOT_VERIFIED"})


def _counts(value):
    if (
        not isinstance(value, dict)
        or set(value) != set(COUNTER_FIELDS)
        or any(type(count) is not int or not 0 <= count <= _MAX_COUNT for count in value.values())
    ):
        raise ValueError("divisional counters must be bounded nonnegative integers")
    return {name: value[name] for name in COUNTER_FIELDS}


def split_divisional_report(payload, company):
    """Return the existing report plus independently validated scoped counters."""
    if not isinstance(payload, dict) or set(payload) != {"report", "divisional_telemetry"}:
        raise ValueError("signed divisional report fields are invalid")
    report, telemetry = payload["report"], payload["divisional_telemetry"]
    if (
        not isinstance(report, dict) or not isinstance(telemetry, dict)
        or not {"company_totals", "divisions"} <= telemetry.keys()
        or telemetry.keys() - {"company_totals", "divisions", "resource_qualification"}
        or not isinstance(telemetry["divisions"], dict)
        or set(telemetry["divisions"]).difference(DIVISIONS[company])
    ):
        raise ValueError("signed divisional telemetry scope is invalid")
    totals = _counts(telemetry["company_totals"])
    divisions = {name: _counts(counters) for name, counters in telemetry["divisions"].items()}
    if any(sum(counters[field] for counters in divisions.values()) > totals[field]
           for field in COUNTER_FIELDS):
        raise ValueError("disclosed division counts exceed company totals")
    scoped = {"company_totals": totals, "divisions": divisions}
    if "resource_qualification" in telemetry:
        resources = telemetry["resource_qualification"]
        if (
            not isinstance(resources, dict) or not resources
            or set(resources).difference(RESOURCE_FIELDS[company])
            or any(not isinstance(status, str) or status not in RESOURCE_STATUSES
                   for status in resources.values())
        ):
            raise ValueError("signed resource qualification scope or status is invalid")
        scoped["resource_qualification"] = dict(resources)
    return report, scoped

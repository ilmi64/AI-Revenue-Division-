"""Strict projection of company-published divisional counters for OCC."""

from occ_company_visibility import COMMON_SUBSYSTEMS, COMPANY_SUBSYSTEMS


COUNTER_FIELDS = ("open_incident_count", "pending_approval_count", "blocker_count")
DIVISIONS = {
    company: tuple(name for name in COMMON_SUBSYSTEMS if name != "main_hub") + subsystems
    for company, subsystems in COMPANY_SUBSYSTEMS.items()
}
_MAX_COUNT = (1 << 53) - 1


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
        or set(telemetry) != {"company_totals", "divisions"}
        or not isinstance(telemetry["divisions"], dict)
        or set(telemetry["divisions"]).difference(DIVISIONS[company])
    ):
        raise ValueError("signed divisional telemetry scope is invalid")
    totals = _counts(telemetry["company_totals"])
    divisions = {name: _counts(counters) for name, counters in telemetry["divisions"].items()}
    if any(sum(counters[field] for counters in divisions.values()) > totals[field]
           for field in COUNTER_FIELDS):
        raise ValueError("disclosed division counts exceed company totals")
    return report, {"company_totals": totals, "divisions": divisions}

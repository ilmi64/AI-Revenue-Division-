"""Render Main Hub's redacted offline projection as a portable executive view."""

from datetime import datetime, timezone
from html import escape

from occ_company_visibility import AEVORA_COUNTS, COMMON_SUBSYSTEMS, COMPANY_SUBSYSTEMS
from occ_divisional_telemetry import COUNTER_FIELDS, DIVISIONS
from occ_readonly import VALID_GATE, VALID_SUBSYSTEM


_COMPANIES = {
    "ai_revenue": "Aevora AI Revenue",
    "trading_technology": "Trading & Technology",
}
_SUBSYSTEM_LABELS = {
    "main_hub": "Main Hub",
    "ai_workforce": "Workforce",
    "research_intelligence": "Research & Intelligence",
    "security_controls": "Security controls",
    "recovery": "Recovery",
    "commercial_operations": "Commercial operations",
    "polybot": "PolyBot",
    "paper_trading": "Paper trading",
    "risk_controls": "Portfolio risk",
}
_INPUT_LABELS = {
    "MISSING": "Missing", "REJECTED": "Rejected", "QUARANTINED": "Quarantined",
    "STALE": "Stale", "UNVERIFIED": "Evidence unverified",
    "UNVERIFIED_UNTIMED": "Evidence time unverified",
}
_UNAVAILABLE = {"MISSING", "REJECTED", "QUARANTINED", "STALE"}
_COUNT_LABELS = {
    "open_incident_count": "Open incidents",
    "pending_approval_count": "Pending approvals",
    "blocker_count": "Unresolved blockers",
}

# Palette and scorecard styling from the existing offline OCC dashboard.
_STYLE = """
:root { color-scheme: dark; --bg:#0d0c14; --panel:#171522; --panel2:#201d2e;
        --line:#302b43; --text:#f4f0ff; --muted:#b8afcb; --accent:#a78bfa; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:1rem/1.55 system-ui,sans-serif; }
header { border-bottom:1px solid var(--line); background:#100e19; }
header > div, main { max-width:65rem; margin:auto; padding:1.35rem 1rem; }
h1,h2,h3,p { margin:0; }
h1 { font-size:1.5rem; }
h2 { font-size:1.15rem; overflow-wrap:anywhere; }
h3,summary { font-size:0.92rem; font-weight:650; }
header p,.label { color:var(--muted); }
.company-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }
article { min-width:0; padding:1.05rem; border:1px solid var(--line);
          border-radius:0.8rem; background:var(--panel); }
.company-title { padding-bottom:0.6rem; border-bottom:1px solid var(--line); }
.panel { margin-top:0.85rem; }
dl { margin:0.35rem 0 0; }
.fact { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,0.85fr);
        padding:0.3rem 0; gap:0.6rem; border-bottom:1px solid var(--line); }
dt,dd { overflow-wrap:anywhere; }
dd { margin:0; text-align:right; font-weight:600; }
details { margin-top:0.6rem; padding:0.65rem; border-radius:0.5rem; background:var(--panel2); }
summary { cursor:pointer; }
details h3 { margin-top:0.75rem; }
summary:focus-visible { outline:2px solid var(--accent); outline-offset:3px; }
@media(max-width:44rem) { .company-grid { grid-template-columns:minmax(0,1fr); } }
"""


def _map(value):
    return value if isinstance(value, dict) else {}


def _text(value, allowed):
    return value.replace("_", " ").capitalize() if isinstance(value, str) and value in allowed else "Unknown"


def _count(value):
    return str(value) if type(value) is int and 0 <= value < 2**53 else "Unknown"


def _facts(values):
    rows = "".join(f'<div class="fact"><dt class="label">{escape(label)}</dt><dd>{escape(value)}</dd></div>'
                   for label, value in values)
    return "<dl>" + rows + "</dl>"


def _divisional_counts(company, telemetry):
    totals = _map(telemetry.get("company_totals"))
    divisions = _map(telemetry.get("divisions"))
    counts = _facts((_COUNT_LABELS[field], _count(totals.get(field))) for field in COUNTER_FIELDS)
    sections = []
    for name in DIVISIONS[company]:
        data = _map(divisions.get(name))
        entries = _facts((_COUNT_LABELS[field], _count(data.get(field))) for field in COUNTER_FIELDS)
        sections.append(f'<h3>{escape(_SUBSYSTEM_LABELS[name])}</h3>{entries}')
    return counts + "<details><summary>Division counts</summary>" + "".join(sections) + "</details>"


def _panel(company, heading, view):
    raw_input = view.get("input_status")
    status = raw_input if isinstance(raw_input, str) and raw_input in _INPUT_LABELS else "MISSING"
    show_counts = status not in _UNAVAILABLE
    verified = view.get("authentication") == "AUTHENTICATED_OFFLINE" and show_counts
    telemetry = _map(view.get("reported_divisional_telemetry")) if verified else {}
    content = _facts((
        ("Input status", _INPUT_LABELS[status]),
        ("Publisher", "Offline signature verified" if verified else "Unverified"),
        ("Reported commissioning",
         _text(view.get("reported_commissioning_status"), VALID_GATE) if show_counts else "Unknown"),
    ))
    if telemetry:
        content += _divisional_counts(company, telemetry)
    if show_counts and (company == "trading_technology" or heading == "Snapshot"):
        subsystems = _map(view.get("reported_subsystem_statuses"))
        gates = _map(view.get("reported_gate_counts"))
        counts = [
            ("Blocked gates", _count(gates.get("BLOCKED"))),
            ("Unresolved critical gates", _count(view.get("reported_critical_gates_not_passed"))),
        ]
        if not telemetry:
            counts.append(("Reported incidents", _count(view.get("reported_incident_count"))))
        content += _facts(counts)
        content += "<details><summary>Reported subsystems</summary>" + _facts(
            (_SUBSYSTEM_LABELS[key], _text(subsystems.get(key), VALID_SUBSYSTEM))
            for key in COMMON_SUBSYSTEMS + COMPANY_SUBSYSTEMS[company]
        ) + "</details>"
        content += "<details><summary>Reported gate counts</summary>" + _facts(
            (_text(gate, VALID_GATE), _count(gates.get(gate))) for gate in sorted(VALID_GATE)
        ) + "</details>"
    elif show_counts:
        counts = _map(view.get("reported_counts"))
        content += _facts((("Reported work items", _count(view.get("reported_total"))),))
        content += "<details><summary>Work queue</summary>" + _facts(
            (_text(key, AEVORA_COUNTS), _count(counts.get(key))) for key in AEVORA_COUNTS
        ) + "</details>"
    return f'<section class="panel"><h3>{heading}</h3>{content}</section>'


def _assessment_caption(assessed_at):
    if assessed_at is None:
        return "<p>Assessment time unknown</p>"
    if not isinstance(assessed_at, datetime) or assessed_at.utcoffset() is None:
        raise ValueError("assessment time must be a timezone-aware datetime")
    instant = assessed_at.astimezone(timezone.utc).isoformat(timespec="seconds")
    timestamp = instant.replace("+00:00", "Z")
    label = instant.removesuffix("+00:00").replace("T", " ") + " UTC"
    return f'<p>Assessed <time datetime="{escape(timestamp)}">{escape(label)}</time></p>'


def render_mobile_visibility(report, *, assessed_at=None):
    """Render separate company views and optional verifier assessment time."""
    if not isinstance(report, dict) or report.get("mode") != "offline_read_only" or report.get("operational_claim") is not False:
        raise ValueError("offline read-only visibility report required")
    reports = _map(report.get("companies"))
    if set(reports) != set(_COMPANIES):
        raise ValueError("two separate company projections required")
    cards = []
    for company, label in _COMPANIES.items():
        view = _map(reports[company])
        if "input_status" in view:
            heading = "Operations" if company == "ai_revenue" else "Snapshot"
            panels = _panel(company, heading, view)
        else:
            panels = _panel(company, "Snapshot", _map(view.get("snapshot")))
            if company == "ai_revenue":
                panels += _panel(company, "Operations", _map(view.get("operations")))
        cards.append(f'<article aria-labelledby="{company}"><h2 id="{company}" class="company-title">{escape(label)}</h2>'
                     f'{panels}</article>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Main Hub / OCC · Executive visibility</title>
<style>{_STYLE}</style>
</head>
<body>
<header><div><h1>Main Hub / OCC</h1><p>Offline, read-only · Operational readiness unverified</p>{_assessment_caption(assessed_at)}</div></header>
<main class="company-grid" aria-label="Separate company reports">{''.join(cards)}</main>
</body>
</html>"""

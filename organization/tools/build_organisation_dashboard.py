#!/usr/bin/env python3
"""Build a read-only consolidated Organisation Control Centre report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from build_dependency_report import build_report
from build_executive_snapshot import build_snapshot, read_csv
from validate_readiness import validate
from validate_operating_framework import build_report as build_operating_framework_report
from validate_work_queue import build_report as build_work_queue_report
from validate_execution_log import build_report as build_execution_log_report
from validate_division_integrations import build_report as build_division_integration_report
from validate_incident_register import validate as validate_incident_register
from validate_security_posture import build_report as build_security_posture_report
from build_task_dispatch import build_dispatch_report
from build_finance_controls import build_report as build_finance_controls_report

RISK_CONTROLS = Path(__file__).resolve().parent.parent / "risk-controls"
sys.path.insert(0, str(RISK_CONTROLS))
from validate_registers import validate_evidence_register


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_governance_links(work_queue, risk_register, decision_register, registry):
    """Validate governance references defensively; malformed input becomes errors, not crashes."""
    errors = []
    tasks = {
        item.get("id") for item in (work_queue or {}).get("tasks", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    divisions = {item.get("id") for item in registry.get("divisions", []) if isinstance(item, dict) and isinstance(item.get("id"), str)}
    risks = risk_register or {"records": []}
    decisions = decision_register or {"records": []}
    risk_rows = risks.get("records", []) if isinstance(risks, dict) else None
    decision_rows = decisions.get("records", []) if isinstance(decisions, dict) else None
    if not isinstance(risk_rows, list) or not isinstance(decision_rows, list):
        return ["Risk and decision records must be arrays in object registers."], {
            "risk_count": 0, "decision_count": 0, "linked_task_count": 0
        }

    def index_records(rows, label):
        indexed = {}
        for position, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{label} record at index {position} must be an object.")
                continue
            record_id = row.get("id")
            if not isinstance(record_id, str) or not record_id.strip():
                errors.append(f"{label} record at index {position} requires a non-empty string id.")
                continue
            if record_id in indexed:
                errors.append(f"{label} record ids must be unique: {record_id}.")
            indexed[record_id] = row
        return indexed

    risk_index = index_records(risk_rows, "Risk")
    decision_index = index_records(decision_rows, "Decision")
    linked_tasks = set()

    def references(row, field, known, label, record_id):
        values = row.get(field, [])
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            errors.append(f"{label} {record_id} field {field} must be an array of non-empty strings.")
            return []
        target_label = {
            "related_task_ids": "task",
            "related_decision_ids": "decision",
            "related_risk_ids": "risk"
        }.get(field, field)
        for value in values:
            if value not in known:
                errors.append(f"{label} {record_id} references unknown {target_label} {value}.")
        return values

    for record_id, row in risk_index.items():
        for field in ("severity", "status", "description", "division_id", "mitigation", "owner_assignment"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"Risk {record_id} requires non-empty {field}.")
        if row.get("severity") not in {"critical", "high", "medium", "low", "unassessed"}:
            errors.append(f"Risk {record_id} has invalid severity.")
        if row.get("status") not in {"open", "mitigating", "accepted_pending_owner_approval", "closed", "unassessed"}:
            errors.append(f"Risk {record_id} has invalid status.")
        if row.get("division_id") not in divisions:
            errors.append(f"Risk {record_id} references unknown division {row.get('division_id')!r}.")
        linked_tasks.update(references(row, "related_task_ids", tasks, "Risk", record_id))
        references(row, "related_decision_ids", decision_index, "Risk", record_id)

    for record_id, row in decision_index.items():
        for field in ("scope", "status", "impact", "reversibility", "requested_action"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"Decision {record_id} requires non-empty {field}.")
        linked_tasks.update(references(row, "related_task_ids", tasks, "Decision", record_id))
        references(row, "related_risk_ids", risk_index, "Decision", record_id)
        if row.get("status") == "approved" and not row.get("owner_outcome_evidence"):
            errors.append(f"Approved decision {record_id} requires explicit owner outcome evidence.")

    return errors, {
        "risk_count": len(risk_rows),
        "decision_count": len(decision_rows),
        "linked_task_count": len(linked_tasks)
    }


def build_risk_escalation_report(risk_register, decision_register, work_queue, execution_report, operating_framework, registry):
    """Derive internal escalation routes; never dispatch notifications or authorise actions."""
    risks = risk_register.get("records", []) if isinstance(risk_register, dict) else []
    decisions = decision_register.get("records", []) if isinstance(decision_register, dict) else []
    tasks = {
        item.get("id"): item for item in (work_queue or {}).get("tasks", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    decision_index = {
        item.get("id"): item for item in decisions
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    task_states = execution_report.get("task_state_from_events", {})
    all_divisions = sorted(item.get("id") for item in registry.get("divisions", []) if isinstance(item, dict) and isinstance(item.get("id"), str))
    risk_division = next(
        (item for item in operating_framework.get("divisions", []) if item.get("id") == "risk"), {}
    )
    broadcast_handoff = next(
        (item for item in risk_division.get("handoffs", [])
         if isinstance(item, dict) and item.get("to") == "all"), None
    )
    escalations = []
    for risk in risks if isinstance(risks, list) else []:
        if not isinstance(risk, dict) or risk.get("status") in {"closed", "unassessed"}:
            continue
        severity = risk.get("severity")
        if severity not in {"critical", "high", "medium", "low"}:
            continue
        task_ids = risk.get("related_task_ids", [])
        decision_ids = risk.get("related_decision_ids", [])
        linked_tasks = []
        for task_id in task_ids if isinstance(task_ids, list) else []:
            if not isinstance(task_id, str):
                continue
            task = tasks.get(task_id)
            if task:
                linked_tasks.append({
                    "task_id": task_id,
                    "division_id": task.get("division_id"),
                    "derived_execution_state": task_states.get(task_id, "no_validated_execution_event")
                })
        pending_decisions = [
            decision_id for decision_id in decision_ids if isinstance(decision_id, str)
            and decision_id in decision_index and decision_index[decision_id].get("status") == "pending"
        ] if isinstance(decision_ids, list) else []
        urgent = severity in {"critical", "high"}
        affected = risk.get("division_id")
        escalations.append({
            "risk_id": risk.get("id"),
            "severity": severity,
            "risk_status": risk.get("status"),
            "description": risk.get("description", ""),
            "mitigation": risk.get("mitigation", ""),
            "owner_assignment": risk.get("owner_assignment", "unassigned_pending_owner_confirmation"),
            "risk_evidence": risk.get("evidence", []) if isinstance(risk.get("evidence", []), list) else [],
            "affected_division": affected,
            "escalation_tier": "immediate_independent_review" if urgent else "standard_risk_review",
            "route": ["risk", "executive"] + ([affected] if isinstance(affected, str) and affected not in {"risk", "executive"} else []),
            "broadcast_scope": "all_divisions",
            "broadcast_divisions": all_divisions,
            "recommended_action": (
                "STOP-ONLY ADVISORY: recommend pausing the affected activity pending independent Risk review and Executive coordination. This is a recommendation, not an executed stop or permission to act."
                if urgent else
                "Route for documented Risk review and proportionate mitigation; no execution authority is created."
            ),
            "linked_tasks": linked_tasks,
            "pending_owner_decision_ids": pending_decisions,
            "owner_decision_path": (
                "Existing linked owner decision is pending."
                if pending_decisions else
                "Create a scoped owner decision request only if the proposed response crosses a reserved approval boundary."
            ),
            "handoff_artifact": broadcast_handoff.get("artifact") if isinstance(broadcast_handoff, dict) else None,
            "handoff_trigger": broadcast_handoff.get("trigger") if isinstance(broadcast_handoff, dict) else None,
            "dispatch_status": "derived_dashboard_route_only_not_dispatched",
            "authority": "Risk may independently challenge and recommend stop; only the owner can approve reserved actions. Deterministic controls remain authoritative."
        })
    escalations.sort(key=lambda row: (row["escalation_tier"] != "immediate_independent_review", row["risk_id"] or ""))
    return {
        "policy": "Escalations are derived from evidence-backed risk records. Dashboard routing does not send notifications, change task states, execute stops, close risks, or approve actions.",
        "count": len(escalations),
        "immediate_review_count": sum(row["escalation_tier"] == "immediate_independent_review" for row in escalations),
        "records": escalations
    }

def build_ai_workforce_report(model_registry=None, agent_roles=None, division_registry=None):
    """Validate and summarize model/agent registry without granting execution authority."""
    if model_registry is None or agent_roles is None:
        return {"status": "not_configured", "model_count": 0, "role_count": 0, "errors": [],
                "policy": "No AI workforce registry supplied; no agent authority is implied."}
    errors = []
    policy = model_registry.get("policy", {})
    if policy.get("incremental_spend_cad") != 0:
        errors.append("AI workforce incremental spend must remain CAD 0.")
    if policy.get("paid_apis") is not False or policy.get("paid_trials") is not False:
        errors.append("Paid APIs and paid trials must remain disabled.")
    models = model_registry.get("models", [])
    model_ids = [m.get("id") for m in models if isinstance(m, dict)]
    if len(model_ids) != len(models) or len(model_ids) != len(set(model_ids)):
        errors.append("Model entries must be objects with unique IDs.")
    model_map = {m.get("id"): m for m in models if isinstance(m, dict)}
    allowed_model_states = {"integrated_in_main_unverified_end_to_end", "evaluation_candidate", "benchmark_candidate_only", "verified"}
    for model in models:
        if not isinstance(model, dict) or model.get("status") not in allowed_model_states:
            errors.append("Every model requires a recognized evidence-based status.")
    roles = agent_roles.get("roles", [])
    role_ids = [r.get("id") for r in roles if isinstance(r, dict)]
    if len(role_ids) != len(roles) or len(role_ids) != len(set(role_ids)):
        errors.append("Agent roles must be objects with unique IDs.")
    for role in roles:
        if isinstance(role, dict) and role.get("model_id") and role["model_id"] not in model_map:
            errors.append(f"Role {role.get('id')} references unknown model {role['model_id']}.")
    if division_registry is not None:
        expected = {d.get("name") for d in division_registry.get("divisions", []) if isinstance(d, dict)}
        declared = set(agent_roles.get("divisions", []))
        if expected != declared:
            errors.append("AI workforce division names do not match the Control Centre division registry.")
    return {"status": "validated" if not errors else "invalid", "model_count": len(models), "role_count": len(roles),
        "models": [{"id":m.get("id"),"provider":m.get("provider"),"model":m.get("model"),"status":m.get("status"),"deployment":m.get("deployment"),"next_gate":m.get("next_gate")} for m in models if isinstance(m,dict)],
        "roles": [{"id":r.get("id"),"model_id":r.get("model_id"),"authority":r.get("authority"),"scope":r.get("scope")} for r in roles if isinstance(r,dict)],
        "policy":"Model outputs are drafts/reviews only. No model can approve spending, publish, contact third parties, trade, sign, merge or deploy.","errors":errors}


def build_occ_control_health_report(snapshot=None):
    """Expose an integrated OCC snapshot audit without granting control authority."""
    if snapshot is None:
        return {"status": "NOT_PROVIDED", "snapshot_id": None, "global_stop_active": None,
                "active_stops": [], "audit": None,
                "gold_specialist_audit": {"status": "NOT_PROVIDED", "instrument_count": 0,
                                          "instruments": [], "trade_authority": False,
                                          "live_readiness": False},
                "portfolio_risk": {"status": "UNKNOWN", "position_count": 0,
                                   "simultaneous_stop_count": 0, "trade_authority": False,
                                   "live_readiness": False},
                "oanda_account_margin_audit": {"status": "NOT_PROVIDED", "report": None,
                                               "errors": [], "trade_authority": False,
                                               "live_readiness": False},
                "oanda_pending_order_audit": {"status": "NOT_PROVIDED", "report": None,
                                              "errors": [], "trade_authority": False,
                                              "live_readiness": False},
                "oanda_closeout_transaction_audit": {"status": "NOT_PROVIDED", "report": None,
                                                      "errors": [], "trade_authority": False,
                                                      "live_readiness": False},
                "errors": [],
                "warnings": ["No unified OCC snapshot supplied to the Main Hub dashboard."],
                "trade_authority": False, "live_readiness": False}
    if not isinstance(snapshot, dict) or snapshot.get("snapshot_type") != "unified_occ_research_intelligence":
        return {"status": "HALT_AUDIT", "snapshot_id": None, "global_stop_active": None,
                "active_stops": [], "audit": None,
                "gold_specialist_audit": {"status": "HALT", "instrument_count": 0,
                                          "instruments": [], "trade_authority": False,
                                          "live_readiness": False},
                "oanda_account_margin_audit": {"status": "HALT", "report": None,
                                               "errors": ["Supplied OCC snapshot is invalid."],
                                               "trade_authority": False, "live_readiness": False},
                "oanda_pending_order_audit": {"status": "HALT", "report": None,
                                              "errors": ["Supplied OCC snapshot is invalid."],
                                              "trade_authority": False, "live_readiness": False},
                "oanda_closeout_transaction_audit": {"status": "HALT", "report": None,
                                                      "errors": ["Supplied OCC snapshot is invalid."],
                                                      "trade_authority": False, "live_readiness": False},
                "errors": ["Supplied OCC snapshot is missing or has an unsupported snapshot_type."],
                "warnings": [], "trade_authority": False, "live_readiness": False}
    audit = snapshot.get("control_health")
    if not isinstance(audit, dict):
        audit = {}
    status = audit.get("status")
    errors = list(audit.get("errors", [])) if isinstance(audit.get("errors", []), list) else ["OCC audit errors field is malformed."]
    warnings = list(audit.get("warnings", [])) if isinstance(audit.get("warnings", []), list) else ["OCC audit warnings field is malformed."]
    if status not in {"PASS_AUDIT", "WARN_AUDIT", "HALT_AUDIT", "NOT_PROVIDED"}:
        status = "HALT_AUDIT"
        errors.append("OCC control-health status is missing or unrecognized.")
    if audit.get("authority") != "research_only_no_execution_authority" or audit.get("trade_authority") is not False or audit.get("live_readiness") is not False:
        status = "HALT_AUDIT"
        errors.append("OCC control-health authority boundary is invalid.")
    if status == "HALT_AUDIT" and not errors:
        errors.append("OCC control-health audit is in HALT_AUDIT state.")
    portfolio_risk = snapshot.get("portfolio_risk")
    if not isinstance(portfolio_risk, dict):
        portfolio_risk = {"status": "UNKNOWN", "errors": [], "warnings": ["Portfolio risk audit was not supplied."],
                          "position_count": 0, "simultaneous_stop_count": 0,
                          "trade_authority": False, "live_readiness": False}
    elif (portfolio_risk.get("status") not in {"HALT", "UNKNOWN", "ASSESSED_WITHIN_CONFIGURED_LIMITS"}
          or portfolio_risk.get("trade_authority") is not False
          or portfolio_risk.get("live_readiness") is not False):
        portfolio_risk = dict(portfolio_risk)
        portfolio_risk["status"] = "HALT"
        errors.append("Portfolio risk audit is malformed or violates its research-only authority boundary.")
        status = "HALT_AUDIT"
    elif portfolio_risk.get("status") == "HALT":
        errors.append("Portfolio-wide risk audit reports a stop or limit breach.")
        status = "HALT_AUDIT"
    elif portfolio_risk.get("status") == "UNKNOWN":
        if status in {"PASS_AUDIT", "NOT_PROVIDED"}:
            status = "WARN_AUDIT"
        warnings.append("Portfolio-wide risk remains UNKNOWN; missing evidence is not treated as zero risk.")
    oanda_margin_audit = snapshot.get("oanda_account_margin_audit")
    if oanda_margin_audit is None:
        oanda_margin_audit = {"status": "NOT_PROVIDED", "report": None, "errors": [],
                              "trade_authority": False, "live_readiness": False}
    elif (not isinstance(oanda_margin_audit, dict)
          or oanda_margin_audit.get("status") not in {"NOT_PROVIDED", "PASS", "HALT"}
          or oanda_margin_audit.get("trade_authority") is not False
          or oanda_margin_audit.get("live_readiness") is not False
          or not isinstance(oanda_margin_audit.get("errors"), list)
          or any(not isinstance(item, str) for item in oanda_margin_audit.get("errors", []))
          or (oanda_margin_audit.get("status") == "NOT_PROVIDED" and oanda_margin_audit.get("report") is not None)
          or (oanda_margin_audit.get("status") in {"PASS", "HALT"} and not isinstance(oanda_margin_audit.get("report"), dict))
          or (oanda_margin_audit.get("status") == "PASS" and oanda_margin_audit.get("report", {}).get("status") != "WITHIN_MARGIN_REQUIREMENTS")
          or (oanda_margin_audit.get("status") == "HALT" and oanda_margin_audit.get("report", {}).get("status") == "WITHIN_MARGIN_REQUIREMENTS")):
        oanda_margin_audit = dict(oanda_margin_audit) if isinstance(oanda_margin_audit, dict) else {}
        oanda_margin_audit["status"] = "HALT"
        errors.append("OANDA account margin audit is malformed or violates its research-only authority boundary.")
        status = "HALT_AUDIT"
    elif oanda_margin_audit.get("status") == "HALT":
        errors.append("OANDA account-level margin audit reports a margin call, closeout or invalid replay.")
        status = "HALT_AUDIT"
    elif oanda_margin_audit.get("status") == "NOT_PROVIDED" and status == "PASS_AUDIT":
        status = "WARN_AUDIT"
        warnings.append("OANDA account-level margin audit was not supplied.")
    oanda_pending_audit = snapshot.get("oanda_pending_order_audit")
    if oanda_pending_audit is None:
        oanda_pending_audit = {"status": "NOT_PROVIDED", "report": None, "errors": [],
                               "trade_authority": False, "live_readiness": False}
    elif (not isinstance(oanda_pending_audit, dict)
          or oanda_pending_audit.get("status") not in {"NOT_PROVIDED", "PASS", "HALT"}
          or oanda_pending_audit.get("trade_authority") is not False
          or oanda_pending_audit.get("live_readiness") is not False
          or not isinstance(oanda_pending_audit.get("errors"), list)
          or any(not isinstance(item, str) for item in oanda_pending_audit.get("errors", []))
          or (oanda_pending_audit.get("status") == "NOT_PROVIDED" and oanda_pending_audit.get("report") is not None)
          or (oanda_pending_audit.get("status") in {"PASS", "HALT"} and not isinstance(oanda_pending_audit.get("report"), dict))
          or (oanda_pending_audit.get("status") == "PASS" and oanda_pending_audit.get("report", {}).get("status") != "PASS")
          or (oanda_pending_audit.get("status") == "HALT" and oanda_pending_audit.get("report", {}).get("status") == "PASS")
          or (oanda_pending_audit.get("status") in {"PASS", "HALT"} and
              (oanda_pending_audit.get("report", {}).get("trade_authority") is not False
               or oanda_pending_audit.get("report", {}).get("live_readiness") is not False
               or oanda_pending_audit.get("report", {}).get("authority") != "research_only_no_execution_authority"))):
        oanda_pending_audit = dict(oanda_pending_audit) if isinstance(oanda_pending_audit, dict) else {}
        oanda_pending_audit["status"] = "HALT"
        errors.append("OANDA pending-order audit is malformed or violates its research-only authority boundary.")
        status = "HALT_AUDIT"
    elif oanda_pending_audit.get("status") == "HALT":
        errors.append("OANDA pending-order audit reports surviving exposure-opening orders or invalid snapshot data.")
        status = "HALT_AUDIT"
    elif oanda_pending_audit.get("status") == "NOT_PROVIDED" and status == "PASS_AUDIT":
        status = "WARN_AUDIT"
        warnings.append("OANDA post-closeout pending-order snapshot was not supplied.")
    oanda_transaction_audit = snapshot.get("oanda_closeout_transaction_audit")
    if oanda_transaction_audit is None:
        oanda_transaction_audit = {"status": "NOT_PROVIDED", "report": None, "errors": [],
                                   "trade_authority": False, "live_readiness": False}
    elif (not isinstance(oanda_transaction_audit, dict)
          or oanda_transaction_audit.get("status") not in {"NOT_PROVIDED", "PASS", "HALT"}
          or oanda_transaction_audit.get("trade_authority") is not False
          or oanda_transaction_audit.get("live_readiness") is not False
          or not isinstance(oanda_transaction_audit.get("errors"), list)
          or any(not isinstance(item, str) for item in oanda_transaction_audit.get("errors", []))
          or (oanda_transaction_audit.get("status") == "NOT_PROVIDED" and oanda_transaction_audit.get("report") is not None)
          or (oanda_transaction_audit.get("status") in {"PASS", "HALT"} and not isinstance(oanda_transaction_audit.get("report"), dict))
          or (oanda_transaction_audit.get("status") == "PASS" and oanda_transaction_audit.get("report", {}).get("status") != "PASS")
          or (oanda_transaction_audit.get("status") == "HALT" and oanda_transaction_audit.get("report", {}).get("status") == "PASS")
          or (oanda_transaction_audit.get("status") in {"PASS", "HALT"} and
              (oanda_transaction_audit.get("report", {}).get("trade_authority") is not False
               or oanda_transaction_audit.get("report", {}).get("live_readiness") is not False
               or oanda_transaction_audit.get("report", {}).get("authority") != "research_only_no_execution_authority"))):
        oanda_transaction_audit = dict(oanda_transaction_audit) if isinstance(oanda_transaction_audit, dict) else {}
        oanda_transaction_audit["status"] = "HALT"
        errors.append("OANDA closeout transaction audit is malformed or violates its research-only authority boundary.")
        status = "HALT_AUDIT"
    elif oanda_transaction_audit.get("status") == "HALT":
        errors.append("OANDA closeout order-cancellation transaction reconciliation failed.")
        status = "HALT_AUDIT"
    elif oanda_transaction_audit.get("status") == "NOT_PROVIDED" and status == "PASS_AUDIT":
        status = "WARN_AUDIT"
        warnings.append("OANDA closeout transaction reconciliation was not supplied.")
    gold_audit = snapshot.get("gold_specialist_audit")
    if not isinstance(gold_audit, dict):
        gold_audit = {"status": "NOT_PROVIDED", "instrument_count": 0,
                      "instruments": [], "trade_authority": False,
                      "live_readiness": False}
    elif (gold_audit.get("status") not in {"PASS", "WARN", "HALT", "NOT_PROVIDED"}
          or gold_audit.get("trade_authority") is not False
          or gold_audit.get("live_readiness") is not False
          or not isinstance(gold_audit.get("instruments"), list)):
        gold_audit = dict(gold_audit)
        gold_audit["status"] = "HALT"
        errors.append("Gold specialist audit is malformed or violates its research-only authority boundary.")
        status = "HALT_AUDIT"
    elif gold_audit.get("status") == "HALT":
        errors.append("Gold specialist audit reports a HALT for at least one instrument.")
        status = "HALT_AUDIT"
    elif gold_audit.get("status") == "WARN" and status == "PASS_AUDIT":
        status = "WARN_AUDIT"
    return {
        "status": status,
        "snapshot_id": audit.get("latest_verified_snapshot_id"),
        "snapshot_status": snapshot.get("status"),
        "global_stop_active": snapshot.get("global_stop_active"),
        "active_stops": snapshot.get("active_stops", []) if isinstance(snapshot.get("active_stops", []), list) else [],
        "gold_specialist_audit": gold_audit,
        "portfolio_risk": portfolio_risk,
        "oanda_account_margin_audit": oanda_margin_audit,
        "oanda_pending_order_audit": oanda_pending_audit,
        "oanda_closeout_transaction_audit": oanda_transaction_audit,
        "audit": audit,
        "errors": errors,
        "warnings": warnings,
        "trade_authority": False,
        "live_readiness": False,
    }


def build_dashboard(registry, readiness, dependency_map, operating_framework, opportunities, ledger, work_queue=None, execution_log=None, risk_register=None, decision_register=None, incident_register=None, recovery_plan=None, security_report=None, ai_model_registry=None, ai_agent_roles=None, finance_policy=None, commitment_register=None, evidence_register=None, occ_control_health=None):
    errors, warnings = validate(registry, readiness)
    security_report = security_report or build_security_posture_report(Path.cwd())
    ai_workforce_report = build_ai_workforce_report(ai_model_registry, ai_agent_roles, registry)
    occ_control_health_report = build_occ_control_health_report(occ_control_health)
    dependency_report = build_report(registry, readiness, dependency_map)
    revenue = build_snapshot(opportunities, ledger)
    operating = build_operating_framework_report(registry, operating_framework)
    work_queue_report = build_work_queue_report(registry, work_queue or {"tasks": []})
    task_dispatch_report = (
        build_dispatch_report(registry, work_queue or {"tasks": []}, ai_agent_roles, work_queue_report)
        if ai_agent_roles is not None else
        {"status": "not_configured", "task_count": 0, "prepared_count": 0,
         "blocked_count": 0, "unassigned_count": 0, "dispatch_count": 0,
         "execution_authority": "none", "tasks": [], "errors": [],
         "policy": "No role registry supplied; no dispatch is possible."}
    )
    finance_controls_report = (
        build_finance_controls_report(finance_policy, commitment_register or [], ledger, registry)
        if finance_policy is not None else
        {"status": "not_configured", "commitments": {}, "revenue": {},
         "halal_screening": {"policy_status": "not_assessed", "flagged_sensitive_activity_count": 0, "flags": []},
         "warnings": ["Finance policy not supplied to this dashboard invocation."],
         "errors": [], "authority": "read_only_accounting_and_control_reporting_only"}
    )
    execution_report = build_execution_log_report(registry, work_queue or {"tasks": []}, execution_log or {"events": []})
    integration_report = build_division_integration_report(registry, dependency_map, operating_framework)
    governance_errors, governance_summary = validate_governance_links(work_queue, risk_register, decision_register, registry)
    risk_records = risk_register.get("records", []) if isinstance(risk_register, dict) and isinstance(risk_register.get("records", []), list) else []
    decision_records = decision_register.get("records", []) if isinstance(decision_register, dict) and isinstance(decision_register.get("records", []), list) else []
    risk_escalations = build_risk_escalation_report(risk_register, decision_register, work_queue, execution_report, operating_framework, registry)
    incident_source = {"records": []} if incident_register is None else incident_register
    incident_errors = validate_incident_register(
        incident_source, risk_register or {"records": []},
        decision_register or {"records": []}, work_queue or {"tasks": []}, registry
    )
    incident_records = incident_source.get("records", []) if isinstance(incident_source, dict) and isinstance(incident_source.get("records", []), list) else []
    evidence_source = {"schema_version": "1.0.0", "records": []} if evidence_register is None else evidence_register
    evidence_errors = validate_evidence_register(evidence_source, incident_source, registry)
    evidence_records = evidence_source.get("records", []) if isinstance(evidence_source, dict) and isinstance(evidence_source.get("records", []), list) else []
    evidence_report = {
        "policy": "Evidence metadata only. References are not independently authenticated merely by appearing here; preserve original evidence and never store secrets.",
        "record_count": len(evidence_records),
        "accepted_count": sum(1 for row in evidence_records if isinstance(row, dict) and row.get("review_status") == "accepted"),
        "unreviewed_count": sum(1 for row in evidence_records if isinstance(row, dict) and row.get("review_status") == "unreviewed"),
        "integrity_failed_count": sum(1 for row in evidence_records if isinstance(row, dict) and row.get("integrity_status") == "integrity_failed"),
        "records": evidence_records,
        "errors": evidence_errors
    }
    recovery_source = recovery_plan if isinstance(recovery_plan, dict) else {"procedures": []}
    recovery_procedures = recovery_source.get("procedures", []) if isinstance(recovery_source.get("procedures", []), list) else []
    technical_recovery = {
        "plan_status": recovery_source.get("status", "unassessed"),
        "scope": recovery_source.get("scope", "unassessed"),
        "procedure_count": len(recovery_procedures),
        "procedures": recovery_procedures,
        "production_recovery_verified": False,
        "drill_scope": "isolated_temporary_fixture_only; CI runs backup, restore, rollback and synthetic health checks",
        "readiness_note": "A passing fixture drill is not production recovery evidence or launch readiness."
    }
    incident_actions = [
        action for incident in incident_records if isinstance(incident, dict)
        for action in incident.get("corrective_actions", [])
        if isinstance(incident.get("corrective_actions", []), list) and isinstance(action, dict)
    ]
    incident_response = {
        "policy": "Incident and corrective-action states are owner-maintained evidence records. The dashboard does not contain, recover, roll back, notify, assign owners, or close incidents. Critical/high records follow the existing Risk stop-only advisory route.",
        "incident_count": len(incident_records),
        "critical_or_high_count": sum(
            1 for row in incident_records if isinstance(row, dict)
            and row.get("severity") in {"critical", "high"}
            and row.get("status") not in {"closed", "unassessed"}
        ),
        "corrective_action_count": len(incident_actions),
        "corrective_actions_completed": sum(1 for row in incident_actions if row.get("status") == "completed"),
        "escalations": [
            {
                "incident_id": row.get("id"),
                "severity": row.get("severity"),
                "route": ["risk", "executive"] + ([row.get("affected_division_id")] if row.get("affected_division_id") not in {"risk", "executive"} else []),
                "recommended_action": "STOP-ONLY ADVISORY: recommend pausing affected activity pending independent Risk review and Executive coordination; no stop is executed.",
                "dispatch_status": "dashboard_route_only_not_dispatched"
            }
            for row in incident_records if isinstance(row, dict)
            and row.get("severity") in {"critical", "high"}
            and row.get("status") not in {"closed", "unassessed"}
        ],
        "records": incident_records
    }

    assessments = {a["division_id"]: a for a in readiness.get("division_assessments", [])}
    divisions = []
    for division in registry.get("divisions", []):
        assessment = assessments.get(division["id"], {})
        dependency = next(
            (row for row in dependency_report.get("divisions", [])
             if row["division_id"] == division["id"]),
            {}
        )
        divisions.append({
            "id": division["id"],
            "name": division["name"],
            "registry_status": division.get("status", "unassessed"),
            "verified_status": assessment.get("verified_status", "unassessed"),
            "dependency_status": dependency.get("dependency_status", "unmapped"),
            "required_blockers": dependency.get("required_blockers", []),
            "supporting_gaps": dependency.get("supporting_gaps", []),
            "open_gaps": assessment.get("open_gaps", []),
            "evidence_count": len(assessment.get("evidence", []))
        })

    risks = []
    decisions = []
    for division in divisions:
        for gap in division["open_gaps"]:
            risks.append({
                "division_id": division["id"],
                "category": "readiness_gap",
                "description": gap
            })
            decisions.append({
                "division_id": division["id"],
                "item": gap,
                "requires_owner_decision": any(
                    term in gap.lower()
                    for term in ("approval", "owner", "reconcile", "review", "fund", "funding")
                )
            })
        for blocker in division["required_blockers"]:
            risks.append({
                "division_id": division["id"],
                "category": "dependency_blocker",
                "description": blocker
            })

    organisation = registry.get("organisation", {})
    reserved_approvals = organisation.get("owner_approval_required_for", [])
    return {
        "schema_version": 1,
        "report_type": "read_only_organisation_control_centre",
        "policy": "This report consolidates source records. It does not change readiness, approve actions, connect accounts, or verify bank balances.",
        "organisation": {
            "name": organisation.get("name", "Organisation"),
            "strategic_priority": organisation.get("strategic_priority", ""),
            "operating_budget_default": organisation.get("operating_budget_default", "Not specified"),
            "division_count": len(divisions),
            "verified_standby_or_operational": sum(
                1 for d in divisions if d["verified_status"] in {"standby", "operational"}
            ),
            "divisions_with_required_dependency_blockers": sum(
                1 for d in divisions if d["required_blockers"]
            )
        },
        "division_scorecard": divisions,
        "cross_division_dependencies": dependency_report,
        "division_operating_framework": operating,
        "division_work_queue": work_queue_report,
        "task_dispatch": task_dispatch_report,
        "division_execution_evidence": execution_report,
        "cross_division_integration": integration_report,
        "ai_workforce": ai_workforce_report,
        "finance_controls": finance_controls_report,
        "ai_revenue": revenue,
        "risk_escalations": risk_escalations,
        "incident_response": incident_response,
        "evidence_register": evidence_report,
        "technical_recovery": technical_recovery,
        "security_posture": security_report,
        "occ_control_health": occ_control_health_report,
        "risk_register": {
            "records": risk_records,
            "readiness_and_dependency_warnings": risks,
            "summary": governance_summary
        },
        "decision_register": {
            "records": decision_records,
            "readiness_gap_prompts": decisions,
            "summary": governance_summary
        },
        "outstanding_decisions": decisions + [row for row in decision_records if isinstance(row, dict) and row.get("status") == "pending"],
        "reserved_owner_approvals": reserved_approvals,
        "data_quality": {
            "readiness_validation_errors": errors,
            "readiness_validation_warnings": warnings,
            "dependency_map_errors": dependency_report.get("errors", []),
            "operating_framework_errors": operating.get("errors", []),
            "work_queue_errors": work_queue_report.get("errors", []),
            "task_dispatch_errors": task_dispatch_report.get("errors", []),
            "finance_control_errors": finance_controls_report.get("errors", []),
            "execution_log_errors": execution_report.get("errors", []),
            "cross_division_integration_errors": integration_report.get("errors", []),
            "governance_link_errors": governance_errors,
            "incident_register_errors": incident_errors,
            "evidence_register_errors": evidence_errors,
            "ai_workforce_errors": ai_workforce_report.get("errors", []),
            "occ_control_health_errors": occ_control_health_report.get("errors", []),
            "revenue_warnings": revenue["data_quality"]["warnings"],
            "note": "Absence of a record is not proof that work or funds do not exist outside these source files."
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path("organization/division-registry.json"))
    parser.add_argument("--readiness", type=Path, default=Path("organization/readiness-register.json"))
    parser.add_argument("--dependencies", type=Path, default=Path("organization/dependency-map.json"))
    parser.add_argument("--operating-framework", type=Path, default=Path("organization/operating-framework.json"))
    parser.add_argument("--work-queue", type=Path, default=Path("organization/work-queue.json"))
    parser.add_argument("--execution-log", type=Path, default=Path("organization/execution-log.json"))
    parser.add_argument("--risk-register", type=Path, default=Path("organization/risk-register.json"))
    parser.add_argument("--decision-register", type=Path, default=Path("organization/decision-register.json"))
    parser.add_argument("--incident-register", type=Path, default=Path("organization/incident-register.json"))
    parser.add_argument("--evidence-register", type=Path, default=Path("organization/risk-controls/evidence-register.json"))
    parser.add_argument("--recovery-plan", type=Path, default=Path("organization/recovery-plan.json"))
    parser.add_argument("--opportunities", type=Path, default=Path("intelligence/opportunity-tracker.csv"))
    parser.add_argument("--ledger", type=Path, default=Path("finance/revenue-ledger.csv"))
    parser.add_argument("--finance-policy", type=Path, default=Path("finance/financial-control-policy.json"))
    parser.add_argument("--commitments", type=Path, default=Path("finance/commitment-register.csv"))
    parser.add_argument("--ai-model-registry", type=Path, default=Path("organization/ai-workforce/model-registry.json"))
    parser.add_argument("--ai-agent-roles", type=Path, default=Path("organization/ai-workforce/agent-roles.json"))
    parser.add_argument("--occ-control-health-snapshot", type=Path)
    args = parser.parse_args()
    report = build_dashboard(
        load_json(args.registry), load_json(args.readiness), load_json(args.dependencies),
        load_json(args.operating_framework), read_csv(args.opportunities), read_csv(args.ledger),
        load_json(args.work_queue), load_json(args.execution_log),
        load_json(args.risk_register), load_json(args.decision_register), load_json(args.incident_register), load_json(args.recovery_plan),
        ai_model_registry=load_json(args.ai_model_registry), ai_agent_roles=load_json(args.ai_agent_roles),
        evidence_register=load_json(args.evidence_register),
        finance_policy=load_json(args.finance_policy), commitment_register=read_csv(args.commitments),
        occ_control_health=load_json(args.occ_control_health_snapshot) if args.occ_control_health_snapshot else None
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["data_quality"]["readiness_validation_errors"] or report["data_quality"]["dependency_map_errors"] or report["data_quality"]["operating_framework_errors"] or report["data_quality"]["work_queue_errors"] or report["data_quality"]["task_dispatch_errors"] or report["data_quality"]["finance_control_errors"] or report["data_quality"]["execution_log_errors"] or report["data_quality"]["cross_division_integration_errors"] or report["data_quality"]["governance_link_errors"] or report["data_quality"]["incident_register_errors"] or report["data_quality"]["evidence_register_errors"] or report["data_quality"]["ai_workforce_errors"] or report["security_posture"]["errors"] or report["data_quality"]["occ_control_health_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

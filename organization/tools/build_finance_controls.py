"""Read-only Finance and Treasury controls for revenue and commitments."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from collections import Counter

RECEIVED = {"paid", "received", "settled"}
ACTIVITY_TYPES = {"income", "expense", "financing", "investment", "yield", "trading", "transfer", "tax", "other"}
SENSITIVE_ACTIVITIES = {"financing", "investment", "yield", "trading"}

def _amount(value, label, errors, warnings, required=False):
    if value is None or str(value).strip() == "":
        if required:
            errors.append(f"{label}: amount is required")
        return Decimal("0")
    try:
        result = Decimal(str(value).strip())
        if not result.is_finite() or result < 0:
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError):
        errors.append(f"{label}: amount must be finite and non-negative")
        return Decimal("0")

def build_report(policy, commitments, revenue_ledger, registry):
    errors, warnings = [], []
    if not isinstance(policy, dict):
        policy = {}
        errors.append("Finance policy must be an object")
    if policy.get("incremental_spend_cad") != 0 or policy.get("approved_spend_ceiling_cad") != 0:
        warnings.append("Non-zero spending ceiling detected; confirm separate owner-approved funding evidence.")
    if policy.get("paid_services_enabled") is not False or policy.get("paid_apis_enabled") is not False or policy.get("paid_trials_enabled") is not False:
        errors.append("Paid services, APIs and trials must remain disabled under the current zero-spend mandate.")
    ceiling = _amount(policy.get("approved_spend_ceiling_cad", 0), "approved_spend_ceiling_cad", errors, warnings)
    division_ids = {d.get("id") for d in registry.get("divisions", []) if isinstance(d, dict)}
    commitment_ids = set()
    committed_total = Decimal("0")
    approved_total = Decimal("0")
    paid_total = Decimal("0")
    currency_totals = Counter()
    halal_flags = []
    commitment_rows = commitments if isinstance(commitments, list) else None
    if commitment_rows is None:
        errors.append("Commitments must be a list")
        commitment_rows = []
    allowed_payment = set(policy.get("payment_statuses", []))
    allowed_approval = set(policy.get("approval_statuses", []))
    allowed_halal = set(policy.get("halal_review_statuses", []))
    for index, row in enumerate(commitment_rows, start=2):
        if not isinstance(row, dict):
            errors.append(f"Commitment row {index} must be an object")
            continue
        record_id = str(row.get("id", "")).strip()
        if not record_id or record_id in commitment_ids:
            errors.append(f"Commitment row {index} requires a unique non-empty id")
        commitment_ids.add(record_id)
        division = row.get("division_id")
        if division not in division_ids:
            errors.append(f"{record_id}: unknown division {division!r}")
        currency = str(row.get("currency", "")).strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            errors.append(f"{record_id}: currency must be a three-letter code")
        estimated = _amount(row.get("estimated_amount"), f"{record_id}.estimated_amount", errors, warnings)
        approved = _amount(row.get("approved_amount"), f"{record_id}.approved_amount", errors, warnings)
        committed = _amount(row.get("committed_amount"), f"{record_id}.committed_amount", errors, warnings)
        paid = _amount(row.get("paid_amount"), f"{record_id}.paid_amount", errors, warnings)
        approval = row.get("approval_status")
        payment = row.get("payment_status")
        if approval not in allowed_approval:
            errors.append(f"{record_id}: invalid approval_status")
        if payment not in allowed_payment:
            errors.append(f"{record_id}: invalid payment_status")
        if approved > 0 or committed > 0 or paid > 0:
            if ceiling <= 0:
                errors.append(f"{record_id}: positive spend is blocked by the CAD 0 approved ceiling")
            if approval != "approved" or not str(row.get("approval_reference", "")).strip():
                errors.append(f"{record_id}: positive approved/committed/paid amounts require owner approval evidence")
        if committed > approved:
            errors.append(f"{record_id}: committed amount exceeds approved amount")
        if paid > committed:
            errors.append(f"{record_id}: paid amount exceeds committed amount")
        if paid > 0 and not str(row.get("proof_reference", "")).strip():
            errors.append(f"{record_id}: paid amount requires proof_reference")
        activity = row.get("activity_type", "other")
        if activity not in ACTIVITY_TYPES:
            errors.append(f"{record_id}: invalid activity_type")
        halal = row.get("halal_review_status", "not_assessed")
        if halal not in allowed_halal:
            errors.append(f"{record_id}: invalid halal_review_status")
        if activity in SENSITIVE_ACTIVITIES and halal == "not_assessed":
            halal_flags.append({"id": record_id, "activity_type": activity, "status": "requires_review"})
        if halal == "reviewed_with_advisory_source":
            if not str(row.get("halal_review_reference", "")).strip() or not str(row.get("halal_review_notes", "")).strip():
                errors.append(f"{record_id}: advisory review status requires source reference and reviewer notes")
        if currency == "CAD":
            approved_total += approved
            committed_total += committed
            paid_total += paid
            currency_totals[currency] += committed
        else:
            if approved > 0 or committed > 0 or paid > 0:
                errors.append(f"{record_id}: non-CAD commitments require documented FX conversion before spend-limit validation")
            warnings.append(f"{record_id}: {currency} commitment excluded from CAD totals; no FX conversion is assumed")
    if approved_total > ceiling:
        errors.append("Aggregate approved CAD amount exceeds the approved spend ceiling")
    if committed_total > ceiling:
        errors.append("Aggregate committed CAD amount exceeds the approved spend ceiling")
    ledger_rows = revenue_ledger if isinstance(revenue_ledger, list) else None
    if ledger_rows is None:
        errors.append("Revenue ledger must be a list")
        ledger_rows = []
    received_cash_cad = Decimal("0")
    received_rows = 0
    for index, row in enumerate(ledger_rows, start=2):
        if not isinstance(row, dict):
            errors.append(f"Revenue ledger row {index} must be an object")
            continue
        status = str(row.get("payment_status", "")).strip().lower()
        net = _amount(row.get("net_received_cad"), f"revenue-row-{index}.net_received_cad", errors, warnings)
        if status in RECEIVED:
            if net > 0 and not str(row.get("proof_reference", "")).strip():
                warnings.append(f"revenue-row-{index}: received status has no proof_reference")
            received_cash_cad += net
            received_rows += 1
    return {
        "schema_version": 1,
        "status": "validated" if not errors else "invalid",
        "policy_status": policy.get("status", "unassessed"),
        "currency_default": policy.get("currency_default", "CAD"),
        "approved_spend_ceiling_cad": str(ceiling.quantize(Decimal("0.01"))),
        "commitments": {
            "record_count": len(commitment_rows),
            "approved_cad": str(approved_total.quantize(Decimal("0.01"))),
            "committed_cad": str(committed_total.quantize(Decimal("0.01"))),
            "paid_cad": str(paid_total.quantize(Decimal("0.01"))),
            "currency_totals": {k: str(v.quantize(Decimal("0.01"))) for k,v in currency_totals.items()}
        },
        "revenue": {
            "ledger_rows": len(ledger_rows),
            "cash_received_cad_by_ledger_status": str(received_cash_cad.quantize(Decimal("0.01"))),
            "rows_with_received_status": received_rows,
            "independently_verified_bank_balance": False
        },
        "halal_screening": {
            "policy_status": policy.get("halal_safeguards", {}).get("status", "not_assessed"),
            "flagged_sensitive_activity_count": len(halal_flags),
            "flags": halal_flags,
            "note": "Screening only; no automated religious ruling or certification."
        },
        "warnings": warnings,
        "errors": errors,
        "authority": "read_only_accounting_and_control_reporting_only"
    }

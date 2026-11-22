#!/usr/bin/env python3
"""Build a read-only executive snapshot from AI Revenue's existing CSV records.

No network access, account access, writes, or financial actions are performed.
Only ledger rows explicitly marked paid/received/settled count as cash received.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def amount(value, field, row_id, warnings):
    if value is None or not str(value).strip():
        return Decimal("0")
    try:
        parsed = Decimal(str(value).strip())
        if not parsed.is_finite():
            raise InvalidOperation
        return parsed
    except InvalidOperation:
        warnings.append(f"{row_id}: invalid numeric value in {field}; treated as zero")
        return Decimal("0")


def money(value):
    return str(value.quantize(Decimal("0.01")))


def build_snapshot(opportunities, ledger):
    warnings = []
    status_counts = Counter((row.get("status") or "unspecified").strip().lower() for row in opportunities)
    eligible_checked = sum(
        1 for row in opportunities
        if (row.get("canada_eligibility_checked") or "").strip().lower() in {"yes", "true", "checked"}
    )
    verified_rows = sum(
        1 for row in opportunities
        if (row.get("evidence_checked_on") or "").strip()
        and (row.get("official_url") or "").strip()
    )

    estimate = Decimal("0")
    accepted = Decimal("0")
    received = Decimal("0")
    fees = Decimal("0")
    direct_costs = Decimal("0")
    paid_rows = 0
    unpaid_accepted_rows = 0
    unclassified_payment_rows = []

    for index, row in enumerate(ledger, start=2):
        row_id = (row.get("opportunity_id") or "").strip() or f"ledger-row-{index}"
        estimate += amount(row.get("gross_estimate"), "gross_estimate", row_id, warnings)
        accepted += amount(row.get("gross_accepted"), "gross_accepted", row_id, warnings)
        row_fees = amount(row.get("fees"), "fees", row_id, warnings)
        row_costs = amount(row.get("direct_costs"), "direct_costs", row_id, warnings)
        fees += row_fees
        direct_costs += row_costs
        payment = (row.get("payment_status") or "").strip().lower()
        net_cash = amount(row.get("net_received_cad"), "net_received_cad", row_id, warnings)
        if payment in {"paid", "received", "settled"}:
            received += net_cash
            paid_rows += 1
        elif payment in {"accepted", "approved", "approved_unpaid", "unpaid", "pending"}:
            if amount(row.get("gross_accepted"), "gross_accepted", row_id, warnings) > 0:
                unpaid_accepted_rows += 1
        elif payment:
            unclassified_payment_rows.append({"row": row_id, "payment_status": payment})

    return {
        "schema_version": 1,
        "source": {
            "opportunity_tracker_rows": len(opportunities),
            "revenue_ledger_rows": len(ledger),
            "mode": "read_only_local_csv_snapshot"
        },
        "pipeline": {
            "status_counts": dict(sorted(status_counts.items())),
            "opportunities_with_official_url_and_evidence_date": verified_rows,
            "canada_eligibility_checked": eligible_checked,
            "canada_eligibility_not_checked": len(opportunities) - eligible_checked
        },
        "finance_cad": {
            "gross_estimate_unconfirmed": money(estimate),
            "gross_accepted_not_necessarily_paid": money(accepted),
            "net_cash_received_verified_by_ledger_status": money(received),
            "recorded_fees": money(fees),
            "recorded_direct_costs": money(direct_costs),
            "paid_ledger_rows": paid_rows,
            "accepted_but_unpaid_rows": unpaid_accepted_rows
        },
        "data_quality": {
            "warnings": warnings,
            "unclassified_payment_statuses": unclassified_payment_rows,
            "note": "Amounts are ledger entries, not independently verified bank balances. Only rows marked paid/received/settled count as received cash. Empty ledgers produce zero recorded amounts, not proof of zero activity outside the ledger."
        }
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opportunities", type=Path, default=Path("intelligence/opportunity-tracker.csv"))
    parser.add_argument("--ledger", type=Path, default=Path("finance/revenue-ledger.csv"))
    args = parser.parse_args()
    snapshot = build_snapshot(read_csv(args.opportunities), read_csv(args.ledger))
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

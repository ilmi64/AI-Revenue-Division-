#!/usr/bin/env python3
"""Validate product-listing CSV files before marketplace import.

This tool is deliberately offline and read-only: it never logs in, uploads,
publishes, edits a store, or sends data anywhere.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    severity: str
    row: int
    field: str
    message: str


def _decimal(value: str, row: int, field: str, findings: list[Finding],
             *, allow_zero: bool) -> Decimal | None:
    try:
        number = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        findings.append(Finding("error", row, field, "Must be a valid number."))
        return None
    if not number.is_finite():
        findings.append(Finding("error", row, field, "Must be a finite number."))
        return None
    if number < 0 or (number == 0 and not allow_zero):
        qualifier = "zero or greater" if allow_zero else "greater than zero"
        findings.append(Finding("error", row, field, f"Must be {qualifier}."))
        return None
    return number


def validate_rows(rows: Iterable[dict[str, str]], *,
                  sku_field: str = "sku", title_field: str = "title",
                  price_field: str = "price", quantity_field: str = "quantity",
                  shipping_field: str = "shipping") -> list[Finding]:
    findings: list[Finding] = []
    seen_skus: dict[str, int] = {}

    for row_number, row in enumerate(rows, start=2):
        normalized = {str(k).strip().lower(): (v or "").strip()
                      for k, v in row.items()}
        fields = {
            "sku": sku_field.lower(),
            "title": title_field.lower(),
            "price": price_field.lower(),
            "quantity": quantity_field.lower(),
            "shipping": shipping_field.lower(),
        }

        for label in ("sku", "title", "price", "quantity", "shipping"):
            column = fields[label]
            if column not in normalized:
                findings.append(Finding(
                    "error", 1, column,
                    f"Required column '{column}' is missing from the CSV header."
                ))
                continue
            if not normalized[column]:
                findings.append(Finding("error", row_number, column, "Value is required."))

        sku = normalized.get(fields["sku"], "")
        if sku:
            if sku in seen_skus:
                findings.append(Finding(
                    "error", row_number, fields["sku"],
                    f"Duplicate SKU; first used on row {seen_skus[sku]}."
                ))
            else:
                seen_skus[sku] = row_number

        price = normalized.get(fields["price"], "")
        if price:
            _decimal(price, row_number, fields["price"], findings, allow_zero=False)

        quantity = normalized.get(fields["quantity"], "")
        if quantity:
            parsed_quantity = _decimal(
                quantity, row_number, fields["quantity"], findings, allow_zero=True
            )
            if parsed_quantity is not None and parsed_quantity != parsed_quantity.to_integral_value():
                findings.append(Finding(
                    "error", row_number, fields["quantity"],
                    "Quantity must be a whole number."
                ))

        shipping = normalized.get(fields["shipping"], "")
        if shipping:
            _decimal(
                shipping, row_number, fields["shipping"], findings, allow_zero=True
            )

    return findings


def validate_csv(path: Path, **column_names: str) -> list[Finding]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return [Finding("error", 1, "header", "CSV is empty or has no header row.")]
        return validate_rows(reader, **column_names)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a product-listing CSV before marketplace import."
    )
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--sku", default="sku", help="SKU column name (default: sku)")
    parser.add_argument("--title", default="title", help="Title column name (default: title)")
    parser.add_argument("--price", default="price", help="Price column name (default: price)")
    parser.add_argument("--quantity", default="quantity", help="Quantity column name (default: quantity)")
    parser.add_argument("--shipping", default="shipping", help="Shipping column name (default: shipping)")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    try:
        findings = validate_csv(
            args.csv_file,
            sku_field=args.sku,
            title_field=args.title,
            price_field=args.price,
            quantity_field=args.quantity,
            shipping_field=args.shipping,
        )
    except (OSError, UnicodeError, csv.Error) as exc:
        print(f"Could not read CSV: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "file": args.csv_file.name,
            "valid": not any(item.severity == "error" for item in findings),
            "finding_count": len(findings),
            "findings": [asdict(item) for item in findings],
        }, indent=2))
    elif not findings:
        print(f"PASS: {args.csv_file.name} has no detected listing issues.")
    else:
        for item in findings:
            print(f"{item.severity.upper()} row {item.row} [{item.field}]: {item.message}")
        errors = sum(item.severity == "error" for item in findings)
        print(f"{errors} error(s), {len(findings) - errors} warning(s).")

    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

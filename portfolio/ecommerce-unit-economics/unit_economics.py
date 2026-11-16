#!/usr/bin/env python3
"""Offline per-order ecommerce contribution calculator; no marketplace integration."""
from __future__ import annotations
import argparse
import csv
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

MONEY = Decimal("0.01")
REQUIRED = {
    "sku", "currency", "selling_price", "buyer_shipping_collected",
    "product_cost", "fulfilment_shipping_cost", "marketplace_fee_pct",
    "payment_fee_pct", "fixed_order_fees", "packaging_cost", "other_variable_costs"
}

def dec(row, key, errors, line):
    try:
        value = Decimal(str(row.get(key, "")).strip())
        if not value.is_finite() or value < 0:
            raise InvalidOperation
        return value
    except (InvalidOperation, ValueError, AttributeError):
        errors.append(f"row {line} [{key}]: must be a finite non-negative number")
        return Decimal("0")

def calculate(row, line=2):
    errors=[]
    missing=REQUIRED-set(row)
    if missing:
        return {"sku":row.get("sku",""),"errors":[f"missing required column: {k}" for k in sorted(missing)]}
    sku=str(row.get("sku","")).strip()
    currency=str(row.get("currency","")).strip().upper()
    if not sku: errors.append(f"row {line}: sku is required")
    if len(currency)!=3 or not currency.isalpha(): errors.append(f"row {line}: currency must be a three-letter code")
    price=dec(row,"selling_price",errors,line)
    buyer_ship=dec(row,"buyer_shipping_collected",errors,line)
    product=dec(row,"product_cost",errors,line)
    fulfil=dec(row,"fulfilment_shipping_cost",errors,line)
    market_pct=dec(row,"marketplace_fee_pct",errors,line)
    payment_pct=dec(row,"payment_fee_pct",errors,line)
    fixed=dec(row,"fixed_order_fees",errors,line)
    packaging=dec(row,"packaging_cost",errors,line)
    other=dec(row,"other_variable_costs",errors,line)
    if market_pct>100: errors.append(f"row {line}: marketplace_fee_pct cannot exceed 100")
    if payment_pct>100: errors.append(f"row {line}: payment_fee_pct cannot exceed 100")
    if price<=0: errors.append(f"row {line}: selling_price must be greater than zero")
    revenue=price+buyer_ship
    market_fee=(revenue*market_pct/100)
    payment_fee=(revenue*payment_pct/100)
    variable_cost=product+fulfil+market_fee+payment_fee+fixed+packaging+other
    contribution=revenue-variable_cost
    margin=(contribution/revenue*100) if revenue else Decimal("0")
    result={
      "sku":sku,"currency":currency,"gross_order_revenue":str(revenue.quantize(MONEY,rounding=ROUND_HALF_UP)),
      "marketplace_fee":str(market_fee.quantize(MONEY,rounding=ROUND_HALF_UP)),
      "payment_fee":str(payment_fee.quantize(MONEY,rounding=ROUND_HALF_UP)),
      "total_variable_cost":str(variable_cost.quantize(MONEY,rounding=ROUND_HALF_UP)),
      "contribution_before_ads_tax_and_overhead":str(contribution.quantize(MONEY,rounding=ROUND_HALF_UP)),
      "contribution_margin_pct":str(margin.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)),
      "break_even_ad_spend_per_order":str(max(Decimal("0"),contribution).quantize(MONEY,rounding=ROUND_HALF_UP)),
      "currency_basis":"all inputs must use the same currency; no FX conversion is performed",
      "excluded":"sales tax, income tax, refunds, chargebacks, returns, discounts, overhead and owner labour unless included in other_variable_costs",
      "errors":errors
    }
    result["valid"]=not errors
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description="Calculate per-order ecommerce contribution from a supplied CSV.")
    parser.add_argument("csv_file",type=Path)
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args(argv)
    try:
      with args.csv_file.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames:
          print("CSV has no header",file=sys.stderr);return 2
        missing=REQUIRED-set(reader.fieldnames)
        if missing:
          print(json.dumps({"valid":False,"errors":[f"missing required column: {x}" for x in sorted(missing)]},indent=2));return 1
        results=[calculate(row,i) for i,row in enumerate(reader,start=2)]
    except (OSError,UnicodeError,csv.Error) as exc:
      print(f"Could not read CSV: {exc}",file=sys.stderr);return 2
    valid=all(x.get("valid",False) for x in results)
    report={"file":args.csv_file.name,"valid":valid,"row_count":len(results),"results":results,"authority":"offline_estimate_only_no_marketplace_or_financial_action"}
    if args.json: print(json.dumps(report,indent=2))
    else:
      for r in results:
        print(f'{r.get("sku","?")} {r.get("currency","")}: contribution {r.get("contribution_before_ads_tax_and_overhead","N/A")} ({r.get("contribution_margin_pct","N/A")}%)')
        for e in r.get("errors",[]): print("ERROR:",e)
      print("VALID" if valid else "REVIEW REQUIRED")
    return 0 if valid else 1

if __name__=="__main__":
    raise SystemExit(main())

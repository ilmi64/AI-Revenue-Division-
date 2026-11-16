# Ecommerce Unit Economics Calculator

Offline, no-dependency Python calculator for per-order contribution economics.

## Input CSV

Required columns:
- `sku`, `currency`
- `selling_price`, `buyer_shipping_collected`
- `product_cost`, `fulfilment_shipping_cost`
- `marketplace_fee_pct`, `payment_fee_pct`, `fixed_order_fees`
- `packaging_cost`, `other_variable_costs`

All amounts must use the same currency for a row. Fee percentages apply to selling price plus shipping collected. No exchange-rate conversion is inferred.

## Run

```bash
python unit_economics.py sample-economics.csv --json
python -m unittest -v
```

## Interpretation

Contribution = selling price + shipping collected - product cost - fulfilment shipping - marketplace/payment percentage fees - fixed order fees - packaging - other variable costs.

The result is **before advertising, taxes, fixed overhead, refunds, returns, chargebacks and owner labour** unless a cost is deliberately included in other variable costs. The break-even ad spend is a mathematical ceiling, not a recommended advertising budget or proof that advertising will be profitable.

This is an estimate tool. Use actual platform fee schedules, product supplier costs, shipping destinations, currency, tax treatment and payout evidence. It does not connect to eBay, Printify or any account, and never changes prices, inventory or listings.

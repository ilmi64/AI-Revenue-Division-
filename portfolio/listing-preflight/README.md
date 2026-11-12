# Listing CSV Preflight

A small, offline Python utility that catches common product-feed mistakes before a seller imports a CSV into a marketplace.

## Checks

- Required columns and non-empty SKU, title, price, quantity and shipping values
- Duplicate SKUs
- Positive prices
- Non-negative shipping amounts and stock quantities
- Whole-number stock quantities
- UTF-8 and UTF-8-with-BOM CSV files
- Custom column names for different export formats

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python listing_preflight.py sample-listings.csv
python listing_preflight.py sample-listings.csv --json
```

If your export uses different column names:

```bash
python listing_preflight.py export.csv --sku "SKU Code" --title "Product Name" --price "Sale Price" --quantity "Stock" --shipping "Postage"
```

## Tests

```bash
python -m unittest -v
```

## Scope and safety

This is a pre-import quality check, not a marketplace integration. It does not connect to eBay, Printify, Shopify, or any seller account; it does not upload, publish, change prices, or modify inventory. It reads the supplied CSV and prints findings only. A clean result means only that these basic checks passed—not that a marketplace will accept the file.

## Example service use

A seller can provide a product CSV and the target column names. The deliverable can include a validation report, a corrected copy only when explicitly requested, and a short explanation of issues found. No account access is required for this basic audit.

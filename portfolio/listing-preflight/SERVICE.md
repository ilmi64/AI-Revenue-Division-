# Product-feed / listing CSV preflight service

## Buyer problem
Product imports can fail or create expensive listing mistakes when a feed contains blank fields, duplicate SKUs, invalid prices, negative stock, or malformed shipping values.

## Starter deliverable
- Run an offline preflight against one supplied CSV export.
- Return a concise findings report with row numbers and field names.
- Explain which issues should be corrected before import.
- Optionally provide a corrected copy only when the client explicitly asks for one and approves the proposed changes.

## Initial scope
- One CSV file, up to 1,000 product rows.
- Basic SKU, title, price, quantity and shipping checks.
- No account login, marketplace access, uploads, publishing, repricing, inventory changes, or customer-data processing.
- No guarantee that a marketplace will accept the feed; platform-specific validation requires the client's current import template and rules.

## Delivery workflow
1. Client supplies a sample/export and names the target marketplace/import format.
2. We confirm scope, fee, delivery date and file-handling expectations before work begins.
3. AI runs the local validator, reviews findings, and prepares the report.
4. A human reviews the report before delivery.
5. Any file edits are separately approved and clearly diffed.

## Portfolio demo
See [Listing CSV Preflight](README.md), including the offline validator, sample CSV and tests.

## Important
This is a proposed service package, not a claim of prior client work or marketplace certification. Do not advertise experience, client results, integrations, or qualifications that have not been independently established.

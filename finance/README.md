# Finance and Treasury controls

This directory contains a read-only, zero-spend financial control baseline.

- `financial-control-policy.json` sets the default CAD 0 approved spending ceiling and records reserved approval gates.
- `commitment-register.csv` records estimates, approvals, commitments and payments separately. It is initially empty.
- `revenue-ledger.csv` remains the income record; estimates, accepted amounts and cash received are not conflated.
- `organization/tools/build_finance_controls.py` validates commitments, cash-receipt statuses, proof references, currency handling and halal-review flags.
- `MONTH-END-CLOSE.md` defines evidence collection, payout reconciliation, commitment review, treasury reporting and exception escalation.

## Operating rules
- Estimates are not spending commitments. Approved, committed and paid amounts are tracked separately.
- Positive spend requires a non-zero owner-approved ceiling, approval reference and supporting evidence. The current ceiling is CAD 0.
- Non-CAD commitments are not converted silently; documented FX evidence is required before spend-limit validation.
- Only ledger entries marked paid, received or settled with a supporting proof reference and CAD basis count toward reported CAD cash received. This is not an independently verified bank balance.
- Financing, investment, yield and trading entries are flagged for further review where applicable. The halal fields are screening records, not religious rulings or certification; uncertain matters require qualified Shafi'i review.
- This is not connected to bank, payment, marketplace or wallet accounts. It performs no transactions.

## Tests
Run the offline tests from the repository root with `python -m unittest discover -s organization/tests -v`. No GitHub Actions run is required.

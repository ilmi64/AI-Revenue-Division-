# AI Revenue → Organisation reporting integration

## Purpose
Provide the Executive Management division with a repeatable, read-only snapshot
from AI Revenue's existing records. This is a file-based integration; it does
not connect to marketplace accounts, bank accounts, payment processors, or
external services.

## Source-of-truth files
| Source | Fields used | Executive reporting use |
|---|---|---|
| `intelligence/opportunity-tracker.csv` | `id`, `status`, `official_url`, `evidence_checked_on`, `canada_eligibility_checked` | Pipeline counts, evidence completeness, Canada eligibility checks |
| `finance/revenue-ledger.csv` | `gross_estimate`, `gross_accepted`, `fees`, `direct_costs`, `net_received_cad`, `payment_status` | Estimate, accepted-not-paid, cash-received and recorded cost totals |

## Classification rules
- Estimated amounts remain unconfirmed and are reported separately.
- Accepted amounts are not treated as cash until payment is recorded.
- Only ledger rows whose payment status is `paid`, `received`, or `settled`
  contribute to cash received.
- Cash totals are based on ledger entries, not independent bank verification.
- Opportunity tracker rows contain no amount field; the integration does not
  invent opportunity values or convert platform advertised rates into revenue.
- An empty ledger means no revenue is recorded in that file, not proof that no
  revenue exists elsewhere.
- The source CSVs remain the system of record. The snapshot is derived output.

## Run
From the repository root:

```sh
python organization/tools/build_executive_snapshot.py
python -m unittest discover -s organization/tests -v
```

The GitHub Actions pull-request workflow runs the snapshot and tests. The JSON
snapshot is printed to the workflow log for review; no files or external systems
are modified.

## Controls and next integration step
- No automatic opportunity applications, client outreach, bounty claims, or
  payment actions.
- No financial account access or independent confirmation of receipts.
- Owner approval remains required for external commitments and paid activity.
- The next extension is a consolidated cross-division dependency/readiness
  report, with evidence and blockers linked to the same executive reporting view.

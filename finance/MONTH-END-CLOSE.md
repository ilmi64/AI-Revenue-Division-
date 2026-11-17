# Finance and Treasury monthly close procedure

**Scope:** internal planning and control records only. This procedure does not connect to banks, create accounting entries in an external system, move funds, file taxes or authorize expenditure.

## 1. Period freeze and source collection

1. Set the reporting period and record its timezone and close timestamp.
2. Collect statements, platform payout records, invoices, receipts and approved commitment evidence from authorized sources.
3. Preserve original source references and access dates. Never copy passwords, API secrets, full payment-card data, private keys or wallet seeds into the register.
4. Separate estimates, accepted/earned amounts, invoices due, paid commitments and cash actually received.

## 2. Revenue reconciliation

For every revenue-ledger row:
- Verify the opportunity/client/platform, work description, earning date, currency and payment status.
- For `paid`, `received` or `settled` status, require a receipt/payout evidence reference before counting the amount as cash received.
- Record the net CAD amount only where a documented CAD conversion and its source/date are available. Non-CAD receipts are excluded from CAD totals until converted with evidence.
- Keep pending, disputed, reversed and unpaid amounts outside cash received.
- Do not treat token mark-to-market value, platform estimates or unpaid balances as cash.

## 3. Commitments and spend controls

- Reconcile estimates, approved amounts, committed amounts and paid amounts separately.
- Every positive commitment requires a recorded owner approval and reference; every paid amount requires proof.
- Compare aggregate approved and committed CAD amounts with the approved spend ceiling.
- The current approved spend ceiling is CAD 0. Any positive spend remains blocked until the owner explicitly changes the policy and the commitment has a recorded approval.
- Do not initiate a subscription, paid API, trial with billing risk, advertising, inventory purchase, financing, wallet action or trade as part of this close.

## 4. Treasury and liquidity view

Report separately:
- evidence-backed cash received during the period;
- cash balance only where a current account statement has been independently reviewed by an authorized human;
- outstanding receivables and their due dates;
- approved but unpaid commitments;
- taxes and statutory liabilities as estimates pending qualified Canadian advice;
- restricted, disputed or unavailable balances.

The repository ledger does not establish a bank balance. Never infer liquidity from an empty register or from an unverified platform dashboard.

## 5. Halal screening and review

Flag financing, interest, yield, leverage, margin, derivatives and trading structures for review. Record the source and reviewer notes when an advisory review is documented. These fields are screening controls, not a religious ruling or certification. Escalate uncertain matters for qualified Shafi'i review; do not automate a fatwa.

## 6. Close report and sign-off

Record:
- reporting period, preparer and reviewer;
- opening balance only if independently evidenced;
- cash receipts supported by evidence;
- fees, direct costs, refunds, chargebacks and currency conversion costs;
- closing balance only if reconciled to an authorized statement;
- open receivables, commitments, disputes and exceptions;
- control validation results and unresolved issues.

A close is marked **draft** until an accountable reviewer verifies the source evidence. Do not describe a ledger-only summary as audited, bank-reconciled or tax-filed.

## 7. Exception escalation

Any missing receipt evidence, unexplained currency conversion, duplicate transaction, unapproved commitment, inconsistent payment status or suspected account compromise is logged as an exception. Preserve evidence, stop affected processing and escalate to the owner. No external dispute, chargeback, legal filing, account change or transfer is initiated without explicit approval.

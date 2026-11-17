# Capital Flow Evidence Review Ledger

Offline, append-only review history for normalized Capital Flow Intelligence events.

## Why it exists

Normalized observations should not be silently edited when reviewers disagree, discover stronger evidence or correct an earlier interpretation. This ledger records a separate sequence of review decisions keyed to the stable `event_id`. The original event and evidence remain separate.

## Controls

- Append-only JSONL history; each entry hashes its canonical JSON payload and links to the previous entry.
- Verification detects changed entries, missing/reordered sequence numbers and broken previous-hash links.
- Review actions are constrained to `review`, `corroborate`, `challenge`, `correct`, `reject`, `expire`, and `reopen`.
- Rejection and expiry require matching terminal statuses. Reopening requires a nonterminal status.
- Reviewer ID, reason and timezone-aware timestamp are required.
- Evidence references are retained with each decision.
- The hash chain is an integrity aid, **not** a digital signature, identity proof, tamper-proof storage or legal non-repudiation.
- Single-writer operation is required. There is no cross-process/distributed locking, authentication, access control, encryption or protected backup in this local prototype.
- Review records never authorize trades, wallet actions, provider access or external publication.

## Commands

From this directory:

```sh
python capital_flow_review.py verify review-history.jsonl
python capital_flow_review.py append review-history.jsonl \
  --event-id cfi_example --action review --reviewer-id analyst-01 \
  --reason "Primary source checked; wallet attribution remains unverified." \
  --status research --evidence-ref "local://evidence/record-001"
```

The append command validates the entire existing ledger before extending it. Do not manually edit or reorder a ledger. Keep the JSONL file and source evidence in controlled local storage with independent backups before any operational adoption.

## Tests

`test_capital_flow_review.py` covers chain construction, sequence linkage, tampering, broken links, action/status constraints, timezone enforcement and append/read integrity. Tests are supplied but have not been run in the hosted repository environment.

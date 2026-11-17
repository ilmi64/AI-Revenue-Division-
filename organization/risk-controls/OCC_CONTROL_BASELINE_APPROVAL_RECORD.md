# OCC Control Baseline — Approval and Evidence Record

**Current state:** draft_control_baseline. **Authority:** not granted. **Permitted publisher behavior:** conservative HALT only. This record is a preparation template; no approval is implied by its existence or completion of software tests.

## A. Required authority decision

The baseline must remain HALT-only until each item below has an identified owner, written evidence and a separately recorded approval.

- [ ] Named accountable owner for the organisation-wide risk policy.
- [ ] Named independent risk reviewer who is not the author of the control implementation.
- [ ] Named security reviewer for signing, secret provisioning, storage and recovery.
- [ ] Named operational owner for monitoring, incident response and day/night handover.
- [ ] Explicitly defined scope: paper-only, instruments/families, jurisdictions and data sources.
- [ ] Explicitly defined risk limits for Crypto, Forex, equity indices, Gold/XAU and prediction markets, with Gold as its own independent family.
- [ ] Portfolio-level aggregate and correlated-exposure limits, plus concentration and counterparty/venue limits.
- [ ] Position/order state reconciliation and deterministic existing-position protection procedures.
- [ ] Documented stop-condition semantics, evidence requirements, operator-clearance authority and audit trail.
- [ ] Source licensing, data rights, privacy and jurisdictional review.
- [ ] Recovery, business-continuity, backup/restore and incident-escalation sign-off.
- [ ] Separate decision on whether a future CLEAR-authority path is permitted. No code or operator may infer this authority from a test passing.

## B. Minimum policy evidence

| Evidence | Required record |
|---|---|
| Policy identity | Version, exact file path, SHA-256, author and approval date |
| Authority | Explicit status and scope; current draft state remains not-authorized |
| Market-family limits | Five separate family limits plus portfolio aggregate limits |
| Instrument controls | Contract/pair identity, units, multiplier, expiry/roll, settlement and financing where applicable |
| Data governance | Provider, licence/terms, timestamp, freshness, fallback and provenance |
| Stop conditions | Stable condition ID, threshold/logic owner, evidence reference and severity |
| Operator clearance | Authorized role, reason, supporting evidence, time and immutable audit reference |
| Change control | Reviewer, change summary, previous/new digest and rollback plan |

## C. Approval record (complete only through the organisation's formal process)

- Policy version:
- Policy SHA-256:
- Portfolio/risk configuration version:
- Accountable owner:
- Independent risk reviewer:
- Security reviewer:
- Operations reviewer:
- Jurisdiction/data-rights reviewer:
- Decision: NOT APPROVED / APPROVED FOR PAPER OBSERVATION ONLY / OTHER EXPLICIT SCOPE
- Scope and exclusions:
- Evidence location:
- Decision timestamp:
- Next review date:
- Outstanding conditions:

## D. Release gates

1. Passing unit tests proves only that the tested software behavior matched assertions; it does not approve the risk policy.
2. Successful HMAC interoperability proves only that the two implementations agree on message authentication; it does not prove sender identity or secure key custody.
3. A fresh authenticated CLEAR message is not an operator clearance and cannot remove an active veto.
4. READY_FOR_REVIEW is a data-readiness status only.
5. No production CLEAR publisher, live credentials, broker/wallet connection, order route, deployment or capital allocation may be enabled by this document.
6. Any future authority change requires a separate explicit owner decision, independent review and controlled implementation plan.

## E. Current engineering evidence status

- Signed snapshot schema and conservative publisher: implemented on the draft OCC branch; not run end-to-end.
- Draft-baseline publisher: HALT-only; tests authored, not executed.
- PolyBot authenticated receiver: source-level integration present on a separate draft PR; not commissioned.
- Shared cross-repository fixture: present; interoperability test authored, not executed.
- Gold/XAU: distinct market family in PolyBot source; no approved live Gold feed or operational risk limit is established by code alone.
- Full repository tests, fault-injection, restore drills and independent review: pending.

# Research & Intelligence — Grok Desk Event Verification & Challenge Record

**Status:** Reusable desk template; no active monitoring, source ingestion or publication.
**Owner:** Research & Intelligence Division. **Authority:** Advisory only.
**Recipients:** One recipient per publication draft; never combine company-private context.

## 1. Event intake
| Field | Entry |
|---|---|
| Event ID / version | UNASSIGNED |
| Desk / shift | UNASSIGNED |
| Recipient | AI_REVENUE / TRADING_TECH / SHARED_PUBLIC_TECH_INTEL |
| Priority | P2 default; P0/P1 only under policy |
| Event title / neutral claim | REQUIRED |
| First observed at | NOT RECORDED |
| Source publication time | UNKNOWN |
| Research as-of time | REQUIRED |
| Expiry / recheck time | REQUIRED |
| Intake status | CANDIDATE |

## 2. Source identity and provenance
For every source, record canonical source ID, publisher/operator, exact URL, source class, product/metric if relevant, primary/secondary status, publication and retrieval timestamps, revision or content digest where available, terms/licence, freshness expectation and known limitations.

Do not treat a search result, model summary or social repost as the primary source when the original record can be located.

## 3. Claim decomposition
Split a broad narrative into atomic claims. For each claim, record exact proposition; evidence supporting and contradicting it; evidence grade (PRIMARY_CONFIRMED, CORROBORATED, SINGLE_SOURCE, VENDOR_ESTIMATE, PUBLIC_CLAIM, ATTRIBUTED, HYPOTHESIS, CONTRADICTED or SUPERSEDED); confidence rationale and missing evidence; and whether the source establishes announcement, intention, execution or outcome.

Never infer wallet ownership from labels alone, fundraising from a promotional post, treasury movement from an unattributed transfer, or causation from correlation.

## 4. Independent challenge checklist
The challenger must be distinct from the initial drafter where practical and answer:
- Is entity, contract, token, venue or product identity exact?
- Is timestamp current and in the correct timezone?
- Does the source prove the precise claim or only a weaker related statement?
- Is the record an announcement, proposal, transaction, completed action or retrospective claim?
- Is there a primary source or native transaction record?
- Are there contradictory records, corrections, deleted posts or later reversals?
- Could the observation be routine operations, internal transfers, market making, custody movement or an alternative explanation?
- Is attribution confidence separate from transaction confidence?
- Are metrics independently defined, or opaque vendor estimates?
- Are terms, privacy, redistribution and commercial-use rights clear?
- What would falsify the draft?
- What decision does the recipient actually need to make?

## 5. Disposition
Use one of: ACCEPT_FOR_SCOPED_DRAFT; NEEDS_CORROBORATION; HOLD_IDENTITY; HOLD_TERMS; HOLD_FRESHNESS; QUARANTINE_CONTRADICTION; REJECT_UNSUPPORTED; EXPIRED.

No source score overrides these hard stops.

## 6. Recipient-scoped publication review
Before any future publication, confirm one recipient, purpose, permitted downstream use, evidence references, counter-evidence, as-of time, expiry, redactions, reviewer and version. Create separate reviewed publications for AI Revenue and Trading even when the underlying public fact is the same. OCC receives only allowlisted aggregate status and evidence references, not unrestricted report contents.

## 7. Handover and coverage
Record outgoing/incoming desk owner, shift window/timezone, accepted tasks, blocked tasks, source exceptions, incidents, unresolved contradictions, next review, missed coverage and acknowledgement. If no shift was actually staffed or monitored, mark UNCOVERED; never backfill a fictional scan.

## 8. Current boundary
No automated monitoring, Grok API, account connection, private-group access, source ingestion, customer contact, public publication, trade, purchase, policy change or spending is authorized. Grok Desk and HyperGrok remain planned roles until runtime, staffing, source rights, identity, review and recovery gates are demonstrated.

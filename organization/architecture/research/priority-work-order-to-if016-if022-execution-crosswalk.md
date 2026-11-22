# Priority R&I Work-Order to IF-016–IF-022 Execution Crosswalk

**Status:** INTERFACE MAPPING PROPOSAL / NOT ACTIVATED / NO SOURCE COLLECTION OR PUBLICATION AUTHORIZED.  
**Date:** 2026-11-21. **Budget:** CAD $0 incremental.  
**Recipients:** AI_REVENUE, TRADING_TECHNOLOGY and SHARED_GOVERNANCE remain separate tenant scopes.

## 1. Purpose

Map the five prepared priority work orders to the canonical research interfaces IF-016–IF-022 so future activation is controlled, auditable and recipient-specific. This document does not assign staff, approve sources, connect accounts, initiate monitoring or authorize publication.

## 2. Work-order mapping

| Work order | Tenant / recipient | Work-order scope and output | Source constraints | Independent challenge |
|---|---|---|---|---|
| RI-2026-11-21-AR-DEMAND-01 | AI_REVENUE | No-upfront buyer/problem and Canadian payment-route opportunity ledger | Public official terms, public demand evidence, dated marketplace records; no account/apply/outreach | R&I Evidence & Reproducibility |
| RI-2026-11-21-AR-DELIVERY-02 | AI_REVENUE | Mini-Review promise/evidence/QA/time/economics consistency map | Internal approved docs and synthetic artifacts only; rehearsal remains owner-gated | Independent QA reviewer not author |
| RI-2026-11-21-TT-SOURCE-03 | TRADING_TECHNOLOGY | Per-market instrument/provider/terms/calendar/freshness qualification matrix | Public official source documentation; no API keys, live feed, sign-up or paid access | Independent Market Data/Quant challenger and CRO as needed |
| RI-2026-11-21-TT-CAPFLOW-04 | TRADING_TECHNOLOGY | Capital-flow event taxonomy and source/attribution qualification | Public official project/fund/chain records and independently corroborated reporting; no wallet access or private attribution | R&I Evidence & Reproducibility plus Market Data/Security |
| RI-2026-11-21-SG-COVERAGE-05 | SHARED_GOVERNANCE | Day/night R&I staffing, persistence, handover and operational-readiness evidence matrix | Existing internal architecture only; no host trial, install, model/API connection or live monitoring | Security & Recovery and read-only OCC reviewer |

A work order may not change its recipient or be copied to another tenant without a new work order and data-classification/sanitisation review.

## 3. IF-016 — Research Work Order

Required validated record:
- immutable work_order_id and schema_version;
- tenant_id, recipient_id and recipient classification;
- bounded question, included scope and exclusions;
- accountable desk/owner and independent challenger role;
- priority, deadline, expiry and output type;
- source class allowlist and approved source IDs (empty until source approval);
- budget ceiling and currency (CAD $0 default);
- work-order state and append-only transition history;
- authorization reference and audit correlation ID.

Reject missing recipient, unbounded question, unknown schema/state, absent owner/challenger, unapproved source, expired deadline, budget above approved ceiling or any attempt to widen scope. Prepared work-order text is not activation authority.

## 4. IF-017 — Source Record and stewardship lifecycle

Proposed source states: CANDIDATE, TERMS_REVIEW, APPROVED_LIMITED, ACTIVE_LIMITED, DEGRADED, SUSPENDED, EXPIRED, REJECTED.

Required fields:
- source_id, owner/publisher, exact domain/endpoint/document, source class;
- tenant and recipient scope;
- access method and authentication class (PUBLIC_NO_AUTH only unless separately approved);
- terms/licence version, permitted purposes, attribution, retention, redistribution and automation restrictions;
- jurisdiction/eligibility where relevant;
- last_reviewed_at, next_review_due, publication/update timestamp, known freshness;
- lineage/dependencies, known upstream sources, limitations and failure modes;
- steward identity, reviewer, approval reference and audit ID.

Candidate discovery is not approval. Approval is narrow to the documented use, tenant, purpose and access method. A terms change, 403/429, access restriction, suspected source compromise, stale review or upstream change moves the source to DEGRADED/SUSPENDED until re-reviewed. No automated retry or access circumvention.

## 5. IF-018 — Evidence Capture

Each capture must be reproducible and immutable:
- capture_id, source_id and exact source revision;
- exact URL/reference or internal file path/blob SHA;
- original publication/effective time and retrieval/capture time, separately;
- capture method and collector identity;
- content digest and retained permitted excerpt/metadata;
- context, scope, limitations, source terms and recipient classification;
- prior/superseding capture links and audit ID.

Do not store prohibited full content or personal data. A URL alone is not evidence of what was observed. If the source cannot lawfully be retained, store only the permitted citation/metadata and mark the limitation.

## 6. IF-019 — Atomic Claim Record

Every report conclusion is decomposed into atomic claims:
- claim_id, exact wording, subject, scope, tenant/recipient;
- claim type: OBSERVED, REPORTED, CALCULATED, INFERRED, HYPOTHESIS, FORECAST or OPINION;
- evidence_capture_ids and calculation/input references;
- confidence rationale, date/as-of, freshness expiry;
- contrary evidence, alternative explanations and unresolved assumptions;
- author, version and state: DRAFT, SUPPORTED, DISPUTED, UNVERIFIED, EXPIRED, SUPERSEDED.

A claim without sufficient evidence remains UNVERIFIED. Multiple sources with the same upstream lineage are not independent corroboration. No silent edits: changed wording or evidence creates a new claim revision.

## 7. IF-020 — Independent Challenge

The challenger must be separate from the primary author and must declare conflicts/independence. Record:
- challenge_id, reviewer identity/role, independence declaration;
- exact claim IDs and publication revision reviewed;
- method, assumptions independently recalculated, source lineage check;
- counter-evidence and alternative explanations;
- disposition: CONFIRM_WITH_LIMITS, AMEND, DISPUTE, REJECT, INSUFFICIENT_EVIDENCE;
- unresolved issues, severity, required correction and timestamp.

Model plurality is not independent challenge where models share the same upstream source, author or calculation. No challenge => no publication approval for material claims.

## 8. IF-021 — Recipient-scoped Research Publication

A publication must bind:
- publication_id, tenant_id and exact recipient;
- report revision/digest and work_order_id;
- included claim IDs, evidence refs and challenge refs;
- sanitisation status and data classification;
- as-of time, issue time, expiry/review date and correction/supersession link;
- publisher identity and owner approval where policy requires.

Reject wrong recipient, cross-tenant data, stale/expired material claims, missing challenge, unresolved critical issue or failed sanitisation. Public facts may be reused only after recipient scope and data-rights review. OCC receives only minimal read-only status metadata, never full confidential reports or approval authority.

## 9. IF-022 — Distribution Receipt

Record:
- receipt_id, publication_id, recipient identity and tenant;
- exact version/digest, delivery channel, delivery time;
- state: QUEUED, SENT, ACKNOWLEDGED, FAILED, EXPIRED, QUARANTINED;
- receiver response/reference, retry attempt and idempotency key;
- acknowledgement identity/time and audit ID.

A SENT message is not proof of delivery or acknowledgement. Missing acknowledgement remains UNACKNOWLEDGED and must not be reported as delivered. Retries are bounded, idempotent and audited; ambiguous outcomes are reconciled, not blindly resent.

## 10. End-to-end lifecycle and state gates

1. Intake creates a PREPARED work order.
2. R&I Operations validates IF-016 and assigns accountable owner/challenger.
3. Source steward qualifies IF-017; no source remains active outside its approved purpose/recipient.
4. Researcher captures IF-018 evidence and writes IF-019 atomic claims.
5. Independent challenger completes IF-020.
6. Recipient-specific publisher checks IF-021 scope, freshness, evidence, challenge and sanitisation.
7. Approved publisher sends; IF-022 records actual receipt and acknowledgement.
8. Corrections, source expiry and claim disputes create superseding records; never erase history.
9. OCC receives read-only status only.

Proposed work-order states: PREPARED, INTAKE_REVIEW, APPROVED_FOR_RESEARCH, IN_PROGRESS, CHALLENGE_PENDING, CORRECTION_REQUIRED, APPROVED_FOR_PUBLICATION, PUBLISHED_UNACKNOWLEDGED, ACKNOWLEDGED, BLOCKED, CANCELLED, EXPIRED. State changes require actor, timestamp, reason and evidence; unknown transitions reject.

## 11. Minimum safe-mode triggers

- source terms/access status unknown or changed;
- source expired, stale or upstream lineage changed;
- recipient or tenant mismatch;
- missing evidence digest or irreproducible capture;
- claim contradicted, materially stale or unsupported;
- reviewer not independent or critical challenge unresolved;
- publication sanitisation failed;
- receiver acknowledgement missing or ambiguous;
- audit/persistence unavailable;
- budget, scope, expiry or approval exceeded.

Affected work is BLOCKED or QUARANTINED; other independent work orders may continue.

## 12. Current state

| Capability | State |
|---|---|
| Five priority work orders | PREPARED / NOT ASSIGNED |
| IF-016 schema/lifecycle | MAPPED / NOT IMPLEMENTED |
| IF-017 source qualification | DESIGN / NO NEW SOURCE APPROVAL |
| IF-018 evidence capture | CONTRACT MAPPED / NO CAPTURE CREATED |
| IF-019 claim registry | CONTRACT MAPPED / NO CLAIMS CREATED BY THIS PACKET |
| IF-020 independent challenge | REQUIREMENTS MAPPED / NO REVIEW ASSIGNED |
| IF-021 publication | DESIGN / NO PUBLICATION |
| IF-022 receipt | DESIGN / NO DISTRIBUTION |
| Day/night coverage | DESIGN ONLY / NOT STAFFED OR OPERATIONAL |
| Tests and live collection | NOT AUTHORIZED / NOT RUN |

**Disposition:** IF-016–IF-022 crosswalk prepared to make the R&I queue activation-ready for later review. No work order is activated and no research collection/publication is claimed.

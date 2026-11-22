# AI Revenue — Delivery QA, Acceptance & Time-Capture Standard

**Status:** Internal operating specification; not rehearsed or validated.  
**Scope:** AI Revenue Company only.  
**Budget:** CAD $0 incremental. No paid tools, APIs, hosting, credits or trials.  
**Authority:** No customer contact, customer-data access, proposal, contract, publishing, invoice or production delivery is authorized.

## 1. Purpose

Make each bounded service delivery measurable, reproducible, reviewable and commercially honest. This standard applies to the Practical Operations Improvement Audit / Mini-Review and may later be adapted to other offers only after a scoped review.

Separate hands-on labour from elapsed time; draft completion from independent QA and customer acceptance; observed customer baseline from estimates and hypotheses; defect correction from scope expansion; synthetic rehearsal evidence from actual customer evidence.

## 2. Work-item lifecycle

Use these states in order and record timestamp and responsible role for every transition:

1. INTAKE_DRAFT
2. SCOPE_REVIEW
3. OWNER_AUTHORIZATION_REQUIRED
4. AUTHORIZED_NOT_STARTED
5. INPUTS_PENDING
6. IN_PROGRESS
7. DRAFT_COMPLETE
8. INDEPENDENT_QA
9. CORRECTION_REQUIRED
10. QA_PASSED
11. RELEASE_AUTHORIZED
12. DELIVERED_PENDING_ACCEPTANCE
13. ACCEPTED / ACCEPTED_WITH_NOTES / REJECTED
14. CLOSED

Paused, blocked, cancelled or expired work records its state and reason; it is never silently treated as complete.

## 3. Time and effort capture

| Field | Meaning |
|---|---|
| Work ID / scenario ID | Unique engagement or synthetic exercise |
| Work stage | Intake, evidence review, mapping, analysis, drafting, QA, correction, admin, handover |
| Start / stop | Timestamp with timezone |
| Active minutes | Actual hands-on time; exclude idle/waiting |
| Elapsed minutes | Wall-clock interval; do not add overlapping parallel tasks |
| Role / contributor | Human or agent role identifier; no invented identity |
| Tool / model | Exact tool/model and version if known; UNKNOWN otherwise |
| Input class | Public, synthetic, customer-provided, internal |
| Cost exposure | CAD amount or ZERO_CONFIRMED / UNKNOWN; never assume free |
| Output / evidence ref | Artifact or evidence record |
| Interruption / wait reason | Client dependency, review queue, technical block, etc. |

Rules:
- Sum active minutes by contributor and stage; do not count the same minute twice for one contributor.
- Report elapsed turnaround separately from labour.
- Include setup, coordination, QA, correction, support and closeout—not just drafting.
- If time was not captured contemporaneously, mark it ESTIMATED_RETROSPECTIVELY and explain the method.
- A synthetic rehearsal can test the capture method but cannot establish actual production time or productivity.

## 4. Defect and rework register

Every defect gets an ID, affected section, detection stage, severity, evidence, root-cause category, owner, correction, review result and closure timestamp.

Severity:
- CRITICAL: privacy/security exposure, wrong recipient, fabricated evidence, materially unsafe or prohibited advice, unauthorized action, or a claim that could cause serious harm. Stop release; escalate.
- MAJOR: materially wrong calculation, unsupported recommendation, wrong scope, missing critical limitation, material source error. Return for correction; full affected-section re-review.
- MINOR: non-material clarity, formatting, citation or consistency issue. Correct before release unless reviewer documents why not.
- OBSERVATION: improvement opportunity, not a defect; do not inflate defect counts.

Track defect count by severity, first-pass QA pass/fail, correction cycles, active rework minutes, recurring root causes and escaped defects. Do not hide a defect by editing without recording it. Do not count a scope change as defect correction.

## 5. Deliverable acceptance rubric

Score each criterion PASS, FAIL, NOT_APPLICABLE or BLOCKED; attach evidence for every PASS. No weighted average may override a critical failure.

| Criterion | Required evidence |
|---|---|
| Scope conformity | All promised sections present; exclusions respected |
| Source traceability | Material factual claims have source, date/as-of time and evidence grade |
| Calculation integrity | Inputs, units, formulas, assumptions and rounding visible; independently recomputed where material |
| Baseline integrity | Customer-observed facts separated from estimates, benchmarks and hypotheses |
| Recommendation quality | Each recommendation links to problem, expected effect, effort, risk and dependency |
| Privacy/data minimization | No unnecessary personal, financial, health or credential data; redactions checked |
| Security and rights | No unauthorized access, copied protected material or unreviewed third-party dependency |
| Halal / regulated issue flags | Relevant financial or regulated mechanisms flagged for qualified review; no unsupported ruling |
| Limitations and uncertainty | Unknowns, alternative explanations and confidence are explicit |
| Readability and actionability | Intended reader can understand the finding and next step |
| Recipient and version control | Correct audience, version, date and release status |
| Commercial honesty | No unsupported savings, revenue, accuracy, time or guarantee claims |

Any FAIL in source traceability, calculation integrity, privacy/security, scope, recipient/version or commercial honesty blocks release.

## 6. Customer acceptance

Before an engagement, define objective acceptance criteria and revision limits in the approved scope. On delivery, record delivery timestamp and approved channel; ask the customer to identify acceptance, rejection or specific defects; distinguish silence from acceptance unless an approved contract expressly defines otherwise and legal review supports it; classify feedback as defect, clarification, preference or scope change; retain only necessary acceptance evidence under an approved retention policy.

No customer engagement or message is authorized by this template.

## 7. Full-cycle economics

Calculate only from captured evidence:
- Active labour hours = sum(active minutes) / 60.
- Elapsed turnaround = delivered_at minus authorized_start_at.
- Rework share = rework active minutes / total active minutes.
- First-pass yield = QA pass without correction / QA reviews.
- Realized revenue = cleared and reconciled customer payment.
- Direct cost = verified inference + software + payment + delivery + contractor + other attributable costs.
- Contribution before overhead = realized revenue - direct cost - valued delivery labour.

If labour has no approved internal valuation, show hours separately and mark contribution incomplete. Do not treat unpaid labour as zero economic cost. Do not count proposals, pipeline, unpaid invoices, promised payments, hypothetical savings or synthetic scenarios as revenue.

## 8. Synthetic rehearsal protocol

For a future separately authorized internal rehearsal, use only the fictional Scenario 1 or Scenario 2 inputs already documented; label every output SYNTHETIC — NOT CUSTOMER EVIDENCE; capture actual hands-on time only if the owner separately authorizes the rehearsal; do not call output customer-ready; do not infer a production time standard from one rehearsal; do not run code, tests, APIs or paid tools under this document.

Current state: both scenario packs are inputs only; no rehearsal, time capture, scoring or QA run is claimed.

## 9. Release hard stops

Block release for unapproved recipient/channel/scope/customer-data access; missing or contradictory material evidence; unverified calculation or unit; unresolved critical/major defect; unclear rights or third-party terms; unnecessary sensitive data or credentials; unapproved paid dependency or deployment; legal/privacy/security/halal questions presented as settled without qualified review; or customer outcome/revenue/savings claims beyond available evidence.

## 10. Governance and review

Delivery owner prepares; independent QA reviewer challenges; accountable AI Revenue lead decides internal readiness; owner approval remains required for external commitments and release where applicable. The producer cannot self-approve a material deliverable.

Review after a real approved pilot, material incident, repeated defect pattern or service-scope change. Preserve prior revisions and link each engagement to the standard version used.

**Disposition:** STANDARD PREPARED; NOT REHEARSED; NOT VALIDATED; NO CUSTOMER WORK OR RELEASE AUTHORIZED.

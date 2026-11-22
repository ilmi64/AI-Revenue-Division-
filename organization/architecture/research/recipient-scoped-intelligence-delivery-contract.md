# Research & Intelligence — Recipient-Scoped Intelligence Delivery Contract

**Status:** Publication and routing design; no live publisher or company adapter deployed.
**Producer:** Organization-level Research & Intelligence Division.
**Recipients:** AI Revenue Company and Trading & Technology Company, independently.

## 1. Purpose

Deliver useful, evidence-backed intelligence without merging company data, authority, memory or decision-making. A report is advisory evidence, never an instruction or permission.

## 2. Product types

- Flash alert: time-sensitive, narrowly scoped, with confidence and expiry.
- Research brief: defined question, methods, sources, caveats and counter-evidence.
- Opportunity dossier: mechanism, evidence, upside hypotheses, costs, feasibility, risks and validation plan.
- Technology/capability dossier: function, architecture, licence, dependencies, security, cost, reproduction status and fallback.
- Source-health notice: outage, freshness, methodology, terms or provenance change.
- Scheduled intelligence digest: curated developments with as-of time and coverage gaps.
- Research handover: tasks, incidents, source changes and ownership transfer.

## 3. Required publication envelope

Every publication includes publication ID/version/digest and supersession reference; producer identity and accountable author; exactly one recipient scope (ORGANIZATION, AI_REVENUE or TRADING_TECHNOLOGY); classification and audience; topic, question and decision relevance; published-at, as-of, expiry/next-review and source freshness; evidence/source references and claim evidence grades; method, assumptions, uncertainty, counter-evidence and alternatives; source-quality disposition and licence constraints; advisory recommendation; reviewer and review timestamp; publication state; prohibited downstream uses and escalation contact.

If a report serves both companies, create two separately reviewed publications with recipient-specific summaries and redactions. Never publish one shared report containing both companies' private context.

## 4. Recipient boundaries

Trading may receive market/venue/chain intelligence, crypto capital flows, Forex, indices, Gold, strategy/bot capability research, data provenance, technology and risk intelligence. Identify exact instrument/product form and relevant jurisdiction/halal issue flags. Nothing authorizes backtesting, paper signals, live execution, wallet operations, broker/exchange orders or risk-limit changes.

AI Revenue may receive customer problems, market demand, competitor offers, pricing evidence, product/service opportunities, AI tooling, creative technology and workflow research. Nothing authorizes outreach, pricing commitments, contracts, publishing, purchases or customer-data ingestion.

Organization-level delivery is limited to governance, shared public-source technology intelligence and portfolio summaries. No raw company-private records.

## 5. Publication state machine

DRAFT → EVIDENCE_REVIEW → INDEPENDENT_CHALLENGE → RECIPIENT_SCOPE_REVIEW → APPROVED_FOR_PUBLICATION → PUBLISHED → EXPIRED or SUPERSEDED.

Alternative states: REJECTED, WITHDRAWN, QUARANTINED. Author cannot approve own high-impact report. Evidence, freshness, identity, licence or recipient-scope failure blocks publication.

## 6. Urgent alerts

Alerts state severity, observed time, source, confidence, verified facts vs interpretation, likely impact, alternatives, expiry and required recipient owner. P0 security/data-integrity alerts use security escalation. P1 market/commercial events require minimum evidence checks. Deduplicate repeated alerts and link to canonical event record.

## 7. OCC summary interface

OCC receives only allowlisted aggregate metadata: publication counts by recipient/status, source freshness bands, queue health, coverage, incident severity and approved evidence references. No raw report body, private task details, customer identifiers, trading strategy or source-vault content by default.

## 8. Delivery failure and recovery

If recipient identity, signature, audience, freshness, schema, digest, replay/order or publication status cannot be verified, quarantine delivery. Preserve last verified publication with STALE label. Recipient acknowledgement is separate from publication success. Retries must be idempotent and preserve publication ID/version/digest.

## 9. Feedback loop

Recipient may ACCEPT_FOR_CONSIDERATION, REQUEST_CLARIFICATION, REJECT or MARK_SUPERSEDED. Feedback is not authorization to act. Recipient retains company decision and audit trail.

## 10. Current status

Contract prepared only. No authenticated publisher, live adapter, automated routing, company acknowledgement or production delivery is established.

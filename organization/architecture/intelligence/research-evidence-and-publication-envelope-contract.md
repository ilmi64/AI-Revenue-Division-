# Research Evidence and Publication Envelope Contract

**Date:** 2026-11-21
**Status:** Conceptual data contract — not implemented, validated, tested or connected to a runtime.
**Applies to:** Shared Research & Intelligence service and its recipient-scoped publications to AI Revenue and Trading & Technology.

## 1. Purpose

Define a consistent, auditable chain from a research request through sources, atomic claims, evidence, independent challenge and recipient-specific publication. This contract complements the Research & Intelligence Operating System and Operating Model/Coverage Contract.

The contract is model-agnostic. Paperclip may own task lifecycle; Ruflo may coordinate bounded work; neither is the authority for evidence integrity, company identity or recipient permissions. Those fields must be validated by deterministic policy services.

## 2. Core record types

| Record | Purpose | Immutable/versioning rule |
|---|---|---|
| ResearchWorkOrder | Defines question, decision use, recipient, scope, priority and acceptance criteria | New version for material scope change; preserve prior request |
| SourceRecord | Identifies a source, owner, permitted use, quality and freshness | Version each metadata or status change; never rewrite past retrieval facts |
| EvidenceCapture | Records the exact source content/locator or dataset snapshot used | Immutable capture reference; content digest where lawful and technically possible |
| ClaimRecord | Atomic factual/inferential/hypothesis/forecast statement | Version on change; each version has evidence and challenge status |
| ChallengeRecord | Independent counter-evidence, source-dependence and falsification review | Append-only disposition history |
| ResearchPublication | Recipient-specific report assembled from approved claims | Immutable version; corrections create a new version and supersession link |
| DistributionReceipt | Records permitted delivery, recipient and acknowledgement | Append-only event; do not infer acknowledgement from delivery success |

## 3. Identity and common envelope fields

Every record must carry or inherit:

- schema_name and schema_version;
- record_id and record_version;
- created_at and updated_at in UTC ISO 8601;
- organization_service_id = research_intelligence;
- company_id = AI_REVENUE, TRADING_TECH or SHARED_GOVERNANCE;
- recipient_scope = exactly one recipient for a company publication;
- classification and permitted_data_classes;
- parent_research_id and parent_task_id;
- owner_role_id, reviewer_role_id where applicable;
- approval_state and policy_revision;
- source/evidence references;
- audit_correlation_id, content_digest and supersedes_id where applicable.

These names are conceptual canonical fields, not asserted native Paperclip, Ruflo, database or OCC schema names. Implementations must preserve their semantics and prove enforcement before use.

## 4. Research work order minimum contract

Required fields: research_id; title; requester identity/role; one primary recipient; decision/use case; question; scope; exclusions; topic taxonomy; P0–P3 priority and rationale; urgency; due date; freshness window; allowed/prohibited source classes; privacy/data classification; legal/licensing constraints; conflict flags; proposed desk; independent challenger; expected deliverable; acceptance criteria; dependencies; resource/cost ceiling; status; cancellation/expiry; closure disposition.

Statuses: NEW, TRIAGED, QUEUED, IN_PROGRESS, CHALLENGE_REVIEW, READY_TO_PUBLISH, PUBLISHED, BLOCKED, SUPERSEDED, CLOSED. Invalid transitions are rejected. PUBLISHED cannot be silently edited.

## 5. Source record minimum contract

Required fields:

- source_id, source_version, canonical_name and canonical_locator;
- publisher/owner, source_class and source_type;
- claim_domains_supported and known_non_supported_domains;
- access_method, retrieval_method and whether authenticated access is involved;
- terms/licence, permitted_use, attribution and redistribution constraints;
- data_classification and allowed_recipient_scopes;
- first_seen_at, last_checked_at, source_published_at and source_updated_at when available;
- revision/version/hash and canonical snapshot reference where available;
- expected_update_cadence, freshness_ttl and outage/deprecation status;
- coverage, methodology, known bias, limitations, conflicts and manipulation risks;
- reliability history, steward_role_id, review_status and review_expiry;
- cost/API exposure and owner approval reference if any cost is contemplated.

Source status must be one of CANDIDATE, UNDER_REVIEW, APPROVED_LIMITED, APPROVED, DEGRADED, SUSPENDED or RETIRED. APPROVED_LIMITED includes exact allowed use and recipient restrictions. Discovery never auto-approves a source.

## 6. Evidence capture minimum contract

Each evidence capture identifies evidence_id, source_id and source_version; exact URL/locator/page/record/bar range; retrieval timestamp; source publication timestamp; content digest or dataset snapshot/version; quoted excerpt or compact factual extraction where legally permitted; retrieval method; transformations/normalisation; units/timezone; analyst role; permitted use; and known capture limitations.

Never claim a source was read or a dataset inspected unless an evidence capture exists. Never invent timestamps, excerpts, hashes, URLs, dataset versions or provenance. Respect source terms and copyright; retain only what is necessary and permitted.

## 7. Claim record and confidence

Each claim should be atomic and include:

- claim_id, claim_version and exact claim text;
- claim_type: OBSERVED_FACT, INFERENCE, HYPOTHESIS, FORECAST or OPINION;
- recipient_scope and decision relevance;
- evidence_refs and source_refs;
- supporting and contradicting evidence separately;
- assumptions, uncertainty, known alternatives and falsification condition;
- confidence_label and written rationale;
- analyst_role_id, independent_reviewer_role_id and review_status;
- valid_time / observation_time and expiry/recheck date when relevant.

Allowed confidence labels: CONFIRMED_PRIMARY, CORROBORATED, SUPPORTED, TENTATIVE, DISPUTED, UNVERIFIED, REJECTED. Do not assign numeric probabilities or precision scores unless a calibration methodology has been validated for the relevant claim class.

Independence rule: two publications are not independent corroboration merely because they are different URLs or models. Record shared upstream feeds, syndication, common ownership, identical datasets, common prompt/retrieval context and other dependencies.

## 8. Independent challenge record

ChallengeRecord must identify the claim/publication version reviewed, challenger role, evidence set, source-independence assessment, counter-hypotheses, contradiction search, missing evidence, reproducibility notes, scope/privacy check, disposition and unresolved objections.

Dispositions: ACCEPT_WITHIN_SCOPE, ACCEPT_WITH_CAVEATS, RETURN_FOR_REVISION, DISPUTED, REJECT, BLOCKED. A challenger cannot be the sole author of the reviewed claim or publication. For Trading risk-sensitive research, independent CRO requirements remain additional and cannot be replaced by R&I review.

## 9. Publication envelope

Every publication must include:

- publication_id, version, title and issue timestamp;
- exactly one recipient company for a company-specific report;
- research_id and parent_task_id;
- executive summary and question/decision context;
- scope, exclusions and methods;
- key findings as claim IDs with confidence labels;
- source freshness and as-of timestamp;
- counter-evidence, uncertainty, assumptions and limitations;
- risk, privacy, licensing and source-quality flags;
- recommended next research action (not authorization to act);
- author and independent reviewer role IDs;
- next review/expiry date;
- content digest, policy revision and audit correlation ID;
- supersedes_id and correction note where applicable.

Do not include raw private records, credentials, secrets, customer data or another company's confidential information. An OCC status envelope is not the full publication; it contains only the minimal authenticated status fields needed for oversight.

## 10. Distribution and recipient controls

Before delivery, enforce recipient allowlist, data classification, source redistribution rights, publication approval state, content digest and policy revision. DistributionReceipt records intended recipient, delivery channel identifier, timestamp, outcome and explicit acknowledgement state.

Cross-company publication requires a separate sanitisation record containing origin company, approved destination, source rights, removed fields, residual leakage/re-identification assessment, reviewer, approval reference, digest and audit ID. If any field is unresolved, block cross-company delivery.

## 11. Corrections, expiry and supersession

- Material corrections create a new publication version and link the previous version using supersedes_id.
- Preserve historical claim and evidence references; never silently replace source snapshots.
- Expired findings are marked STALE/EXPIRED for new decisions, not deleted from historical context.
- A source suspension triggers review of dependent claims/publications through reverse lineage.
- Material correction or suspension triggers recipient notification through the approved channel and a durable receipt.
- Retention/deletion follows approved legal and data-class policies; immutable audit does not justify retaining personal data beyond lawful need.

## 12. Fail-closed validation rules

Reject or quarantine records when: recipient is missing or ambiguous; company identity is invalid; source is unregistered for the claimed use; licence/redistribution is unclear; evidence locator cannot be resolved; timestamp/units/timezone are ambiguous; digest or revision mismatches; claim lacks evidence; author equals sole independent reviewer; publication includes disallowed data; policy revision is stale; approval is missing; parent task expired/revoked; or recipient scope was widened.

Missing or stale evidence must not be converted into a positive status. A failed validation is an explicit BLOCKED, DISPUTED, STALE or REJECTED state with reason and audit trail.

## 13. Reference JSON-shaped examples (illustrative only)

The following examples are conceptual payloads to clarify semantics. They are not a validated JSON Schema, production configuration or executable code.

### Claim

    {
      "schema_name": "research_claim",
      "schema_version": "1.0-draft",
      "claim_id": "CLM-example-001",
      "claim_version": 1,
      "company_id": "TRADING_TECH",
      "recipient_scope": "TRADING_TECH",
      "claim_type": "OBSERVED_FACT",
      "claim_text": "A source reports the specified event at the recorded time.",
      "evidence_refs": ["EVC-example-001"],
      "confidence_label": "SUPPORTED",
      "review_status": "PENDING_INDEPENDENT_REVIEW",
      "parent_research_id": "RI-example-001",
      "audit_correlation_id": "AUD-example-001"
    }

### Publication

    {
      "schema_name": "research_publication",
      "schema_version": "1.0-draft",
      "publication_id": "PUB-example-001",
      "version": 1,
      "recipient_scope": "TRADING_TECH",
      "claim_refs": ["CLM-example-001"],
      "review_status": "ACCEPT_WITH_CAVEATS",
      "approval_state": "INTERNAL_RESEARCH_RELEASE_ONLY",
      "supersedes_id": null,
      "audit_correlation_id": "AUD-example-001"
    }

All example IDs and values are synthetic placeholders and do not refer to real research or approved records.

## 14. Implementation and acceptance sequence

1. Reconcile fields with the existing Research & Intelligence Operating System and work-order register; preserve existing IDs.
2. Define canonical JSON Schema and versioning rules in a separate implementation phase.
3. Map canonical records to the chosen storage and Paperclip task metadata without treating Paperclip as the security authority.
4. Define deterministic validation for tenant identity, recipient scope, source status, claim lineage, reviewer independence, expiry and revocation.
5. Define signed publication and OCC status envelope mappings; verify canonical serialization, digest, sequence and anti-replay semantics.
6. Prepare synthetic fixtures for valid, stale, revoked, cross-tenant, unlicensed, contradictory, unsupported and superseded records.
7. Obtain explicit owner approval before schema implementation, code changes, tests, data collection, compute or service connections.

## 15. Non-authorization and current status

This document is a design-only contract. It does not approve any source, authorize API calls or data collection, create a database, implement a schema, execute tests, connect services, provision agents, use compute, publish reports, contact customers, spend funds or enable 24/7 operations.

No evidence registry or publication pipeline is implemented by this document. Existing work-order/source-stewardship registers remain the current planning records.
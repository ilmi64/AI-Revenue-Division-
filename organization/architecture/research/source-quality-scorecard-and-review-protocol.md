# Research & Intelligence — Source Quality Scorecard & Review Protocol

**Status:** Governance and assessment template; not an approval to connect, subscribe, collect data or publish signals.  
**Owner:** Research & Intelligence Director; maintained by Data & Knowledge Governance.  
**Default budget:** CAD $0 incremental.  
**Applies to:** Public, licensed and explicitly authorized sources used by either company or the shared Research & Intelligence Division.

## 1. Purpose and decision rule

Assess the reliability and fitness of a source for a specific claim, metric, event type, time horizon and recipient. A source is never globally “trusted”: a source may be strong for one fact and weak for another. Score the source-product-endpoint-metric combination, not merely the vendor brand.

The score is a triage aid, not proof of truth. A high score does not authorize API use, commercial use, a purchase, account connection, wallet connection, trading, customer contact or production dependency.

## 2. Mandatory identity and scope record

Before scoring, record:

- source ID; exact product, service, endpoint or publication; canonical domain and URL;
- legal/operator identity where publicly verifiable; ownership/affiliation and conflicts;
- exact data or claim being assessed; supported chains, venues, instruments, geographies and time periods;
- publisher/source timestamp, retrieval timestamp and timezone;
- source method: primary disclosure, direct observation, derived metric, estimate, model output, editorial report or social claim;
- source documentation and version; metric definitions, units, cohort selection and known transformations;
- access path: public webpage, public API, MCP, account-gated interface, paid plan, local software or other;
- free-tier availability and exact limits, if evidenced; distinguish API from MCP, webpage and self-hosted access;
- licence, terms, redistribution, attribution and commercial-use status;
- data retention, privacy, security and jurisdiction concerns;
- intended recipient: shared research, AI Revenue, Trading & Technology, or restricted;
- permitted use and prohibited use; accountable source steward and independent reviewer.

Unknown values must be marked UNKNOWN, not inferred from marketing copy or a similarly named product.

## 3. Weighted score (0–100)

Give each dimension a rating from 0 to 5. Weighted points = rating ÷ 5 × dimension weight. Record evidence and rationale for every rating. Use N/A only with a written reason and normalize the remaining weights to 100; do not use N/A to hide missing evidence.

| Dimension | Weight | What is assessed |
|---|---:|---|
| Identity and provenance | 15 | Canonical product/operator identity; traceable origin of the data or claim |
| Methodology and definitions | 15 | Transparent metric definitions, transformations, cohorts, labels and limitations |
| Primary evidence / reproducibility | 15 | Link to primary records or independently reproducible raw observations |
| Freshness and cadence | 10 | Publication/observation/retrieval timestamps, update cadence, delay and stale-data behavior |
| Coverage and representativeness | 10 | Chain/venue/instrument/entity coverage, sampling gaps, selection bias and exclusions |
| Independent corroboration | 10 | Independent sources support the same specific claim; not merely syndicated copies |
| Terms and permitted use | 10 | Clear access, licence, attribution, redistribution and commercial-use conditions |
| Reliability history | 5 | Availability, correction history, continuity and documented incident behavior |
| Conflict and uncertainty disclosure | 5 | Conflicts, estimates, uncertainty, alternative explanations and corrections are visible |
| Security and privacy posture | 5 | Data minimization, safe access path, account/wallet exposure and security disclosures |

Rating guide: 0 = absent or contradicted; 1 = very weak; 2 = material gaps; 3 = adequate for limited use; 4 = strong; 5 = unusually strong and independently evidenced. A vendor's own assertion alone cannot justify a 4 or 5 for performance or accuracy.

## 4. Hard-stop gates (override the numerical score)

Set disposition to **HOLD** regardless of score if any applies:

- exact product/operator identity is ambiguous or impersonation risk is unresolved;
- source provenance or metric construction cannot be understood well enough for the proposed use;
- access would require credentials, wallet connection, private-group access, scraping contrary to terms, bypassing controls or exposing secrets;
- terms/licence or commercial-use rights are unclear for the intended use;
- material privacy, security, jurisdiction or legal concern is unresolved;
- freshness is inadequate for the decision horizon, or stale/partial data cannot be detected;
- source makes a material performance claim that cannot be independently checked;
- API, MCP or plan limits/costs are unknown where use could incur charges;
- source is the sole basis for a high-impact trading, financial, safety or customer decision.

A halal/Shafi’i issue flag is required when the source relates to instruments, financing, leverage, derivatives, interest, staking/yield or other potentially relevant financial mechanisms. The source score does not determine religious permissibility; refer the underlying product/mechanism for qualified review.

## 5. Disposition bands

| Score | Default disposition | Permitted use |
|---:|---|---|
| 80–100 | CONDITIONAL_CANDIDATE | May be considered for scoped research after every hard gate passes and a reviewer signs off |
| 65–79 | LIMITED_CONTEXT_ONLY | Background/context; corroborate material claims independently |
| 0–64 | HOLD | Do not rely on it for decision support; investigate gaps or reject |

The band never overrides a hard stop. No score automatically approves integration or production dependency.

## 6. Claim-level evidence grades

Keep source quality separate from claim evidence:

- **PRIMARY_CONFIRMED:** claim directly supported by an authoritative primary record or reproducible native event.
- **CORROBORATED:** independently supported by two or more relevant sources.
- **SINGLE_SOURCE:** supported by one source only.
- **ATTRIBUTED:** interpretation of identity, ownership or cause; attribution confidence recorded separately.
- **VENDOR_ESTIMATE:** vendor-derived estimate or modelled metric.
- **PUBLIC_CLAIM:** claim made by a project, vendor, influencer or third party, not independently verified.
- **HYPOTHESIS:** testable interpretation, not established.
- **CONTRADICTED / SUPERSEDED:** evidence conflicts with or replaces the prior claim.

Never promote a source score into a claim evidence grade. A reliable provider can publish a weakly supported claim; an unknown source can point to a primary record that is independently verified.

## 7. Freshness policy

Assign a freshness class per source/metric and use case:

- **EVENT_DRIVEN:** material changes require a new observation; record event time and detection delay.
- **INTRADAY:** specify maximum acceptable lag in minutes/hours for the intended decision.
- **DAILY:** specify expected publication window and stale threshold.
- **SLOW_CONTEXT:** weekly/monthly or longer; suitable only for context, not execution timing.
- **STATIC_REFERENCE:** recheck on version, policy, terms or product change.

Every record stores published_at, observed_at (if applicable), retrieved_at, timezone, expected cadence, expires_at/review_due_at and last successful verification. Missing timestamps are explicit. Expired evidence becomes STALE; it is not silently treated as current.

## 8. Source-change and incident controls

Re-score when product identity, ownership, methodology, metric definition, endpoint, access tier, licence, terms, cadence, coverage or security posture changes. Preserve the previous record and mark it superseded; do not overwrite history.

Quarantine a source on unexplained discontinuity, suspected manipulation, provenance failure, material correction, compromised account, unexpected billing, privacy/security incident or terms change. Notify the source steward and affected recipient leads. Stop publication or downstream reliance until reviewed.

## 9. Required review workflow

1. Register source and exact intended claim/use.
2. Verify canonical identity and operator.
3. Read official documentation, terms and pricing/access pages.
4. Distinguish webpage, API, MCP, SDK, local/self-hosted and paid access.
5. Record methodology, data provenance, timestamps, limits and coverage.
6. Find primary corroboration and counter-evidence.
7. Complete weighted score and hard-stop checklist.
8. Independent reviewer challenges the score and intended use.
9. Approve only a narrowly scoped disposition with expiry and permitted recipient.
10. Re-review on expiry or material change; preserve the audit trail.

No API calls, account creation, trials requiring payment details, subscriptions, wallet connections, data collection jobs or integrations are authorized by this protocol.

## 10. Existing specialist-source dispositions

- **J7:** exact intended product/operator identity remains unresolved. **HOLD**; do not substitute a same-name extension or assume its identity.
- **Buildix.trade:** public documentation supports a limited, vendor-defined Hyperliquid perpetuals analytics context. Treat outputs as estimates/aggregates with documented cadence and coverage limits; **LIMITED_CONTEXT_ONLY** pending metric-specific corroboration and terms review. Perpetuals require separate leverage/derivative and halal issue review.
- **Sanbase / Santiment:** potentially useful for slow-moving contextual analytics; current free access has material lag and real-time API access is plan-gated according to current official material. **LIMITED_CONTEXT_ONLY** for eligible public/context use; no API integration or paid plan approved.
- **NVIDIA Build:** optional model-provider candidate, not a research source of truth. Assess each model, endpoint, model card, access tier, terms, rate limit, privacy and production licence separately. Free developer inference must not be represented as unrestricted production capacity.

These dispositions are provisional and must be rechecked against current official documentation before any future use.

## 11. Company and OCC boundaries

Research & Intelligence retains source-level evidence under its own identity and access controls. Trading & Technology receives only approved market, strategy, capital-flow, instrument and technology intelligence. AI Revenue receives approved customer, competitor, product, pricing, distribution and technology intelligence. Do not disclose one company's private information to the other.

The Main Hub/OCC receives only allowlisted aggregate status, freshness bands, source IDs, evidence references and incident metadata. It does not receive unrestricted raw research content. Research recommendations cannot authorize trades, spending, customer contact, publishing or other company actions.

## 12. Assessment record template

```yaml
source_id: SRC-YYYY-NNNN
product_endpoint_metric: UNKNOWN
canonical_domain: UNKNOWN
operator_identity: UNKNOWN
intended_claim_and_use: UNKNOWN
recipient_scope: SHARED_RESEARCH | AI_REVENUE | TRADING_TECHNOLOGY | RESTRICTED
access_path: WEB | API | MCP | SDK | LOCAL | OTHER | UNKNOWN
terms_status: UNKNOWN
commercial_use_status: UNKNOWN
methodology_version: UNKNOWN
coverage: UNKNOWN
published_at: UNKNOWN
retrieved_at: YYYY-MM-DDTHH:MM:SSZ
expected_cadence: UNKNOWN
freshness_expiry: UNKNOWN
ratings_0_to_5: {}
weighted_score: NOT_SCORED
hard_stops: []
claim_evidence_grade: UNKNOWN
disposition: HOLD
permitted_use: NONE
prohibited_use: []
halal_issue_flag: NOT_ASSESSED
source_steward: UNASSIGNED
independent_reviewer: UNASSIGNED
reviewed_at: UNKNOWN
next_review_due: UNKNOWN
limitations_and_conflicts: []
evidence_references: []
```

**Current status:** Framework prepared. No new source is approved, connected, subscribed to, or operational through this document.

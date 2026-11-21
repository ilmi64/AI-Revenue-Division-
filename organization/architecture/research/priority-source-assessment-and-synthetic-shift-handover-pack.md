# Research & Intelligence — Priority Source Assessment & Synthetic Shift Handover Pack

**Status:** Preparation and synthetic examples only; no live monitoring, source ingestion, API use, staffed shifts or 24/7 coverage.
**Owner:** Organization-level Research & Intelligence Division. **Budget:** CAD $0 incremental.
**Recipients:** Separate, scoped intelligence for AI Revenue and Trading & Technology.

## 1. Purpose
Apply the existing Source Quality Scorecard to sources that could materially change current decisions, then demonstrate a day/night handover using fictional records. This pack does not approve a provider, account, API, subscription, collection or publication. The existing weighted scorecard and hard-stop rules remain authoritative. Scores below are NOT_SCORED where exact source-product-metric evidence has not been re-verified.

## 2. Priority source assessment queue

| Priority | Source / family | Intended use | Current disposition | Next evidence needed |
|---|---|---|---|---|
| 1 | Coinbase Exchange official market-data documentation | BTC-USD spot candle/feed semantics | Endpoint-specific documentation candidate | Exact endpoint/channel, sequence/finality, timestamps, terms and intended-use review |
| 2 | Binance Spot official market-data documentation | Separate BTCUSDT spot comparison and candle mapping | Public-data documentation candidate only; not an Ontario execution venue | Exact endpoint/stream, UTC convention, finality, rate limits, terms and jurisdiction |
| 3 | Primary project/foundation announcements and governance execution records | Fundraising, treasury, grants, launches and unlocks | Candidate source class; register each canonical source | Identity, announcement vs executed event, date, amount, contract/transaction and corrections |
| 4 | Chain explorers / public RPC / native transaction records | Observable transfers, contract events and treasury movements | Candidate source class; no endpoint approved | Chain ID, event decoding, finality/reorg policy, terms and attribution limits |
| 5 | Santiment / Sanbase exact metric or product | Slow-moving contextual on-chain and capital-flow analytics | LIMITED_CONTEXT_ONLY, provisional | Exact metric, lag, cohort, coverage, current free limits, terms and commercial use |
| 6 | Buildix.trade exact product/metric | Hyperliquid perpetuals analytics context | LIMITED_CONTEXT_ONLY, provisional | Canonical identity, methodology, data sources, cadence, terms and derivative/halal flags |
| 7 | J7 | Potential capital-flow / smart-money intelligence | HOLD — exact identity unresolved | Establish canonical product/operator before scoring or use |
| 8 | Statistics Canada / CFIB / BDC primary research | Canadian small-business and AI demand context | Public research candidates; claim-specific review | Publication/version/date, population, survey question, sample and interpretation limits |
| 9 | Canadian workflow-automation competitor pages | Advertised scope and price positioning | PUBLIC_CLAIM / snapshot context only | Page date, scope, tax, inclusions; never infer actual transaction prices |
| 10 | Official documentation/licences for agent/tool candidates | Workforce architecture, runtime, licence, security and cost | Candidate documentation only | Exact product/version/licence/runtime/dependencies/data handling/cost |

### Hard stops retained
- J7 remains HOLD; do not substitute a same-name product.
- Buildix.trade and Santiment remain context-only; no API or subscription.
- Binance is a public-data research candidate only, not an Ontario execution venue.
- Public access does not automatically permit API use, redistribution or commercial use.
- No score grants operational approval.
- Financial-source work retains leverage, derivatives, financing, yield and Shafi'i issue flags.

## 3. Claim-level evidence grades
PRIMARY_CONFIRMED = authoritative primary record or reproducible native event. CORROBORATED = independently supported by multiple relevant sources. SINGLE_SOURCE = one source. VENDOR_ESTIMATE = modelled/vendor metric. PUBLIC_CLAIM = marketing/social/third-party assertion not independently verified. ATTRIBUTED = inferred ownership/cause with separate confidence. HYPOTHESIS = testable interpretation. CONTRADICTED / SUPERSEDED = evidence conflicts with or replaces the prior record.

Source quality and claim evidence are separate. A high-scoring provider does not prove a particular claim.

## 4. Synthetic day/night handover example

**Every name, event, timestamp, value and ID below is invented training data. It is not a real market observation or operational coverage.**

### Outgoing day shift — fictional
| Field | Synthetic value |
|---|---|
| Handover ID | RIH-SYN-20261121-DAY-001 |
| Coverage window | 09:00–17:00 America/Toronto |
| Outgoing lead | SYNTHETIC_DAY_LEAD |
| Incoming lead | SYNTHETIC_NIGHT_LEAD |
| Status | HANDOVER_PENDING |
| Actual coverage | Fictional exercise only; no real shift staffed |

Synthetic desk status:
- Crypto / PolyBot: documentation review task; endpoint mapping pending.
- Capital Flow: fictional project announcement candidate; no transaction evidence.
- AI Business Intelligence: fictional competitor pricing-page change candidate.
- Grok Desk: discovery concept only; no monitoring or autonomous scanning.

| Task | Recipient | Priority | Status | Next action |
|---|---|---:|---|---|
| SYN-TT-001 | Trading & Technology | P2 | BLOCKED | Verify exact candle endpoint and quote asset |
| SYN-RI-002 | Shared Research | P2 | NEEDS_CORROBORATION | Find primary governance execution record |
| SYN-AR-003 | AI Revenue | P2 | DRAFT | Recheck advertised scope/date; label public claim |

Synthetic source exceptions:
- Market-data record has unknown finality: HOLD; no indicator input.
- Wallet attribution has no evidence: UNKNOWN; do not report as verified.
- Competitor page lists a monthly price without contract evidence: public advertised price only.

Resource state: CAD $0 incremental; no API, paid tool or account use.

### Incoming night shift — fictional acceptance
Incoming lead:
- accepts SYN-TT-001 only as a documentation task, not data collection;
- accepts SYN-RI-002 subject to executed primary evidence;
- accepts SYN-AR-003 as a dated public-claim comparison only;
- retains wallet attribution as UNKNOWN;
- confirms no source/task has been promoted to operational approval;
- records any real unstaffed period as UNCOVERED.

Synthetic acknowledgement: HANDOVER_ACCEPTED at 2026-11-21T17:05:00-05:00; incoming owner SYNTHETIC_NIGHT_LEAD. This is an example, not evidence of a real shift.

## 5. Blank reusable handover record
    handover_id: RIH-YYYYMMDD-SHIFT-NNN
    coverage_window: UNKNOWN
    timezone: UNKNOWN
    outgoing_lead: UNASSIGNED
    incoming_lead: UNASSIGNED
    status: HANDOVER_PENDING
    desk_status: {}
    active_tasks: []
    new_findings: []
    source_freshness_exceptions: []
    source_holds_or_changes: []
    contradictions_and_unknowns: []
    incidents: []
    escalations: []
    blocked_tasks: []
    uncovered_desks_or_windows: []
    resource_cost_status: UNKNOWN
    decisions_required: []
    next_actions: []
    archive_revision: UNKNOWN
    incoming_acknowledgement: PENDING
    acknowledged_at: UNKNOWN

## 6. Next review sequence
1. Complete endpoint-specific Coinbase/Binance documentation and terms review before any data use.
2. Register canonical primary sources individually for priority capital-flow events.
3. Revisit Santiment and Buildix only when a specific metric and recipient decision justify it.
4. Resolve J7 identity before further assessment.
5. Refresh Canadian business-demand/competitor evidence only where it can change the first AI Revenue offer.
6. Keep agent/tool comparisons in Technology Intelligence; no installation or connection.

## 7. Current disposition
**SOURCE QUEUE PREPARED; NO NEW SOURCE APPROVED; NO SCORES INVENTED; SYNTHETIC HANDOVER ONLY; NO STAFFED SHIFT OR CONTINUOUS MONITORING CLAIMED.**

## 8. Reusable event verification and challenge record

See [Grok Desk Event Verification & Challenge Record](grok-desk-event-verification-and-challenge-record.md). It is mirrored in the Trading & Technology repository. The template is advisory and does not authorize automated monitoring, ingestion or publication.


## 9. Desk roster and assignment protocol

See [Research & Intelligence Desk Roster, Work Assignment & Challenge Protocol](research-intelligence-desk-roster-and-assignment-protocol.md). This defines specialist desk responsibilities, company-scoped work orders, priority, independent challenge, dispositions and day/night handover requirements. It is mirrored in the Trading & Technology repository. The roster is proposed, not staffed or operational.


## 10. Organization-level Security & Recovery Division

The organization-level Security & Recovery Division is a first-class division alongside Crypto/Trading, Treasury/Finance, Technology/Infrastructure, Research/Intelligence and Business/Commercial. See [Security & Recovery Division Charter](../security-recovery/security-and-recovery-division-charter.md) and [Incident Register, Corrective Actions & Recovery Assurance Standard](../security-recovery/incident-register-and-recovery-assurance-standard.md). This is separate from AI Revenue's embedded Security, Privacy & Recovery responsibilities; company authority, records, credentials and recovery paths remain isolated. Charter and register are prepared only; no monitoring, containment, backup, restore, rollback or recovery drill is operational.

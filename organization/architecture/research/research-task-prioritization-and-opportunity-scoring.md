# Research & Intelligence — Task Prioritization & Opportunity Scoring Protocol

**Status:** Decision framework; no automated scheduler or live queue policy deployed.
**Owner:** Research Operations Lead; domain priority set by the Director of Research.
**Authority:** Research may rank and recommend. Recipient companies retain their decisions and risk authority.

## 1. Purpose

Convert incoming questions, events and opportunities into a transparent research queue without allowing model enthusiasm, vendor alerts or speculative upside to dominate. Separate urgency from value, evidence quality, effort and risk. A high score never authorizes external action.

## 2. First-stage triage and hard gates

Record requester, recipient scope, question, decision/use, desk, deadline, allowed sources, data classes, deliverable and acceptance criteria.

- P0: integrity/security/privacy incident, suspected compromise, cross-tenant leak, secret exposure, unexpected billing or urgent source/data poisoning. Stop affected work and escalate.
- P1: time-sensitive material event with a narrow verification or decision window.
- P2: scheduled research with clear decision relevance.
- P3: exploratory backlog, enrichment or low-urgency discovery.

BLOCK if identity, legality, licence, privacy, cost, source provenance or recipient scope is unresolved. Do not score around a hard stop.

## 3. Research-value score (0–100)

Rate each dimension 0–5 with written evidence. Weighted points = rating / 5 × weight.

| Dimension | Weight | Assessment |
|---|---:|---|
| Decision relevance | 20 | Does this answer a real, named decision or remove a blocker? |
| Potential impact | 15 | Plausible scale of benefit or risk avoided; forecasts remain forecasts |
| Time sensitivity | 15 | How quickly will the finding lose relevance? |
| Evidence readiness | 15 | Are reliable, accessible, lawful sources available now? |
| Strategic fit | 10 | Does it support an approved objective? |
| Reusability | 10 | Can it improve future decisions without crossing data boundaries? |
| Effort efficiency | 10 | Is expected value proportionate to time and free-tier/resource limits? |
| Uncertainty reducibility | 5 | Can research materially resolve uncertainty? |

Bands:
- 80–100: PRIORITY_CANDIDATE, subject to gates and capacity.
- 65–79: SCHEDULE with a due window.
- 45–64: BACKLOG.
- 0–44: DEFER_OR_CLOSE.

P0/P1 urgency determines escalation independently; it does not inflate the value score. High-value low-urgency work cannot displace an incident.

## 4. Opportunity assessment

For opportunity dossiers, separately record evidence strength, economic plausibility, feasibility, time-to-validation, downside/risk and halal issue flags. Do not collapse these into one profitability number. Unverified revenue, airdrops, screenshots, projected token appreciation or vendor performance claims are not available capital.

Halal/Shafi'i review flags include financing, interest, leverage, derivatives, shorting, staking/yield, underlying business and other relevant mechanisms. The score is not a religious ruling.

## 5. Capacity and queue policy

P0 incidents interrupt normal work only within the affected scope. P1 receives rapid triage and verification plan; no publication before evidence review. P2 is scheduled by desk. P3 is batched, deferred or closed. Each task has one accountable owner, next-review time and acceptance criteria; material work has an independent reviewer. Limit work in progress by desk. Reserve capacity for source maintenance, challenge, corrections and handovers. Models cannot self-assign unlimited work or change their own priority. Reprioritization records old/new priority, reason, actor and timestamp.

## 6. Company routing

Trading-only market/strategy/capital-flow work routes to Trading's approved intake and risk-review queues. AI Revenue customer/product/competitor/service work routes to AI Revenue's intake. Shared public-source or general technology research may be organization-scoped. Cross-company benefit does not authorize cross-company data access. Each recipient gets a separately reviewed publication. Research cannot override company risk, finance or owner approvals.

## 7. Stop, pause and expiry

Pause or close if evidence is unavailable/stale; source identity, terms or provenance fail; costs exceed CAD $0 boundary; scope drifts into unauthorized access or personal data; work requires installation, execution, external contact, publishing, deployment, purchase or financial action; relevance expires; or independent review finds material contradiction. Record reason, owner, evidence and restart condition.

## 8. Lifecycle and audit

INTAKE → TRIAGE → PRIOR-WORK/SOURCE CHECK → SCORING → QUEUED → ASSIGNED → RESEARCH → CHALLENGE → RECIPIENT REVIEW → PUBLISHED/CLOSED. Alternative states: BLOCKED, PAUSED, EXPIRED, CANCELLED, SUPERSEDED, DEAD_LETTER.

Record task ID, requester, recipient, desk, urgency, ratings, score, hard stops, evidence stage, sources, owner, reviewer, due date, resource estimate, status changes, reprioritization reason, publication version and closeout result.

## 9. Synthetic illustration

A fictional public documentation change relevant to a market-data contract might score 4/5 decision relevance, 4/5 impact, 4/5 time sensitivity, 5/5 evidence readiness, 5/5 strategic fit, 4/5 reusability, 4/5 effort efficiency and 4/5 uncertainty reducibility: 84/100. Arithmetic illustration only; not a live task, measured impact or permission to collect data/change code.

## 10. Current status

Protocol prepared for future queue implementation. No automated ranking, scheduler, alerts, live task reassignment, data collection or execution is active. P0/P1 escalation channels must be established before operational use.

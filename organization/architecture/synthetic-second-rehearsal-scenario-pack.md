# AI Revenue — Synthetic Rehearsal Scenario 2: Appointment Confirmation & Preparation

**Status:** Synthetic input specification only; NOT RUN.
**Purpose:** Provide a second distinct workflow for a future internally authorized delivery rehearsal.
**Data:** Every entity and number below is fictional. Not industry averages, customer evidence, a savings forecast or proof of demand.
**Execution boundary:** Do not calculate, time, run a test or claim a rehearsal occurred unless separately authorized.

## 1. Fictional business and workflow
"Harbourlight Repair Services" receives customer requests for repair appointments. A coordinator checks the request, asks for missing details, proposes a time slot, records confirmation and prepares a technician visit summary. The scenario is designed to test document clarity and evidence discipline, not to recommend automation by default.

Workflow boundary: request received → appointment confirmed → technician-ready summary prepared. Excludes service delivery, payment, dispatch optimization, customer communications and production system access.

## 2. Fictional inputs

| Input | Synthetic value | Unit / period |
|---|---:|---|
| New appointment requests | 80 | per month |
| Initial request review | 5 | minutes / request |
| Requests missing one or more required details | 25 | per month |
| Follow-up preparation / internal handling | 4 | minutes / incomplete request |
| Appointment slot coordination | 6 | minutes / confirmed appointment |
| Requests resulting in confirmed appointment | 52 | per month |
| Technician summary preparation | 7 | minutes / confirmed appointment |
| Summary corrections | 8 | per month |
| Time per correction | 3 | minutes / correction |
| No-show / cancellation rate | UNKNOWN | Not supplied |
| Customer satisfaction | UNKNOWN | Not supplied |
| Revenue per appointment | UNKNOWN | Not supplied |
| Technician idle time attributable to intake | UNKNOWN | Not supplied |

All figures are invented scenario inputs. Do not infer that 52/80 represents a market conversion rate or that missing details cause lost revenue.

## 3. Questions the rehearsal should answer
1. Map the trigger, coordinator role, required fields, decision points, handoffs, system records and completion definition.
2. Calculate workload by activity only when an authorized rehearsal is run; preserve each unit and period.
3. Separate routine handling from correction/rework and avoid double-counting overlapping tasks.
4. Identify missing evidence needed to assess appointment delay, duplicate work, missed confirmations or technician readiness.
5. Propose no more than three improvements, starting with a process/control change before software or AI.
6. For each improvement, state implementation effort, recurring effort, dependency, failure mode, privacy risk, human approval and measurement method.
7. Do not monetize minutes without an owner-selected labour rate and a defensible capacity/cash-impact model.
8. Do not estimate recovered appointments, reduced no-shows or increased revenue from the supplied data.

## 4. Scope and privacy guardrails
- Use only the synthetic inputs in this pack.
- No names, phone numbers, addresses, repair details or real customer records.
- Do not connect to email, calendar, CRM, dispatch or payment systems.
- Do not propose autonomous customer messaging or appointment changes as a default.
- Human confirmation remains mandatory for any scheduling decision in a future implementation concept.
- Treat any real-world health/safety, home-access, location or sensitive data as a hard stop pending qualified review.

## 5. QA acceptance rubric for a future rehearsal
A reviewer may mark each item PASS / FAIL / NOT APPLICABLE only after reviewing a completed artifact:
- scope boundary is exact and exclusions visible;
- all scenario values remain labelled synthetic;
- process map contains roles, handoffs and end states;
- arithmetic is reproducible and unit-consistent;
- facts, assumptions, hypotheses and unknowns are not conflated;
- no unsupported savings, conversion, revenue or accuracy claims;
- recommendations are ranked by impact, effort, risk and dependency;
- process-first/no-cost alternatives are considered;
- privacy and human-approval controls are explicit;
- report is concise, understandable and traceable;
- actual hands-on and elapsed time are separately captured;
- QA defects and rework are recorded;
- no production action or external communication occurred.

## 6. Relationship to first rehearsal
This is a second, distinct synthetic scenario. The existing Northstar enquiry-intake scenario remains Scenario 1. Both are preparation inputs only. Two completed synthetic rehearsals may help estimate repeatability but cannot establish buyer demand, a market price or commercial profitability.

## 7. Current disposition
**SCENARIO PREPARED; NOT CALCULATED; NOT TIMED; NOT REHEARSED; NO CUSTOMER DATA; NO DEMAND OR SAVINGS CLAIM.**

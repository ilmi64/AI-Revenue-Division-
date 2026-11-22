# Synthetic Worked Sample — Practical Operations Improvement Audit

**Status:** Fictional demonstration only; not a customer report, not a completed delivery rehearsal, and not evidence of realized savings.  
**Data source:** `synthetic-rehearsal-input-pack.md`; every input is invented.  
**Currency / jurisdiction:** No prices or legal/tax advice are modelled.  
**Rehearsal status:** NOT RUN. The calculations below are hand-derived from the synthetic inputs; no test or Python execution was performed.

## 1. Executive summary

This fictional service business receives 120 enquiries per month. The scenario assigns 4 minutes to copying/normalizing each enquiry, 3 minutes of owner review per enquiry, 8 minutes to prepare each of 60 monthly quotes, and 5 minutes for one manual follow-up per quoted enquiry.

The four measured activities total **1,620 minutes, or 27 hours per month** under the scenario assumptions:

- Intake copying/normalization: 480 minutes (8 hours).
- Owner review: 360 minutes (6 hours).
- Quote preparation: 480 minutes (8 hours).
- Manual follow-up: 300 minutes (5 hours).

This is an activity-time baseline, not a savings estimate. It does not establish that all activity is avoidable, that automation can remove it, or that released time converts to cash or additional sales.

Only 70% of enquiry records have a complete outcome status. Applied to 120 records, that means 84 records have complete outcomes and 36 do not. This is a data-quality limitation; it is not proof that 36 enquiries were lost.

## 2. Scope and evidence classification

### In scope
- Arithmetic of the four supplied activity-time inputs.
- Record-outcome completeness.
- Potential improvement hypotheses and the evidence needed to evaluate them.

### Out of scope
- Customer system inspection, implementation, automation, integration or deployment.
- Conversion, quote acceptance, revenue uplift, missed-lead or customer-satisfaction claims.
- Labour-cost monetization, ROI, payback, pricing or guaranteed savings.
- Legal, tax, accounting, cybersecurity certification or regulated advice.

### Evidence labels
| Label | Meaning | Application in this report |
|---|---|---|
| SYNTHETIC INPUT | Invented scenario value | All volumes, minutes and completeness rate |
| CALCULATED | Arithmetic derived from synthetic inputs | Activity minutes/hours and incomplete-record count |
| HYPOTHESIS | Plausible explanation or improvement to investigate | Standardized capture, queue visibility, follow-up controls |
| UNKNOWN | Required evidence not supplied | Rework, actual outcomes, wage cost, tool capabilities, quote acceptance |
| NOT VERIFIED | Requires observation or independent evidence | Whether any proposed change reduces time or errors |

## 3. Baseline calculations

Formula: monthly activity minutes = monthly activity volume × minutes per activity.  
Conversion: monthly hours = monthly minutes ÷ 60.

| Activity | Scenario volume | Minutes each | Monthly minutes | Monthly hours |
|---|---:|---:|---:|---:|
| Copy/normalize enquiry | 120 | 4 | 120 × 4 = 480 | 8.0 |
| Owner review | 120 | 3 | 120 × 3 = 360 | 6.0 |
| Quote preparation | 60 | 8 | 60 × 8 = 480 | 8.0 |
| Manual follow-up | 60 | 5 | 60 × 5 = 300 | 5.0 |
| **Total** | — | — | **1,620** | **27.0** |

**Interpretation:** The scenario describes 27 hours per month across these four activities. The total is not necessarily 27 hours of waste: owner review and quote preparation may be valuable work, and the supplied figures do not include quality, exception handling or rework.

### Outcome-status completeness

- Total enquiries: 120.
- Complete outcome status: 120 × 70% = 84.
- Incomplete outcome status: 120 − 84 = 36.
- Completeness: 70%; incompleteness: 30%.

**Interpretation:** The business would not yet have a complete outcome record for 36 of 120 enquiries in this fictional scenario. We cannot infer whether those records represent lost leads, open opportunities, duplicates, non-qualifying enquiries or simple data-entry omissions.

## 4. Findings and limitations

| ID | Observation | Evidence | Business implication | Confidence |
|---|---|---|---|---|
| F-01 | Enquiry copying/normalization is assigned 8 hours/month | SYNTHETIC INPUT + CALCULATED | Standardized capture may reduce duplicate entry; actual avoidability is unknown | High arithmetic confidence; no real-world confidence |
| F-02 | Owner review is assigned 6 hours/month | SYNTHETIC INPUT + CALCULATED | Review criteria and routing may be worth mapping; review itself may be essential | High arithmetic confidence; no real-world confidence |
| F-03 | Quote preparation is assigned 8 hours/month for 60 quotes | SYNTHETIC INPUT + CALCULATED | Reusable quote inputs/templates may be worth examining | High arithmetic confidence; no real-world confidence |
| F-04 | Follow-up is assigned 5 hours/month | SYNTHETIC INPUT + CALCULATED | A visible due-date/ownership process may reduce omissions; no omission rate supplied | High arithmetic confidence; no real-world confidence |
| F-05 | 36 records lack complete outcome status | SYNTHETIC INPUT + CALCULATED | Reporting and process diagnosis are limited until outcomes are consistently recorded | High arithmetic confidence; no real-world confidence |

## 5. Prioritized improvement hypotheses

These are options for a later customer-specific review, not instructions to change a live system.

### H-01 — Standardized enquiry capture
- **Hypothesis:** A consistent intake form or structured capture template could reduce repeated copying and missing fields.
- **Potential benefit:** Less duplicate entry and more consistent handoff.
- **Implementation effort:** UNKNOWN; first map current channels, required fields and exceptions.
- **Recurring effort/cost:** UNKNOWN; depends on existing tools and ownership.
- **Dependencies:** Existing approved capture channel, field definitions, data-retention rules and a responsible owner.
- **Risks:** Incomplete form submissions, inaccessible channels, unnecessary personal-data collection, mistaken auto-classification.
- **Measurement:** Sample a defined period; record handling time, missing-field rate, duplicate rate and exception rate before and after.
- **Guardrail:** Keep human review for ambiguous, high-value or sensitive enquiries.

### H-02 — Quote preparation template
- **Hypothesis:** A reusable quote structure with validated input fields could reduce repetitive formatting and omissions.
- **Potential benefit:** More consistent quote preparation and easier quality review.
- **Implementation effort:** UNKNOWN; depends on product/service complexity and pricing rules.
- **Recurring effort/cost:** UNKNOWN; templates require maintenance and version control.
- **Dependencies:** Approved pricing source, scope rules, exclusions, tax treatment and quote approval authority.
- **Risks:** Stale prices, incorrect scope, unauthorized discounts, accidental disclosure or sending an unapproved quote.
- **Measurement:** Compare preparation time, correction/rework rate and quote completeness on comparable samples.
- **Guardrail:** No automated price changes, commitments or customer sending; human approval remains mandatory.

### H-03 — Follow-up ownership and outcome tracking
- **Hypothesis:** A simple status, next-action date and named owner may make follow-up work visible and improve outcome completeness.
- **Potential benefit:** Better operational visibility; any effect on response or conversion remains unproven.
- **Implementation effort:** UNKNOWN; first establish statuses and ownership.
- **Recurring effort/cost:** UNKNOWN; depends on existing tools and review cadence.
- **Dependencies:** Agreed outcome definitions, an accountable owner, privacy/retention rules and an existing approved tracker.
- **Risks:** Incorrect status, duplicate reminders, inappropriate contact, over-retention of personal information.
- **Measurement:** Track outcome completeness, overdue tasks, duplicate follow-ups and time spent maintaining the tracker.
- **Guardrail:** No messages are sent automatically; no customer data is moved without separate authorization.

## 6. Missing information before an actual recommendation

1. Which channels generate enquiries, and are any enquiries duplicated across channels?
2. Does the 4-minute intake figure include searching, re-keying, validation and corrections?
3. Is owner review required for every enquiry? What decisions does it make?
4. Do all 60 quotes require the same preparation steps and approvals?
5. Is the single 5-minute follow-up performed for every quote, and are additional attempts common?
6. What do the 30% incomplete outcome records actually represent?
7. What are the observed error, rework, response-delay and overdue-follow-up rates?
8. Which tools are already licensed and used, and what export/integration restrictions apply?
9. Who owns each step, and what are the privacy, retention and access requirements?
10. What management-approved labour-cost or capacity value, if any, should be used for economic modelling?

## 7. Economic treatment

No dollar value is calculated. A future model would require customer-approved assumptions for loaded labour cost, productive capacity, actual avoidable minutes, implementation and maintenance effort, software/API costs, training, review, exception handling and rework.

Do not multiply all 27 hours by an hourly rate and call the result savings. At most, that would be a gross time-value illustration before determining which minutes are genuinely released and economically usable.

Any later scenario must separately show:
- observed baseline;
- measured post-change result;
- time released versus cash cost removed;
- implementation and recurring costs;
- exception/rework cost;
- conservative/base/stress assumptions;
- confidence and sample size.

## 8. Customer acceptance and QA rubric

Score each item Pass / Fail / Not Applicable. A report must not be delivered as complete if any critical item fails.

| QA item | Critical? | Acceptance condition |
|---|---|---|
| Source traceability | Yes | Every input has a source, owner and period |
| Evidence labels | Yes | Facts, calculations, hypotheses and unknowns are visibly separated |
| Arithmetic | Yes | Independent recalculation agrees; units and formulas are shown |
| Scope discipline | Yes | No unsupported ROI, savings, conversion or revenue claim |
| Data minimization | Yes | No unnecessary personal or sensitive data is collected or reproduced |
| Workflow coverage | Yes | Start, end, handoffs, exceptions and ownership are represented |
| Risk review | Yes | Privacy, security, human approval and operational risks are recorded |
| Recommendations | Yes | Each recommendation has effort, dependency, risk and measurement plan, or is marked unknown |
| Economics | Yes | Time value is not presented as cash savings without evidence |
| Customer readability | No | Findings and next actions are understandable to the intended buyer |
| Version and reviewer | Yes | Report version, preparer, reviewer and review date are recorded |
| Acceptance record | Yes | Customer acceptance or outstanding disagreement is documented |

### Delivery stop conditions
Stop and request clarification if source data conflicts, the period/units are unclear, material workflow steps are missing, calculations cannot be reconciled, personal/sensitive data is unnecessarily exposed, or the customer requests an unsupported guarantee.

## 9. Rehearsal record

- Rehearsal operator: NOT ASSIGNED.
- Start/end timestamps: NOT RECORDED.
- Actual preparation time: NOT RECORDED.
- Independent arithmetic review: NOT PERFORMED.
- QA scoring: NOT PERFORMED.
- Rework and defect log: NOT CREATED.
- Acceptance: NOT ASSESSED.
- Rehearsal status: **NOT RUN**.

This document demonstrates a report format and transparent arithmetic only. It does not establish that the service can be delivered within the proposed time target or profitably sold.

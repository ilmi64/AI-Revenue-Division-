# Synthetic Demonstration — Practical Operations Improvement Audit

<badge>Fictional example — not a client case study</badge>

**Purpose:** Demonstrate the structure and reasoning of the proposed AI Revenue service. All business details, volumes, timings and calculations below are invented for illustration. They are not market averages, actual savings or customer results.

## 1. Fictional business and workflow

**Business:** Northstar Home Services (fictional small residential maintenance company).  
**Workflow:** New enquiry to quote preparation.  
**Illustrative monthly volume:** 30 enquiries.  
**Current tools:** shared email inbox, phone calls and a spreadsheet.  
**Scope:** process analysis only. No real systems or customer records are accessed.

## 2. Current-state process

1. Customer contacts the business by email or phone.
2. Staff member reads the message and manually copies key details into a spreadsheet.
3. Missing information is chased through a separate email or call.
4. Staff member prepares a quote using information gathered from the message and spreadsheet.
5. The quote is sent and a follow-up reminder is managed manually.

The sequence is hypothetical. A real audit would verify each step with the business.

## 3. Illustrative baseline

| Metric | Synthetic value | Assumption |
|---|---:|---|
| Enquiries per month | 30 | Fixed example volume |
| Admin time to record and organize each enquiry | 6 minutes | Assumed average |
| Monthly admin time for this step | 180 minutes / 3 hours | 30 × 6 minutes |
| Time spent on missing-information follow-up | Not measured | No savings estimate made |
| Lost enquiries | Unknown | No lost-lead claim made |
| Quote conversion | Unknown | No revenue uplift estimate made |

### Calculation

Baseline admin time for the intake-recording step:

30 enquiries × 6 minutes = 180 minutes = 3 hours per month.

This is an illustrative workload estimate, not evidence that three hours can be eliminated.

## 4. Friction hypotheses to validate

| ID | Hypothesis | Evidence required in a real engagement |
|---|---|---|
| F-01 | Staff re-enter the same information into email notes and the spreadsheet | Observe a sample of redacted enquiries and the corresponding records |
| F-02 | Required quote details are not captured consistently at intake | Compare a sample of completed quotes and intake records |
| F-03 | Follow-up ownership is unclear | Review the current handoff and reminder method |

None of these hypotheses should be presented as a confirmed problem until verified.

## 5. Improvement options

| Option | Description | Relative effort | Cost / risk |
|---|---|---|---|
| A — Standard intake checklist | One consistent list of details required before quote preparation | Low | No new software required; staff adoption needed |
| B — Single lead-tracker structure | Define one record format and clear owner/status fields in an existing approved spreadsheet | Low–medium | Existing-tool permissions and client approval required |
| C — Automation concept | Explore pre-filling or routing information using a client-approved tool | Medium–high | Tool cost, privacy, security and integration review required; not included in this audit |

**Recommended first step:** validate and document the intake checklist before introducing automation. A process that is unclear should not be automated prematurely.

## 6. Example measurement plan

For a two-week client-approved observation period, record:
- number of enquiries received;
- time required to create a complete intake record;
- percentage with missing required information;
- number of duplicate entries;
- time between enquiry and quote-ready status;
- staff effort spent correcting records.

Compare like-for-like periods and note changes in enquiry volume or staffing. Do not claim causation from a small uncontrolled comparison.

## 7. Illustrative recommendation

Create a standard intake checklist with:
- customer contact channel;
- service requested;
- location at an appropriately coarse level;
- requested timeframe;
- information required to scope the quote;
- missing-information status;
- responsible staff member;
- next action and due date.

Avoid collecting sensitive information unless genuinely necessary. Store the record only in the client's approved system.

## 8. Acceptance criteria for a real engagement

A real deliverable would be accepted only if:
- the assessed workflow matches the approved scope;
- each confirmed finding links to client-provided evidence;
- assumptions and unknowns are clearly separated;
- recommendations are prioritized and include effort, dependencies and risks;
- calculations can be reproduced;
- no production changes or customer communications occurred without authorization.

## 9. What this demonstration does not prove

- It does not prove a real business has this problem.
- It does not prove a buyer will pay for the audit.
- It does not prove the proposed process saves time or money.
- It does not prove an automation is technically or legally suitable.
- It is not a customer testimonial, case study or performance claim.

**Demonstration status:** synthetic example prepared for internal offer design only.

# AI Revenue — Bug Bounty Programme Authorization & Finding Review Template

**Status:** Blank safety and authorization record. No programme or target is authorized by this template.  
**Parent contract:** commercial-opportunity-intake-selection-and-payout-reconciliation-contract.md  
**Company:** AI Revenue Company only.

## 1. Programme identity and authoritative terms
- Programme ID:
- Programme / vendor name:
- Official programme URL:
- Programme platform (if any):
- Terms / policy version:
- Last verified timestamp:
- Official safe-harbour wording reference:
- Official disclosure channel:
- Reward policy and severity rubric reference:
- Source steward / reviewer:
- Terms archive / digest:
- Terms re-check due:

## 2. Researcher and eligibility
- Eligible researcher identity / legal entity:
- Country / residency eligibility:
- Age / account / identity / KYC requirements:
- Tax / payout requirements:
- Employer / contractor / conflict restrictions:
- AI-assisted research permitted?:
- AI disclosure / attribution requirement:
- Personal attestation or signature required?:
- Prior findings / duplicate eligibility:
- Eligibility decision: NOT_ASSESSED / PASS / BLOCKED
- Evidence and reviewer:

## 3. Exact target authorization
- Authorized asset / hostname / app / repository / product:
- Exact scope entry copied from current official policy:
- Asset owner:
- In-scope versions:
- Explicitly excluded assets:
- Third-party / vendor dependencies:
- Authorized test environments:
- Permitted methods:
- Prohibited methods:
- Rate limits / request constraints:
- Test account requirements:
- Test data requirements:
- Data minimization rules:
- Time window / expiry:
- Stop conditions:
- Authorization evidence reference:
- Scope reviewer:
- Scope decision: NOT_AUTHORIZED / AUTHORIZED_FOR_REVIEW_ONLY / AUTHORIZED_FOR_SPECIFIED_TESTS / EXPIRED / REVOKED

**Important:** A programme's existence, general public policy or an asset appearing in a broad list does not establish that a particular researcher, account, asset, method or test is authorized. If any scope or method is ambiguous, do not test.

## 4. Separate owner authorization for live testing
- Proposed test objective:
- Exact asset:
- Exact method:
- Test account / environment:
- Maximum request rate / test volume:
- Data that may be touched:
- Data that must not be accessed:
- Start/end window:
- Monitoring / stop mechanism:
- Incident escalation owner:
- Cost CAD:
- Exact owner approval reference:
- Approver:
- Approval timestamp:
- Expiry:
- Approval status: NOT_REQUESTED / PENDING / APPROVED / DENIED / EXPIRED / REVOKED

No live test may begin without both current programme authorization and separate exact owner approval. This record is not a substitute for programme rules, legal advice or a vendor-issued authorization.

## 5. Safe research plan
- Hypothesis (not a confirmed vulnerability):
- Source-code / local-lab / sandbox / non-invasive method:
- Expected observable result:
- Minimum evidence required:
- Prohibited actions:
- Potential impact and worst-case:
- Stop triggers:
- Data handling / deletion:
- Independent reviewer:
- Plan review: NOT_REVIEWED / PASS / BLOCKED

## 6. Suspected finding record
- Finding ID:
- Discovery timestamp:
- Affected authorized asset/version:
- Suspected vulnerability class:
- Claim statement:
- Reproduction steps limited to authorized scope:
- Preconditions:
- Expected vs observed behavior:
- Minimal proof:
- Data accessed (should be none unless explicitly permitted):
- Potential impact:
- Confidence:
- Known duplicate / prior disclosure check:
- False-positive alternatives:
- Source/evidence references:
- Researcher notes:
- Status: SUSPECTED / NEEDS_REPRODUCTION / REPRODUCED_IN_AUTHORIZED_SCOPE / DUPLICATE / FALSE_POSITIVE / OUT_OF_SCOPE / STOPPED

Do not copy secrets, credentials, personal data or unrelated user content into this record. Stop and follow programme instructions if unexpected sensitive data or production impact occurs.

## 7. Independent technical review
- Reviewer:
- Independence / conflict check:
- Exact scope and policy revision rechecked:
- Reproduction independently completed?:
- Reproduction environment:
- Impact validated?:
- Severity rubric and rationale:
- Duplicate/known issue status:
- False-positive challenge:
- Exploitability evidence safely bounded:
- Remediation relevance:
- Evidence minimization:
- Reviewer decision: NOT_REVIEWED / CONFIRMED_IN_SCOPE / NOT_CONFIRMED / DUPLICATE / OUT_OF_SCOPE / BLOCKED
- Required corrections:
- Review timestamp:

AI-generated suspicion alone is never sufficient. A finding is not confirmed until independently reproducible with human-verifiable evidence.

## 8. Disclosure and submission packet
- Exact report version / digest:
- Programme's current submission endpoint/channel:
- Recipient:
- Required format:
- Impact statement:
- Minimal reproduction:
- Evidence attachments and sanitization review:
- No personal data/secrets check:
- Disclosure embargo / publication restrictions:
- Reward eligibility and caveats:
- Owner approval bound to exact report, recipient and channel:
- Approval reference / expiry:
- Submission status: NOT_PREPARED / READY_FOR_OWNER_REVIEW / APPROVED / SUBMITTED / ACKNOWLEDGED / UNDER_REVIEW / ACCEPTED / REJECTED / DUPLICATE

No disclosure, report submission, public write-up, vendor contact or follow-up is authorized by preparing this packet.

## 9. Award and payment evidence
- Programme outcome / award reference:
- Severity accepted:
- Gross award:
- Award discretion / conditions:
- Payout trigger:
- Payout method and eligibility:
- KYC / tax / withholding:
- Expected payment date:
- Amount received:
- Settlement status:
- Fees / FX / withholding:
- Cleared amount:
- Finance ledger reference:
- Independent reconciliation reviewer:
- Net cleared receipt:
- Final disposition:

Advertised maximum, submitted claim, accepted award and cleared funds are distinct. Only verified cleared funds count as realized revenue.

## 10. Incident / stop record
- Stop trigger:
- Time detected:
- Asset / method:
- Unexpected data or impact:
- Actions stopped:
- Minimum evidence preserved:
- Programme stop/report requirement:
- Internal escalation:
- Incident record ID:
- Remediation / recovery authority:
- Closeout and reviewer:

**Blank template non-claim:** No bug bounty programme is selected or authorized, no live test is approved, no vulnerability is asserted, no report is submitted and no reward or revenue is claimed.

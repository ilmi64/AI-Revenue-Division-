# AI Revenue — Commercial Opportunity Intake, Selection & Payout Reconciliation Contract

**Status:** Architecture contract; not an active intake queue, bounty account, customer pipeline or revenue ledger.  
**Company:** AI Revenue Company only.  
**Owner:** CRO / Revenue Operations, with CFO and division-owner review.  
**Budget:** CAD $0 incremental by default.  
**Authority:** Research may discover and recommend. Internal analysis may proceed within approved free/offline resources. External contact, account registration, accepting programme terms, customer proposals, bounty submissions, vulnerability disclosure, publication, contracts, invoices, payments and other commitments require explicit owner approval.

## 1. Purpose and scope

Provide one traceable lifecycle for every AI Revenue opportunity, including:
- commissioned software engineering, website/app work, bug fixes, features and maintenance;
- GitHub/open-source coding bounties, technical challenges, hackathons and AI/data/ML challenges;
- paid bug bounty and coordinated vulnerability disclosure programmes;
- AI automation and business solutions;
- AI Creative Studio production;
- digital products, SaaS, subscriptions and licensing;
- paid research/intelligence services;
- SEO, content, recurring marketing, maintenance and support services;
- capital-light commercial intelligence and other approved portfolio opportunities.

This contract complements, and does not replace:
- ai-revenue-stream-catalogue-and-governance.md (portfolio and historical disposition);
- revenue-first-commercialization-plan.md (commercial sequencing and first-offer preparation);
- prospect-qualification-and-validation-framework.md (customer validation);
- delivery/ai-revenue-engagement-delivery-record-template.md (authorized customer engagement delivery);
- ai-revenue-delivery-qa-acceptance-and-time-capture-standard.md (delivery quality/economics);
- Research & Intelligence intake/source/evidence contracts (research provenance and recipient scope).

An opportunity is not an offer, contract, authorized engagement, accepted bounty, receivable or revenue merely because it is recorded.

## 2. Core records and identifiers

Every opportunity receives an immutable ID, e.g. OPP-YYYY-NNNNN. Child work items and deliverables reference the parent ID; do not reuse IDs or silently overwrite history.

Required record groups:

### 2.1 Discovery and source
- Opportunity ID, title, opportunity family, division, discovery date and discoverer.
- Canonical source URL/reference, source owner/publisher, source type, retrieval timestamp and content revision/digest where available.
- Official terms/rules/brief, version and last-checked timestamp.
- Deadline, expiry, submission window and required milestones.
- Source reliability, provenance, permitted use, known limitations and source-steward review.

### 2.2 Eligibility and legal/ethical scope
- Company and individual claimant eligibility; jurisdiction/residency; age/identity/KYC requirements where relevant.
- Whether the owner or authorized researcher must personally register, attest, sign, certify or perform any step.
- Programme/customer terms, licence, IP assignment, confidentiality, NDA, exclusivity, indemnity, dispute, disclosure and tax conditions.
- Required qualifications, certifications, competition restrictions, prior-work rules, duplicate rules and conflicts of interest.
- Privacy, data classification, security authorization, halal/Shafi'i issue flags and qualified-review needs.
- Explicit prohibited activities, assets, methods, data and environments.

If eligibility, legal authority, IP/licence, payment terms, permitted scope or cost cannot be established, mark BLOCKED; do not proceed on assumptions.

### 2.3 Scope, effort and economics
- Buyer/programme, problem, expected deliverable, acceptance criteria, exclusions and success evidence.
- Required skills, estimated active hours, elapsed time, review/rework allowance and deadline feasibility.
- Tool/runtime/data/hosting dependencies, incremental cost and whether each is already available at zero cost.
- Gross advertised amount, award discretion, probability of acceptance/payment, payment timing, currency, fees, withholding, FX, tax and net-receipt assumptions.
- Probability-adjusted expected value and downside, clearly labelled as estimates.
- Opportunity cost, reputation/security risk, maintenance/support tail and reusable IP value.
- Decision: pursue, defer, reject or request clarification, with reason and reviewer.

Do not equate gross prize, advertised bounty, projected subscription value or theoretical contract value with expected or realized income. Unpaid labour is not economically zero.

### 2.4 Approval and accountability
- Accountable division owner and execution lead.
- Independent reviewer/QA owner; reviewer must not approve their own material work.
- Approval reference, exact authorized action/payload, company, target/recipient, scope, limits, expiry and one-time/reusable status.
- Approval status and timestamps.
- Any change to target, scope, deliverable, price, terms, recipient, account, test method or cost invalidates the prior approval for the changed portion and requires re-approval.

An approval to research or prepare is not approval to contact, register, accept terms, submit, publish, deploy, access production, spend or transact.

## 3. Lifecycle and state machine

Use the following states. State changes are append-only, attributable and timestamped; a state cannot be advanced merely to improve a dashboard.

1. DISCOVERED — candidate found; source and discovery time recorded.
2. SOURCE_VERIFIED — canonical source and current terms captured from an authoritative source.
3. ELIGIBILITY_REVIEW — company/claimant/jurisdiction and programme conditions being checked.
4. BLOCKED — hard gate unresolved; no execution or external action.
5. QUALIFIED — scope, acceptance, legal/security/IP, costs, deadline and economics assessed.
6. PRIORITIZED — ranked against other opportunities using time-to-cleared-cash, acceptance/payment probability, zero-upfront fit, effort, risk and strategic reuse.
7. OWNER_APPROVAL_PENDING — exact proposed internal/external action and limits presented for owner decision.
8. APPROVED_FOR_INTERNAL_WORK — only the named internal preparation/execution scope is authorized.
9. INTERNAL_IN_PROGRESS — work occurs only in approved environments and within scope.
10. INDEPENDENT_QA — separate reviewer assesses correctness, completeness, safety, reproducibility, rights and acceptance criteria.
11. READY_FOR_EXTERNAL_ACTION — QA passed; exact payload, recipient, submission method and consequences prepared for owner review.
12. EXTERNAL_ACTION_APPROVED — owner approved the exact action; this status is narrow, scoped and expires as recorded.
13. SUBMITTED_OR_DELIVERED — evidence of actual authorized transmission/delivery recorded.
14. UNDER_REVIEW — recipient/programme evaluating the work.
15. ACCEPTED / PARTIALLY_ACCEPTED / REJECTED / DUPLICATE / OUT_OF_SCOPE — outcome supported by recipient evidence.
16. AWARD_CONFIRMED — award or contractual amount confirmed; still not cleared cash.
17. PAYMENT_PENDING — payable amount and expected date recorded.
18. PAYMENT_RECEIVED_UNCLEARED — receipt observed but settlement/reversal/FX reconciliation incomplete.
19. CLEARED_AND_RECONCILED — funds verified as cleared and matched to company ledger, fees, FX, tax/withholding and costs.
20. CLOSED — outcome, economics, evidence, lessons and residual obligations recorded.

Terminal or exceptional states: DECLINED, EXPIRED, CANCELLED, WITHDRAWN, DISPUTED, UNPAID, ABANDONED. A rejected, duplicate, expired or unpaid opportunity remains in the history and cannot be represented as revenue.

## 4. Opportunity scoring and selection

Hard gates are evaluated before scoring. A high score cannot override illegality, lack of authorization, unclear IP, unsafe data handling, prohibited cost or missing owner approval.

Use a documented 0–5 rating for:
- time to plausible cleared payment;
- probability of acceptance and payment;
- zero-upfront feasibility;
- current capability fit;
- estimated active effort and deadline feasibility;
- buyer/programme and payout reliability;
- legal, privacy, security, platform and IP risk;
- reusability/strategic learning;
- maintenance, support and dispute burden.

Record evidence and rationale for each score. The prioritization is comparative decision support, not a promise or statistical forecast. Prefer narrow, verifiable, low-cost opportunities with clear acceptance and credible payout over large advertised rewards with low probability, high effort or opaque conditions.

## 5. Division-specific acceptance controls

### 5.1 Software engineering and coding contracts
- Confirm requirements, repository/access authority, licence, contribution agreement, IP ownership and permitted dependencies.
- Establish reproducible acceptance criteria, supported versions, security requirements, test expectations, documentation and rollback/maintenance scope.
- Work in a controlled branch or local copy where authorized; do not modify upstream or production systems without explicit permission.
- Preserve provenance of code, dependencies, generated content and third-party assets.
- Independent review must cover correctness, security, maintainability, licence compliance and acceptance criteria.
- Submission, pull-request publication, release, deployment and customer delivery require exact owner approval.

### 5.2 Coding bounties and technical challenges
- Verify whether first-come/first-accepted, competitive, judged, sponsor-discretionary or guaranteed payment; identify duplicate/claimed issue rules.
- Verify whether AI-assisted work is permitted, disclosure is required, and whether claimant identity or authorship attestations must be made personally.
- Confirm submission format, branch/PR requirements, deadline, review process, payout trigger, minimum threshold, dispute process and payment method.
- No fabricated authorship, copied submissions, manipulated rankings, sockpuppet accounts, collusion or multiple claims contrary to rules.
- Never represent a merged PR or completed code as paid until award/payment evidence exists and funds clear.

### 5.3 Bug bounty and vulnerability research
- Use a separate programme/target authorization record containing exact eligible assets, scope boundaries, exclusions, approved methods, rate limits, safe-harbour language, stop conditions, disclosure channel and policy revision.
- Verify the current official programme terms and eligibility before any test. A public programme page alone does not authorize every asset, method, researcher or account.
- Default preparation path: source-code review, local lab, supplied sandbox, test fixture or non-invasive reasoning. Live testing requires exact explicit authorization, approved target/method and a separate owner approval.
- Prohibit arbitrary scanning, credential attacks, phishing, social engineering, persistence, lateral movement, destructive testing, denial of service, data exfiltration, real-user access, privacy invasion and any action outside written scope.
- Stop immediately if unexpected sensitive data, production impact, third-party systems or out-of-scope assets are encountered; preserve minimal evidence and follow the programme's stop/report rules.
- Validate the finding independently; confirm reproducibility, impact, affected versions, prerequisites, exploitability within safe limits, remediation relevance and whether it is already known/duplicate.
- Report only minimum necessary evidence. Never include secrets, personal data or unrelated user content. Do not publish details before authorized disclosure.
- AI-generated suspicion is a lead, not proof. No finding may be submitted as confirmed without human-verifiable evidence and independent review.
- Check reward discretion, duplicate handling, severity rubric, payout timing, KYC, residency, tax, disclosure and IP terms. A maximum reward is not an expected reward.

### 5.4 Creative, marketing and content services
- Verify customer brief, deliverable formats, usage rights, source material, likeness/trademark permissions, revision limits, platform rules and factual claim substantiation.
- No fake testimonials, synthetic endorsements presented as real, deceptive claims, undisclosed sponsorships or guaranteed results.
- Drafting/production is distinct from publication, ad spend, account access and customer delivery; each external action remains separately approved.

### 5.5 Automation and managed services
- Confirm process owner, permitted data, customer-system authority, integration scopes, error handling, human fallback, logging, retention, incident response, service levels and exit/portability.
- Separate synthetic/offline proof from production deployment. No production credentials, customer data connection, paid API, hosting or automation activation without explicit approval.
- Define ongoing support, monitoring, service availability and liability boundaries before offering recurring service.

### 5.6 Digital products, SaaS and research reports
- Verify demand evidence, source/data rights, IP ownership, hosting/API economics, security, maintenance and customer support burden.
- Research reports require claim-level provenance, confidence, limitations and independent challenge.
- Do not launch a product, publish a report, open sales or activate subscriptions without explicit approval.

## 6. Independent QA and external-action packet

Before an external submission/delivery, the packet must contain:
- opportunity ID and current terms revision;
- exact target, recipient, channel and action;
- deliverable version/hash and complete acceptance checklist;
- evidence/provenance and reproducibility instructions;
- independent reviewer decision and unresolved defects;
- legal/security/privacy/IP/halal review flags and disposition;
- cost and dependency statement (including CAD $0 confirmation or approved amount);
- expected payment mechanics and caveats;
- owner approval bound to the exact action and payload;
- rollback/withdrawal or incident stop plan where applicable.

Any material payload or terms change requires new review and approval. Host success or submission receipt is not proof of acceptance or payment.

## 7. Payment and revenue reconciliation

Maintain separate values and evidence for:
- advertised maximum/prize/bounty;
- internal probability-adjusted expected value;
- amount submitted/claimed;
- amount accepted/awarded;
- amount invoiced or payable;
- amount received but uncleared;
- amount cleared;
- fees, platform charges, withholding, tax, FX spread and other direct costs;
- net cash received and contribution after measured delivery costs.

CLEARED_AND_RECONCILED requires:
1. evidence of the payment receipt in the authorized company-controlled account/ledger;
2. settlement status confirmed, with reversibility/chargeback/hold risk addressed;
3. currency and FX conversion reconciled;
4. fees and withholding recorded;
5. opportunity ID matched to ledger entry;
6. CFO/finance reviewer and independent evidence check;
7. any contractual/tax/accounting treatment flagged for qualified review.

Do not ask for or place bank credentials, passwords, private keys, seed phrases or MFA codes in agent prompts or work records. No payment collection, transfer, withdrawal or financial transaction is authorized by this contract.

## 8. Portfolio dashboard and reporting

The dashboard should report, by division and opportunity family:
- counts by state and ageing;
- source/terms freshness and eligibility review status;
- qualified opportunities by expected effort and risk;
- owner-approval queue and expiry;
- active work-in-progress and independent QA capacity;
- submitted, accepted, rejected, duplicate, disputed and unpaid outcomes;
- gross award versus actual cleared receipts and net contribution;
- time-to-first-cleared-payment and actual delivery hours;
- rejection/rework/root-cause trends;
- recurring revenue, renewals, churn and support load where applicable.

Never combine pipeline, advertised rewards, accepted awards, receivables and cleared cash into one “revenue” number. Report actual cash separately from estimates.

## 9. Company and data boundaries

- All opportunity records belong to AI Revenue's tenant and company ledger.
- Trading & Technology records, private strategies, wallet data and treasury are not accessible through this contract.
- Shared R&I may deliver only scoped, approved, sanitized public-source intelligence; it does not receive default access to AI Revenue private pipeline or customer data.
- Main Hub/OCC receives only approved status summaries and evidence references; it cannot approve or execute commercial actions.
- Customer, programme, source and vulnerability information is classified and access-limited; confidential reports are never reused as public portfolio material without explicit rights and approval.

## 10. Current implementation status and next gates

DESIGNED / NOT OPERATIONAL. No automated opportunity queue, scoring engine, bounty registry, bug bounty account, customer CRM, payout integration or commercial ledger is implemented or activated by this document. No programme has been selected, no bounty submitted, no vulnerability testing performed and no cleared revenue claimed.

Architecture-only next steps:
1. Assign stable record schemas and interface owners.
2. Map existing customer engagement and R&I records to this contract without conflating research intake with commercial opportunity state.
3. Create a blank opportunity dossier and independent QA checklist.
4. Prepare a source registry seed from official programme pages only after a separate research work order; verify terms at time of use.
5. Define ledger reconciliation evidence without connecting payment accounts.
6. Conduct an authorized synthetic tabletop only if separately approved; do not run tests or contact external parties.

**Non-authorization:** This contract does not authorize account creation, programme acceptance, live vulnerability testing, repository changes in third-party projects, customer/programme contact, bounty submissions, publication, spending, payment actions, deployments or production access.

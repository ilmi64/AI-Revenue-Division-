# Zero-Upfront Technical Revenue Opportunity Screen — 2026-11-21

**Company:** AI Revenue  
**Workstream:** Research & Intelligence → Commercial Opportunity Acquisition  
**Status:** RESEARCH SCREEN COMPLETE; NO OPPORTUNITY APPROVED FOR EXECUTION  
**Prepared:** 2026-11-21  
**Budget constraint:** CAD $0 incremental spend  
**Scope:** Software/coding bounties, open-source contributor funding, and bug-bounty programmes.  
**Authority:** Internal research only. This record does not authorize account creation, acceptance of programme terms, code contribution to an external repository, security testing, disclosure, submission, customer contact, or any financial action.

## 1. Executive decision

The research does **not** support treating a headline bounty or a platform's historical payout list as a currently available, payable opportunity. The first screen found:

1. **GitHub Sponsors is a viable Canada-supported contributor-funding route**, but it is sponsorship-based, not a guaranteed issue bounty or quick-cash route. It requires approval, bank and tax information, and 2FA.
2. **HackerOne is the strongest currently evidenced AI-compatible bug-bounty platform route** in this screen: its current Code of Conduct explicitly permits responsible AI-assisted research, while requiring human validation, reproducible proof, program-specific compliance, and a human-in-the-loop model. Payout setup requires identity verification, a payment method and approved tax form. Actual Meta programme eligibility, current scope and payout terms remain unverified.
3. **Meta Bug Bounty remains a named priority candidate, not an approved target.** Meta's official portal was located but returned HTTP 429 during this review, preventing verification of the current programme rules, assets, payout schedule, researcher eligibility and safe-harbour terms. Meta's official 2025 report describes the bug-bounty programme and reports more than US$2.3 million in bounties awarded during 2024; this historical aggregate does not establish current programme availability or an expected reward.
4. **Algora / ProjectDiscovery is a proven historical payout route but the surfaced example issues are already closed and paid.** The platform discovery page showed apparent bounty availability for two issues, but direct GitHub issue inspection showed the issues closed; Algora's own completed-bounties page confirms the two awards were paid. This is a concrete false-positive/staleness lesson: never select work from a discovery card without checking the canonical issue and reward state.
5. **Immunefi is HOLD for AI Revenue's initial acquisition queue.** Its current rules prohibit mainnet/public-testnet contract testing, high-volume automated testing, and AI-generated/automated scanner reports that lack demonstrated asset-specific impact; its guidance sets a high proof-of-concept and originality bar. Program-specific KYC/payment terms also need review. Do not infer that general AI use is approved.
6. **Code4rena is excluded from the zero-upfront queue** because its published bounty instructions require a US$25 USDC deposit per submission. That fails the CAD $0/no-deposit constraint even before evaluating current programme availability.
7. **IssueHunt remains a discovery candidate only.** Its public description supports funded issue discovery and reward after accepted PRs, but this screen did not verify a specific currently funded issue, payout mechanics, Canadian eligibility or fee schedule. No work should be selected from it until those checks are complete.

**Immediate acquisition strategy:** prioritize paid, bounded software/coding work with clearly funded, still-open issues and verifiable acceptance/payout terms; develop GitHub Sponsors as a slower contributor-funding channel; pursue bug-bounty research only through a current, explicitly authorised programme with clear scope and payout terms. Do not forecast any of these as revenue until funds are actually received and cleared.

## 2. Ranked route assessment

| Rank | Route | Evidence and fit | Main blockers / risk | Decision |
|---|---|---|---|---|
| 1 | Algora-funded open-source issues | Algora's ProjectDiscovery page documents historical cash awards, including US$25–US$250 examples and 224 total payouts on the viewed page. This demonstrates the platform has processed real contributor awards. | The two apparently available Nuclei issues checked in this review were closed; Algora's own completed list shows them paid. Current open issue, reward availability, claimant competition and Canadian payout eligibility must be rechecked per issue. | **NEXT DISCOVERY TARGET; no issue selected yet.** |
| 2 | GitHub Sponsors | Canada appears in GitHub's supported payout regions. Contributions may include code, issue triage, documentation, project management and design. Personal-account sponsorships have no GitHub platform fee. | Sponsorship is discretionary and relationship/reputation-driven, not an immediate bounty. Requires approved profile, bank and tax details, and 2FA. No sponsor or payout is secured. | **BUILD IN PARALLEL as a longer-term channel.** |
| 3 | HackerOne public bug-bounty programmes, including Meta if current terms qualify | Current HackerOne policy permits responsible AI-assisted research with human validation and reproducible PoC. Published payment guidance describes bank transfer in local currency, 1–10 day processing, and PayPal/crypto alternatives, subject to method thresholds and setup. | Identity verification, valid payment method and approved tax form required. Individual programme scope, AI limits, eligibility and award discretion govern. Meta's current programme page could not be fetched during this review. Security research has high skill, legal and safety risk and uncertain time-to-reward. | **CONDITIONAL CANDIDATE; no testing or submission.** |
| 4 | IssueHunt | Public platform describes funded open-source issues, PR submission and reward following acceptance. | No current funded issue or complete payout/eligibility terms independently verified in this screen. | **WATCHLIST ONLY.** |
| 5 | Immunefi | Large Web3 bounty ecosystem and public programme listings. | Rules ban mainnet/public-testnet contract testing and prohibit low-quality AI-generated/automated scanner reports; require original, high-quality, impact-grounded reports and applicable PoCs. KYC and USDC payment terms vary by programme. | **HOLD; not an initial AI-assisted route.** |
| Excluded | Code4rena bounty submissions | Published instructions state a US$25 USDC deposit is required per submission. | Upfront deposit and possible non-refund violate the no-spend/no-deposit constraint. Current programme availability also not established. | **EXCLUDE under current policy.** |

## 3. Evidence register

### 3.1 GitHub Sponsors — Canada-supported but not guaranteed

- Official contributor eligibility documentation says contributors living in supported regions can receive sponsorships for code, issue triage, documentation, leadership, business development, project management, mentorship and design.
- The official supported-region list includes Canada.
- Official setup requires a completed sponsored-developer profile, bank and tax information, 2FA and GitHub approval.
- GitHub states personal-account sponsorships incur no GitHub platform fee; organization-account sponsorships may incur up to 6%.
- This is a potential recurring/one-time support stream around demonstrable open-source value, not an issue bounty or promised income.
- Links:
  - https://docs.github.com/en/sponsors/receiving-sponsorships-through-github-sponsors/about-github-sponsors-for-open-source-contributors
  - https://docs.github.com/en/sponsors/getting-started-with-github-sponsors/about-github-sponsors
  - https://docs.github.com/en/sponsors/receiving-sponsorships-through-github-sponsors/setting-up-github-sponsors-for-your-personal-account

### 3.2 Algora / ProjectDiscovery — historical payout evidence, stale candidate issue cards

- Algora's ProjectDiscovery community page showed a total of US$35,625 awarded and 47 paid contributors at the time of inspection.
- The Algora completed-bounties page listed ProjectDiscovery/Nuclei issue #6532 as a US$25 award and issue #6674 as a US$100 award, both marked paid approximately eight months before this review.
- The corresponding GitHub issue pages were closed. Their bounty labels/cards were therefore not actionable opportunities despite discovery-page presentation.
- Lesson: an issue is eligible for selection only after checking the canonical repository issue is open, the sponsor's bounty remains active/unclaimed or claimable, the exact amount and acceptance requirements are clear, and the payment route is currently supported.
- Links:
  - https://algora.io/projectdiscovery/bounties/community
  - https://algora.io/projectdiscovery/bounties
  - https://github.com/projectdiscovery/nuclei/issues/6532
  - https://github.com/projectdiscovery/nuclei/issues/6674

### 3.3 HackerOne — AI-assisted research and payout controls

- HackerOne's current Code of Conduct permits and encourages responsible AI use for learning, reconnaissance, vulnerability discovery, PoC development and report improvement.
- AI use does not remove the researcher's responsibility: reports must be accurate, reproducible, impact-grounded and supported by a clear PoC. Human experts must investigate, validate and confirm findings; hackbots must not operate fully autonomously.
- Program rules may be stricter than platform-wide rules. Unsafe testing, excessive traffic, DoS, phishing/social engineering, production data alteration and unapproved access are prohibited absent explicit authorization.
- HackerOne's payment guidance states that monetary awards require identity verification through Veriff, a valid payment method and an approved tax form. It lists bank transfer in local currency with 1–10 day processing and method-specific minimums; PayPal has no stated minimum, while bank-transfer thresholds differ by normal/priority routing.
- These payment details do not prove that any particular program will award a bounty or that every payment route will be available to this researcher; setup and jurisdiction checks are still required.
- Links:
  - https://www.hackerone.com/policies/code-of-conduct
  - https://www.hackerone.com/terms/disclosure-guidelines
  - https://docs.hackerone.com/en/articles/8395720-payment-preferences
  - https://docs.hackerone.com/en/articles/8395787-external-payments

### 3.4 Meta Bug Bounty — programme not yet fully verified

- Meta's official 2025 Responsible Business Practices Report describes its bug-bounty programme and reports more than US$2.3 million awarded during 2024; this historical report does not independently establish the programme's current November 2026 terms.
- Meta's official programme portal, https://bugbounty.meta.com/, was identified, but returned HTTP 429 during this review. The current programme terms could therefore not be read.
- The official Meta vulnerability disclosure policy distinguishes Meta's reporting of third-party vulnerabilities from vulnerabilities in Meta technologies and directs Meta-technology findings to its Bug Bounty Programme.
- Before any research, obtain and archive the current Meta programme terms directly from Meta, including eligible assets, permitted techniques, prohibited tests, safe-harbour language, researcher eligibility, payout criteria and disclosure restrictions.
- Links:
  - https://bugbounty.meta.com/
  - https://www.meta.com/sr/responsible-business-practices-report/
  - https://www.meta.com/ph/legal/security-vulnerability-disclosure-policy/

### 3.5 Immunefi — hold for AI-assisted acquisition

- Current platform rules prohibit mainnet or public-testnet contract testing, high-volume automated testing, phishing/social engineering, out-of-scope attacks and incomplete or low-quality reports.
- The rules also prohibit AI-generated/automated scanner reports that do not supply the required asset-specific impact information. Separate Immunefi guidance has historically warned against submitting AI-generated or automated reports; do not treat AI assistance as approved without reconciling the current platform rules and each programme's terms.
- Some programmes require PoCs and KYC; one reviewed programme page specifies USD-denominated awards paid in USDC and identity checks for critical findings. Payment and eligibility are programme-specific.
- Links:
  - https://immunefi.com/rules/
  - https://immunefi.com/common-vulnerabilities-to-exclude/
  - https://immunefi.com/bug-bounty/immunefi/information/

### 3.6 Code4rena — upfront deposit disqualifies

- Published Code4rena bounty instructions state each bounty submission requires a US$25 USDC deposit, which may not be refunded for unsatisfactory/spam submissions.
- This is incompatible with the current zero-upfront-spend constraint.
- Link: https://docs.code4rena.com/bounties

### 3.7 IssueHunt — incomplete verification

- IssueHunt describes an issue-based bounty platform where contributors find funded issues, submit PRs and receive rewards based on accepted work and available funds.
- This review did not verify a currently live funded issue or complete payout/fee/Canada eligibility terms.
- Link: https://oss.issuehunt.io/


### 3.8 Additional live GitHub issue checks — no zero-cost execution candidate yet

A second pass queried currently open GitHub issues carrying bounty signals and fetched the canonical issue bodies and comment histories. This reduced several apparent opportunities to the following dispositions:

- **Paraspell / xcm-tools #2591** — open and labelled `Bug bounty`, with a concrete Polkadot.js/Hydration fee-asset bug description. However, the issue body and available comment history do not state a reward amount, a funded escrow, payment asset/network, acceptance/payout conditions, or explicit confirmation that external contributors are invited. A public bounty label alone is insufficient. **Status: WATCH / TERMS UNVERIFIED; do not begin work.**
  - https://github.com/paraspell/xcm-tools/issues/2591
- **Claude Builders Bounty #5** — open and advertises US$200 for an n8n weekly GitHub summary workflow, payable on merge. Its acceptance criteria explicitly require the Anthropic Claude API and a successful run on a real n8n instance. The paid API requirement conflicts with CAD $0/no paid API usage; the exact current Opire payout and eligibility terms also need independent verification. **Status: BLOCKED BY PAID API / EXCLUDE FROM CURRENT ZERO-SPEND QUEUE.**
  - https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5
- **Githoney documentation #3** — issue remains open and has a bounty label, but its bot history records a 10 ADA bounty with a January 20, 2025 deadline and a later merged-PR message stating the bounty was closed. **Status: STALE / CLOSED REWARD; EXCLUDE.**
  - https://github.com/githoney-io/documentation/issues/3
- **Lateralus language #447** — open issue with a substantive compiler defect description, but no verified funded reward or payout terms were present in the fetched issue record. A proposed autonomous solution comment is not sponsor authorization or evidence of a bounty. **Status: UNFUNDED / TERMS UNVERIFIED; WATCH ONLY.**
  - https://github.com/bad-antics/lateralus-lang/issues/447
- **Paid Lean mathematics #223** — open research coordination issue, but the body describes multiple distinct prize sources and requirements; no single bounded, Canada-eligible, zero-upfront, payment-ready task was established in this screen. It also has a high and uncertain proof-effort profile. **Status: DEFER pending exact prize-specific terms and effort assessment.**
  - https://github.com/1337isnot1337/solved-conjectures/issues/223

**Screen result:** despite several open issues carrying bounty signals, this pass has not yet verified a currently funded, claimable, Canada-eligible, zero-upfront coding issue with complete payment terms. This is a discovery gap, not a reason to lower the selection standard or begin unpaid work speculatively.

## 4. Execution gates and zero-cost operating rules

No external work starts until the individual opportunity dossier contains:

1. Canonical source URL and a dated evidence capture.
2. Canonical issue/program identifier and a fresh open/active status check.
3. Exact reward, currency, sponsor identity and remaining funding/claim state.
4. Contributor eligibility for a Canada/Ontario-based individual, including age, residency, sanctions and account requirements.
5. Written platform/program AI policy and any limits on AI, agents, scanners, automation or third-party assistance.
6. Scope, allowed methods, exclusions, disclosure/embargo requirements and safe-harbour coverage where security research is involved.
7. Acceptance criteria, reviewer/maintainer process, expected time, competition/duplicate risk and realistic effort estimate.
8. Payment method, KYC/tax requirements, payout threshold, currency conversion, fees and realistic time to cleared funds.
9. IP/licence terms and ownership of pre-existing tools, code, templates and work product.
10. A risk-adjusted effort/value assessment and an explicit owner approval record.

**Hard stops:** no deposits, paid subscriptions, paid APIs, payment-backed trials, paid hosting, purchases, account/permission changes, external contact, accepting contracts/terms, live security testing, production access, pull-request submission, disclosure or other external action without the required explicit owner approval. No unauthorized scanning, exploitation, credential attacks, phishing, social engineering, persistence, lateral movement, destructive testing, denial of service, data exfiltration or access to real-user data.

## 5. Opportunity economics and reporting discipline

- Expected reward is not revenue.
- A bounty advertised by a platform is not secured capital.
- A claimed or submitted reward is not an award.
- An award is not cleared cash.
- Only funds received, cleared and reconciled may enter realized revenue.
- Estimate net value after platform/payment fees, currency conversion, tax obligations, tool cost (must be zero unless approved), effort, review latency, rejection/duplicate risk and opportunity cost.
- Do not use headline maximum rewards as the base case. Where no reliable acceptance probability exists, report it as unknown and avoid manufacturing expected-value estimates.

## 6. Next sprint work orders

### R&I-WO-AR-TECH-001 — Live funded coding bounty discovery
**Priority:** P0  
Search Algora and other zero-upfront contributor platforms for genuinely open funded issues. Check every candidate on the canonical GitHub issue and sponsor page; reject closed, already paid, claimed, stale, unfunded, unclear or technically mismatched tasks. Confirm Canadian payout terms and AI policy before ranking. Deliver a maximum five-item shortlist with exact acceptance criteria and evidence.

### R&I-WO-AR-BB-001 — Meta and HackerOne programme eligibility
**Priority:** P0  
Retrieve the current Meta programme policy and identify a small set of public HackerOne programmes whose AI rules, Canada eligibility, scope, payout and safe-harbour terms can be fully verified. Do not test or submit. Deliver programme-specific authorization dossiers.

### R&I-WO-AR-OSS-001 — GitHub Sponsors readiness
**Priority:** P1  
Assess the existing public GitHub portfolio and contribution evidence for a compliant sponsored-contributor profile. Prepare profile copy and a contribution portfolio draft only; do not publish or submit an application without owner approval.

### R&I-WO-AR-DELIVERY-001 — First paid engineering/service offer
**Priority:** P0  
In parallel with bounty discovery, identify zero-upfront, clearly scoped software/automation deliverables that can be sold as a direct service without requiring paid infrastructure. Reconcile the first offer with existing delivery QA, economics and approval gates. No customer outreach or pricing commitment until owner approval and the required rehearsal/economics evidence exist.

## 7. Current status

| Item | Status |
|---|---|
| Official source research | Completed for this initial screen |
| Canada eligibility | Confirmed for GitHub Sponsors supported-region list; not yet confirmed for individual bounty programmes |
| Current live funded coding issue | Not verified |
| Meta current policy and exact eligibility | Not verified; official portal fetch blocked during this review |
| HackerOne platform AI policy | Verified at platform level; programme-specific terms still required |
| Immunefi fit | Hold |
| Code4rena fit | Excluded due deposit |
| External account setup / terms accepted | Not performed |
| External code contribution / security testing / submission | Not performed |
| Owner approval | Not requested or granted |
| Cleared revenue | CAD $0 evidenced by this research |

**Next action:** execute R&I-WO-AR-TECH-001 and R&I-WO-AR-BB-001 in parallel, then convert only fully verified candidates into individual opportunity dossiers for owner review.

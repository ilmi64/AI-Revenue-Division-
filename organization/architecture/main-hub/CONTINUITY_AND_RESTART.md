# Organization continuity and restart register — draft v1
Date: 2026-11-22
Status: DRAFT FOR REVIEW. No claim of completed launch, deployed agent runner or tested Codex dispatcher.

## Continuity objective
Preserve source, decisions, current blockers and restart instructions independently of a ChatGPT subscription. GitHub is the durable source of versioned engineering artifacts; this register must not contain credentials, personal secrets or customer data. Repository availability still depends on the GitHub account and GitHub service.

## Operating model (approved direction)
- Main Hub/OCC: shared, read-only oversight and audit; no authority over company treasuries, customer data, credentials or trading execution.
- Research & Intelligence: company-scoped research, reviewed publication and continuous coverage design.
- AI Revenue: standalone AI-operated commercial company with its own independent launch and governance; coding, QA, research, permitted bounties and commercial delivery opportunities in scope for future work.
- Trading & Technology: standalone company; paper-mode safety and market/data verification before any separate authorization for live trading.
- Both companies build in parallel and can launch independently. Shared infrastructure must not create shared private authority or a prerequisite for either company.
- Zero-upfront-cost preference; no paid services, API spend, deployments, live trades, merges or external customer contact without explicit approval.
- Target: January 2027 launch window (preferred January 4–8), per explicit user decisions on 2026-11-22. December 2026 acceleration CANCELLED. December is the full integration, testing, hardening and operational-readiness cycle, not merely minimum viable scope. If justified by incomplete reliability, security, revenue-workflow or independent-company readiness gates, extend to mid-January (January 11–22) or late January (January 25–29). Both companies remain independent; no launch date overrides mandatory approval, financial, legal or operational safeguards. Noncritical enhancements may continue after launch.

## Current verified GitHub handoff artifacts
AI Revenue repository: https://github.com/ilmi64/AI-Revenue-Division-
- Issue #24: QA and R&I recipient-isolation offline verification.
- Issue #25: OCC M2 fixture parity offline verification.
- Issue #26: offline issue-handoff validator and dispatcher gate.
- Draft PR #27: root AGENTS.md on default-line review branch; NOT MERGED.
- Draft PR #28: offline handoff validator, dispatch gate and design; NOT MERGED. Python tests authored, not confirmed executed.
Trading repository: https://github.com/ilmi64/Solana-memecoins
- Issue #71: paper-veto and Gold intake verification.
- Draft PR #72: root AGENTS.md on default-line review branch; NOT MERGED.
- Existing paper and Gold implementation branches require exact-source tests.
- The Codex Cloud automatic task-start connection remains UNVERIFIED / NOT ENABLED.
- GitHub Issues are a handoff queue, not an automatic runner.

## Restart protocol after any ChatGPT plan interruption
1. Sign in to GitHub independently and open the two repository URLs above. Check open issues and draft PRs.
2. Read this register, then review the current main branch and all relevant task branches. Never assume draft PRs have been merged.
3. Prioritize exact-source offline tests and safety gates for #24, #25 and #71, followed by #26. Record actual test commands, counts and commit SHAs.
4. Review AGENTS.md PRs #27 and #72; merge only after explicit authorization and review.
5. Confirm available supported Codex Cloud task-start interface. If none exists, continue using issue-based manual starts. Never claim automation without a real authenticated run and GitHub status readback.
6. Keep both companies independent and maintain day/night research coverage as an operating goal, not a claim of running 24/7 services.
7. Reconstruct missing decisions from the decision registers and previous approved project records before changing scope. Do not substitute guesses for missing history.

## Backup and exit plan
- Keep work product as committed Markdown/code/tests in GitHub, not only in chats.
- Export ChatGPT account data from the app/settings when available and store the archive privately, separate from public repositories. This register is not a full chat export.
- Maintain an independent copy of each repository (Git clone or GitHub ZIP export) and any important issue/PR descriptions; a Git ZIP does not preserve Git history or GitHub Issues.
- Keep recovery methods for GitHub access current, with private offline copies of recovery codes; never commit secrets.
- Before any subscription interruption, capture an updated status snapshot: branch SHAs, open issues, draft PRs, blockers, and exact next actions.

## Known gaps
- No independently verified cloud Codex dispatcher or automatic GitHub issue-to-task launch.
- Full Python test suites not yet evidenced as executed.
- This register summarizes known decisions but does not prove complete capture of every past conversation or repository.

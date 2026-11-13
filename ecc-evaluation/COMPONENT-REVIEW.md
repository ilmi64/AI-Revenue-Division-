# ECC Component Review — 2026-11-13

Repository under evaluation: https://github.com/affaan-m/ECC
Reviewed upstream license: MIT (Copyright 2026 Affaan Mustafa)
Upstream source reviewed from the official repository's `main` branch. Upstream may change; pin a commit before any future import.

## Executive decision

**Conditional GO for a small, documentation-only adaptation. NO-GO for installing the complete plugin, hooks, MCP configuration, or running ECC installer scripts in this GitHub Actions pilot.**

The four selected skills are relevant, but they are guidance documents, not drop-in agents. They need tailoring to this repository and our explicit approval model.

## Component findings

### 1. `skills/security-review/SKILL.md`

**Value:** High. Covers secret handling, input validation, injection, authorization, XSS, CSRF, rate limiting, logging, and blockchain-related checks.

**Risks / required tailoring:**
- Contains framework-specific examples (TypeScript, Next.js, Supabase, Express) that do not directly map to this Python research agent.
- Some recommendations are context-dependent rather than universal (for example, token storage and cookie/CSRF patterns); must be validated against the actual architecture.
- Includes example code for sensitive operations. Treat as illustrative, not as executable code or an authoritative security standard.
- Its broad checklist needs a least-privilege / no-secrets / no-external-write gate aligned to our workflow.

**Decision:** Adapt principles only; do not copy framework-specific examples as policy.

### 2. `skills/tdd-workflow/SKILL.md`

**Value:** High. Strong RED/GREEN/refactor discipline, test-runner detection, plan-as-untrusted-input rules, and evidence mapping.

**Risks / required tailoring:**
- Recommends 80% coverage as a general target; coverage is a signal, not proof of correctness, and the current pilot may not have meaningful E2E coverage.
- Mentions running helper scripts and package-manager detection from a trusted ECC checkout. We will not execute these during evaluation.
- Explicitly flags shell commands, network installers, and chained commands for human review; preserve this.
- Recommends checkpoint commits during TDD; our normal PR workflow should avoid excessive commits and retain test evidence in reports instead.

**Decision:** Adapt RED/GREEN and untrusted-plan safeguards; omit installer/helper execution and rigid coverage claims.

### 3. `skills/verification-loop/SKILL.md`

**Value:** High. Six phases: build, type check, lint, tests, security scan, and diff review. Importantly, it distinguishes local checks from target-environment acceptance.

**Risks / required tailoring:**
- Sample commands are JavaScript/Python mixed and assume tools that may not be installed.
- Shell pipelines and grep checks are incomplete security scans; they must not be represented as comprehensive secret or vulnerability detection.
- It includes a continuous-mode suggestion; we will not create a new schedule or persistent service from this.
- The workflow should use only commands explicitly allowlisted by this repository.

**Decision:** Adapt its reporting structure and separate local vs target verification. Resolve actual project commands from repository configuration before running anything.

### 4. `skills/market-research/SKILL.md`

**Value:** Very high for Research Radar. It requires sourced claims, recent data, contrarian evidence, clear separation of fact/inference/recommendation, and decision-oriented output.

**Risks / required tailoring:**
- Its examples mention market sizing and investor diligence beyond the current release-metadata pilot.
- It references other research capabilities; do not assume the referenced tools or MCP servers are installed.
- It correctly treats fetched sources as untrusted data and forbids a source from authorizing outbound actions.

**Decision:** Adapt its source attribution, freshness, counter-evidence, and untrusted-source rules for Research Radar.

## Security and licensing

- Upstream LICENSE is MIT. Preserve copyright and licence notices if any substantial portion is copied or adapted.
- No executable scripts, hooks, MCP servers, credentials, or third-party packages were imported or run for this review.
- No external write permissions were granted.
- No repository secrets were read or changed.
- No live account, trading, publishing, payment, or production action is in scope.

## Compatibility finding

The official ECC Codex documentation describes native installation through Codex CLI marketplace/plugin commands and states a Codex version requirement. A GitHub Actions runner and a GitHub repository connection do not, by themselves, install the Codex plugin or provide a Codex runtime.

Therefore this pilot can safely evaluate reviewed skill guidance in source control, but cannot claim that the ECC Codex plugin is installed or active.

## Proposed next step

Prepare a small, original, repository-specific guidance pack in this branch:
1. `security-review`: Python/read-only workflow checks and explicit approval boundaries.
2. `tdd-workflow`: test-first changes, without ECC installer scripts or automatic checkpoint commits.
3. `verification-loop`: evidence report using only repository-approved test commands.
4. `research-quality`: source freshness, citations, counter-evidence, uncertainty, and prompt-injection resistance.

Keep these as documentation only. Test them by reviewing the next Research Radar report and test run. Do not add executable hooks, MCP servers, or full ECC plugin files. Do not merge to `main` without separate approval.

## Sources reviewed

- https://github.com/affaan-m/ECC/blob/main/LICENSE
- https://github.com/affaan-m/ECC/blob/main/skills/security-review/SKILL.md
- https://github.com/affaan-m/ECC/blob/main/skills/tdd-workflow/SKILL.md
- https://github.com/affaan-m/ECC/blob/main/skills/verification-loop/SKILL.md
- https://github.com/affaan-m/ECC/blob/main/skills/market-research/SKILL.md
- https://github.com/affaan-m/ECC/blob/main/.codex-plugin/README.md

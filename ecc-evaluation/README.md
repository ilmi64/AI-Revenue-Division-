# ECC Selective Evaluation

Status: evaluation only. This branch does not install or execute ECC components.

## Upstream
- Official project: https://github.com/affaan-m/ECC
- License: MIT (verify the upstream LICENSE at the time of vendoring)
- Review upstream security guidance before importing executable components.

## Proposed minimal skill set
1. `security-review` — review agent instructions, permissions, secrets handling, and workflow boundaries.
2. `tdd-workflow` — strengthen tests before implementation changes.
3. `verification-loop` — standardize test, lint, typecheck, and security verification.
4. `market-research` — improve source-attributed research briefs.

## Explicit exclusions for this pilot
- No hooks or shell scripts.
- No MCP server configuration or new connectors.
- No external API keys, paid services, or hosted services.
- No automatic posting, publishing, purchases, trading, account changes, or production writes.
- No changes to the existing Printify Store Analyst.
- No merge to main without separate owner approval.

## Test plan
1. Inspect each selected upstream skill and its referenced files.
2. Review all instructions for prompt injection, secret exposure, unsafe commands, and unintended external actions.
3. Import only the reviewed skill documentation into this branch.
4. Run the existing unit tests and Research Radar workflow.
5. Compare output quality and security behavior against the pre-ECC baseline.
6. Produce a report; do not merge unless separately approved.

## Environment compatibility
ECC's Codex integration targets Codex App/CLI environments. A GitHub repository connection alone does not install or execute Codex plugins, skills, or hooks. This repository evaluation is therefore a source-controlled, manually reviewed subset, not a claim that ECC is installed in ChatGPT.


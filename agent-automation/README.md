# AI Agent & Automation Division

## Purpose
Provide a zero-upfront-cost, governed agent and workflow layer for the organisation. The division supports all business units without replacing their existing systems or granting agents unrestricted authority.

## Current implementation decision
- **Existing automation control plane:** Make, using the connected account and existing scenarios.
- **Development and scheduled-code layer:** GitHub Actions in the existing public repository, using standard public runners.
- **Local AI runtime candidate:** Ollama running temporarily inside the GitHub Actions runner.
- **Model candidate:** Qwen2.5 1.5B through Ollama; the selected model is listed under Apache 2.0. The model is small and its analysis must be treated as a draft.
- **Workflow platform candidate:** Activepieces Community Edition, subject to a separate always-on hosting feasibility review.
- **Knowledge/agent application candidate:** Dify Community Edition, subject to hosting feasibility.
- **No paid API or persistent server is assumed.**

## Cost and device reality
The repository is public, so standard GitHub-hosted runners are currently documented as free and unlimited for public repositories. The workflow uses an ephemeral runner and deletes the model with the runner after the job. No paid hosting, API key, account credential, or persistent server is required for this pilot. GitHub policy and plan terms must be rechecked before scaling use.

The owner's Android phone/tablet are not treated as a reliable always-on Docker host. A persistent Activepieces or Dify deployment still needs a separately approved host.

## First pilot: Local AI Research Radar
A read-only GitHub Actions workflow:
1. Collects latest stable release metadata from official Activepieces, Dify, n8n, and Ollama repositories.
2. Runs unit tests.
3. Starts a pinned Ollama version in the temporary runner.
4. Downloads Qwen2.5 1.5B and performs local inference without a paid AI API.
5. Produces Markdown and JSON reports as a downloadable workflow artifact.

The AI receives public release notes as untrusted data, is instructed not to follow embedded instructions, and cannot access credentials or perform external write actions. Its analysis is a draft and must be checked against source links.

## Limitations
This is a narrow AI research assistant, not yet a multi-agent orchestration platform. It runs only when GitHub Actions executes; it does not remain online between runs. Small-model quality, CPU runtime, Ollama installation, and GitHub Actions execution must be validated in the first workflow run before expansion.

## Division map
- [Agent charters](agent-charters.md)
- [Security and approval policy](security-and-approval-policy.md)
- [Implementation roadmap](implementation-roadmap.md)
- [Research Radar collector](research_radar.py)
- [Multi-lane revenue source registry](REVENUE-LANE-REGISTRY.md)
- [Revenue lane registry validator](validate_revenue_lane_registry.py)
- [Local AI research agent](ai_research_agent.py)

## Status
Implementation is on the agent-automation-foundation branch in a draft PR. No production deployment, external account connection, paid service, or live business action has been performed.

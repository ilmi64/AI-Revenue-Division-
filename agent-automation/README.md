# AI Agent & Automation Division

## Purpose
Provide a zero-upfront-cost, governed agent and workflow layer for the organisation. The division supports all business units without replacing their existing systems or granting agents unrestricted authority.

## Current implementation decision
- **Existing automation control plane:** Make, using the connected account and existing scenarios.
- **Development and scheduled-code layer:** GitHub Actions in the organisation's existing repositories, within free-tier limits.
- **Candidate self-hosted agent platform:** Activepieces Community Edition, the first candidate for a later deployment.
- **Knowledge/agent application candidate:** Dify Community Edition, subject to hosting and model-cost feasibility.
- **Not selected yet:** no new platform is installed, deployed, connected to accounts, or activated by this repository change.

## Cost and device reality
Software may be free while hosting, electricity, storage, model inference, API calls, data transfer, or domains are not. No paid hosting or model API is assumed. The owner's Android phone/tablet are not treated as a reliable always-on Docker host.

## First pilot: Research Radar
A read-only GitHub Actions workflow collects latest stable release metadata from official Activepieces, Dify, n8n, and Ollama repositories. It runs weekly and can also be started manually. It uses Python's standard library, public GitHub endpoints, no LLM, no API key, no credentials, and no external write actions. It produces Markdown and JSON artifacts for human review.

This is an automated research collector, **not yet a generative AI agent**. It creates a useful no-cost automation foundation while model inference and always-on hosting remain unresolved.

## Division map
- [Agent charters](agent-charters.md)
- [Security and approval policy](security-and-approval-policy.md)
- [Implementation roadmap](implementation-roadmap.md)
- [Research Radar script](research-radar.py)

## First AI agent after the pilot
Start with a read-only Research & Reporting Agent. It may gather public information, summarize sources, prepare internal reports, and flag uncertainty. It must not submit applications, contact third parties, publish content, spend money, sign transactions, or change production systems.

## Status
Architecture and governance foundation committed on the agent-automation-foundation branch. Research Radar code and a weekly/manual workflow are added on that branch; workflow execution and runtime deployment still require testing and owner review.

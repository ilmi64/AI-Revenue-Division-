# AI Agent & Automation Division

## Purpose
Provide a zero-upfront-cost, governed agent and workflow layer for the organisation. The division supports all business units without replacing their existing systems or granting agents unrestricted authority.

## Current implementation decision
- **Existing automation control plane:** Make, using the connected account and existing scenarios.
- **Development and scheduled-code layer:** GitHub Actions in the organisation's existing repositories, within free-tier limits.
- **Candidate self-hosted agent platform:** Activepieces Community Edition. It is the first candidate for a later deployment because its Community Edition is MIT-licensed and supports self-hosted flows and agent steps.
- **Knowledge/agent application candidate:** Dify Community Edition, subject to a hosting and model-cost feasibility check.
- **Not selected yet:** no new platform is installed, deployed, connected to accounts, or activated by this repository change.

## Cost and device reality
Software may be free while hosting, electricity, storage, model inference, API calls, data transfer, or domain names are not. No paid hosting or model API is assumed. The owner's current Android phone/tablet are not treated as a reliable always-on Docker host. A real always-on runtime must be identified before agents can run unattended.

## Division map
See:
- [Agent charters](agent-charters.md)
- [Security and approval policy](security-and-approval-policy.md)
- [Implementation roadmap](implementation-roadmap.md)

## First pilot
Start with a read-only **Research & Reporting Agent**. It may gather public information, summarize sources, prepare internal reports, and flag uncertainty. It must not submit applications, contact third parties, publish content, spend money, sign transactions, or change production systems.

## Status
Architecture and governance foundation committed on the 'agent-automation-foundation' branch. Runtime deployment and live agent execution remain pending hosting and model-cost validation plus owner review.

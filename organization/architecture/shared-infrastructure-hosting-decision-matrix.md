# Shared Infrastructure Hosting Decision Matrix

**Assessment date:** 2026-11-21  
**Scope:** Shared technical foundation for AI Revenue and Trading & Technology  
**Status:** Research and architecture planning only. No host is being provisioned or activated.

## Executive decision

There is currently **no verified, zero-cost, persistent, always-on cloud computer** in this shortlist that can be approved as the production host for Paperclip, Ruflo, databases, policy services, and continuous Research & Intelligence operations.

The practical split is:
1. **GitHub Codespaces:** use as the current repository-centred development environment when the personal-account free allowance is available. It is an interactive development workspace, not an always-on production server.
2. **Zo Computer:** retain as the preferred future persistent cloud workstation candidate. Its free tier is a 14-day trial; normal always-on computer access requires a paid plan. Do not start the trial merely to postpone the decision, and do not subscribe under the CAD $0 rule.
3. **Cloudroom:** retain as a possible bounded cloud-agent sandbox, not as a proven always-on server. Public documentation currently conflicts about free-plan availability and session/history behavior; verify actual account entitlement and terms before any use.
4. **Colab and Kaggle:** use only as possible ephemeral notebook/research compute, never as production hosting.
5. **E2B and Rig:** bounded sandbox/desktop candidates with cost or payment constraints; not persistent free hosting.
6. **PequeRoku:** self-hosted VM-lab software requiring separate suitable Linux/KVM hardware; not a hosted-compute provider.

Until a qualifying host is available, keep all platform work in portable design, repository documentation, and offline preparation. Do not claim Paperclip/Ruflo is running or that any company is operational.

## Candidate comparison

| Candidate | Best-fit role | Persistence / runtime | Free route | Main constraint | Current disposition |
|---|---|---|---|---|---|
| GitHub Codespaces | Development, repository work, bounded coding sessions | Interactive workspace; idle timeout and monthly quota; not dependable always-on service | Personal Free account includes 120 core-hours and 15 GB-month | 2-core machine consumes 2 core-hours/hour; no free allowance for org/enterprise accounts; usage blocks at quota if no payment method | **Current development choice** |
| Zo Computer | Persistent cloud workstation, hosted services and agent infrastructure | Free computer trial sleeps when idle; after 14 days ordinary computer access ends; paid Basic advertises always-on 4 CPU/32 GB | 14-day trial only | Basic advertised at US$18/month; trial is not persistent hosting; paid use prohibited by current budget rule | **Future preferred host; HOLD** |
| Cloudroom | Isolated Linux cloud sandboxes for Codex/Claude Code/Pi Agent | Per-thread cloud sandboxes; not demonstrated as general-purpose always-on server | Docs advertise 3,000 credits/30 days | Pricing page labels Free “SOON” and shows differing limits; actual entitlement must be resolved; agent/model subscription remains separate | **Investigate only** |
| Google Colab | Notebook research, data analysis, bounded ML experiments | Ephemeral sessions; availability and runtime limits vary | Free tier subject to dynamic limits | Disconnects/idle/runtime/GPU restrictions; not a persistent service | **Research-only candidate** |
| Kaggle Notebooks | Notebook research and bounded data science/ML | Ephemeral notebook sessions with accelerator quotas | Free notebooks/accelerators subject to availability and quotas | Session, weekly accelerator and resource limits | **Research-only candidate** |
| E2B | Disposable isolated agent sandboxes | Short-lived sessions; current Hobby information indicates up to one hour | One-time promotional usage credit, not recurring free compute | Some accounts may require card verification; paid usage metered | **Optional sandbox; HOLD pending no-card route** |
| Rig | Browser/computer-use desktop for coding agents | E2B-backed cloud desktop; pauses when idle | Software is MIT-licensed; compute is not free | E2B metering; project estimate around US$0.46/hour for a 4-CPU/16-GB desktop; browser-cookie import creates session-security risk | **HOLD / no paid compute** |
| PequeRoku | Self-hosted Linux VM lab and MCP/API experimentation | Depends on the host machine/server | Software is MIT-licensed | Requires separate Linux host, Docker Compose and KVM-capable hardware for best performance | **Future self-hosted candidate** |
| Grok Bot cloud computer | Hosted desktop | Paid subscription | None under reviewed offer | Previously reviewed pricing US$20.99 first month, then US$41.99/month or US$419.90/year | **Rejected under current no-spend rule** |
| “Open Frames” | Unknown | Unknown | Unknown | Exact product identity has not been verified; do not substitute OpenHands by assumption | **Unresolved name** |

## Verified source notes

### GitHub Codespaces
- Personal Free account quota: 120 compute core-hours and 15 GB-month storage.
- GitHub Pro: 180 core-hours and 20 GB-month storage.
- Compute usage is multiplied by machine size. A 2-core Codespace uses two core-hours per wall-clock hour.
- If no valid payment method is on file, usage is blocked after the included quota is exhausted.
- Default idle timeout is 30 minutes unless changed.
- Organisation and enterprise accounts do not receive the personal-account free quota by default.
- Sources:
  - https://docs.github.com/en/billing/concepts/product-billing/github-codespaces
  - https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage

### Zo Computer
- Free trial includes 14 days of computer and limited AI usage; the computer sleeps when idle.
- After 14 days ordinary computer access ends; the account has limited recovery sessions to retrieve files.
- Basic is advertised at US$18/month and provides always-on compute (4 CPU / 32 GB RAM), 5 hosted services and 100 GB storage.
- The paid plan is the feature that restores always-on access. Credits or BYO API keys do not restore ordinary free computer access after the trial.
- Sources:
  - https://www.zo.computer/pricing
  - https://www.zo.computer/guide/billing

### Cloudroom
- Documentation currently says Free includes 3,000 Cloud Credits every 30 days and estimates typical agent work at roughly 100 credits/hour.
- The pricing page separately labels Free “SOON” and shows 100 cloud agents/30 days and 25 compute hours; this conflicts with the documentation's current free-plan statement.
- Cloudroom says agent sandboxes are isolated Linux environments; this does not establish a durable always-on general-purpose server for our control plane.
- Sources:
  - https://www.cloudroom.dev/docs/cloud-credits
  - https://www.cloudroom.dev/docs/faq
  - https://www.cloudroom.dev/pricing
  - https://www.cloudroom.dev/about

### E2B / Rig
- E2B's Hobby credit is a one-time credit rather than recurring monthly free compute; short session limits and possible card verification make it unsuitable as a guaranteed zero-cost persistent host.
- Rig is free MIT-licensed software but delegates cloud desktop compute to E2B, so the underlying compute is metered.
- Sources:
  - https://e2b.dev/pricing
  - https://github.com/kaijiabo/rig

### Notebook candidates
- Google Colab: https://research.google.com/colaboratory/faq.html
- Kaggle Notebooks: https://www.kaggle.com/docs/notebooks

### PequeRoku
- Self-hosted Linux/KVM lab software; it requires a separate host.
- Source: https://pequeroku.net/

## Architecture implications

### Control plane versus worker compute
Do not place the entire organisation on a short-lived notebook or sandbox. Separate:
- **Control plane:** company identity, tenant boundary, approval records, task registry, deterministic policy gateway, audit, secrets references, revocation, recovery and Main Hub/OCC read-only reporting.
- **Workforce management:** Paperclip candidate for company org chart, roles, tasks, approvals, budgets and lifecycle.
- **Orchestration:** Ruflo candidate for bounded specialist swarms inside an approved parent task.
- **Worker runtimes:** Claude Code and Codex first; other models/runtimes only after adapter, permission, cost and data handling verification.
- **Research compute:** Colab/Kaggle/E2B/Cloudroom only for scoped, temporary tasks with synthetic or approved non-sensitive inputs.

### Company isolation
Two independent company tenants/configurations are mandatory. Each must have separate executive authority, agent identities, task queues, memory, customer/private data, credentials, budgets, audit history and recovery. Shared infrastructure does not mean shared treasury, keys, secrets, or decision authority.

### Always-on Research & Intelligence
The Research & Intelligence division is a first-class organisation-level shared service. Continuous/day-night coverage cannot be claimed until persistent hosting, staffing, source stewardship, monitoring, incident handling, restart/recovery and coverage handover are tested and approved. Ephemeral free notebooks are not a substitute.

### Security & Recovery
Security & Recovery remains a first-class shared service. Any host must support least privilege, separate secrets, immutable audit, backup/restore, revocation, data export, incident isolation and independent recovery. No browser-cookie/session import into cloud desktops.

## No-cost operating sequence

1. Continue repository-centred design and source verification without creating compute sessions unnecessarily.
2. Use existing Codespaces only for approved development tasks and only within the user's actual free quota; stop sessions when idle.
3. Do not activate Zo's 14-day trial until there is a concrete, time-bounded task that benefits from it and the owner approves trial activation. Do not treat the trial as a persistent host.
4. Resolve Cloudroom's free-plan contradiction from current account-visible terms before considering any sandbox task.
5. Keep Colab/Kaggle as optional research tools only; do not place credentials, secrets or customer data in notebooks.
6. Reassess persistent hosting only when a genuinely free, durable, no-card/no-overage option is verified or the owner explicitly changes the spending rule.

## Explicit non-authorization

This matrix authorizes research and architecture preparation only. It does not authorize account creation, trial activation, software installation, compute execution, API calls, credentials, production connections, tests, repository settings changes, deployments, merges, publishing, spending, customer contact, trading or financial transactions.

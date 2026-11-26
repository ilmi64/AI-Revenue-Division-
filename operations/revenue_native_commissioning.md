# Aevora AI native runtime prerequisites and current blockers

Read-only reconciliation used pinned workforce architecture
`954a5c25720af01e00d3b79899d05b60e34edcc2` and the existing adapter
contract, technical assessment and acceptance scenarios. It installed
nothing and used no network, credentials, provider API or model execution.

| Candidate | Pinned architecture requirements | Local observation and remaining commissioning evidence |
| --- | --- | --- |
| Paperclip | Candidate release v2026.1106.0 observed upstream. Node.js 24.11+, pnpm 9.15+, runner on qualified x64/ARM64 with glibc 2.39+. Pin reviewed releases and dependency artefacts. Paperclip owns the company parent task and accountability. | This x86-64 local environment previously reported Node 24.22.3, pnpm 11.25.0, glibc 2.41. Paperclip was absent from inspected PATH/cache. Need authenticated identities, tested tenant isolation, role/task adapters, scoped runner and outside policy/tool enforcement. |
| Ruflo | Candidate release v3.76.0 observed upstream. Full CLI install would add hooks, MCP, configuration and a daemon. Select only reviewed, least-privilege integration and pin versions. | Ruflo and a vetted cached adapter were absent from inspected PATH/cache. Need scoped parent-to-child translation, cancellation/revocation, permission intersection, no direct model/tool bypass and bounded retries. |
| Worker/model | A separately version-pinned, cost-classified and authorized runtime with isolated workspace/tools, no unapproved provider/account access. Model must not confer authority. | Python and a Codex executable were available. No approved offline model/weights or native adapter was located in examined paths. Code and OS process checks remain local. Executable presence is not credential, adapter or runtime authorization. |

No native end-to-end verification is recorded. Production also requires
current identity and trust, signed audit/custody, independently witnessed
recovery, actual appointment of operational roles, and explicit owner
approval. Main Hub/OCC receives only existing read-only counters. Neither
the scheduler fixture nor signed test recovery grants external delivery or
company operational authority.

- [Workforce adapter contract](https://github.com/ilmi64/AI-Revenue-Division-/blob/954a5c25720af01e00d3b79899d05b60e34edcc2/organization/architecture/workforce-platform-adapter-contract.json)
- [Technical assessment](https://github.com/ilmi64/AI-Revenue-Division-/blob/954a5c25720af01e00d3b79899d05b60e34edcc2/organization/architecture/workforce-platform-current-technical-assessment.md)
- [Adapter acceptance tests](https://github.com/ilmi64/AI-Revenue-Division-/blob/954a5c25720af01e00d3b79899d05b60e34edcc2/organization/security/workforce-platform-adapter-acceptance-tests.json)

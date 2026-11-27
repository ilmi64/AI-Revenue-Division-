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

## Pinned pilot acquisition manifest

Use [revenue_native_artifacts.json](revenue_native_artifacts.json) as the
starting bill of materials. Its six entries are exact upstream archive or
weight candidates with source revisions, licenses and digest pins. The
Paperclip CLI and server are both pinned at `2026.1106.0`. Ruflo and its CLI
are both pinned at `3.79.0` for the pilot review because this is the first
release with published npm SLSA provenance. Moving from the earlier 3.76.0
architecture candidate requires compatibility review. The CPU-only llama.cpp
`b12644` build is an upstream prerelease candidate. Qwen's 1.5B Q4_K_M weight
is an Apache-2.0 smoke-test candidate for code and structured output. Its
quality and tool protocol suitability require measurement.

On November 26, 2026 the inspected Linux x86-64 host had Node 24.22.3,
pnpm 11.25.0, glibc 2.41, two CPUs available under the cgroup quota, an
8 GiB cgroup memory limit and about 7.3 GiB available storage. Begin with a
single model process and 2,048 tokens of context. Budget 8 GiB total memory
and 5 GiB free staging storage for the initial integrity and pilot review.
Confirm CPU ISA, native library resolution, actual dependency-store size,
peak RSS and task latency before scheduling two concurrent workers. The
host budget is an engineering estimate. The complete dependency tree and
native workers still need qualification.

### Separate acquisition and execution decisions

1. Approve staging the six candidate files and their license and provenance
   records from the exact manifest URLs in a restricted, clean environment.
   Compare publisher attestations to expected package names, source commits
   and CI workflow identities. A registry digest by itself checks bytes.
2. Resolve the reviewed Node lockfiles for the exact pinned graph on this
   platform. Approve and stage each transitive tarball and platform-specific
   dependency with its integrity, source, license and advisory status.
   Include any bundled PostgreSQL/runner and ACP packages used by Paperclip.
   Keep the frozen lockfile and offline store in review custody. The six
   primary artifacts do not establish a complete executable dependency set.
3. On the isolated staging host, obtain the candidate files under the
   manifest basenames. Run this verifier with a directory under company
   control. It does not unpack, install, execute or fetch anything.

   ```sh
   python operations/check_revenue_native_artifacts.py /path/to/private/staging
   ```
4. Review the candidate dependency graph, lifecycle scripts, native
   libraries and archive contents before a separate execution decision.
   Paperclip's advisory history includes inherited account connectors,
   cross-tenant key handling, approval attribution and local-server risks.
   Ruflo exposes hooks, MCP tools, memory and updater paths. Do not run its
   bootstrap or enable native plugins, connectors, self-update, memory
   federation, telemetry or external model providers as a commissioning
   shortcut. Require explicit per-process allowance for any unavoidable
   install-time script and retain its outputs and hashes.
5. Commission Paperclip as the company-local parent-task tracker, and verify
   Ruflo as a bounded worker capability under that task. Run the local model
   as inference only. Inventory an empty credential store, restrict runner
   identity, process, filesystem, IPC and outbound network privileges, bind
   worker outputs to exact scope, and require the external policy/tool
   gateways to recheck identity, cost, revocation and tool authorization.
   Prove denial of direct tools, unapproved network, reused grants, peer
   tenant access and insecure retries. If the vendor runner cannot use the
   approved local model path without an externally authenticated harness,
   keep native execution blocked and record that compatibility evidence.
6. Review native execution, QA and supervision against the pinned workforce
   acceptance cases. Operator signatures and release gates are independent
   of candidate staging, artifact checks and model results.

The shortest current service path is a fixed-scope coding review for one
owner-approved inbound opportunity. Start with the existing intake, delivery
plan, QA evidence and exact private review bundle. Commission on synthetic
inputs first, then require written customer authority and agreed scope,
price, data handling and acceptance criteria before processing customer
materials. Require an independent artifact review, owner release decision
through the authorized delivery path and lawful billing records. Do not
treat an internal ZIP acceptance, unsigned proposal or bounty eligibility as
revenue. These steps do not require a public launch or paid software, and
the current synthetic release denial stays in force.

- [Paperclip candidate release](https://github.com/paperclipai/paperclip/releases/tag/v2026.1106.0)
- [Paperclip vendor advisories](https://github.com/paperclipai/paperclip/security/advisories)
- [Ruflo signed npm release](https://github.com/ruvnet/ruflo/releases/tag/v3.79.0)
- [llama.cpp CPU release](https://github.com/ggml-org/llama.cpp/releases/tag/b12644)
- [Qwen exact weight digest and license](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/blob/f86cb2c1fa58255f8052cc32aeede1b7482d4361/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf)

The upstream Paperclip build lock `pnpm-lock.yaml` at the pinned source
commit has Git blob ID `95c28f080c25654038e6e4ed641a017835f7eea4`.
Verify the build lock against that source when reviewing the candidate.
Record a separate, platform-specific offline install lock for the actual
distribution graph, including optional dependencies needed by the chosen
runner.

The pilot manifest now pins the Paperclip and Ruflo upstream source
build locks by Git blob and SHA-256. During staging review, check the
candidate archive directory and the separately staged source lock files.

```sh
python operations/check_revenue_native_artifacts.py \
  "$candidate_archive_directory" --source-lock-directory "$source_lock_directory"
```

Archive byte matches and source build lock matches are reported separately.
The build locks cover upstream source workspaces. Commissioning still needs
the published-distribution dependency closure for the exact execution
profile and approval for any required lifecycle script. If a publisher
attestation names a different source revision from the approved manifest,
remove that archive from the candidate execution set and retain it in
restricted evidence custody. Resolve the difference against independently
approved source and build provenance before promotion.

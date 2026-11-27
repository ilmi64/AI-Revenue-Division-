# Rootless CPU inference approval

The managed rootless Docker 29.9.2 service with gVisor runsc systrap
passed namespace, inherited process limit and forced-removal probes.
The test image contained only locally compiled inert code and, for
the inheritance check, the trusted local `prlimit` and its libraries.

```sh
bash operations/revenue_isolation_probe/probe-rootless-docker.sh runsc test-inherited-limits
bash operations/revenue_isolation_probe/probe-rootless-docker.sh runsc test-timeout-cleanup
```

The probe read UID/GID 65534, a read-only root and input, loopback-only
networking, absent host paths and daemon socket, cleared proxies and
bounded file descriptors and output. It denied an over-limit mapping
and verified a reduced process cap in a separate test. The timeout
probe created a waiting child in a separate session, observed it ready,
killed the attachment at three seconds, force-removed the container,
and confirmed its ID disappeared. No staged component ran.

## Mandatory aggregate host qualification

The managed daemon reports cgroup driver `none` with memory, swap,
PID and CPU quota support disabled. The workspace mount is read-only
cgroup v2 with two CPUs, 8 GiB and no PID cap for the workspace as a
whole. Its user systemd bus is absent. Container configuration flags
and process limits give no per-workload aggregate guarantee here. The
launcher and in-image guard fail closed on this host. Host selection or
controller delegation requires infrastructure owner approval and a
rehearsal on an existing no-cost system.

On the proposed host, require successful rootless daemon preflight
and a same-profile inert probe before signing the run record.

```sh
bash operations/revenue_isolation_probe/run-approved-native-pilot.sh --preflight
bash operations/revenue_isolation_probe/probe-rootless-docker.sh runsc test-aggregate-controls
bash operations/revenue_isolation_probe/probe-rootless-docker.sh runsc test-timeout-cleanup
```

The aggregate probe checks both the inner private cgroup view and
kernel readback from the container's host PID. Require
`cpu.max=200000 100000`, `memory.max=6442450944`,
`memory.swap.max=0` and `pids.max=32`. Stop if either view lacks
these limits or the host cannot prove the mapping. Independently
review the exact no-network image, cap drops, namespace and filesystem
inputs with Security & Recovery. Preserve an operator-owned, out-of-band
stop procedure. Per-process address space, task, CPU-time and file
limits provide a second layer.

## Exact candidate

Maximum expenditure CAD $0. The approved assembly must pin the
verified archive and GGUF from [the CPU pilot request](revenue_native_pilot_approval.md),
the unpacked executable and library inventory, trusted GNU
`timeout` and `prlimit` with their loader and libraries, and the
locally compiled `require-aggregate-cgroup.c` binary. Build the latter
from the approved source using the already approved local compiler.

```sh
gcc -std=c11 -O2 -Wall -Wextra -Werror -static \
  operations/revenue_isolation_probe/require-aggregate-cgroup.c \
  -o "$approved_root/pilot/require-aggregate-cgroup"
```

The prepared root places `llama-cli` and its reviewed libraries under
`/pilot/runtime` and the two trusted utilities under `/usr/bin`.
Pin the exact local image ID, with no inherited image volumes. The
synthetic prompt is `operations/fixtures/native-pilot-prompt.txt`
at SHA-256 `05e35b5b43dbda72f293b70b796878d169f3e5f64187d7f59eb72d56ac471e42`.

Only after owner approval to assemble and execute and independent
Security & Recovery signoff, run the pinned capsule on the qualified
host. Pass a fresh owner-private evidence parent with mode 0700.

```sh
python operations/check_revenue_native_artifacts.py "$verified_stage" --cpu-model-smoke
bash operations/revenue_isolation_probe/run-approved-native-pilot.sh \
  "$approved_local_image_id" "$verified_stage" "$private_evidence_parent"
```

The launcher uses the local Unix socket, `--pull=never`, runsc,
a read-only root, no network or shared IPC, a 64 MiB temporary
filesystem, no privileges, no health check and no restart.
Only the pinned prompt and GGUF are mounted read-only. Keep the
approved paths owner-controlled and stable through the run. Deny
credentials, repository paths, customer content and cross-company
data. The in-image guard checks all four aggregate values before
invoking `timeout` and then the passive model process. It has an
inner SIGKILL deadline of 115 seconds and an outer SIGKILL deadline
of 120 seconds. There are two CPU threads, no GPU layers, context
2,048, up to 256 generated tokens and seed 42. File output is
bounded to 64 KiB per stream. Forced container removal clears the
whole PID namespace even when a child changed process group. The
launcher records elapsed time, output hashes, exit status and
verified removal. The witness retains host memory peak and cgroup
observations separately. A nonzero exit, timeout, missing evidence
or unconfirmed cleanup invalidates the run. Suspend the approved
host if the daemon cannot acknowledge removal. Security & Recovery
must use its local runtime controls to terminate the named capsule
and confirm that the exact scope is empty before another run.

The fixture expects one simple Python `add` function. Review the
output as text, without executing generated code. Record scope, exit,
quality, containment and independent approval. Keep all output inside
Revenue. First-service acceptance, external delivery and billing
remain independently gated.

## Ruflo and Paperclip

The company-held Ruflo wrapper and CLI both attest to version 3.79.0
and source `861179f6210d7d934ea7283fd33fb433ca8cdd29`. The source's
`v3/package-lock.json` links CLI version 3.32.2. The shipped archives
supply no published runtime lock. Of 30 required direct edges after npm's
optional override, 16 match the source lock, 13 are incompatible and
one is absent. Two of 16 optional and zero of three peer edges match.
The published CLI bundles `@claude-flow/codex` 3.0.8,
`@claude-flow/mcp` 3.1.8, `@claude-flow/plugin-agent-federation` 1.0.7
and `@claude-flow/security` 3.0.8. The bundled security manifest
still declares `zod ^4.6.7`; four embedded packages do not close the
distribution graph. The CLI postinstall reads AgentDB paths and writes files. Retain the
installation block until the exact published Linux x86-64 closure,
advisory applicability, licenses and lifecycle scripts are reviewed
independently. Keep both Paperclip archives quarantined.

The first fixed-scope coding review still needs verified inbound
authority, exact written scope, reproducible permitted checks and
independent acceptance of the exact deliverable. Commercial release and
billing remain separate owner decisions. [Service commissioning](revenue_fixed_scope_service_commissioning.md)

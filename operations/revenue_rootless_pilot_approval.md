# Rootless CPU pilot and Ruflo security disposition

Docker 29.9.2 rootless with gVisor runsc systrap passed an inert local
probe. The probe compiled its own canary, pulled no image and used no
staged executable or model. It checked UID/GID 65534, read-only root
and input, disposable scratch, absent host workspace and Docker socket,
cleared proxies, loopback-only interfaces and file and core limits.
A process-limit check refused an over-limit mapping under a 6 GiB address
space cap and blocked a fourth child in a four-task sandbox. The exact
local `prlimit` wrapper and its three host libraries were also separately
hashed and verified to preserve the address-space, 32-task and CPU-time
limits across an exec of the inert canary.

```sh
bash operations/revenue_isolation_probe/probe-rootless-docker.sh runsc test-inherited-limits
```

The managed daemon reports cgroup driver `none` and no container CPU,
memory or PID controller. Docker configuration fields alone do not
establish enforcement. The inert probe qualifies the namespace and
per-process mechanisms for review. Require a separately verified
cgroup-enabled existing host if approval calls for aggregate container
limits. Bubblewrap and Landlock remain unavailable on this host.

## Approve one exact passive workload

Maximum expenditure CAD $0. The two artifact hashes, synthetic input
and acceptance conditions are in [the CPU pilot request](revenue_native_pilot_approval.md).
Re-run the inert probe and recheck both staged hashes before approving
any execution. The approved assembly record must pin the minimal local
root image, independently reviewed `prlimit` and its dependencies,
signed runner archive and extracted native library inventory. Use the
exact local image digest and `--pull=never`. Keep the model and prompt
out of the image. Approval must explicitly accept the verified
per-process scope and the absence of a container cgroup controller.

After separate approval, use the independently witnessed local image
and the exact staged model and synthetic prompt. The command below is
the candidate replacement for the prior Bubblewrap recipe.

```sh
d() {
  env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY \
    -u DOCKER_CERT_PATH docker --host=unix:///var/run/docker.sock "$@"
}
id=$(d create --runtime runsc --pull=never \
  --read-only --network=none --log-driver=none --cap-drop=ALL --security-opt=no-new-privileges \
  --user=65534:65534 --ulimit fsize=65536:65536 --ulimit nofile=64:64 --ulimit core=0:0 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=67108864,mode=1777 \
  --mount "type=bind,src=$verified_model,dst=/pilot/model.gguf,readonly" \
  --mount "type=bind,src=$verified_prompt,dst=/pilot/prompt.txt,readonly" \
  --env HOME=/tmp --env LD_LIBRARY_PATH=/pilot/runtime \
  --env HTTP_PROXY= --env HTTPS_PROXY= --env ALL_PROXY= --env NO_PROXY= \
  --env http_proxy= --env https_proxy= --env all_proxy= --env no_proxy= \
  --entrypoint /usr/bin/prlimit "$approved_local_image_id" \
  --as=6442450944:6442450944 --nproc=32:32 --cpu=240:240 -- \
  /pilot/runtime/llama-cli --single-turn --simple-io --no-display-prompt \
  -m /pilot/model.gguf -f /pilot/prompt.txt -ngl 0 -t 2 -c 2048 -n 256 --seed 42)
cleanup() { d rm -f "$id" >/dev/null; }
trap cleanup EXIT
timeout --kill-after=5s 120s prlimit --fsize=65536:65536 -- \
  env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS \
  -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH docker --host=unix:///var/run/docker.sock \
  start -a "$id" > "$private_evidence/output.txt" 2> "$private_evidence/runner.log"
test "$(d inspect -f '{{.State.ExitCode}}' "$id")" = 0
```

Repeat the inherited-limit test against the exact approved wrapper and
minimal root image, then verify the supervisor bounds the captured
stdout and stderr as well as the container's writable files.
Scope is one passive process, two compute threads, a pinned synthetic
prompt and private output. Deny tool authority, credentials, customer
input, repository mounts and cross-company paths. Measure elapsed time,
observed memory, exact output digest and cleanup. Keep the original
native workforce and independent commercial release requirements.

## Published Ruflo review

The staged wrapper and CLI are both 3.79.0 with verified publisher
attestations on their exact bytes. The attested source's
`v3/package-lock.json` at `861179f6210d7d934ea7283fd33fb433ca8cdd29`
instead locks a linked CLI workspace version of 3.32.2. The archives
supply no published runtime lock. After npm's optional dependency
override, the shipped CLI declares 30 required direct edges. The
source lock offers 16 compatible version entries, 13 incompatible
entries and one missing entry. Two of 16 optional version entries
match. None of three peer entries matches. The archived CLI postinstall
reads AgentDB paths and contains local file writes.

Keep Ruflo blocked pending an exact Linux x86-64 distribution lock,
transitive license and advisory review, and independent lifecycle
approval. Earlier advisory evidence qualifies source graph candidates
only. Keep the Paperclip archives quarantined. The passive CPU request
covers only llama.cpp and Qwen.

The first fixed-scope coding review needs verified inbound authority,
exact written scope, reproducible permitted checks and independent
acceptance of the exact deliverable. Commercial release and billing
remain separate owner decisions. [Service commissioning](revenue_fixed_scope_service_commissioning.md)

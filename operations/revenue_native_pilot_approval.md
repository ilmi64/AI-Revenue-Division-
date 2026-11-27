# Revenue request for an isolated CPU inference pilot

The long-term workforce design retains Paperclip coordination and Ruflo
worker capabilities. The only immediate independent pilot candidate is
one passive llama.cpp CPU inference on a company-owned synthetic fixture.
Its output is private text for an independent reviewer. It does not meet
the workflow, identity, privilege or release requirements of a workforce
commissioning run. Ruflo's published dependency closure and postinstall
behavior still require independent qualification.

Keep both Paperclip 2026.1106.0 archives in quarantine. Their verified
npm attestations and successful publisher workflow run identify source
`da9a4cb96c46945d693f0ddffdcb0e0743649a01`. The approved release tag points
to `d69631b01b9c658f80bf8bed389863dce82643e1`. The Git trees differ.
The attested source build lock can guide review. It cannot replace the
approved source or certify the published runtime graph. [Publisher run](https://github.com/paperclipai/paperclip/actions/runs/42295041150) · [Release tag](https://github.com/paperclipai/paperclip/releases/tag/v2026.1106.0)

## Exact proposed scope

- `llama-b12644-bin-ubuntu-x64.tar.gz`, 23,299,158 bytes, MIT, SHA-256
  `7cff30bdd348bd2cf1b999e9323c97491d77dab4f5ce129629f590d75f9e6756`.
  The publish workflow attestation identifies the exact archive, and the
  release targets build `94f3af3d09e74a0fb35f703194318d3b4037714a`.
- `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf`, 1,117,320,768 bytes,
  Apache-2.0, SHA-256
  `cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046`.
  The publisher LFS pin is at `f86cb2c1fa58255f8052cc32aeede1b7482d4361`.
- Maximum expenditure CAD $0. One unprivileged process tree, two CPU
  threads, zero GPU layers, 6 GiB memory, at most 32 tasks, 120 seconds
  with a 5-second termination grace, 2,048 context tokens, up to 256
  new tokens and a 64 KiB output file. Record exit code, content hash,
  elapsed time and peak memory. Keep all output company-local.
- No model tools, network, writable host mounts, process spawning from
  prompts, shells invoked by model output, customer input, host credentials,
  Trading data, publication or external actions. The binary and model
  mounts are read-only and the output file belongs to the isolated run.
  Allow write access to disposable scratch space only.
- One signed company attestation must bind the exact archive and model
  hashes, compute profile, fixture hash, reviewed executable and library
  inventory, and independently verified boundary. The owner approves the
  scoped run and Security & Recovery witnesses isolation. The actual
  candidate host failed Bubblewrap preflight with a read-only UID map.
  This run awaits a qualified existing host and separate execution approval.

## Commands for the approved host

First run the local byte check. Its success does not authorize a run.

```sh
python operations/check_revenue_native_artifacts.py "$verified_stage" --cpu-model-smoke
```

After separate authorization, extract only the bound archive as an
unprivileged user into a fresh directory. Inspect and retain the member
and library inventory. Keep the original archive and model read-only.
The checked host image must contain its own verified loader and system
libraries. Mount no account home directories or other company files.

```sh
tar --no-same-owner --no-same-permissions --keep-old-files \
  -xzf "$verified_stage/llama-b12644-bin-ubuntu-x64.tar.gz" -C "$fresh_unpack"
```

With the independent boundary checks already passed, use a host with a
cgroup manager supporting the shown limits. The only additional inputs
are the read-only approved host root, exact unpacked directory,
pinned model file and one hash-pinned synthetic prompt. Save stdout and
stderr to the private evidence path outside the child.

```sh
systemd-run --user --wait --pipe --collect \
  -p MemoryMax=6G -p CPUQuota=200% -p TasksMax=32 -p RuntimeMaxSec=125 \
  timeout --kill-after=5s 120s prlimit --fsize=65536:65536 --nofile=64:64 --core=0:0 -- \
  bwrap --unshare-all --disable-userns --die-with-parent --new-session --clearenv \
  --ro-bind "$approved_host_root" / \
  --ro-bind "$fresh_unpack/llama-b12644" /pilot/runtime \
  --ro-bind "$verified_stage/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf" /pilot/model.gguf \
  --ro-bind "$approved_prompt" /pilot/prompt.txt \
  --proc /proc --dev /dev --size 67108864 --tmpfs /tmp --chdir /tmp \
  --setenv HOME /tmp --setenv LD_LIBRARY_PATH /pilot/runtime \
  -- /pilot/runtime/llama-cli --single-turn --simple-io --no-display-prompt \
  -m /pilot/model.gguf -f /pilot/prompt.txt -ngl 0 -t 2 -c 2048 -n 256 --seed 42 \
  > "$private_evidence/output.txt" 2> "$private_evidence/runner.log"
```

Before model execution, run a vetted harmless probe with the same mount,
namespace and resource configuration. It must verify denial of IPv4,
IPv6, access to host and other-company paths, writes outside scratch and
attempts to reach host credentials. Confirm process cleanup after timeout.
The company chooses a bounded synthetic coding prompt with acceptance
criteria. The reviewer records model failures, instruction-following and
limits. A successful output remains a model-quality observation. The
separate commercial workflow and native workforce identity and approval
controls still govern the next stage.

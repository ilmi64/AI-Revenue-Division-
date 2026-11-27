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
  threads, zero GPU layers, 6 GiB memory, at most 32 tasks, 120 seconds with a
  separate bounded cleanup verification, 2,048 context tokens, up to 256
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

Complete static byte verification first.

```sh
python operations/check_revenue_native_artifacts.py "$verified_stage" --cpu-model-smoke
```

After separate authorization, extract the bound archive offline as an
unprivileged user into an empty private directory with an independently
reviewed member inventory.

```sh
tar --no-same-owner --no-same-permissions --keep-old-files \
  -xzf "$verified_stage/llama-b12644-bin-ubuntu-x64.tar.gz" -C "$fresh_unpack"
```

The [rootless CPU request](revenue_rootless_pilot_approval.md) specifies
the aggregate host proof, exact launcher and prompt, inner and outer
deadlines and mandatory process-tree cleanup. Each gate must be
satisfied before execution. The current managed host fails aggregate
qualification.

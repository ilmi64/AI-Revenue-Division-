# ECC Pilot — Existing Workflow Security Finding

Date: 2026-11-13
Branch: `ecc-selective-evaluation`
Affected default-branch file: `.github/workflows/research-radar.yml`

## Finding: network installer is executed directly through a shell

The current Research Radar workflow contains:

```sh
curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.40.16 sh
```

This downloads a remote shell script and executes it immediately. Pinning the requested Ollama version in an environment variable does not pin or verify the installer script itself. The script is fetched at runtime from the network, so its contents can change independently of the workflow commit.

The ECC TDD skill itself explicitly says network installers and fetch-and-execute remote code require human review and should be rejected as a validation command. This is a pre-existing workflow risk; it is not introduced by ECC.

## Impact

- The workflow runner executes downloaded code with the permissions available to the job.
- A compromised or changed installer endpoint/script could run unintended commands.
- Current job permissions are restricted to `contents: read` and no repository secrets are configured for this pilot, which limits (but does not eliminate) impact.
- This does not mean the observed run was compromised. The available run completed successfully; no evidence of compromise was observed.

## Required remediation before scaling

Prefer a pinned release artifact with a verified SHA-256 checksum and a controlled installation procedure. If a checksum-verifiable official artifact is not available, document the residual risk and require an explicit review of the exact installer script revision before execution.

Also:
- Pin third-party GitHub Actions to full commit SHAs rather than mutable major-version tags when practical.
- Keep job permissions minimal and avoid secrets.
- Keep the 30-minute timeout and artifact retention policy.
- Do not add hooks, MCP servers, or additional write permissions.

## Decision

**Do not expand or scale the Research Radar workflow until the installer approach is hardened.** This is a security improvement task, not an emergency incident. Keep the ECC evaluation branch isolated; no change has been made to `main` or the existing workflow.

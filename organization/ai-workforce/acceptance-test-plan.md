# AI Workforce Acceptance and Release Gates

## Model validation
- Verify exact model tag, runtime version, quantization and license.
- Measure cold/warm latency, peak RAM, storage, timeout and failure rate.
- Benchmark factual extraction, summarisation, schema compliance, consistency, contradiction detection and uncertainty handling.
- Test prompt-injection resistance using untrusted release notes and documents.
- Compare Qwen2.5 1.5B with candidate Llama 3.2 1B and candidate Qwen3.5 0.8B on the same fixed test set.
- Record unsupported-claim rate, invalid-output rate, pass rate, latency and resource use. Do not rely on vendor benchmarks alone.

## Governance
- Confirm agents cannot approve spending, applications, outreach, publishing, contracts, trades, transfers, wallet actions, merges or deployments.
- Confirm secrets are excluded from prompts, reports and logs.
- Confirm external text is always treated as untrusted data.
- Confirm timeouts, malformed output and unavailable models fail safely.
- Confirm human approval is captured before consequential external actions.

## Division integration
- Each division needs a role, queue, deliverable contract, dependencies and escalation path.
- Every handoff needs evidence and receiving-division acknowledgement.
- OCC must distinguish proposed, in-progress, blocked, review and complete.
- No division is operational without real evidence and a readiness assessment.
- Crypto, Forex, indices and XAUUSD remain research/paper-only pending separate approval and validation.

## Operational release
- Offline validator and tests pass.
- End-to-end Qwen workflow runs after Actions usage reset and generated artifacts are reviewed.
- Model comparison and failure/recovery drills pass.
- Incremental spend remains CAD $0.
- Owner approval is obtained before merge, deployment, account connection or production activation.

# Baseline Registry & Control-Plane Inventory

**Baseline date:** 2026-11-21  
**Status:** Read-only inventory from the active architecture branches; not an implementation or security certification.  
**Repositories:** `ilmi64/AI-Revenue-Division-` and `ilmi64/Solana-memecoins`.

## 1. Inventory method and limits

The active architecture branches were inspected through the open architecture PR file inventories and exact-path fetches. The files below were fetched from their named branches and their blob identities recorded. This is a targeted inventory of the existing registries and policy/control-plane foundations relevant to the current fast-track work—not a claim that every file, historical branch, notebook, external repository or prior research artifact has been exhaustively reconciled.

Do not overwrite or replace an existing registry merely because a new consolidated index exists. The capability-opportunity registry is an index and routing layer; detailed source records remain authoritative in their owning workstreams.

## 2. Existing registries and canonical records

| Existing artifact | AI Revenue path / blob | Trading path / blob | Function and handling |
|---|---|---|---|
| Two-company workforce registry | `organization/architecture/two-company-workforce-registry.json` — `292c250973cf0dad4827868e31871e9483a6cf39` | Corresponding organization-level structure is in company architecture and charter records; no Trading-side duplicate JSON asserted | Existing target-state company and shared workforce candidate registry. Keep exactly two companies; Research & Intelligence remains a division/shared service. |
| GitHub Skills & Capability Registry | `organization/architecture/github-skills-capability-registry.md` — `78a89a80b159589a202ac409c8aebff1d3fc4a8d` | `docs/architecture/github-skills-capability-registry.md` — same blob | Existing P0/P1 tool/skill evaluation portfolio, including REA and Creative Studio candidates. Preserve its decisions; no installation implied. |
| Research record schema | `organization/architecture/research/schemas/research-records.schema.json` — `e44b4a1326b2114bea37a57e361ca9b594a89571b` | `docs/architecture/research/schemas/research-records.schema.json` — same blob | Existing source, evidence, publication and handover record contract. Not yet a live research database or validated operating queue. |
| Main Hub registry/workstream and decision examples | `organization/architecture/main-hub/fixtures/registry-and-workstreams.example.json`, `decisions.example.json`, `main-hub-envelope.example.json` | Mirrored under `docs/architecture/main-hub/fixtures/` | Synthetic fixtures for two-company identity, workstreams and decisions. Not actual operational records. |
| Production-readiness evidence register | `organization/security/production-readiness-evidence-register.md` — `e846d487eb8da67390e13a48bfdcd16e77fc447a` | `docs/security/production-readiness-evidence-register.md` — mirrored record | Gate evidence register; distinguishes documents, authored tests, executed tests and production evidence. All open gates remain open until evidence is attached. |
| Capability & Opportunity Registry (new index) | `organization/architecture/intelligence/capability-opportunity-registry.md` — `a9a7e2641400c16f54256c9c56904562a884c211` | `docs/architecture/intelligence/capability-opportunity-registry.md` — same blob | Cross-organization index of preserved named opportunities, status vocabulary, scoring method and recipient scopes. Detailed source reconciliation remains pending. |

## 3. Existing deterministic policy and authorization foundation

The following exact files were fetched from the AI Revenue branch and their matching Trading-side contracts were confirmed where present:

| Artifact | AI Revenue blob | Current status / important limitation |
|---|---|---|
| `organization/security/policy-gateway-production-contract.md` | `310ca2f6a1c4a1e95c83337c3f98ac879e18c6cb` | Reference contract; sole decision boundary is intended, but no production enforcement or independent security review. |
| `organization/security/deterministic-policy-enforcement-interface.json` | `f0609caab81cfb277665487f44ef6a551b172130` | Proposed interface; CAD $0 default, scoped short-lived grants and all enforcement points defined; implementation not present. |
| `organization/security/durable-approval-audit-contract.md` | `97dc1b3ce06331e8744ce6c7faa344dae08c50a8` | SQLite reference transaction contract; no production owner-signature verifier or multi-node ledger. |
| `organization/security/trusted-control-plane-facade-reference-contract.md` | `87886176d793b3b9f8a7b480dd9b344d414df59f` | Offline prototype contract; current SQLite approval schema does not persist every field required by the façade. Do not wire together before migration design. |
| `organization/security/linearizable-control-store-contract.md` | `e56086b94815912802e7621efb33ef8fc4f6dd45` | Local SQLite reference; no distributed consistency, production crypto, receiver idempotency or WORM checkpoint. |
| `organization/security/transactional-dispatch-recovery-contract.md` | `659fcb8c3ae22a7e9db6abdd11339766c52474c2` | Offline reference; ambiguous remote effects must not be resent automatically; receiver-side idempotency and signed evidence absent. |
| `organization/security/identity-lifecycle-production-requirements.md` | `d09636c2b08112f2d1b2b078361ca9b594a89571b` | Design requirements; asymmetric issuer, key custody, revocation and production identity remain unimplemented. |
| Trading company isolation contract | `docs/security/company-isolation-and-agent-authority.md` — `1175adf1bbf943451341425111d918bc560d28fb` | Trading's separate company identity, private data and independent risk authority; proposed, not deployed. |

The corresponding Trading policy gateway, approval and control-store contracts are maintained under `docs/security/`. Company-local namespaces, risk hard-denies, audit streams and authority must remain separate. A matching document or blob does not imply that the underlying code is production-ready.

## 4. Known registry and architecture gaps

1. The skills registry is a candidate/evaluation list; source revisions, current compatibility, license, runtime and measured value still need per-item refresh.
2. The two-company workforce registry is a target-state JSON record, not proof of live identities, queues, credentials or company operations.
3. Research schema defines records but does not itself create continuous day/night collection, source monitoring, shift staffing or a durable store.
4. OCC registry/workstream/decision examples are synthetic and must never be presented as current company status.
5. The capability-opportunity registry is a high-level index; detailed source-level reconciliation, existing IDs, evidence links and scoring remain pending.
6. The policy gateway and related prototypes are not connected or deployed. Identity/approval cryptography, approval schema compatibility, distributed atomicity, final enforcement coverage, receiver idempotency, audit checkpoint protection and operational recovery remain blockers.
7. No test execution, schema validation, GitHub Actions run, installation, deployment or external connection was performed for this inventory.

## 5. Immediate work sequence

1. Preserve this inventory as the current baseline and update it only when exact sources or revisions change.
2. Reconcile source-level research and capability records into the index without copying private company evidence.
3. Advance PG-0 through PG-4 in `policy-gateway-integration-and-gap-closure-plan.md`, starting with company-specific operation taxonomies and the approval schema mismatch.
4. Create distinct REA work orders for AI Revenue business workflows and Trading bot/strategy capabilities; publish only recipient-scoped findings.
5. Continue AI Revenue commercial capability discovery and Trading Crypto/PolyBot research in parallel; neither is dependent on OCC or Research & Intelligence becoming operational.
6. Keep all validation/test execution, installation, credentials, spending, deployments, Actions, publishing, customer contact and live financial actions behind their existing separate approvals.

**Disposition:** targeted source inventory captured; detailed legacy research reconciliation and all runtime/production gates remain pending.

## 6. Additional discovery source reviewed — Public APIs

- Repository: `public-apis/public-apis` (MIT-licensed catalogue, not a service).
- README blob at review: `9374f27062f9fa239ba7a00a5b1ae8babe5536ff`.
- LICENSE blob: `196b23b178fbf71317fc55c3d3e01d481b5760e5`.
- CONTRIBUTING blob: `a8181acab01ac58ca80f3ef807b99fd5ec5e6e9d`.
- Review and recipient-scoped shortlist: `organization/architecture/research/public-apis-directory-evaluation.md` / `docs/architecture/research/public-apis-directory-evaluation.md`.
- Disposition: discovery/reference only. The catalogue license does not license listed providers' APIs or data. No endpoints called, accounts created, keys issued, MCP servers installed or API integrations authorized.
- Initial research candidates include DefiLlama, 0x, CoinGecko, CryptoCompare, FRED, SEC EDGAR, Frankfurter, Currency-api, OpenAlex and selected Canadian public data. All remain individually unverified for plan terms, current authentication, data rights, quotas, quality and commercial use.


## 7. Additional provider assessment — MoonPay PayBox

- Assessment: `organization/architecture/research/moonpay-paybox-and-airdrop-assessment.md` / `docs/architecture/research/moonpay-paybox-and-airdrop-assessment.md`.
- Official terms last updated 2026-08-06 identify Launchpad Limited (BVI), state the services are unregulated, and prohibit use on behalf of a business entity. PayBox is therefore excluded as a company wallet, treasury or Trading execution layer under the published terms.
- PayBox remains a Research & Intelligence technology-intelligence subject for MCP/OAuth, scoped grants, operation-bound approvals, revocation and audit design. Provider claims are not independent certification.
- The USDC faucet is a historical July 2026 launch promotion. Current official campaign status and Canadian eligibility were not verified; third-party reporting says Canada may be excluded.
- No PayBox account, wallet, connector, X authorization, API call, claim, installation, funding or transaction was performed.

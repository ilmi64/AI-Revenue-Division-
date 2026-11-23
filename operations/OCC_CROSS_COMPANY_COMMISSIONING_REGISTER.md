# OCC cross-company commissioning evidence register (review-only v1)

**Status: NOT COMMISSIONED.** This register is a review artifact, not an OCC runtime integration, approval, deployment, or release decision. It contains no keys, customer data, private manifests, financial authority, or order-routing capability. Both companies retain independent approval and operating boundaries.

## Immutable review references

| Company | Exact reviewed source | Evidence | CI observation | Gate |
| --- | --- | --- | --- | --- |
| Aevora AI Revenue | `ilmi64/AI-Revenue-Division-` draft PR #51; head `33a113a502048667d046aae0ce1a49f7a98bd538`; stacked on draft #49 | `operations/durable_commissioning_evidence.md` reports 7 focused, 47 adversarial/integration and 95 full offline tests; private fixture SHA-256 `1c5df5b254012cc7a0f7da389189ff94b7cc41e5deba43acd869a7126a3b27be`; redacted OCC fixture SHA-256 `f7f25048cbc8e27be54dcacaf40b8ab674f0b17e6ae681998b26a87f13e96de2` | No GitHub Actions workflow runs observed for this exact head during executive review | **BLOCKED** |
| Trading & Technology / PolyBot | `ilmi64/Solana-memecoins` draft PR #91; head `41a598f969d5068b666d2a72b194054601a08ed5`; #92 follow-on unfinished | `docs/PAPER_COMMISSIONING_CUSTODY_90.md` specifies independent custody, authenticated feed lineage, exact-claim recovery journal and pending signoffs; 875 full offline tests previously reported for #91 | No GitHub Actions workflow runs observed for this exact head during executive review | **BLOCKED** |

*All test counts are developer/Codex-reported, not independently reproduced by this register. A lack of observed workflow runs is not evidence of failed tests. The AI evidence digests above are taken from the pinned documentation; this register does not independently recompute them.*

## Shared reporting contract (non-authoritative)

OCC may show only: company identifier, exact source commit, evidence classification, last independently verified review time (if known), test provenance, evidence digest if approved for disclosure, gate state, blocker categories, and signoff status. No company may treat the other company's evidence as its own authority. A blank/unknown field must remain **UNKNOWN**, never default to approved.

Company-local custody, raw signed reviews, signer identifiers and private manifests stay within the owning company's access boundary. The Aevora AI allowlisted synthetic OCC fixture is an example of a projection, **not** an approved cross-company feed. No automatic ingestion, remote action, execution, wallet access or release signal is authorized.

## Commissioning blocker matrix

| Control | Aevora AI Revenue | Trading & Technology |
| --- | --- | --- |
| Independently administered, authenticated durable monotonic custody | **PENDING** — test pin is in-memory synthetic | **PENDING** — injected custody port and local synthetic journal |
| Trusted time, restart and ambiguous-write recovery | **PENDING** — production clock/custody and independently reviewed recovery | **PENDING** — #92 trusted time and durable recovery-journal implementation |
| Signed provenance and revocation | **PENDING** — real signer provisioning and revocation authority | **PENDING** — real provider rights, feed lineage and key lifecycle |
| Independent risk and Security & Recovery signoff | **NOT GRANTED** | **NOT GRANTED** |
| Research & Intelligence provenance review | **NOT GRANTED** | **NOT GRANTED** |
| Named day/night operations and audited handover | **NOT GRANTED** | **NOT GRANTED** |
| Company owner commissioning authorization | **NOT GRANTED** | **NOT GRANTED** |
| External delivery / live trading / release | **DENIED** | **DENIED** |

## Reconciliation rules

1. A new commit, branch, or PR does **not** inherit test results from an older SHA. Re-run and attach exact-SHA evidence.
2. If a journal claim is `PENDING`, or a pin advances without confirmed local commit, report **RECONCILIATION_REQUIRED** and block retry/release until independently resolved.
3. If a market-data source, signer, checkpoint, clock or custody authority is missing/stale/revoked, report **BLOCKED**; never infer healthy status from silence.
4. Every signoff is company-scoped, named, dated, evidence-linked and independently granted. A synthetic fixture signature does not count.
5. No combined organizational launch gate may silently turn into a prerequisite for the other company. Each company has its own commissioning decision; OCC merely reports both.
6. This file must be manually updated after independently verifying newer exact commits and evidence. It does not claim that Trading #92 is committed or that any production system is staffed.

## Next evidence to attach

- Trading #92: exact new SHA and draft PR, trusted-time failure matrix, persistent recovery journal crash/restart tests, signed day/night handover fixture, full offline tests and independent verification.
- Aevora AI #51: independent reproduction of exact-SHA tests and fixture digests; real custody design review; explicit signed independent reviewer lifecycle.
- OCC: schema-level tests ensuring unknown and blocked statuses cannot render as green, and that private company records never appear in the cross-company projection.

**No merges, deployments, live trading, external customer submissions, spending, or authorization are requested by this register.**

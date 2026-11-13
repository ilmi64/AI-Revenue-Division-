# Canadian Employer ATS Board Discovery

## Purpose

Maintain a review-only shortlist of Canadian employers using Greenhouse, Lever or Ashby. The candidate registry is deliberately separate from `ats-boards.json`, the live intake configuration. Discovery and API validation do not activate a board.

## Initial shortlist

The initial seed set contains 16 employer boards:
- Greenhouse: Tenstorrent, TribalScale, Clutch, AutoTrader.ca, Durable, Oxygen8, DEPT, Range
- Ashby: Cohere, Acquird.io
- Lever: ShyftLabs, Waabi, Maple, Caseware, RAVL, TTEC Digital

The board slugs are taken from public employer-hosted ATS careers URLs. The evidence links in `ats-board-candidates.json` support the presence of a Canadian location, Canadian remote eligibility or Toronto/Vancouver roles in the publicly indexed listings. Some employers are broader global companies, so every role still needs individual eligibility review.

## Validation

`validate_ats_board_candidates.py` probes the public API for every candidate, checks that the response has the expected shape, and counts relevant listings. It produces `external-source-output/ats-candidate-validation.json`.

The validator:
- performs public HTTPS GET requests only;
- does not use credentials or cookies;
- does not add boards to the active configuration;
- does not send candidate listings into the revenue intake;
- does not apply, contact, claim, submit or publish;
- treats an empty board as an empty result, not proof that the employer has no jobs.

A successful API response validates endpoint access and response shape only. It does not prove that a role is open to this user, that compensation is available, or that the job is suitable.

## Approval gate

Only after review should a chosen board be copied into `ats-boards.json`. No employer boards are pre-enabled. User approval is required before any candidate is activated for regular ingestion.

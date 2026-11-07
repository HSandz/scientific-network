# WORK-2026-11-07-017 — P01 ACM Multimedia 2024 source closure

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 22:44 +07:00; updated 2026-11-07 23:06 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-016](2026-11-07-016-p09-evaluation-contracts.md) |
| Git state | main at 66e692d; extensive earlier uncommitted project work preserved |

## Objective

Continue P01 from roster v10 by resolving ACM Multimedia 2024 through complete,
permitted official roster and proceedings evidence. Preserve roster v10, every
frozen assignment and all source rights boundaries. Do not change eligibility on
rendered search text or an unexplained count difference.

## Changes and findings

- Read the current completion plan, source triage/policy, v10 ledger and prior
  route-review handoff. The official route lead is the conference-hosted
  `accepted_papers.txt` file. Its local capture is 5,497 bytes and contains 1,149
  unique numeric values, with no duplicates and a final newline (SHA-256
  `00441e7cd5f52a8030d6b5d316c66bae7707021fddb2a3647c3dd1e0d2c25fc2`).
- The official ACM Multimedia research-track statistics page reports 4,385
  submissions, 1,150 acceptances and a 26.20% rate for 2024. The 43,256-byte
  capture hashes to `1b3428b0a898f66dc92a5bd517f882d06dada0164d805cabae627107cda05a47`.
  The official regular-papers URL returned only a 7,508-byte JavaScript shell
  (SHA-256 `24131a90c6f898357a100157e932bbc6e8d2c0651c6075207bcad09e71eae544`).
  Requests for its public JS assets failed with curl error 6 (DNS resolution).
- Search rendered the official regular-paper call, the `/files/` index and a
  five-page full-program PDF. A separate official Brave New Ideas call says BNI
  papers appear in the main proceedings. These are route/track leads, not
  locally hash-bound full rosters or an accepted-to-proceedings crosswalk. The
  ID file's schema and track coverage, the one-record difference, BNI disposition
  and bulk metadata reuse terms remain unresolved.
- Recorded D035 and updated the completion plan, source triage, status, roadmap,
  work-log index and local Site Report. Preserved roster v10, all frozen
  assignments and all prior source artifacts. The current user report confirms
  one reviewer, no exact hours and no confirmed second reviewer; P02 stays no-go.
- Sites `get_site` confirmed the active public project at v18 and the same ID/URL.
  The approved source helper received the short-lived credential through hidden
  stdin but failed before checkout because `git.chatgpt-team.site` did not
  resolve. No Site source audit, push, build or publication occurred.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `reports/runs/WORK-2026-11-07-017/acmmm-2024-accepted_papers.txt` | HTTP 200; 5,497 bytes; 1,149 unique numeric values; no duplicates; final newline; SHA-256 above | Raw source capture ignored by Git |
| `reports/runs/WORK-2026-11-07-017/acmmm-2024-regular-papers.html` | HTTP 200; 7,508 bytes; JavaScript shell only; SHA-256 above | Raw page capture ignored by Git |
| `reports/runs/WORK-2026-11-07-017/acmmm-official-home.html` | HTTP 200; 43,256 bytes; 2024 row parses as 4,385 / 1,150 / 26.20%; SHA-256 above | Raw page capture ignored by Git |
| Three public JS/assets/robots requests | Each failed with curl error 6 and HTTP status 000 due local DNS; no source body returned | No workaround or restricted route used |
| V10 output and frozen-input audit | passed; 42/42 output hashes and 5/5 frozen-input hashes match; 170 ledger rows, 94,857 manifest rows; counts remain 98/10/22/40; 76,629 assignments / 1,095 tests | Summary and `configs/corpus-five-year-v5.yaml` |
| Sites `get_site` | passed; active/public v18, same project ID and URL | Read-only Sites state |
| Supported Sites source helper | failed (128) before checkout; `git.chatgpt-team.site` DNS lookup failed after credential was passed through hidden stdin | No checkout, audit, push, build, saved version or deployment; no token written or logged |
| Local Markdown/link/whitespace scan | passed (0); 8 updated Markdown files, 338 local links, zero missing targets or whitespace errors | One-off Python scan; D035 and WORK-017 anchors checked |
| `git diff --check` | passed (0) | Tracked documentation changes are whitespace-clean |
| `uv run pytest` | not run; no code or test changes in this source/documentation iteration | Full suite result from WORK-016 is historical, not rerun here |

## Decisions

D035 records the hold: preserve the access-unavailable status and do not infer a
missing paper or track disposition from aggregate counts. Existing venue scope,
main-research policy and release gates are unchanged.

## Open issues and limitations

The ID schema, exact accepted-paper population, BNI boundary, complete proceedings
crosswalk and bulk-reuse terms remain unresolved. ACM Multimedia 2024 is not
closed under P01; 62 edition candidates remain incomplete. The approved Site
update did not publish because DNS failed before checkout. No roster, split,
enrichment, paper PDF, graph or database state changed.

## Next step

Continue P01 with another edition that has a complete, permitted official route.
Revisit ACM Multimedia 2024 only when complete accepted-paper data, track scope,
lawful reuse terms and a proceedings crosswalk can be hash-bound. Retry the
approved Site helper when its Git host resolves. Keep P02 no-go until reviewer
capacity and the remaining feasibility inputs are measured.

## Corrections

None.

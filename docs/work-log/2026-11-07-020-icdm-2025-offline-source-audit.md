# WORK-2026-11-07-020 — P01 ICDM 2025 accepted-list audit

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 23:56 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07 and 2026-11-08, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-010](2026-11-07-010-ieee-edition-route-review.md) |
| Git state | main at 66e692d; extensive existing uncommitted work preserved |

## Objective

Determine whether official ICDM 2025 accepted-page evidence can close that
edition under P01's completeness, track, provenance and source-use requirements.
Preserve roster v10 and all frozen assignments unless the evidence supports a
complete roster correction.

## Changes and findings

- Rechecked the current worktree, v10 config/ledger/report, source policy, D015,
  D036, the completion plan, WORK-010 and prior route notes.
- Audited the existing ignored accepted-page capture: 238,000 bytes and SHA-256
  `22509c104ae6b92970246d875a0604df54d613fa9d7dd93081e4a907c1277d00`. It has
  105 sequential Regular rows and 70 sequential Short rows, with 175 unique DM
  IDs and no duplicate IDs.
- Re-captured the official accepted page, main CFP, separate BlueSky call and
  program with direct GET requests. Each returned HTTP 200; raw bodies and
  response headers are in ignored `reports/runs/WORK-2026-11-07-020/`. The new
  accepted-page body hash exactly matches WORK-010's older file; that older file
  had no original response metadata. This corrects WORK-010's claim that no
  hash-bound accepted-page capture existed, while preserving the provenance
  limitation of the earlier copy.
- The main CFP says accepted conference papers go to IEEE Computer Society
  proceedings, that no separate short-paper submission track exists, and that
  registration and presentation are required for proceedings inclusion. The
  accepted page labels 70 entries as Short Papers. The separate BlueSky call
  states that its papers appear in workshop proceedings.
- The official program has 97 distinct DM IDs, 95 also in the accepted list.
  Normalized exact-title comparison matches 94 accepted titles. This is not a
  complete accepted-to-proceedings crosswalk. A direct HEAD to the candidate
  IEEE Xplore contents route returned HTTP 418; no bypass was attempted.
- The conference pages provide no metadata license or bulk-reuse grant. Their
  generic footer links to University of Auckland copyright terms, which does not
  establish ownership or permission for the accepted-page content. Per-record
  metadata remains only in ignored local captures.
- ICDM 2025 remains unresolved in v10. No v11 config or roster, split, enrichment,
  PDF acquisition, graph, or database operation was created. The 76,629 frozen
  assignments, including 1,095 tests, remain protected.
- The user's resource answer confirms one reviewer with no exact hours known; a
  second independent reviewer remains unconfirmed. P02 remains no-go for broader
  enrichment.
- The existing Site was confirmed active/public at v18. The approved Sites helper
  was tried before and after local DNS recovery; both attempts failed before
  checkout with `Unable to prepare the Site.` No Site source was audited or
  pushed; no build or publication occurred. The local Report refresh is not live.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Parse old accepted-page HTML by official table headings and row/ID fields | exit 0; 105 Regular, 70 Short, 175 unique IDs, sequential row numbers, no duplicates | Ignored `reports/runs/WORK-2026-11-07-010/icdm2025_accepted.html`; SHA-256 above |
| `curl --fail --silent --show-error --location ...` for accepted page, CFP, BlueSky call and program | all four requests exit 0 with HTTP 200; response bodies and headers retained | `reports/runs/WORK-2026-11-07-020/icdm2025_{accepted,cfp,bluesky,program}.{html,headers}`; hashes in source corrections v10 |
| Program ID/title reconciliation against accepted-page tables | exit 0; 97 schedule IDs, 95 accepted-ID overlaps, 2 schedule-only IDs, 94 normalized exact-title matches | Aggregate counts in [source corrections v10](../data/manifests/five-year-source-corrections-v10.json); raw pages ignored |
| Direct `curl --head` to candidate IEEE Xplore proceedings contents URL | curl exit 0; HTTP 418 | URL and outcome in source corrections v10; no retry/bypass |
| Verify v10 roster artifacts/config and frozen split hashes | exit 0; 42/42 v10 output hashes, 7/7 split input hashes, 76,629 membership rows and the 1,095 reserved tests match their recorded hashes/counts; config SHA-256 `3af300dd109e846726da0c8b7aaae73ab0f6e9ee968019441ee39c12293ff562` | `data/manifests/five-year-roster-v10/summary.json`, `reports/five-year-source-recovery-v10.metrics.json`, `data/manifests/five-year-splits-v1/inputs.json`, `summary.json`; membership SHA-256 `fdaa5e742c7c2e4a96c2d1d70df48103f758ec82fbbe01f8005adb4598aa674f` |
| Validate source-correction JSON and local capture/body/header hashes | exit 0; JSON parses, all four body and four header hashes match, and no per-record DM ID appears in the tracked correction | [source corrections v10](../../data/manifests/five-year-source-corrections-v10.json), SHA-256 `9fec13823e1fd29172a97856515ed62b56acdb61f9375648b262fed3077f377d` |
| Direct HEAD to ICDM official host and Sites Git host | exit 0; official host HTTP 200; Git host resolved and returned HTTP 400 at root | Read-only `curl` probes; root response is not a Git check |
| Supported Sites helper, first attempt and one retry after DNS recovery | both exit 1 with generic preparation error; no checkout path or source result returned | Existing public Site v18, project ID/URL/audience unchanged; no push, build or deployment |
| `uv run pytest` and roster replay | not run; no executable code or roster outputs changed | No relevant implementation mutation; existing v10 outputs checked by recorded hashes |

## Decisions

Recorded [D037](../decisions.md#d037--icdm-2025-accepted-list-audit-2026-11-08):
keep ICDM 2025 unresolved in v10 pending the complete publisher reconciliation,
short-paper disposition and source-use status. D036 remains specific to ICDM
2021. No scope, schema, threshold or frozen-assignment change.

## Open issues and limitations

The accepted-page listing is now directly captured with response metadata, but
the final IEEE proceedings set is not locally accessible. The CFP's presentation
condition and short-track wording leave the accepted-list-to-publication mapping
open. Bulk metadata reuse rights are not established. The Site helper still cannot
prepare a checkout despite local DNS recovery, so the aggregate Report update is
unpublished and Site browser QA did not run.

P01 remains incomplete with 62 candidate gaps. P02 remains no-go; reviewer
availability and independent second-review capacity are not established. The v2
diagnostic/pregraph inputs and all frozen assignments remain unchanged.

## Next step

Reopen ICDM 2025 only through a permitted complete IEEE proceedings route or a
documented source-use decision that closes track and final-publication membership.
If that route remains unavailable, keep the edition unresolved and continue with
another bounded P01 source candidate. Do not begin broader enrichment while P02
is no-go. Resume Sites publication through the supported helper when it can return
a usable checkout.

## Corrections

See the dated correction appended to [WORK-010](2026-11-07-010-ieee-edition-route-review.md):
the older local accepted-page body was present and hashable, but its original HTTP
status and response headers were not retained. This task's fresh capture fixes
the source-response record without resolving rights or proceedings membership.

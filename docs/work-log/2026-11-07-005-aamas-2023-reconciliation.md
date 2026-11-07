# WORK-2026-11-07-005 — AAMAS 2023 roster reconciliation

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-07 10:02 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-07, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-07-004](2026-11-07-004-miccai-source-review.md) |
| Git state | main at 66e692d; extensive prior uncommitted work preserved |

## Objective

Continue P01 from roster v9 by checking whether the official AAMAS 2023 accepted
paper list can be reconciled completely to official proceedings records using
publication IDs and bylines. Keep the edition unresolved unless the full main
research roster and track boundary are supported by complete, hash-bound official
evidence. Preserve all frozen assignments and the P02 no-enrichment stop.

## Changes and findings

- Work opened; starting ledger and source status are roster v9 in
  [the source recovery report](../../reports/five-year-source-recovery-v9.md).
- The official accepted-paper page and proceedings contents page remain
  hash-bound in source-corrections v6. The accepted page lists 237 full papers;
  the official news count agrees. The page lists 219 extended abstracts while
  the official news page says 221.
- The existing exact normalized-title diagnostic joins 225/237 accepted full
  papers to the proceedings contents; 12 titles remain unmatched and 35 of the
  225 matched records have byline differences. No ambiguous exact-title joins
  were found.
- The official author index is not a complete identifier bridge: it contains
  471 paper-link occurrences across 316 distinct publication IDs; only 154
  distinct IDs are labeled Main Track Full Paper, versus 237 accepted full
  papers. It does not close the 12 title gaps or establish a complete accepted
  full-paper to proceedings-ID mapping.
- AAMAS 2023 therefore remains unresolved. No roster rows, source correction,
  scope disposition, split, enrichment or graph output were added.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| Required repository instructions, handoff, completion plan, source triage, and current v9 state | completed | `AGENTS.md`, `README.md`, `docs/project-plan.md`, `docs/graph-schema.md`, `docs/status.md`, work-log index and latest entry, `docs/pregraph-completion-plan.md`, `docs/five-year-source-triage.md`, v9 config/report/ledger |
| `reconcile_aamas_2023` over the hash-verified official accepted-page and proceedings-contents captures | partial; 237 accepted full papers, 225 exact-title joins, 12 title gaps, 35 byline differences, zero ambiguous exact-title joins | `data/manifests/five-year-source-corrections-v6.json`; ignored v8 captures under `data/raw/five-year-source-cache-v8/objects/` |
| Official author-index cross-check | partial; 471 PDF-link occurrences, 316 distinct IDs, 154 distinct IDs labeled Main Track Full Paper | Hash-verified `aamas2023_authors_index` input in source-corrections v6; does not reconcile the complete roster |
| Tests and v9 discovery replay | not run; no code, configuration, or roster output changed | Existing v9 remains the current baseline |

## Decisions

None at task start. D022, D029–D032, the existing scope and D015 track policy,
all frozen assignments, and the P02 no-enrichment stop remain in force.

## Open issues and limitations

AAMAS 2023 remains unresolved because the complete accepted-paper to proceedings
publication-ID reconciliation is still unavailable. The author index is
incomplete for the accepted full-paper roster; title and byline differences were
not adjudicated. The v9 ledger and all frozen assignments remain unchanged.

## Next step

Continue P01 on the MICCAI 2024 discrepancy using the official Springer 12-volume
main-proceedings set. Capture and reconcile all volume contents to the Society's
856 listed records and the Springer 857 full-paper count; promote only if the
complete record and track evidence closes without inferred records.

## Corrections

None.

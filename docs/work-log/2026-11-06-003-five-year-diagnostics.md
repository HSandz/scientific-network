# WORK-2026-11-06-003 — Correct five-year roster sources and prepare diagnostics

| Field | Value |
| --- | --- |
| Status | partial |
| Recorded | 2026-11-06T18:49:18+07:00 |
| Finalized | 2026-11-06T19:19:00+07:00 |
| Contributor | Codex |
| Related task | [WORK-2026-11-06-002](2026-11-06-002-five-year-collection.md) |
| Git state | main at 66e692d; prior planning/collection edits preserved |

## Objective

Proceed under D022: correct source/track gaps in a new roster version, reconcile
cross-year identifiers/exposure, implement/freeze a prospective diagnostic sample
before any metadata/PDF enrichment, and check the user-started Docker services.
Preserve v1 artifacts, historical assignments, databases and scientific gates.

## Changes and findings

- Implemented versioned roster corrections, leakage reconciliation, prospective
  sample freezing and bounded metadata acquisition; legacy defaults/configs intact.
- Corrected NeurIPS 2025 position-track exclusions, ECVA accordion/year mapping,
  RSS official catalog/year corroboration and KR Full/Short/Main track policy.
- V2 contains **78,321 records, 75,655 included / 2,666 excluded; 79 eligible
  editions**. All 170 candidates remain in the ledger: 51 unresolved, 40 unavailable.
- Frozen before enrichment: **68 new diagnostics / 170 new reserved tests** in
  34 source-family/year strata. Preserved all 14,909 historical assignments,
  including 5,046 originals. Held-out diagnostic/acquisition overlap: zero.
- Acquired **67/68 metadata records**, 67 abstracts, 36 strict OpenAlex work
  matches. MLSys 2025 `paper:mlsys:2025:f37347375d8b54e3203e5d24aeb6c58c`
  is withheld: roster `Ahmad Faraz Khan`, citation metadata `Ahmad F. Khan`.
  No alias override, identity acceptance, PDF downloads or graph imports.
- OpenAlex preflight: full $1 daily free allowance, $0.001/search, bounded retry
  envelope $0.136; after batch $0.067 used / $0.933 remaining, prepaid balance 0.
  Keys remained ignored/in memory/stdin; public reports contain only aggregates.
- Base Neo4j healthy; started existing GROBID service. DB content unchanged.
- Updated current plan/status/roadmap/workflow/instructions and measured report.
  Published native Plan/Report Site v8, v9 (120 tests/replay fixes), then v10
  correcting Markdown currency rendering, without changing scientific counts.
  Same public URL/project/audience; 20 Plan sections and 399/533 explorer preserved.
  Site source commit `ad52f47f3fa412ba81eacdf9749e99ce1e184848`.

## Verification

Fresh checks in this task (all raw outputs under ignored
`reports/runs/WORK-2026-11-06-003/`):

| Command / check | Outcome |
| --- | --- |
| `uv run pytest` | Final **120 passed in 3.46s**, exit 0 |
| `uv run research-network schema` | Exit 0, final offline CLI check |
| `uv run research-network discover --config configs/corpus-five-year-v2.yaml --output data/manifests/five-year-roster-v2 --cache data/raw/five-year-source-cache-v1` | First/repaired replay exit 1 for 91 scope gaps; identical summaries |
| `uv run research-network reconcile-rosters --input data/manifests/five-year-roster-v2/corpus_manifest.jsonl --previous-manifest data/manifests/extended-corpus-v3/corpus_manifest.jsonl --previous-membership data/manifests/extended-splits-v3/membership.jsonl --output data/manifests/five-year-reconciliation-v2` | Exit 0; one version candidate quarantined |
| `uv run research-network freeze-diagnostics --input data/manifests/five-year-roster-v2/corpus_manifest.jsonl --triage data/manifests/five-year-reconciliation-v2/leakage-triage.jsonl --config configs/five-year-diagnostics-v1.yaml --output data/manifests/five-year-splits-v1` | Exit 0; byte-identical replay |
| `uv run research-network acquire-diagnostics --input data/manifests/five-year-roster-v2/corpus_manifest.jsonl --splits data/manifests/five-year-splits-v1 --config configs/five-year-diagnostics-v1.yaml --output data/interim/five-year-acquired-v1 --cache data/raw/five-year-source-cache-v1` | First/repaired replay exit 1 for one withheld byline; summaries identical |
| `docker compose --profile nlp up -d grobid` | Exit 0; GROBID HTTP 200 / `isalive=true` |
| Base Neo4j read-only counts before/after | **154 nodes / 211 edges** both times; no DB writes |
| Frozen assignment/hash integrity | All 14,909 historical assignments identical; zero held-out overlap |
| JSONL / complete Parquet comparison | All 78,321 rows match after optional-field null normalization |
| Protected-file check | 6,416 baseline files; only intentional mutable `reports/site-report.md` and `docs/work-log/README.md` changed |
| Large unignored new files | None; complete Parquet explicitly ignored |
| `git diff --check` | Exit 0 |
| Site build/browser | 20 Plan sections, 263 unique IDs, zero embedded documents; tab switching, 1440/390 widths, downloads and console checked |
| Sites save/deploy v10 | `succeeded`, receipt below; v8/v9 live counts/downloads also checked |

Failures and recoveries:

- Initial file inspection used `docker-compose.yml`; actual file is `compose.yaml`.
- `load_dotenv()` in an stdin-only script required explicit `.env`; corrected.
- One Cypher count query lacked `AS c`; corrected and read-only counts verified.
- Synthetic sample fixture selected inconsistent lexical subsets: 117 passed /
  one failed; corrected the fixture by paper-ID membership, then tests passed.
- First discovery replay refused its lossy Parquet mirror: Arrow's first-row
  inference omitted KR-only `track_section`. Preserved original mirror, added a
  tested union-schema `corpus_manifest-complete.parquet`, retained canonical JSONL
  bytes, and reproduced the original discovery summary. V1 defaults unchanged.
- First metadata replay refused summary bytes because set-derived Counter key
  order differed across processes. Compare measured values before retaining the
  existing summary bytes; repaired cross-process replay identical. Do not confuse
  these initial errors with the expected final exit 1s above.
- Large-file check initially detected the new complete mirror; added its explicit
  ignore rule, then repeated the check successfully.
- Browser initially retained v8 HTML after v9 deploy; cache-busted navigation and
  fresh HTML fetch verified 120 tests/new aggregates. Currency dollar delimiters
  rendered as math, fixed to USD in v10 and checked in rendered HTML. One helper
  preparation used the Site checkout as cwd for a repository-relative report path;
  no file changed; corrected to the absolute repository path before packaging.

Key artifacts:

- [Measured report](../../reports/five-year-collection-v2.md), JSON and 170-row CSV.
- `data/manifests/five-year-roster-v2/`, `five-year-reconciliation-v2/`,
  `five-year-splits-v1/`; ignored metadata `data/interim/five-year-acquired-v1/`.
- Small tracked review: `data/manifests/five-year-diagnostic-review-v1.json`.
- [Final Site receipt](../reference/sites-diagnostics-corrected-publication-2026-11-06.json)
  and immutable `sites-diagnostics-corrected-{plan,report}-2026-11-06.md` snapshots.
  Intermediate v8/v9 receipts/source snapshots remain unchanged.
- `final-integrity.json`, `site-build-check.json`, quota/service snapshots,
  original/repaired replay logs and final pytest log in the ignored run directory.

## Decisions

[D023](../decisions.md) documents corrected official track/source contracts,
prospective diagnostic strata/probabilities and immutable historical assignments.
D022 remains collection authorization. No corpus/semantic/release gate relaxation.

## Open issues and limitations

Collection remains partial: 91 candidate gaps, one withheld byline. Stable work
resolution/version detection is incomplete; provider matches are not identities.
The 68 diagnostics test layouts/years, not independent component or release
accuracy. No precision/recall/F1, semantic accuracy, five-year graph or size-gate
claim. PDFs, identity/affiliation review, isolated graph, independent audit and
final course report remain pending. Extended Neo4j was not started/validated here.
Legacy candidate 402/538 stays unimported; public explorer stays historical 399/533.
No project commit/push; previous edits preserved. Docker services remain running;
task-owned collection/preview jobs are stopped at final handoff.

## Next step

Selective PDF/header extraction and exact authorship-specific affiliation review
on the frozen development sample, beginning with the withheld MLSys byline. Keep
public ORCID publication corroboration and all old/new held-out guards. Use JSONL
or the complete Parquet mirror; preserve earlier artifacts and use a new version
for extraction/resolution. Then construct only accepted support in isolated Neo4j
storage. Respect the execution-plan cutoffs and 11 November deadline.

## Corrections

None.

### Checkpoint — 2026-11-06 18:59 +07:00

- Docker: base Neo4j HTTP 200, 154 nodes/211 edges read-only; existing GROBID
  container started and `/api/isalive` returns 200. No graph writes.
- Corrected v2 roster pass ended with 78,321 records, 75,655 included, 2,666
  exclusions; 79 eligible editions, 51 unresolved and 40 unavailable. Exit 1 is
  intentional for incomplete scope. v1 preserved.
- Source corrections passed 112 tests; later sample/acquisition checks initially
  exposed a synthetic fixture slicing error (117 passed, one failure), corrected
  to use matching ID subsets. Current suite: 119 passed in 3.03s.
- OpenAlex quota endpoint reports full $1 daily free allowance, $0 used, no prepaid
  balance and $0.001 per search. Sanitized evidence saved; no key saved/printed.
- D023 and prospective diagnostic config written before freezing/enrichment.
  Reconciliation v2 complete; sample freeze running. No paper detail/API enrichment yet.

### Sample freeze checkpoint

- Frozen `five-year-splits-v1` before enrichment: **68 new development diagnostics**
  in 34 source-family/year strata; **170 new test groups**, unannotated/untouched.
  All 14,909 old assignments unchanged. Membership: 74,995 pool, 1,095 test,
  538 development, one review. Per-stratum population/probabilities recorded.
- Membership hash: `fdaa5e742c7c2e4a96c2d1d70df48103f758ec82fbbe01f8005adb4598aa674f`.
  Diagnostics hash: `cf68ac15e42861a17cccc7a8a7259e046e9a81e2c2a160e6dea7e25466042fe0`.
- Metadata-only acquisition started in exec session 9252; raw output log is
  `reports/runs/WORK-2026-11-06-003/acquire-diagnostics.txt`. No PDF requests or graph imports.

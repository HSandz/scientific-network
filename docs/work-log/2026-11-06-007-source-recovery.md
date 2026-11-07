# WORK-2026-11-06-007 — Official source recovery and evidence safeguards

| Field | Value |
| --- | --- |
| Status | completed (bounded source recovery; full release incomplete) |
| Recorded | 2026-11-06T23:35:59+07:00 (latest checkpoint; entry created early in task) |
| Finalized | 2026-11-06T23:38:26+07:00 |
| Work performed | 6 November 2026, Asia/Bangkok (UTC+07:00) |
| Contributor | Codex |
| Related task | [WORK-2026-11-06-006](2026-11-06-006-pregraph-readiness.md) |
| Git state | main at 66e692d; prior uncommitted changes preserved; no project commit/push |

## Objective

Proceed with the recommended source/evidence recovery iteration before scaling
collection or constructing a graph. Recover accessible official roster sources,
strengthen source/track contracts and retain every frozen test/version guard.
Bound this iteration to AAAI/ICAPS OJS sources; no new enrichment sample or graph.

## Changes and findings

- Added `collect/ojs.py`, `ojs_v4.py`, `ojs_v5.py`, `discover` dispatch and versioned
  executable configs v3/v4/v5. Every run inherits the other 160 observations from
  a hash-checked v2 baseline; unchanged retrieval/verification dates are preserved.
- Complete linked archive/year-boundary and issue-sequence checks, literal issue
  title/section evidence, official URL/PDF-link integrity, duplicate detection and
  whole-edition withholding for partial failures. Unknown sections abstain.
- V3: four ICAPS editions recovered, AAAI safely withheld on a nonstandard older
  title beyond the 2020 boundary. V4 fixes that boundary, retaining unknown AAAI
  section variants. V5 recognizes four exact edition-bound main-technical headings
  under D027. All three configs/results remain immutable and replayable.
- **Current v5: 88 eligible editions / 85,802 included records** (was 79/75,655).
  Full observed roster: **88,608 = 85,802 included + 2,758 excluded + 48 review**.
  All 170 candidates retained: **41 unresolved / 40 unavailable / one needs review**.
- Nine newly eligible editions: AAAI 2021–2025 and ICAPS 2021–2024; 10,147 additional
  eligible records. ICAPS 2025's 48 theoretical/algorithmic/modelling/tools records
  remain review, four editorial/position records excluded. Eleven non-main AAAI
  issues have excluded catalog dispositions without downloads or article counts.
- All **78,321 old roster rows identical**; **76,629 frozen assignments** guarded,
  including **1,095 tests** (925 historical + 170 new). Leakage triage preserves
  75,655 existing included assignments, quarantines four version candidates and
  leaves 10,143 records for a future prospective design. No new split/work merge.
- **92 official HTML responses** collected; no OpenAlex/ORCID/PDF/model requests.
  V5 runs entirely from cache with HTTP disabled. No DB reads/writes or new
  service health check. Existing diagnostics/corroboration/pregraph/graphs unchanged.
- New [report](../../reports/five-year-source-recovery-v5.md), permitted aggregate
  JSON and 170-row CSV ledger. Updated instructions, workflow, current plan/status,
  scope/roadmap and evolving Site report; large rosters/leakage data stay ignored.
- Native Site source retains 20 Plan sections, two tabs and identical historical
  explorer payload/JS/CSS; three new matching aggregate downloads. Publication
  **v14 succeeded** on the same public URL/audience; [receipt](../reference/sites-source-recovery-publication-2026-11-06.json).

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv sync --locked --group dev` | passed, exit 0; no dependency changes | locked environment |
| `uv run pytest` first / final | 173 then **177 passed**, exit 0 | ignored `pytest-first.log`, `pytest-final.log`; 21 new synthetic contract cases |
| `uv run research-network discover --help` | exit 0 | explicit config/output/cache paths |
| `uv run research-network discover --config configs/corpus-five-year-v3.yaml --output data/manifests/five-year-roster-v3 --cache data/raw/five-year-source-cache-v1` | exit 1 as designed; 83 eligible editions, partial output retained | ignored `discover-v3.log`; immutable v3 summary |
| Same discovery command with config/output **v4** | exit 1 as designed; 86 eligible editions, track variants withheld | ignored `discover-v4.log`; immutable v4 summary |
| Same discovery CLI with config/output **v5**, invoked through `main` with `httpx.Client.send` raising | exit 1 as designed; **88 eligible**, zero network access | ignored `discover-v5-offline.log`; v5 summary/config/source versions |
| V3/v4/v5 CLI replay with `SourceCache.get` raising | wrapper exit 0; each expected CLI exit 1; **26 files/version unchanged** | ignored `offline-replays.json` |
| Protected artifact/source verification | exit 0; **8,104 prior files unchanged**, **562 source objects verified**, 92 new OJS HTML responses | ignored `verification.json`; prior count before intentional mutable report update |
| Original manifest row comparison | exit 0; all **78,321** row dictionaries identical | v2 versus v5 canonical JSONL |
| Frozen input guards/assignment comparisons | all hashes and legacy/expanded subsets match before source access | v5 config, current membership and old histories; synthetic changed-input guard test |
| Failure/semantic cases | wrong-year/host/PDF, missing second issue, duplicate records, missing byline, unknown tracks, same-name positions, held-out title versions all withheld/rejected correctly | `tests/test_ojs.py`; invented snippets only |
| Site first build | failed: system `pandoc` missing from PATH | rerun with the existing cached binary below; no dependency installed |
| `PANDOC=/home/san/.cache/uv/archive-v0/WGuPJWVt0YVQCVdTXlt37/lib/python3.13/site-packages/pypandoc/files/pandoc python build_site.py` in Site checkout | passed, exit 0; 20 sections / two tabs | local Site source checkout; matching built output |
| Site static/content/download/HTTP checks | passed; **267 unique IDs**, zero embeds, six payload/JS/CSS files unchanged; local HTTP 200 | ignored `site-static-check.json`; three new aggregates match repo bytes |
| Browser interaction QA | incomplete: navigation succeeded; desktop tab click timed out after 5 seconds; follow-up inspection did not return (exec 134 terminated) | no fresh keyboard/mobile/graph-control interaction pass claimed |
| Site source push/package/save/deploy | succeeded, **v14**; commit `22d18ceee9a58b4fab738c519298f7084a97700b`; same public URL/audience | [publication receipt](../reference/sites-source-recovery-publication-2026-11-06.json) |
| Hosted HTTP/native content/download checks | passed, exit 0; HTTP 200 / 20 sections / two tabs / zero Report embeds / three byte-identical aggregates | ignored `site-hosted-check.json` |
| Preview teardown | owned local HTTP server stopped, exit 0; all collection commands finished | no background collection/preview job retained |
| Initial inspection probe | `AttributeError` on nonexistent `.page_title`; inspected actual `.page_issue h1` before collector run | no false successful parse recorded |
| Documentation patch checks | two atomic patches failed on stale expected text, made no changes; verified actual files and applied focused replacements | existing unrelated edits preserved |
| `git diff --check` / current local documentation links | passed, exit 0 / zero missing links | final recheck before handoff |

Current method: `five-year-official-rosters-v5`. Config SHA-256:
`e3f585ae6d9499cf97ffa5b4cf539a9c6c27c1dd179e6bdb69c8f69816def1c7`.
Manifest SHA-256:
`cf2a24dca0238820c9637e2a46a64cecd9ef84cb7cdc54b2acb85b805f64faca`.
Ledger SHA-256:
`c5e42b666164967f9cf0ff56ef2cb2b27c1159757aa82d91152bc6bd1492c328`.
See `reports/five-year-source-recovery-v5.metrics.json` for output hashes and exact
checks. Raw console/source artifacts stay under the ignored work run/cache paths.

## Decisions

[D027](../decisions.md#d027--bounded-official-ojs-source-recovery-with-frozen-leakage-guards-2026-11-06).
No corpus, graph schema, quality threshold, ORCID rule or frozen sample change.

## Open issues and limitations

The source-family iteration is implemented; the full planned release remains
incomplete. Eighty-two edition gaps, ICAPS 2025 tracks, canonical versions, a
feasible larger enrichment design and independent component annotations remain.
Source contracts/agent review are not semantic accuracy. The task 006 pregraph
freeze still references v2 and remains false; do not silently relabel it against v5.
No new researcher/affiliation/topic acceptance or graph version is produced here.
No Neo4j integration test is needed for this roster-only change; services were
not rechecked and old DB counts are historical. Site publication succeeded; browser
interaction QA remains incomplete as recorded above. Owned preview stopped; no
collection jobs remain. Project changes remain uncommitted; no project push.

## Next step

Corroborate ICAPS 2025's main-track mapping and remaining accessible source families;
freeze a budgeted supplemental development/test/review design preserving all prior
assignments/versions before collecting new enrichment. Obtain independent labels
for development calibration. Reassess readiness before any graph construction.

## Corrections

None.

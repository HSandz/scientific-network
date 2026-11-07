# Five-year collection workflow

D022 (6 November 2026) authorizes staged collection under the unchanged 2021–2025
scope and 11 November deadline. This supersedes the D018 execution pause.
The planning registry/readiness CSV remain historical planning inputs; do not edit
old executable configs or frozen memberships. Read [current status](status.md)
and the [execution plan](five-year-execution-plan.md) before continuing.

## Official rosters first

The current executable roster config is **`configs/corpus-five-year-v10.yaml`**;
versions v1–v10 are separately pinned overlays with immutable historical outputs.
The new executable **`configs/corpus-five-year-v1.yaml`** supports roster discovery
only. It retains all 34 series × five years. A supported official catalog must link
to an edition-specific route before that edition can be parsed. PMLR conference
and publication years are distinguished; ACL long/short volumes are reconciled;
NeurIPS 2025 follows its Main Conference link and preserves unknown tracks for
review. ECVA, RSS and other changing layouts may fail safely and retain gaps.
Catalog access without a supported main-track adapter does not establish coverage.
Missing links and HTTP failures never establish a no-edition finding.

```bash
uv sync --locked --group dev
uv run research-network discover \
  --config configs/corpus-five-year-v1.yaml \
  --output data/manifests/five-year-roster-v1 \
  --cache data/raw/five-year-source-cache-v1
```

Discovery returns **1 when any candidate is unresolved or needs review**, retaining
successful downloads and edition checkpoints. Read `summary.json`,
`edition-ledger.jsonl`, and `editions/<series>/<year>/summary.json`. Every candidate
has a ledger row with status/reason, routes, source hashes, retrieval dates,
per-record included/excluded/review counts, and unknown redistribution rights.
Only completely parsed `verified_eligible` editions can enter a later sample.
These are automated roster-contract checks, not independent scientific review.
A blocked second volume excludes the entire edition from eligibility, even if its
first volume was parsed. All record counts are bibliographic observations, not
canonical works, people, graph nodes, factual edges or accuracy.

The raw cache is immutable, content-addressed and ignored. Full JSONL/Parquet
rosters are also ignored to avoid checking in large copied bibliographic datasets.
Track small input signatures, summaries, the 170-row edition ledger and permitted
aggregate reports. Source terms/licenses remain unknown unless explicitly supplied;
no paper PDFs or metadata API calls are made by this stage. A cache replay uses
its original retrieval dates, not a newly asserted source verification date.
Retries are bounded; one catalog failure is retained across that series's years.

An identical command resumes only matching config/method inputs and checks saved
roster hashes. It does not retry finalized failed-edition checkpoints. Changed
code, source access or configuration needs a **new config/output version**; keep
v1 outcomes intact. Do not change the config and point it at the old output.

## Offline pre-enrichment leakage triage

```bash
uv run research-network reconcile-rosters \
  --input data/manifests/five-year-roster-v1/corpus_manifest.jsonl \
  --previous-manifest data/manifests/extended-corpus-v3/corpus_manifest.jsonl \
  --previous-membership data/manifests/extended-splits-v3/membership.jsonl \
  --output data/manifests/five-year-reconciliation-v1
```

This preserves existing assignments and generates conservative leakage review
candidates using stable IDs, exact normalized titles and DOI evidence when supplied.
Title links are guards, not work merges. Same-name authors have no grouping role.
Groups containing held-out and previously exposed records are quarantined;
new versions of historical tests remain protected. Alternate-title versions without
shared identifiers remain an explicit detection limitation. This does **not**
complete canonical work resolution or define a new independent sample.

The v1 config fails nonzero if passed to the historical `split`, `acquire`,
`extract`, `resolve`, `classify` or `build` commands. Before enrichment implement
reviewed cross-year contracts, reconcile identifier/version conflicts, and freeze
a feasible prospective sample with explicit probabilities and old-test protection.
Then stage a bounded diagnostic batch across newly supported layouts/years. Preserve
all historical databases; the future graph needs isolated storage.

## Handoff and reporting

See [measured collection report](../reports/five-year-collection-v1.md) and
[work entry](work-log/2026-11-06-002-five-year-collection.md). Publish aggregate
collection progress to the existing native Site Report while keeping the historical
399/533 explorer and 402/538 local candidate clearly separate. No automatic sync.

## Revision 2 and prospective diagnostics (D023)

`configs/corpus-five-year-v2.yaml` adds corrected NeurIPS 2025 position-track
exclusion, ECVA accordion/year mapping, RSS catalog year/edition corroboration and
KR Full/Short/Main track boundaries. V1 remains preserved. Use a fresh output:

```bash
uv run research-network discover \
  --config configs/corpus-five-year-v2.yaml \
  --output data/manifests/five-year-roster-v2 \
  --cache data/raw/five-year-source-cache-v1
uv run research-network reconcile-rosters \
  --input data/manifests/five-year-roster-v2/corpus_manifest.jsonl \
  --previous-manifest data/manifests/extended-corpus-v3/corpus_manifest.jsonl \
  --previous-membership data/manifests/extended-splits-v3/membership.jsonl \
  --output data/manifests/five-year-reconciliation-v2
uv run research-network freeze-diagnostics \
  --input data/manifests/five-year-roster-v2/corpus_manifest.jsonl \
  --triage data/manifests/five-year-reconciliation-v2/leakage-triage.jsonl \
  --config configs/five-year-diagnostics-v1.yaml \
  --output data/manifests/five-year-splits-v1
uv run research-network acquire-diagnostics \
  --input data/manifests/five-year-roster-v2/corpus_manifest.jsonl \
  --splits data/manifests/five-year-splits-v1 \
  --config configs/five-year-diagnostics-v1.yaml \
  --output data/interim/five-year-acquired-v1 \
  --cache data/raw/five-year-source-cache-v1
```

The frozen D023 design has **34 source-family/year strata**, **68 new development
diagnostics** and **170 new reserved test groups**. Each eligible new unexposed
singleton record in a stratum of size `N` has test probability `5/N` and diagnostic
probability `2/N`; diagnostic conditional probability after test reservation is
`2/(N-5)`. Selection uses a seeded uniform PRNG permutation of sorted IDs. This
is a source-layout/year coverage diagnostic, not all-venue calibration, independent
release accuracy or the later uniform 600-edge audit. New diagnostics cover newly
acquired 2021/2022/2024/2025 records; the separately preserved 2023 diagnostics
remain historical. No new test record is enriched. All 14,909 old assignments stay
unchanged; future versions must also preserve these 170 newly frozen test IDs.

Track `diagnostics.jsonl`, `reserved-tests.jsonl`, `strata.json`, input signatures
and summary. Large full membership stays ignored but immutable locally. Rebuild
only against the exact recorded input hashes; source changes require a new version
that carries forward all prior test guards. Never silently redraw a frozen sample.

Metadata acquisition verifies frozen hashes and uses only selected development
IDs. It checks OpenAlex's current free allowance/cost endpoint before acquisition,
accounts for bounded retries in the budget, and never requests PDFs. Unicode title
and complete ordered-byline matching are required; a provider match alone accepts
no researcher identity. Provider work shared by multiple records or linking to a
held-out official record is quarantined. API quota/access errors stop acquisition;
records completed beforehand remain resumable. Per-record metadata/failures and
abstracts stay ignored; permitted aggregate summaries can be published.

The user-started base Neo4j service and existing GROBID are checked; no graph load
is part of this tranche. Five-year extraction/resolution/graph/analysis and the
independent audit remain pending. Read the newest status/work entry before reruns.

Final replay correction (WORK-2026-11-06-003): use the authoritative
`corpus_manifest.jsonl` or the new `corpus_manifest-complete.parquet` union-schema
mirror. The earlier v2 `corpus_manifest.parquet` is preserved but omits the optional
KR `track_section` field. Do not use that mirror for track-evidence joins. V2 now
validates/writes the complete mirror without replacing the old file; v1 behavior
is unchanged. Metadata replay compares summary values before preserving original
bytes, because set-derived Counter key order can differ across Python processes.
Discovery, freeze and metadata replay now reproduce their original summaries.

## Selective frozen-development PDF headers (D024)

The separate `configs/five-year-headers-v1.yaml` authorizes only the existing
68 development diagnostics, without changing the frozen sampling/metadata config:

```bash
uv run research-network extract-diagnostics \
  --input data/interim/five-year-acquired-v1/papers.json \
  --manifest data/manifests/five-year-roster-v2/corpus_manifest.jsonl \
  --splits data/manifests/five-year-splits-v1 \
  --config configs/five-year-headers-v1.yaml \
  --output data/interim/five-year-headers-v1 \
  --cache data/raw/five-year-source-cache-v1
```

Before source access, this verifies manifest, acquisition, historical sampling
inputs, frozen assignments, reserved tests and title/version groups. Local GROBID
must pass its health check. Exactly the frozen selection is processed; held-out
papers and linked held-out PDF URLs are rejected. Retrieval is serial and bounded;
access failures stop that PDF host for the batch. No OpenAlex requests, external
GROBID consolidation, fulltext/reference parsing or graph imports occur.

The withheld MLSys record can have its official PDF inspected as **source review
only**; original acquisition status is retained. Source/header title agreement,
ordered complete byline agreement and within-paper name uniqueness are separate
observations. Candidate affiliation records preserve author position, printed
institution, PDF/TEI hashes and all support locators. Provider corroboration uses
only the aligned author's institution list. Repeated observations do not create
new support; ambiguous mappings stay unresolved. Every candidate remains in
review: GROBID nesting is not an independently verified printed-marker mapping,
accepted identity, accepted affiliation triple or measured accuracy.

PDFs/TEI, full metadata and `source-review.json` remain ignored/local. Preserve
per-record checkpoints even on parse failure; use a new output version for changed
methods or retries. A completed replay verifies inputs/checkpoints and reuses its
immutable records without contacting providers or GROBID. Only permitted aggregate
measurements and source hashes may be published to the Site. Next acceptance work
requires canonical-work checks, public ORCID publication corroboration and exact
paper-specific printed marker review before isolated graph construction.

## Reviewed development corroboration (D025)

```bash
uv run research-network corroborate-diagnostics \
  --input data/interim/five-year-headers-v1/papers.json \
  --manifest data/manifests/five-year-roster-v2/corpus_manifest.jsonl \
  --splits data/manifests/five-year-splits-v1 \
  --reviews data/manifests/five-year-source-corrections-v1.json \
  --config configs/five-year-corroboration-v1.yaml \
  --output data/processed/five-year-corroborated-v1 \
  --cache data/raw/five-year-source-cache-v1
```

Checks original acquisition/frozen/header hashes, historical graph/acquisition,
reviewed record/PDF bindings and raw evidence before any network access. Five
printed-source decisions overlay bylines without altering original parser or
acquisition statuses. No OCR/parser-success claim or global name alias is made.
Requires complete ordered source/provider bylines, work title/year, valid ORCID
checksum and provider author IDs. Shared works, held-out provider locations,
contradictory names or stable crosswalks remain in review. Multiple provider IDs
for one ORCID are conservatively withheld until reviewed; no automatic merging.

Only eligible public ORCID works are requested, serially, maximum 120 unique IDs,
with typed self DOI or nonempty Unicode exact title plus year support. No new
OpenAlex or PDF collection. Printed affiliations additionally need a ledger review
and exact institution inside that author's metadata. Deduplicated staging tables
are `authorship-support.json` and `affiliation-triples.json`; they are not a graph.
Original failures and uncorroborated mentions remain in `papers.json`/review queue.

Checkpoints, source responses and outputs are immutable. A replay validates inputs
and reuses all checkpoints without network access; input/method changes or retries
require a new version/output directory. Quota/access stops persist through replay.
Exit 1 means unresolved review rows or a collection stop; outputs are retained.
[Measured result](../reports/five-year-corroboration-v1.md): 10 people, 11 authorship
supports, one triple. Accuracy/recall/F1 are not measured. Do not combine these
staging counts with historical graph totals without canonical support reconciliation.

## Pregraph staging and explicit readiness gates (D026)

The current source ledger/config/output are `five-year-source-corrections-v3.json`,
`configs/five-year-corroboration-v3.yaml` and `five-year-corroborated-v3/`; v1/v2
remain immutable historical outputs. Run the same `corroborate-diagnostics` command
above with those three paths. It retains 19 source reviews, 55 source-eligible
papers, 10 people, 11 authorships and 12 reviewed triples. All original acquisition
and parser failures remain unchanged. Then run:

```bash
uv run research-network prepare-pregraph \
  --config configs/five-year-pregraph-v3.yaml \
  --output data/processed/five-year-pregraph-v3
```

This is an offline, immutable preparation stage. It verifies frozen/hashed inputs,
public ORCID/person publication bindings and exact printed same-author affiliations;
checks known work links against both current/historical rosters and all reserved IDs;
stages papers, organizations, topic/citation candidates and full claim dispositions;
and writes a content-addressed `freeze.json`. It constructs no graph artifact,
materializes no relationships and imports nothing. A title match can guard leakage,
never canonically merge works. Full-population canonical completeness remains a gate.

**Exit 1 is required while full pregraph gates fail**; a technically reproducible
diagnostic bundle does not establish full readiness. Current inputs fail scope,
full enrichment, identity/affiliation/topic coverage and global work-resolution
gates. Topic candidates remain uncalibrated/unaccepted; independent quality is
unmeasured. Prior v1/v2 pregraph outputs are historical iterations, superseded by
v3's specific-institution claim checks. Preserve all versions and use a new output
for further changes. [Measured readiness report](../reports/five-year-pregraph-v3.md).

Blank exposed-development annotation forms for two reviewers are local/ignored in
`data/annotations/five-year-development-review-v1/`; their tracked manifest is
`data/manifests/five-year-development-review-packet-v1.json`. They contain no model
predictions/acceptance flags and no completed annotations. Development labels can
inform calibration; they cannot replace independent held-out/component/release audits.

## AAMAS official rosters v8 (D031)

Roster v8 overlays four complete official AAMAS rosters onto v7 while preserving
all 170 candidate rows and prior roster versions. The year-specific included
sections are Main Track (2021: 151; 2022: 166), Full Research Papers (2024: 230),
and Research Paper Track (2025: 260). Other listed contents sections stay excluded
under D015. AAMAS 2023 remains unresolved: official accepted-paper and proceedings
titles/bylines are not fully reconciled, so the roster adds no 2023 records.

IFAAMAS notices restrict republication/redistribution. Detailed captured pages
and full rosters remain in ignored local storage; the tracked correction contains
only source URLs, response hashes and aggregates. No PDFs were downloaded.

```bash
uv run research-network discover \
  --config configs/corpus-five-year-v8.yaml \
  --output data/manifests/five-year-roster-v8 \
  --cache data/raw/five-year-source-cache-v8
```

Measured v8: **94 eligible editions / 88,211 included records** across 91,712
observations, with 3,501 exclusions. Of all 170 candidates, 10 have verified
no-edition findings, 26 remain unresolved at adapter/roster level, and 40 remain
publisher-access unavailable. The 26 include 25 unsupported adapters and AAMAS
2023's incomplete reconciliation. The 76,629 guarded assignments, including
all 1,095 held-out tests, remain guarded; no split, enrichment, canonical merge,
graph, or database operation occurred. The source-disabled replay matched all 34
recorded output hashes and exits 1 while 66 candidates remain incomplete. The full
offline suite passed **193 tests** during this iteration. See the [v8 recovery
report](../reports/five-year-source-recovery-v8.md),
[metrics](../reports/five-year-source-recovery-v8.metrics.json),
[ledger](../reports/five-year-edition-ledger-v8.csv), and
[D031 source correction](../data/manifests/five-year-source-corrections-v6.json).

P01 remains incomplete. P02 remains no-go for broader enrichment until the
complete eligible frame, canonical population, prospective P03 design, current
resource/storage limits, and actual reviewer capacity are measured. The diagnostic
and pregraph inputs remain bound to v2; v8 does not refresh them.

## MICCAI 2024 full-proceedings reconciliation v10 (D033)

V10 overlays the immutable v9 roster and the hash-bound source correction v8.
The 856 Society accepted research records reconcile one-to-one to 856 distinct
chapters from all 12 Springer MICCAI 2024 main-proceedings volumes. The complete
Springer capture covers 49 contents pages and 857 unique chapters: 836 exact-title
matches, 20 unique title-and-byline matches, and one correction notice tied to a
listed paper that is excluded as nonresearch. No record remains unmatched.

```bash
uv run research-network discover \
  --config configs/corpus-five-year-v10.yaml \
  --output data/manifests/five-year-roster-v10 \
  --cache data/raw/five-year-source-cache-v10
```

The captured detailed source pages and generated rosters remain in ignored local
storage. V10 records aggregate counts and hashes only in tracked summaries. The
measured roster has **98 eligible editions / 91,355 included records** across
94,857 observations (3,502 excluded); 22 unresolved roster/adapter and 40
access-unavailable candidates remain. Discovery exits 1 while 62 candidates are
incomplete. All 76,629 assignments, including 1,095 tests, remain guarded; no split,
enrichment, PDF, or graph operation occurred. MICCAI 2022 and AAMAS 2023 remain
unresolved. P02 remains no-go and the diagnostic/pregraph inputs stay v2-bound.
See [D033](decisions.md#d033--miccai-2024-full-proceedings-reconciliation-2026-11-07),
[the v10 report](../reports/five-year-source-recovery-v10.md),
[metrics](../reports/five-year-source-recovery-v10.metrics.json),
[ledger](../reports/five-year-edition-ledger-v10.csv), and [source triage](five-year-source-triage.md).

## Historical MICCAI source closure v9 (D032)

V9 overlays the immutable v8 roster and the hash-bound MICCAI correction manifest.
It adds eligible main-conference title/record rosters for 2021, 2023 and 2025.
2022 stays unresolved after its official accepted-list route returned HTTP 522;
2024 stays unresolved because the Society page contains 856 numbered records
against Springer’s 857 full-paper count. Springer series-index counters are
recorded separately and never treated as accepted-paper totals. The 2021/2023
lists lack bylines, so D015 still requires authoritative detail bylines before
work matching or core-paper acceptance. Full rosters remain ignored local data.

```bash
uv run research-network discover \
  --config configs/corpus-five-year-v9.yaml \
  --output data/manifests/five-year-roster-v9 \
  --cache data/raw/five-year-source-cache-v9
```

The command returns **1 as expected** while 63 edition candidates remain
incomplete. V9 has **97 eligible editions / 90,499 included records** across
94,000 observations; 23 unresolved roster/adapter editions and 40
access-unavailable editions remain. It guards all 76,629 assignments, including
1,095 tests, and creates no split. See the [v9 report](../reports/five-year-source-recovery-v9.md),
[metrics](../reports/five-year-source-recovery-v9.metrics.json),
[ledger](../reports/five-year-edition-ledger-v9.csv), and
[source correction v7](../data/manifests/five-year-source-corrections-v7.json).
The roster does not refresh the v2-bound diagnostic/pregraph inputs, authorize
broader enrichment, or construct a graph. P02 remains no-go.

## Historical official edition-route correction and COLING 2024 roster v7 (D030)

Roster v7 applies official conference-history evidence to the 11 route candidates
that were still unverified in v6. Ten are verified no-edition findings. The
official joint LREC-COLING 2024 main volume is added once under COLING, with the
LREC co-host preserved in a joint-event crosswalk. Its one frontmatter record is
excluded; the 1,554 paper records are included. V7 inherits all other v6 roster
observations and does not alter earlier versions or the v2-bound diagnostic frame.

```bash
uv run research-network discover \
  --config configs/corpus-five-year-v7.yaml \
  --output data/manifests/five-year-roster-v7
```

Measured v7: **90 eligible editions / 87,404 included records** across 90,163
observations, with 2,759 exclusions. Of all 170 candidates, 10 have verified
no-edition findings, 30 remain unsupported by an implemented adapter, and 40
remain publisher-access unavailable. The 76,629 guarded assignments, including
all 1,095 held-out tests, remain guarded; no split, enrichment, canonical merge,
graph, or database operation was performed. The offline replay reproduces all
recorded hashes and exits 1 while 70 candidates remain incomplete. See the
[v7 recovery report](../reports/five-year-source-recovery-v7.md),
[metrics](../reports/five-year-source-recovery-v7.metrics.json),
[ledger](../reports/five-year-edition-ledger-v7.csv), and
[source triage](five-year-source-triage.md).

P01 remains incomplete. P02 remains no-go for broader enrichment until the
complete eligible frame, canonical population, prospective P03 design, current
resource/storage limits, and actual reviewer capacity are measured.

## Historical ICAPS 2025 source correction and roster v6 (D029)

Roster v6 is the prior roster-only source correction. It inherits 160 unchanged
edition observations from the v2 baseline and reprocesses the ten AAAI/ICAPS
editions covered by the OJS workflow. The official ICAPS 2025 main technical call,
topic-based policy and accepted-paper page establish that all 48 theoretical,
algorithmic, modelling and tools records in the previously unresolved OJS sections
are accepted main-research papers. The three accepted position papers remain
excluded under the existing archival-research policy; front matter is excluded.

```bash
uv run research-network discover \
  --config configs/corpus-five-year-v6.yaml \
  --output data/manifests/five-year-roster-v6 \
  --cache data/raw/five-year-source-cache-v1
```

Measured v6: **89 eligible editions / 85,850 included records** across 88,608
observations (2,758 excluded; zero record-level review). All 170 candidate editions
remain: **41 unresolved / 40 unavailable**, or 81 gaps. The source-disabled replay
returns exit 1 for those edition gaps. The 76,629 guarded assignments, including
all 1,095 tests, remain unchanged; no split, enrichment, merge, graph or DB operation
was made. The older diagnostic/pregraph freeze remains bound to v2 and is not
refreshed by v6. V1–v5 and their outputs remain historical and intact.

See [the v6 recovery report](../reports/five-year-source-recovery-v6.md),
[edition ledger](../reports/five-year-edition-ledger-v6.csv), and
[ICAPS/route triage](five-year-source-triage.md). P01 remains incomplete; P02
feasibility is a no-go for broader enrichment until the population, sampling frame,
live resource limits, storage budget and actual reviewer capacity are established.

## Historical official OJS roster recovery v5 (D027)

The prior roster config/output was **v5**. This overlay inherits 160 unchanged v2
edition observations and recovers AAAI/ICAPS only. It hash-checks its protected
baseline and all frozen assignments before source access, including the 170 new
test groups. No split, enrichment, identity acceptance or graph is produced.

```bash
uv run research-network discover \
  --config configs/corpus-five-year-v5.yaml \
  --output data/manifests/five-year-roster-v5 \
  --cache data/raw/five-year-source-cache-v1
```

The linked OJS archive must reach a corroborated pre-2021 boundary or its end,
within 12 pages. The collector checks year order, official journal URLs, issue
sequences, archive/issue heading agreement, complete article sections and unique
record IDs. A failed second issue withholds the entire edition. Unknown categories
stay in review; an access failure stops that journal's remaining retrieval.

AAAI 2021–2025 main technical issues qualify. Eleven non-main special/student/
IAAI/EAAI issues have excluded catalog dispositions without being downloaded;
their article counts are unknown. ICAPS 2021–2024 Main Track qualifies; the 48
ICAPS 2025 theoretical/algorithmic/modelling/tools records remain in review.
D027 documents the four exact, edition-specific AAAI heading variants in v5.

Measured v5: **88 eligible editions / 85,802 included records**; all 170 candidates
retained, **82 gaps**. Full roster totals: 88,608 including 2,758 excluded and 48
review. All 78,321 v2 rows remain identical. Source-disabled v3/v4/v5 replays pass;
discovery still exits **1** for unmet scope/track gates. Preserve v3's older-title
failure and v4's unknown-section results as historical outputs.

The local `leakage-triage.jsonl` protects the current 76,629 frozen assignments
(1,095 tests). Four included records are quarantined as version candidates; exact
titles never merge works. This output creates no sampling or enrichment permission.
The old frozen diagnostics/corroboration/pregraph bundle remain bound to their v2
inputs. Do not replace their manifests with v5. Future supplemental sampling needs
a new reviewed, budgeted design retaining all historical and newly reserved IDs.

Full rosters, per-record leakage candidates and raw HTML remain ignored/local.
Track only hashes, source/edition summaries and permitted aggregates. Read
[measured recovery](../reports/five-year-source-recovery-v5.md) and
[170-row ledger](../reports/five-year-edition-ledger-v5.csv). Independent component
quality, canonical work resolution and the final graph/audit remain incomplete.

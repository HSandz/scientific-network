# Release plan — submission on 11 November 2026 (D040)

Active from **8 November 2026, 03:00 +07:00** until submission. Decision:
[D040](decisions.md#d040--release-reset-for-the-11-november-submission-2026-11-08).
For this release it supersedes the P00–P10 pregraph sequence, gates G01–G12, the
P02 enrichment no-go, readiness receipts and the 600-edge two-reviewer audit.
Those documents stay as history. Where anything conflicts with this plan, this
plan wins. If this plan is wrong or blocked, ask the user; don't route around it.

## 0. Every session starts here

1. Read `AGENTS.md`, this plan, `docs/status.md` and the latest work-log entry.
   Skip `pregraph-completion-plan.md`, `five-year-source-triage.md`,
   `five-year-collection.md`, `docs/reference/` and older decisions unless a task
   needs one specific fact from them.
2. Run `git status`, `uv sync --locked --group dev --extra analysis` and
   `uv run pytest`.
3. Continue the first unticked phase in the `docs/status.md` checklist. Don't start
   a phase before the previous phase's exit check passes.
4. Open or continue one work entry for the phase, about one page.
5. At each checkpoint: run tests, commit locally (no push), tick the checklist,
   replace `docs/status.md` (≤60 lines) and give the user a five-line summary.
   Then continue.

## 1. What "done" means

| Course requirement | Release evidence | Check |
| --- | --- | --- |
| Meaningful social network built with NLP | Collaboration, citation and topic projections; embedding topic classifier compared with the phrase baseline | Analysis outputs and report |
| ≥2,000 nodes | Node counts by label | Resolved researchers alone ≥2,000 |
| ≥5,000 edges | Unique R1–R4 factual edges; derived edges counted separately | ≥5,000 |
| Ten relationship types | All ten predicates nonempty | Inventory in the graph summary |
| Accuracy >90% | Frozen edge audit with a Wilson 95% interval | Course: point estimate >90%. Project target: ≥95% with lower bound >90% |
| Suitable graph DBMS | Neo4j 5.26 Community, isolated `neo4j-five-year` service | Load, integrity queries, idempotent re-import |
| Report ≥10 pages | `reports/final-report/` rendered to PDF | All sections in §6 |
| Real GitHub URL | <https://github.com/HSandz/scientific-network> plus a release tag | The lecturer can open it |

Report every gate as passed, failed or not run, with numbers. A failed gate is
reported, not hidden, and is not a reason to stop.

## 2. Decisions (D040)

These are defaults. The user can change them before Phase 1; record any change as
a dated D040 amendment.

### 2.1 Scope

- AAAI and IJCAI 2021–2025 main-track papers from roster v10: **13,617 papers**
  (§8.1). One cumulative graph; year is a paper property; per-year results come
  from analysis.
- Roster v10 is final. No edition, roster, source-route or rights audits before
  submission. The collected roster (98 eligible editions, 91,355 papers) and the 62
  unresolved or unavailable candidates are reported as collected data and coverage
  limits.
- Why these venues: every official URL yields a DOI that OpenAlex returns in
  batches. ICML and NeurIPS 2021 have no bulk route (§8.2).

### 2.2 Evidence rules

| Claim | Accept when | Otherwise |
| --- | --- | --- |
| Work match | OpenAlex returns the derived DOI, normalized titles agree (similarity ≥0.9 accepted with a flag) and author counts agree | Review queue; the paper keeps PUBLISHED_IN and gets an `unresolved_author_reason` |
| R1 AUTHORED | OpenAlex author ID at the same byline position with a compatible name (`names_compatible`, or a tested initials-tolerant variant) | Withhold that position. Withhold all of the paper's authorships if more than one position is incompatible or one ID appears twice; withhold an ID that carries conflicting ORCIDs |
| R2 AFFILIATED_WITH | Institution with an OpenAlex ID on that authorship; evidence is the raw affiliation string (prefer `authorships[].affiliations`, which maps strings to institutions) | An institution without an ID is unknown, not a node. Paper-level copying (≥3 authors who all carry the same set of ≥2 institutions) goes to review |
| R3 PUBLISHED_IN | Roster row | — |
| R4 CITES | The `referenced_works` target is another matched in-scope work | Drop out-of-scope targets, self-loops and targets that map to two papers |
| R5 HAS_TOPIC | Frozen classifier label with a supporting excerpt | Below threshold: abstain |
| R6 SUBTOPIC_OF | Frozen taxonomy | — |
| R7–R10 | `graph/materialize.py` rules on accepted core support | — |

ORCID is recorded when present but not required. PDFs and GROBID are optional
spot-checks. All integrity rules in `AGENTS.md` still apply: no name-only merges,
triples before aggregation, a sole dual-affiliated author creates no
COLLABORATED_WITH, distinct-paper counts, raw and fractional weights, separate
evidence classes and a review queue for conflicts.

### 2.3 Topics

- Embedding classifier with abstention (Phase 5), compared with the phrase
  baseline on a topic test set frozen before tuning: 30 random papers from the 80
  in-scope reserved tests (all IJCAI) plus 20 random AAAI papers reserved then.
- Thresholds are chosen on non-test papers only. Don't look at test-set
  predictions before the classifier is frozen.

### 2.4 Accuracy audit (`configs/quality-release-v1.yaml`)

- Frame: all accepted edges of the frozen graph.
- Global sample: 200 edges, uniform without replacement, with the seed recorded in
  the config before sampling. Per type: 10 per relation (census if fewer),
  reported separately and never pooled into the global estimate.
- Reviewers A and B (names in `docs/team.md`): each sampled edge is reviewed once,
  split between them; 50 global-sample edges are reviewed by both; disagreements
  are adjudicated together.
- Decision per edge: correct, incorrect or unverifiable (counts as incorrect), with
  an error category. Report k/n, precision, Wilson 95% interval, per-type k/n,
  agreement (percent and Cohen's κ) and error categories.
- If only one reviewer is available: 200 uniform plus 5 per type, no overlap, and
  say so in the report.
- Size and coverage targets keep their `configs/quality.yaml` values.

### 2.5 Other

- Site: one update in Phase 9 if its helper works; no intermediate publications.
- Superseded for this release: D009's ORCID-only identity and PDF-plus-exact-match
  affiliation rules, D022's enrichment preconditions, D028's P00–P10 sequence,
  D029's P02 no-go and the readiness receipts in `analyze` and
  `freeze-audit-sample`.
- Kept: everything else in `AGENTS.md`, the five labels and ten predicates, and
  all historical artifacts and held-out IDs.

## 3. Schedule (Asia/Bangkok, UTC+07:00)

| Phase | Work | Time box | Due |
| --- | --- | --- | --- |
| 0 | Housekeeping | 30 min | Sun 8 Nov |
| 1 | Tooling fixes | 2 h | Sun 12:00 |
| 2 | OpenAlex acquisition | 2 h | **CP1** Sun 14:00 |
| 3 | Graph v1 (all ten types, phrase topics) | 3 h | Sun 19:00 |
| 4 | Neo4j load, integrity, replay | 2 h | **CP2** Sun 22:00 |
| 5 | Embedding topics, graph v2 | 4 h | Mon 9 Nov 12:00 |
| 6 | Analysis, figures, findings | 4 h | **CP3** Mon 16:00 |
| 7 | Freeze, review sheets, report methods | 3 h | **CP4** Mon 20:00 |
| — | Human review: edge audit and topic labels | ~4 h per person | Mon 20:00 → Tue 12:00 |
| 8 | Scoring, full report, README | 6 h | **CP5** Tue 10 Nov 20:00 |
| 9 | PDF, release, submission | 3 h | **CP6** Wed 11 Nov 12:00 |

If work starts after Sun 09:00, shift CP1–CP2 by the delay but keep CP4 fixed;
cut Phase 6 extras first. If a phase overruns its time box by half, or a blocker
lasts 30 minutes, stop and tell the user the blocker and two options. Fallbacks
are in §4.

### Phase 0 — Housekeeping

- The user stops `grobid`, `neo4j` and `neo4j-extended` (free RAM was 2.8 GiB with
  swap full on 8 Nov):
  `docker compose --profile nlp --profile extended stop grobid neo4j neo4j-extended`.
  Their data stays in the volumes.
- Add the `neo4j-five-year` service to `compose.yaml` (§8.4).
- Create `configs/release-v1.yaml` (scope, roster path and sha256, OpenAlex
  settings, cache and output paths), `configs/quality-release-v1.yaml` (a copy of
  `quality.yaml` with the audit section from §2.4) and
  `configs/analysis-release-v1.yaml` (a copy of `analysis.yaml` with
  `status: frozen`, `strict_evidence_filter: {minimum_support_count: 2}` and
  `stricter_evidence_filter_status: frozen`).
- Exit: configs committed; tests pass.

### Phase 1 — Tooling fixes

1. `graph/validate.py`: build per-node indexes once (PUBLISHED_IN and HAS_TOPIC per
   paper, authored papers, parents per leaf) instead of scanning every edge per
   node (lines ~99–109). It is quadratic now: 0.37 s at 1k and 7 s at 4k invented
   papers. Results must stay identical on existing fixtures.
2. `graph/load.py`: use labeled `MATCH` per relation (labels from `RELATIONSHIPS`
   in `graph/schema.py`), batches of ~5,000 rows in separate transactions, then the
   existing count reconciliation. Keep `MERGE` on `edge_id`, project/version
   stamping and constraints. Take the URI from the environment
   (`bolt://localhost:7689`).
3. `analysis/analyze.py` and `evaluation/edge_audit.py`: real graphs no longer need
   a readiness receipt or passing size gates. Compute the gates and record each as
   passed or failed in the output. Keep the frozen-config requirement.
4. `evaluation/edge_audit.py`: support `review_design: split_with_overlap` (§2.4)
   and write an HTML review sheet next to the CSV (§5).
- Leave the CLI guard in `cli.py` (~lines 175–178) that stops old stages from
  running five-year roster configs; the release uses new commands.
- Exit: `uv run pytest` passes with the §7 tests for these changes; validator
  timing on a 10k-paper invented graph recorded in the work entry.

### Phase 2 — OpenAlex acquisition (CP1)

- Read roster rows with `status == "included"` and `venue_id` in `venue:aaai` or
  `venue:ijcai`; expect 13,617 (§8.1). Derive DOIs; fail on any row that doesn't
  derive and on any duplicate DOI.
- Preflight `GET https://api.openalex.org/rate-limit` with the key in
  `secret_params`. Log `daily_remaining_usd` and `endpoint_costs_usd`; stop if the
  worst-case batch cost exceeds the remaining allowance.
- Fetch through `SourceCache` (§8.2), 50 DOIs per request (~273 requests). Retry
  missing DOIs once with `GET /works/doi:<doi>`; record the rest as not found.
- Apply the work-match rule (§2.2). Write `data/interim/release-v1/works.jsonl`
  (ignored: one row per roster paper with match status, authorships, references
  and reconstructed abstract) and `reports/release-v1/acquisition.json` (tracked:
  counts and match rate per venue-year, failure reasons, requests, allowance used).
- Exit (CP1): match rate reported. If it is below 95%, spend at most 30 minutes on
  the largest failure reason, then continue.

### Phase 3 — Graph v1

- New module (e.g. `resolve/release.py`) that builds a `GraphArtifact`
  (`is_synthetic: false`) from the roster and `works.jsonl` with the rules in §2.2
  and the conventions in §8.3.
- Paper properties: year, official_url, pdf_url, track, `is_core: true`,
  `official_author_count`, doi, openalex_id. Keep full abstracts out of nodes; they
  stay in `works.jsonl`.
- Topics for v1: reuse the phrase baseline (`nlp/baseline.py`), adapted to read
  title and abstract from `works.jsonl`. It also adds the taxonomy (R6).
- Derived R7–R10: `materialize()`.
- Evidence granularity: one record per (source response, work); byline positions
  go in edge properties. This keeps memory down.
- Validate, then write `data/processed/release-graph-v1/{graph.json,review-queue.jsonl,summary.json}`
  (ignored) and `reports/release-v1/graph-summary.json` (tracked): counts by label,
  relation and evidence class; coverage of abstracts, affiliated author–paper pairs
  and topic-labeled papers; review reasons; size gates.
- Exit: validation passes and all ten relations are nonempty.

### Phase 4 — Neo4j (CP2)

- Start `neo4j-five-year` (the user does this if the agent has no Docker access).
- `NEO4J_URI=bolt://localhost:7689 uv run research-network build --input data/processed/release-graph-v1/graph.json --config configs/quality-release-v1.yaml --output reports/release-v1/neo4j-load-v1.json`
- Run `queries/02_integrity.cypher` (expect no rows) and `queries/01_inventory.cypher`
  (counts must equal the graph summary). Re-run `build` with a new output path;
  counts must not change.
- Exit (CP2): load, integrity and replay results recorded; commit.

### Phase 5 — Embedding topics, graph v2

1. First, freeze `data/manifests/release-v1/topic-test.jsonl` (§2.3), recording
   the seed and the source of each ID.
2. Copy `configs/topics.yaml` to `configs/topics-release-v1.yaml`. Leaf
   definitions, includes and synonyms may be improved now, without looking at test
   papers; then set `status: frozen`.
3. Add `nlp/embeddings.py`. Use a small sentence-embedding model (e.g.
   `BAAI/bge-small-en-v1.5` or `sentence-transformers/all-MiniLM-L6-v2`) with a
   pinned revision, installed as an optional `nlp` extra with CPU-only torch (§8.5)
   and imported lazily so tests don't need it.
   - Label text: leaf name, definition, includes and synonyms.
   - Paper text: title plus abstract; flag title-only papers.
   - Assign the top leaf if cosine ≥ τ, plus extra leaves (three at most) that are
     ≥ τ and within δ of the top; otherwise abstain.
   - Excerpt: the abstract sentence most similar to the label, or the title if
     there is no abstract.
4. Choose τ and δ on non-test papers: aim for 80–90% labeled coverage and inspect
   about 30 development or pool predictions. Record model, revision, τ and δ in the
   method version.
5. Rebuild as `release-graph-v2` (R5 from embeddings, R9/R10 re-derived) and
   validate. Then reload Neo4j: first clear only the `neo4j-five-year` database
   (`MATCH (n) CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS`) and
   record that you did.
6. Write `reports/release-v1/audit/topic-label-sheet.csv` and `.html`. For each
   test paper show the title, the abstract and the 16 leaves with definitions, with
   columns for up to three labels, labeler and notes. Don't show predictions.
- Exit: v2 validated and loaded; classifier frozen; label sheet ready.

### Phase 6 — Analysis (CP3)

- `uv run research-network analyze --input data/processed/release-graph-v2/graph.json --config configs/analysis-release-v1.yaml --quality-config configs/quality-release-v1.yaml --output reports/release-v1/analysis.json`
- Add what `analyze` lacks, under `src/scientific_network/analysis/`:
  - per-year counts: papers, active researchers, new collaboration pairs
  - sector mixing (academia, industry, government, nonprofit, unknown)
  - country-pair collaborations
  - topic shares by year and venue
  - top in-scope cited papers (in-degree, PageRank)
  - bridge researchers (betweenness), with their communities' top topics
- Figures, each with its table (PNG plus CSV), in `reports/final-report/figures/`:
  - researcher degree CCDF
  - component sizes
  - community topic profiles
  - sector-mixing heatmap
  - topic trends 2021–2025
  - top cited papers

  Each caption states the projection, filter, counting rule and graph version.
- Draft `reports/release-v1/findings.md`:
  - Three findings, each with a statistic, denominator, ≥2 supporting papers and
    one material limitation: an academia–industry partner map in one topic, a
    researcher bridge profile, and an organization topic comparison.
  - Two shortlists with explicit criteria.
  - Business wording rules are in `docs/project-plan.md`.
- Exit (CP3): analysis JSON, figures and findings draft committed.

### Phase 7 — Freeze and review preparation (CP4)

- Write `reports/release-v1/freeze.json` with the graph version, the sha256 of
  `graph.json` and the config hashes. After this the graph does not change; any fix
  needs a new version and a new audit.
- Run `freeze-audit-sample` with `quality-release-v1.yaml` and assign edges to
  reviewers A and B with the overlap (§2.4). Write
  `reports/release-v1/audit/edge-review-sheet.{csv,html}` (§5).
- Start `reports/final-report/report.md` with the method sections (§6 rows 2–7).
- Exit (CP4): both sheets delivered to the user; commit.

### Human review — Mon 20:00 → Tue 12:00

- Edge audit: about 3.5 hours per reviewer. Topic labels: about 40 minutes each
  (25 papers each, 10 overlapping). Meanwhile the agent writes report sections
  that don't depend on the results.

### Phase 8 — Scoring and report (CP5)

- Run `score-edge-audit` → `reports/release-v1/audit-results.json`, with the Wilson
  interval from `audit-precision`. State pass or fail against both thresholds.
- Evaluate the embedding classifier and the phrase baseline on the 50 test papers:
  micro/macro precision, recall, F1, coverage and labeler agreement →
  `reports/release-v1/topic-eval.json`.
- Finish `reports/final-report/report.md` (§6) using only measured numbers with
  versions.
- Rewrite the top of `README.md`: what the project is, scope, measured results,
  how to reproduce, and links. Move old iteration notes to the bottom or the
  archive.
- Exit (CP5): a complete draft that renders to ≥10 pages; commit.

### Phase 9 — Package and submit (CP6)

- Render the PDF: Markdown → HTML → `google-chrome --headless --print-to-pdf=reports/final-report/report.pdf <html>`
  (or `pdflatex`). `*.pdf` is gitignored, so attach the PDF to the submission and
  the GitHub release.
- Names, student IDs and contributions come only from `docs/team.md`.
- Final checks: tests pass; no secrets, PDFs or raw data tracked; README commands
  work.
- The user pushes, tags the release, gives the lecturer access and submits.
  Optional: one Site update with the final numbers, with its receipt recorded.

## 4. Pre-decided fallbacks

| Problem | Trigger | Action |
| --- | --- | --- |
| OpenAlex unreachable or over quota | Requests still fail after retries | Back off, resume from the cache and tell the user. Don't switch sources |
| Many DOIs not found | >5% after singleton retries | Keep those papers with PUBLISHED_IN only; report coverage |
| Many name mismatches | >5% of positions | Add a tested initials-tolerant comparison; report both counts |
| Memory pressure | Build swaps or is killed | Stream tables to JSONL; stop other services |
| Neo4j load slow or failing | Not loaded by Mon 10:00 | Bulk import with `neo4j-admin database import full` from CSV exports |
| Embedding classifier blocked | Not working by Mon 12:00 | Keep phrase-baseline topics (graph v1) and say so in the report |
| Full scope not built | Not loaded by Mon 12:00 | Ship the largest complete, validated subset and document it |
| Audit unfinished | Tue 14:00 | Score the completed reviews; report the actual n and interval |

## 5. Review sheet contents

Each row has the edge ID, relation, endpoints with names, and links to the
official paper page, the PDF, the DOI (`https://doi.org/…`), the OpenAlex work
(`https://openalex.org/W…`) and the OpenAlex author or institution where relevant.

| Relation | Also show | Correct when |
| --- | --- | --- |
| AUTHORED | Byline position, roster name, ORCID if any | The person is on the official byline at that position, and the OpenAlex author page shows no obvious merge of different people |
| AFFILIATED_WITH | Supporting papers, raw affiliation string, organization | The paper's PDF lists that author at that organization |
| PUBLISHED_IN | Venue and year | The official page lists the paper in that venue and year |
| CITES | Citing PDF, cited title | The reference list contains the cited paper |
| HAS_TOPIC | Title, excerpt, topic definition | The topic is a substantive topic of the paper |
| SUBTOPIC_OF | Both topics | The hierarchy matches the taxonomy |
| COAUTHORED_WITH | One supporting paper | Both people are on that byline |
| COLLABORATED_WITH | Supporting paper, the two authors, raw affiliation strings | Two distinct authors are at the two organizations on that paper |
| RESEARCHES_TOPIC | Two supporting papers | The person authored both and both have the topic |
| CONTRIBUTES_TO_TOPIC | Three supporting papers | Each paper has the topic and an author affiliated with the organization |

Error categories: wrong identity, wrong affiliation, wrong citation, wrong topic,
unverifiable.

## 6. Report outline (≥10 pages; target 12–16)

| # | Section | Content | Sources |
| --- | --- | --- | --- |
| 1 | Task allocation | Names, IDs, roles, who reviewed what; AI-tool use if the course requires disclosure | `docs/team.md` (filled in by the user) |
| 2 | Network rationale | Business questions and the decisions they support | `docs/project-plan.md` |
| 3 | Data and stack | Official rosters (98 editions and 91,355 papers collected; release scope and why), OpenAlex, Python, Neo4j, NetworkX, sentence-transformers | `reports/five-year-source-recovery-v10.md`, `reports/release-v1/acquisition.json` |
| 4 | Preprocessing and resolution | DOI matching, name checks, identity, affiliation triples and guards; what the ORCID-only pilot yielded and why the method changed | `docs/data-dictionary.md`, D040, pilot reports |
| 5 | NLP | Taxonomy, phrase baseline, embedding classifier, held-out topic evaluation; earlier GROBID header experiments | `configs/topics-release-v1.yaml`, `topic-eval.json`, historical header reports |
| 6 | Graph design and DBMS | Five labels, ten relations, evidence classes, derivations and weights; Neo4j load and checks | `docs/graph-schema.md`, load reports |
| 7 | Network statistics | Counts by type, degrees, components, density, per-year growth | `graph-summary.json`, `analysis.json`, figures |
| 8 | Analysis and business findings | Communities, bridges, sector and country mixing, topic portfolios, citation influence; three findings and two shortlists | `findings.md`, figures |
| 9 | Quality | Edge audit (k/n, precision, interval, per type, agreement, errors), topic metrics, coverage | `audit-results.json`, `topic-eval.json` |
| 10 | Achievements and limitations | Targets met or missed, scope narrowing, OpenAlex dependence, review design | All of the above |
| 11 | Reproducibility | Commands, versions, hashes, GitHub URL, release tag | Configs, README |

## 7. Tests to add

- DOI derivation for AAAI (`Vol. V No. I` plus record ID) and IJCAI URLs,
  including malformed input.
- Work match: a title or author-count mismatch goes to review.
- Authorship: one incompatible position is withheld; two withhold the whole paper;
  the same author ID twice is withheld.
- Affiliation: the paper-level copying guard; an institution without an ID creates
  no node.
- Citations: out-of-scope targets and self-loops are dropped; duplicates collapse.
- Validator: unchanged results on existing fixtures; a 10k-paper invented graph
  finishes within a few seconds.
- Loader: generated Cypher uses labels and batches (unit test on the query text);
  integration run when Neo4j is available.
- Topics: abstention below τ, at most three labels, an excerpt always present; tests
  must not download the model.
- Audit: split-with-overlap validation; unverifiable counts as incorrect; Wilson
  interval.

## 8. Technical reference

### 8.1 Input

- Roster: `data/manifests/five-year-roster-v10/corpus_manifest.jsonl` (local,
  gitignored, rebuildable from `configs/corpus-five-year-v10.yaml`; sha256
  `84ff8ca78073e5d5e0d94f909aac63d18d71435cbd60f30630b7c3090b3c1cbe`).
  Fields used: `paper_id`, `venue_id`, `year` (int), `title`, `authors` (list, in
  byline order), `official_url`, `pdf_url`, `issue_series` (AAAI),
  `official_record_id`, `track`, `source_url`, `source_sha256`, `retrieved_at`,
  `source_locator`.
- Included papers, 2021–2025: AAAI 1,654 / 1,319 / 1,578 / 2,331 / 3,028; IJCAI
  586 / 678 / 639 / 790 / 1,014. Rough size from the bylines: ~65.5k authorships,
  ~33k distinct name strings, ≤153k co-author pairs, largest team 20.
- DOIs: AAAI is `10.1609/aaai.v{V}i{I}.{official_record_id}`, with V and I from
  `issue_series` "Vol. V No. I". IJCAI is `10.24963/ijcai.{year}/{n}`, from
  `https://www.ijcai.org/proceedings/{year}/{n}`. On 8 Nov every one of the 13,617
  rows produced a DOI, with no duplicates.
- Held-out IDs: `data/manifests/five-year-splits-v1/membership.jsonl` (76,629 rows,
  local). In scope it has 80 `test`, 38 `development` and 1 `review` row, all
  IJCAI; AAAI papers are not listed. Keep test papers out of tuning and leave
  `review` rows out of evaluation samples.

### 8.2 OpenAlex

- Request: `GET https://api.openalex.org/works?filter=doi:<d1>|…|<d50>&per_page=50&select=id,doi,title,publication_year,authorships,abstract_inverted_index,referenced_works`
- Use `SourceCache.get(url, params=…, secret_params={"api_key": …})` with
  `OPENALEX_API_KEY` from `.env`, and never log the key. Cache directory:
  `data/raw/openalex-release-v1/`.
- Keyless checks on 8 Nov:
  - 24 of 24 sampled AAAI/IJCAI DOIs were found.
  - Every sampled author had an ID, an institution and a raw affiliation string;
    every sampled work had an abstract and references (median 25).
  - Sampled ICML papers exist only as arXiv records, and only half of NeurIPS 2021
    sits under its source. Those venues would need one search per paper: about
    $0.001 each against a ~$1/day free allowance, going by the earlier measured
    cost.

### 8.3 IDs and evidence

- Paper: the roster `paper_id`.
- Researcher: `researcher:openalex:A…`, with `resolution_status: resolved`,
  `identity_method: openalex_author_id` and `orcid` when present.
- Organization: `organization:I…`, with `ror`, `country_code` and `sector` mapped
  from the OpenAlex type (education → academia, company → industry, government →
  government, nonprofit → nonprofit, anything else → unknown).
- Venues: `venue:aaai`, `venue:ijcai`. Topics: taxonomy IDs.
- Edge IDs: `graph.schema.edge_id`. Graph version: `release-` plus the first 12 hex
  digits of sha256(method version + input and config hashes).
- `EvidenceRecord` needs `source_url`, `retrieved_at`, `raw_sha256` and
  `source_locator`, plus `excerpt` for topics. Derived evidence lists its support
  edges and papers; `materialize` already does this.

### 8.4 Neo4j service (`compose.yaml`)

```yaml
  neo4j-five-year:
    image: neo4j:5.26.12-community
    profiles: ["five-year"]
    ports:
      - "127.0.0.1:7476:7474"
      - "127.0.0.1:7689:7687"
    environment:
      NEO4J_AUTH: "neo4j/${NEO4J_PASSWORD:?Set NEO4J_PASSWORD in ignored .env}"
      NEO4J_server_memory_heap_initial__size: 512m
      NEO4J_server_memory_heap_max__size: 1500m
      NEO4J_server_memory_pagecache_size: 1G
    volumes:
      - neo4j-five-year-data:/data
      - neo4j-five-year-logs:/logs
      - ./queries:/workspace/queries:ro
    # healthcheck: same as the neo4j service
```

Add both volumes under the top-level `volumes:`. Start it with
`docker compose --profile five-year up -d neo4j-five-year`; the Browser is at
<http://localhost:7476>. Never touch the `neo4j` or `neo4j-extended` volumes.

### 8.5 CPU-only embeddings

On Linux, torch from PyPI pulls in CUDA libraries (several GB). Add the CPU index
first:

```toml
[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[tool.uv.sources]
torch = [{ index = "pytorch-cpu" }]
```

Then run `uv add --optional nlp sentence-transformers torch` and commit `uv.lock`.
If this fails, `fastembed` (ONNX, no torch) is an acceptable substitute.

### 8.6 Outputs

| Path | Content | Git |
| --- | --- | --- |
| `configs/*-release-v1.yaml` | Scope, quality/audit, analysis and topic configs | Tracked |
| `data/raw/openalex-release-v1/` | Immutable OpenAlex cache | Ignored |
| `data/interim/release-v1/works.jsonl` | Matched works, authorships, references, abstracts | Ignored |
| `data/processed/release-graph-v{N}/` | Graph, review queue, summary | Ignored |
| `data/manifests/release-v1/topic-test.jsonl` | Frozen topic test IDs and seed | Tracked |
| `reports/release-v1/` | Acquisition, graph summary, load and replay, analysis, freeze, audit and topic results, findings | Tracked |
| `reports/release-v1/audit/` | Review sheets and completed reviews (IDs, decisions, reviewer letters) | Tracked |
| `reports/final-report/` | `report.md` and `figures/` (PNG plus CSV) | Tracked; the PDF is ignored |

## 9. Operating rules

Do:

- Work phase by phase and meet each exit check; commit locally at checkpoints.
- Report measured numbers with graph, config and method versions.
- Ask the user when blocked for 30 minutes, with two options.

Don't:

- Run edition, roster, source-route or rights audits, or add source adapters.
- Write new planning documents, gate frameworks or readiness receipts.
- Publish the Site before Phase 9.
- Append history to `docs/status.md`, or restate roster and assignment totals
  across files.
- Tune on test papers, or change the graph after seeing audit results.
- Invent names, student IDs, URLs or scores.

## 10. What the user provides

| When | Item |
| --- | --- |
| Before Phase 1 | Confirm or change the §2 defaults; stop the old services |
| Sun | Start `neo4j-five-year` when asked; fill in `docs/team.md` (names, IDs, roles) |
| By Mon | Decide how the lecturer reaches the repo (public, or an invite); check the course's AI-use disclosure rule |
| Mon 20:00 → Tue 12:00 | Edge audit and topic labels (two reviewers, about 4 h each) |
| Tue afternoon | Review the report draft; write the task-allocation section |
| Wed | Push, tag the release, submit |

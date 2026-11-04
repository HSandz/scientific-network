# WORK-2026-11-03-004 — Corpus discovery, frozen splits and first pilot graph

| Field | Value |
| --- | --- |
| Status | completed (bounded implementation and diagnostic pilot; release pending) |
| Recorded | 2026-11-03 07:58 +07:00 (Asia/Bangkok) |
| Finalized | 2026-11-03 09:09 +0700 (Asia/Bangkok) |
| Work performed | 2026-11-03, from 07:58 +07:00 |
| Contributor | Codex, implementing the user's requested next tasks |
| Related task | [Setup readiness](2026-11-03-003-next-steps-readiness.md) |
| Git state | `main`; no commits/remote; scaffold and implementation uncommitted |

## Objective

Implement official discovery, freeze development/test/pilot membership before tuning,
collect a balanced 100-paper pilot with the configured OpenAlex access, extract
PDF affiliations, resolve conservative identities, classify baseline topics and
construct/verify the first Neo4j graph. Preserve corpus boundaries and held-out isolation.

## Changes and measured findings

- Added official NeurIPS/PMLR adapters, immutable content-hash caching, sanitized
  quota/access stops, resumable acquisition, JSONL/Parquet roster and frozen splits.
- Discovery: **5,368 records**, including **3,218 NeurIPS main + 1,828 ICML main =
  5,046 eligible papers**, and **322 excluded Datasets and Benchmarks**; no unknown tracks.
- Reserved **60 test and 30 development papers per venue**, seed `20261102`.
  The 50-per-venue pilot includes development papers and excludes all held-out IDs.
- Acquired **100 official records/abstracts**, **61 strict OpenAlex work matches**,
  39 unmatched enrichments retained without guessing. User supplied the missing
  API key through ignored `.env`; no key was copied into records or this log.
- Added GROBID PDF/header processing, explicit TEI-author affiliation nesting and
  source locators; **100 valid TEI headers**, **51 papers with affiliation structures**.
  Payload sum **437,835,764 bytes**, median PDF **1,619,295 bytes**; corrected-run
  summed record durations **736.93 s**, partly warm cache, not a cold benchmark.
- Conservative resolution requires public ORCID publication corroboration, exact
  printed institution matches and authorship-specific provider evidence. Retains
  crosswalk/name variants, aligned triples and a review queue; no name-only merges.
  **28/464 resolved author–paper slots**, **5/464 affiliated slots**, **5 triples**.
- Added literal phrase baseline with spans/abstention: **40/100 topic coverage**,
  53 assignments, 60 abstentions; draft taxonomy, no measured label accuracy.
- Added full R7–R10 materialization and structural support/weight recomputation;
  distinct-paper support, full-byline coauthor denominator and distinct-author
  organization pairs. Added transactional version-safe Neo4j importer.
- Live graph **`pilot-topic-0bb7f11a404e`**: **154 nodes, 211 edges**; labels:
  Paper 100, Researcher 28, Organization 4, Topic 20, Venue 2. Evidence counts:
  observed **133**, inferred-topic **53**, curated-taxonomy **16**, derived **9**.
  Seven predicates nonempty; CITES, RESEARCHES_TOPIC and CONTRIBUTES_TO_TOPIC absent.
- Saved [pilot report](../../reports/pilot-v1.md) and [sanitized metrics](../../reports/pilot-v1.metrics.json).
  Created ignored `data/annotations/pilot-affiliation-review-v1.csv`: 20 blank-review
  diagnostic rows, five auto-accepted triples plus 15 unresolved institution candidates.
  No human review has been performed by this task.
- Updated locked dependencies (`python-dotenv`, `pyarrow`), workflow docs, stage
  status, roadmap, schema-weight clarification and agent handoff. `analyze` and
  `evaluate` remain explicit nonzero placeholders. Original Sites snapshot unchanged.

### Failed approaches and checkpoints retained

1. Initial OpenAlex configuration had an empty key. After the user placed it in
   ignored `.env`, authenticated acquisition succeeded; key values were never logged.
2. Initial GROBID 0.8.1 image pull: registry inspection showed **12,512,073,348 bytes**
   compressed. Cancelled only this task's Docker client with SIGINT; no volumes or
   unrelated images were deleted. Official Docker docs and registry identified
   **`0.8.2-crf` (536,794,708 bytes compressed)**; corrected startup succeeded.
3. Initial extraction negotiated a non-XML HTTP 200 response. At 66 recorded review
   rows, cancelled only the task's extractor (PID 82699, SIGINT; process exit **130**).
   Preserved `data/interim/pilot-headers-v1/records` and `extract.log`. A live explicit
   XML probe succeeded. Added `Accept: application/xml`, TEI-root validation and
   regression tests; reran into **`pilot-headers-v2`**, with all 100 parsed.
4. Preliminary metadata-only resolution/topic runs produced 28 researcher identities,
   zero affiliations and 40 topic-labeled papers. They were diagnostic warm-cache
   outputs under `data/processed/pilot-identity-check`, **never imported**. Final
   versioned PDF-backed metrics above supersede them.
5. First credential-boundary scan exited **1**, finding the example Neo4j password
   matched local configuration. Cleared `.env.example`'s password only and ignored
   editor `.history/`; local `.env` and running credentials remained unchanged.
   Repeat scans found no configured secrets in Git-eligible files.
6. Earlier test checkpoints: 42, 43, 44, 47 then 48 passed as implementation grew.
   Final fresh suite below is authoritative. Failed atomic documentation patches
   changed no files and were reapplied against inspected contexts. Two filename
   inspections used incorrect query/CI filenames (exit 1); corrected to actual files.

## Verification

All commands ran from `/home/san/Code/scientific-network` on 2026-11-03.
Raw command output is in ignored `reports/runs/WORK-2026-11-03-004/`.

| Command/check | Outcome / exit | Artifact |
| --- | --- | --- |
| `uv sync --locked --group dev`; `uv lock --check` | Passed, **0** each | Current locked environment; 60 packages resolved |
| `uv run pytest` | **48 passed**, **0** | `pytest-final.log`; 0.34 s reported test time |
| `uv run research-network schema` | Passed, **0**; ten predicates | `schema-final.json` |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json --config configs/quality.yaml --output reports/runs/WORK-2026-11-03-004/synthetic-validation-final.json` | Structural pass, **0**; explicitly synthetic | `synthetic-validation-final.json` |
| `docker compose --progress plain --profile nlp up -d grobid`; `GET http://localhost:8070/api/isalive` | Corrected CRF startup **0**; HTTP **200**, `true` | `grobid-start.log`; live process inspection |
| Discovery, split and acquisition commands below, followed by unchanged replay | Passed, **0** each; same immutable output summaries | `discover-replay.log`, `split-replay.log`, `acquire-replay.log` |
| Frozen-membership/acquired-ID comparison | Passed, **0**; exactly 100 pilot IDs, zero test overlap | `split-isolation.json` |
| Corrected extraction / resolution / classification commands below | Passed, **0** each | `extract-v2.log`, `resolve.log`, `classify.log` |
| Pilot structural validation command below | Passed, **0**, no structural errors | `pilot-validation.json` |
| Same validation with `--require-size` and separate `pilot-size-gates.json` output | **Expected exit 1**; researcher/factual-edge/ten-type gates all false | `pilot-size-gates.json` |
| First build and unchanged build replay below | Passed, **0** each; first 0→154 nodes; replay remains 154/211 | `import.json`, `import-replay.json` |
| `uv run python reports/runs/WORK-2026-11-03-004/verify-neo4j.py` | Passed, **0**; six queries/zero violations; version conflict rejected without data change | `neo4j-integration.json` |
| SHA-256 of every distinct graph/metadata/PDF/TEI referenced source object | Passed, **0**; **429** objects, zero mismatches | `source-hash-check.json` |
| `uv run python reports/runs/WORK-2026-11-03-004/summarize-pilot.py` | Passed, **0**; sanitized metrics/report and unannotated 20-row CSV | `pilot-summary.log`, versioned report/metrics |

Exact stage commands (shell output redirection omitted here; each has its own run log):

```bash
uv run research-network discover --config configs/corpus.yaml --output data/manifests/corpus-v1 --cache data/raw/source-cache
uv run research-network split --input data/manifests/corpus-v1/corpus_manifest.jsonl --config configs/quality.yaml --corpus-config configs/corpus.yaml --output data/manifests/splits-v1
uv run research-network acquire --input data/manifests/corpus-v1/corpus_manifest.jsonl --splits data/manifests/splits-v1/membership.jsonl --config configs/corpus.yaml --output data/interim/pilot-v1 --cache data/raw/source-cache
uv run research-network extract --input data/interim/pilot-v1/papers.json --config configs/corpus.yaml --output data/interim/pilot-headers-v2 --cache data/raw/source-cache
uv run research-network resolve --input data/interim/pilot-headers-v2/papers.json --config configs/corpus.yaml --output data/processed/pilot-resolved-v1 --cache data/raw/source-cache
uv run research-network classify --input data/processed/pilot-resolved-v1/graph.json --config configs/topics.yaml --quality-config configs/quality.yaml --output data/processed/pilot-graph-v1.json --cache data/raw/source-cache
uv run research-network validate --input data/processed/pilot-graph-v1.json --config configs/quality.yaml --output reports/runs/WORK-2026-11-03-004/pilot-validation.json
uv run research-network build --input data/processed/pilot-graph-v1.json --config configs/quality.yaml --output reports/runs/WORK-2026-11-03-004/import.json
uv run research-network build --input data/processed/pilot-graph-v1.json --config configs/quality.yaml --output reports/runs/WORK-2026-11-03-004/import-replay.json
```

Graph SHA-256: `f300f726b03fd0c06c714d1bf1b31941cba96b9df9ca592eb8940c1e965c4f5a`.
Full source/config/input hashes and method versions are in the portable metrics.
Core methods: `official-roster-v1`, `pilot-acquire-v1`,
`grobid-0.8.2-crf-xml-header-v2`, `orcid-public-work-pdf-affiliation-v2`,
`literal-phrase-baseline-v1`, `core-derivation-v1`; schema `0.1.0`.

## Decisions

[D008–D013](../decisions.md): frozen title-leakage groups; conservative identity/
institution evidence; CRF image and XML negotiation; version-safe import; explicit
full-byline fractional denominator clarification; uncalibrated topic baseline.
These preserve corpus, predicates and release thresholds. Independent review pending.

## Open issues and limitations

This is a diagnostic 100-paper graph, not the full 5,046-paper release. Identity,
affiliation and topic coverage are far below targets. The queue retains 39 unmatched
works, 138 uncorroborated ORCID-publication cases, 121 missing/ambiguous identifier
cases, 16 institution candidates and one missing/ambiguous PDF-author alignment;
these are different review units. No independent human annotation, precision,
recall/F1, global audit, final SNA, GDS compatibility, model benchmark or cold/full-run
resource test was performed. Full canonical stage Parquet exports and reviewed
cross-version migration remain pending. Lecturer interpretation and owner/team
metadata remain unspecified. No commit, remote, push or deployment was created.

No acquisition/extraction job remains running; Neo4j/GROBID services remain up.
The loader intentionally rejects changed graph versions sharing existing IDs.
Do not erase the current graph automatically to bypass that guard.

## Next step

Both reviewers inspect the saved 20-row diagnostic packet independently, record
mapping decisions and minutes, then adjudicate. Use the resulting development
cases to improve conservative identity/institution matching and context-aware
topics before scaling. Keep all 120 held-out IDs untouched; retain original review
records. A fresh graph version needs a separate database or reviewed migration.

## Corrections

None. Future corrections must be dated and preserve these original outcomes.

### Final verification addendum — 2026-11-03 09:10 +0700 (Asia/Bangkok)

Final Git-eligible-file/Markdown scan exited **0**: 96 eligible files, zero
configured secret values, zero trailing-whitespace findings and zero missing local
links (`reports/runs/WORK-2026-11-03-004/final-hygiene.json`). `docker compose ps`
confirmed both services still running, Neo4j healthy. `git check-ignore` confirmed
`.env`, editor history, raw/interim data, review packet and raw run logs are ignored.
Git still has no remote; no commit/push was performed. This addendum adds final
verification evidence without revising the measured pilot outcomes above.

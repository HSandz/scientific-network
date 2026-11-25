# WORK-2026-11-25-005 — M3: application core (analysis v2 fixes, QA references, GraphRAG, multi-hop engine, Explorer pages)

| Field | Value |
| --- | --- |
| Status | in_progress |
| Recorded | 2026-11-25 15:05 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-25 |
| Contributor | Claude/Gemini execution session with the user |
| Related task | [WORK-2026-11-25-004](2026-11-25-004-analysis-s1-s3.md) |
| Git state | `main` from `222c59e`; untouched: ~15 line-ending CSVs, user's `docs/README.md`, untracked `docs/prompts/implement-final-exam-track-a.md` |

## Objective

Deliver M3 of the final-exam Research Trend Navigator (specification §6.2–6.5):
1. Phase 0: six reviewer fixes in `configs/analysis-final-exam-v2.yaml` → `reports/final-exam/analysis-v2/` (preserving v1 outputs).
2. Phase 1: deterministic Cypher benchmark reference answers frozen in `data/manifests/qa-benchmark-v1/references-v1.jsonl` (test questions never run through the system in M3).
3. Phase 2: closed read-only tool layer (`src/scientific_network/rag/tools.py`).
4. Phase 3: D042 amendment on GraphRAG community source + GraphRAG index (`reports/final-exam/rag-v1/`, Neo4j vector index, SQLite vector export) + local/global retrieval.
5. Phase 4: multi-hop reasoning engine (`rag/{planner,executor,answer}.py`), dev-only iteration, and scripted demo cache.
6. Phase 5–6: FastAPI routes + React/Sigma/ECharts Explorer pages, Playwright tests, live latency and memory measurements.

## Changes and findings

- **Phase 0 (`analysis-final-exam-v2`, v1 outputs untouched):**
  - Added `configs/analysis-final-exam-v2.yaml` and updated `src/scientific_network/analysis/{fx_data,smallworld,communities,trends,fx_cli,fx_report}.py` with 5 new tests in `tests/test_fx_analysis.py`.
  - **Fix 1 (subject-specific lift & RCA):** Personalized PageRank (`ranking/personalized-pagerank.json`) now ranks subject `Organization` (`min_subject_papers >= 3`) and `Researcher` (`>= 2`, fallback `>= 1` if `< 5` qualify) primarily by `lift = ppr_score / global_n4_pagerank`, alongside `rca`, `subject_papers`, and secondary `top_by_raw_ppr`.
  - **Fix 2 (government bodies in `PART_OF` roll-up):** Replaced the ministry-only rule with `skip_rule: government_body` using Wikidata `parent_instance_of` + name checks guarded by a research/education allowlist. Skipped 55 government parents (112 edges, including `State Council of the People's Republic of China`, `SASAC`, US federal departments, and ministries) while keeping `Chinese Academy of Sciences` (28 units, 626 papers), `Tsinghua University` (3 units, 490 papers), `Peking University`, `Zhejiang University`, `NIH`, `CSIRO`, etc.
  - **Fix 3 (organization-anchored communities):** Replaced `"labs"` with `organization_anchored_communities` (`groups-org-anchored-communities.csv`, 124 communities), marking `> 100` members as `size_tier: "large"` (1 community: USTC Computer vision, 329 members) and disambiguating duplicate org names by top topic.
  - **Fix 4 (single clustering definition):** `smallworld.evolution` now sets `C` to `clustering(lcc)["average_local"]` (`igraph` mode=`"zero"` on LCC); verified exact equality with headline `C` for 2025 (`N1 = 0.81023579`, `N2 = 0.49838477`).
  - **Fix 5 (N3 citation sparsity):** Added `in_corpus_citations`, `out_corpus_citations`, and `sparsity_note` to `ranking-N3.json` / `scores-N3.csv.gz`.
  - **Fix 6 (trend wording & display aliases):** Labelled trend classes `descriptive (p <= 0.10 per subject, no multiple-testing correction)` and built `trends/display-aliases.json` (32 display-only alias groups, no entity merging).

- **Phase 1 (QA benchmark references frozen before any RAG/planner code):**
  - Added `src/scientific_network/evaluation/qa_references.py`, CLI `research-network qa-references`, and `tests/test_qa_references.py` (2 passed).
  - Executed deterministic parameterized Cypher against `neo4j-enriched` (`bolt://127.0.0.1:7690`, `enriched-cb371912e308`), freezing `data/manifests/qa-benchmark-v1/references-v1.jsonl` (SHA-256 `d2fcf2c0cba2fae7e5cfa7f6dd030971a9083604081ea4bebdb93ddf424b2c19`) and `references-v1-receipt.json`.
  - Test kept: **69 / 80** (`>= 60` gate passed): hop-1 `14/20`, hop-2 `22/25`, hop-3 `18/20`, global `15/15` (11 dropped for `empty_reference_result`: 6 hop-1, 3 hop-2, 2 hop-3).
  - Development kept: **19 / 20**: hop-1 `4/5`, hop-2 `6/6`, hop-3 `5/5`, global `4/4` (1 dropped: `qa-v1-d002`, `empty_reference_result`).

- **Phase 2 (closed 9-tool layer):**
  - Added `src/scientific_network/rag/tools.py` (`find`, `neighbors`, `path`, `papers`, `aggregate`, `rank`, `community`, `community_report`, `trend`) with `Neo4jToolBackend` (read-only `READ_ACCESS`, 15s timeouts, `LIMIT` caps, label/predicate allowlists) and `InMemoryGraphBackend`.
  - Same-name researchers return `ambiguous: true` with an OpenAlex-ID choice list; Method/Task/Dataset neighbors supplement sparse extracted edges with shared-paper co-occurrence tagged `source_kind: "paper_cooccurrence"`; `trend` and `find` resolve Phase 0 display aliases.
  - Added `tests/test_rag_tools.py` (2 passed: synthetic offline fixture + live Neo4j 7690 integration test).

- **Phase 3 (D042 amendment & GraphRAG index `rag-v1`):**
  - Recorded dated D042 amendment (`docs/decisions.md`, `docs/final-exam/specification.md`): weighted co-occurrence research graph (`2,020` nodes, `16,072` edges, LCC `2,016`) partitioned with Leiden (`res=1.5` → `18` Level-1 super-communities; recursive `res=1.2` for L1 ≥ 25 → `148` Level-0 leaves, `114` with ≥ 5 members), alongside S3 N1 (89 ≥ 50 members) and N2 (15 ≥ 10 members).
  - Added `configs/rag-v1.yaml`, `ops/llm/qwen3.5-4b-q4km-live.env` (`LLM_CTX=16384`, `LLM_PARALLEL=2`), `src/scientific_network/rag/{sqlite_vectors,index,retrieval}.py`, `tests/test_rag_index_retrieval.py` (4 passed), and `research-network rag-index`.
  - Built 228/233 community reports with `qwen3.5-4b-q4_k_m` (`temperature=0`, `enable_thinking=false`; 209 first-try, 19 retry, 5 dropped for ungrounded numbers; `382,343` prompt / `106,048` completion tokens), 4,316 entity descriptions (231 Wikipedia, 251 LLM from mentions, 3,834 template, 0 failures), 12,000 annotated abstract chunks, SQLite vector store (`data/processed/rag-v1/vectors.sqlite`), and Neo4j vector indexes (`rag_report_vec`, `rag_entity_vec`, `rag_chunk_vec` on `:RagReport`, `:RagEntityDesc`, `:RagChunk`) on Bolt 7690 with core/enrichment counts unchanged (`50,144` non-RAG nodes, `242,048` edges).
  - Dual-service resource check (`neo4j-enriched` + `sn-llm` live env): host `10 GiB / 11 GiB` used (`1.3 GiB` avail), `sn-llm` `7.238 GiB` RAM & `5,067 / 8,151 MiB` GPU VRAM, `neo4j-enriched` `862.7 MiB` RAM.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run pytest -q tests/test_fx_analysis.py` | exit 0; 16 passed | `tests/test_fx_analysis.py` |
| `research-network final-analysis` (sanity, smallworld `--reuse-baselines`, ranking, communities, trends, report) with `configs/analysis-final-exam-v2.yaml` | exit 0; 20/20 v4 sanity match; N1/N2 2025 `C` equals headline | `reports/final-exam/analysis-v2/`, `reports/runs/WORK-2026-11-25-005/analysis-v2.log` |
| `uv run pytest -q tests/test_qa_references.py` | exit 0; 2 passed | `tests/test_qa_references.py` |
| `uv run research-network qa-references` (against Neo4j 7690) | exit 0; 69/80 test kept, 19/20 dev kept | `data/manifests/qa-benchmark-v1/references-v1.jsonl`, `references-v1-receipt.json` |
| `uv run pytest -v tests/test_rag_tools.py` | exit 0; 2 passed (synthetic + live 7690) | `tests/test_rag_tools.py` |
| `uv run research-network rag-index --config configs/rag-v1.yaml --skip-neo4j` + `--load-neo4j-only` | exit 0; 228/233 reports, 4,316 descriptions, 12,000 chunks; SQLite + Neo4j 3 vector indexes (`rag_report_vec`, `rag_entity_vec`, `rag_chunk_vec`); non-RAG `50,144` / `242,048` intact | `reports/final-exam/rag-v1/`, `data/processed/rag-v1/vectors.sqlite`, `reports/runs/WORK-2026-11-25-005/rag-index.log` |
| `uv run pytest -q tests/test_rag_index_retrieval.py` | exit 0; 4 passed | `tests/test_rag_index_retrieval.py` |

## Decisions

- **2026-11-25 D042 amendment:** Research-graph Leiden hierarchy (`L1=18` at `res=1.5`, `L0=148` at `res=1.2`, `114` leaves `>=5`) + S3 N1/N2 communities for GraphRAG indexing; `all-MiniLM-L6-v2` retained (`docs/decisions.md`, `docs/final-exam/specification.md`).

## Open issues and limitations

- In progress.

## Next step

Complete Phase 0 (`analysis-final-exam-v2`), then freeze Phase 1 QA benchmark references.

## Corrections

None.

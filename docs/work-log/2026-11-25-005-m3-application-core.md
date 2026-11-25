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

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `uv run pytest -q tests/test_fx_analysis.py` | exit 0; 16 passed | `tests/test_fx_analysis.py` |
| `research-network final-analysis` (sanity, smallworld `--reuse-baselines`, ranking, communities, trends, report) with `configs/analysis-final-exam-v2.yaml` | exit 0; 20/20 v4 sanity match; N1/N2 2025 `C` equals headline | `reports/final-exam/analysis-v2/`, `reports/runs/WORK-2026-11-25-005/analysis-v2.log` |

## Decisions

- Pending D042 amendment for GraphRAG community source (Phase 3).

## Open issues and limitations

- In progress.

## Next step

Complete Phase 0 (`analysis-final-exam-v2`), then freeze Phase 1 QA benchmark references.

## Corrections

None.

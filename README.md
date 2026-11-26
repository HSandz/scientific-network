# AI Research Network — AAAI and IJCAI, 2021–2025

This course project for **Social Media Network Analysis for Business** builds an
evidence-backed social network from AAAI and IJCAI main-track papers, 2021–2025.
The network connects researchers, papers, organizations, topics and venues. It is
used to analyze collaboration, citation and topic patterns for research-program
planning.

The release covers 13,617 papers from roster v10, matched to OpenAlex by DOI and
checked against title and author count. It is frozen as graph **v4
`release-d3c788c3114a`** (SHA-256
`6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`, bound by its
[content freeze](reports/release-v4/content-freeze-v4.json)). The submission
deadline was 11 November 2026. See [current status](docs/status.md) for what
remains open.

**Current phase:** the final exam (due 20 December 2026) builds a research-trend
application, the Research Trend Navigator, on an enriched version of this graph. See the
section below and the [final exam specification](docs/final-exam/README.md).

## Research Trend Navigator (final exam, D042)

The Navigator is a web application for research-trend analysis of the same 13,617 AAAI and IJCAI
papers, 2021–2025. It answers which topics, methods, tasks and datasets are rising, and which
organizations and groups work on them. It runs on an **enriched graph** (`enriched-cb371912e308`,
graph v3): the frozen v4 graph plus a text-derived layer of Method, Task and Dataset entities
extracted from abstracts and linked to Wikidata and Wikipedia. That gives 50,144 nodes and 242,048
edges. Its pages are Trends, Topic/Method, Groups, Communities, Network Science, Ask, Node 360,
Explorer and About the data. **Ask** answers questions in natural language. It uses GraphRAG
community reports (local and global search) and a multi-hop planner over nine read-only graph
tools, run by a ≤9B local language model (Qwen3.5-4B, Q4_K_M). Every answer shows its reasoning
trace and highlighted subgraph.

- **Subject specialization everywhere:** `rank` computes N4 Personalized PageRank and lift on
  demand (and caches it) for subjects outside the precomputed top 30, falling back to
  revealed comparative advantage (`trends/group-interest.csv`), while entity linking prefers
  the question's implied kind (`Method`/`Task`/`Topic`/`Dataset`), offers alternatives, and
  retries once on empty steps.
- **Fast warm-up:** backend startup preloads embeddings, vector store, analysis artifacts, Neo4j
  verification and a 4-token LLM ping when configured, cutting cold-start time before the first
  event from ~20.7 s to ~1.5 s.

| Link | Status |
| --- | --- |
| System URL (deployed Navigator) | **pending**: deployment prepared ([plan](ops/azure/navigator-deployment.md)), awaiting approval |
| arXiv report | **pending** (milestone M5) |
| Data release (enrichment layer, analysis outputs, benchmark) | **pending**: bundle built locally by [`ops/release/build-data-release.py`](ops/release/build-data-release.py), publication awaiting approval |
| Frozen v4 Explorer (earlier deliverable) | <https://scientific-network-explorer.pages.dev/> |

### Key results and their caveats

- **Enrichment quality (E4).** All figures are AI-assessed, with Wilson 95% intervals
  ([v1](reports/enrichment-v1/quality.md), [v3](reports/enrichment-v3/quality.md)).
  - Entity precision 0.927 [0.891, 0.952] and recall estimate 0.590 [0.536, 0.641].
  - APPLIED_TO (single paper) 0.983 [0.911, 0.997]; linking 0.895 [0.806, 0.946].
  - PART_OF 0.951 [0.839, 0.987] on decided items, but 0.780 when its 9 unclear items count as
    incorrect, which is below the 0.80 target. MEMBER_OF is ambiguous: 13 of 26 items are unclear.
- **Small world (S1).** The declared rule (σ > 1 against Erdős–Rényi and degree-preserving baselines,
  and L ≤ 2 L_rand) holds for co-authorship N1, organization collaboration N2 and the full graph N4
  ([analysis v2](reports/final-exam/analysis-v2/README.md)). N1 has L = 8.81 against L_rand =
  5.15–5.77 and C = 0.81, so it is a clustered, long-path graph (ω = −0.73), not a textbook small
  world.
- **QA benchmark (K3).** 69 kept test questions, run once
  ([results](reports/final-exam/qa-eval-v1/results.md)). The full multi-hop system (S4) scores
  0.427 [0.313, 0.540] on factual questions, against 0.124 for the SLM alone, 0.055 for vector RAG
  and 0.163 for GraphRAG. Its automatic faithfulness is 60/69.
  - **Disclosure:** the factual score measures agreement with the graph's edges, not truth.
  - A post-hoc, AI-assessed check of literature-supported precision puts vector RAG (0.433) and S4
    (0.350) close together.
  - S4's AI-assessed citation validity of 0.36 describes the earlier citation labelling, which the
    product changed on 2026-11-26.
- **Model choice (K1).** **Team decision (2026-11-26): keep Qwen3.5-4B (4.66B total parameters).**
  Qwen3.5-4B was chosen on development extraction F1 ([K1 report](reports/enrichment-v1/k1-model-selection.md)).
  - On the development answer-accuracy arm ([K1 answer results](reports/final-exam/k1-answer/results.md)),
    Qwen3.5-9B (9.65B total parameters, above the ≤9.0B ceiling) scored 0.634 against 0.502 for
    Qwen3.5-4B; it remains the **parameter-scale reference** only.
  - Gemma-4-E4B-it (8.0B) scored 0.469, slightly below Qwen3.5-4B.

**AI-assessed statement.** All quality figures for the enrichment and the application (precision,
linking, citation validity, pairwise and supplementary precision) are judged by isolated LLM
evaluators. They are not human annotations, independently validated gold labels or verified course
accuracy. Wilson and bootstrap intervals cover sampling error only, not evaluator error.
Generated text in the app is labelled "AI-generated from graph data".

### Quick start (local)

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js, Docker, and an ignored `.env` with
`NEO4J_PASSWORD`. A fresh clone has no graph files (they are ignored). Restore them from the data
release when it is published, or rebuild from the original sources.

```bash
uv sync --locked --group dev --extra analysis --extra report
npm --prefix apps/research-explorer/frontend ci

# Enriched graph database (Bolt 7690) and load graph v3 into it
docker compose up -d neo4j-enriched
NEO4J_URI=bolt://localhost:7690 uv run research-network enrich load-graph \
  --graph data/processed/enriched-graph-v3/graph.json --report reports/runs/manual-load-v3.json

# Network analysis S1–S3 and trend metrics (writes to a new path)
uv run research-network final-analysis all --config configs/analysis-final-exam-v2.yaml \
  --graph data/processed/enriched-graph-v3/graph.json --output reports/runs/manual-analysis-v2

# Local language model (one at a time; 8 GB GPU), OpenAI-compatible on 127.0.0.1:8080
docker compose -f ops/llm/compose.yaml --env-file ops/llm/qwen3.5-4b-q4km-live.env up -d

# GraphRAG index: the committed reports in reports/final-exam/rag-v1 are used as they are.
# Rebuilding overwrites them; local search also needs the ignored data/processed/rag-v1/vectors.sqlite.
uv run research-network rag-index --config configs/rag-v1.yaml --skip-llm   # optional rebuild
# Re-cache the seven scripted demos (development questions only; never the test benchmark)
uv run python -m scientific_network.rag.dev_eval --demos-only

# Navigator app: API on :8000, UI on :5173 (both graphs served from the enriched database)
EXPLORER_NEO4J_URI=bolt://127.0.0.1:7690 EXPLORER_LLM_BASE_URL=http://127.0.0.1:8080/v1 \
  PYTHONPATH=apps/research-explorer:src uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000
npm --prefix apps/research-explorer/frontend run dev -- --host 127.0.0.1 --port 5173
```

Port and memory notes:

- On about 12 GB of RAM, run the language model and the frozen v4 database (`neo4j-five-year`,
  Bolt 7689) separately.
- If port 8080 is taken, start the model with `LLM_PORT=8081` and point `EXPLORER_LLM_BASE_URL` at
  it.
- Without a model, Ask serves the seven cached scripted demos.

## Frozen release graph v4: results

| Requirement or artifact | Frozen v4 evidence |
| --- | --- |
| Graph size | 47,875 nodes; 225,731 total edges; 32,189 resolved researchers |
| Course edge threshold | 110,026 unique factual R1–R4 edges; derived/topic/taxonomy edges counted separately |
| Relationship types | All 10 predicates are nonempty |
| OpenAlex coverage | 13,606/13,617 works matched (99.92%); 11 remain in review |
| Affiliation coverage | 48,259/65,469 matched author positions (73.71%); **fails the 80% target** |
| Topic coverage | 11,575/13,617 papers labeled (85.00%); coverage is not accuracy |
| Graph database | Isolated Neo4j Community 5.26; inventory, six integrity queries and idempotent replay pass |
| Network analysis | Five projections plus strict sensitivity, six figures/CSV tables, three source-backed findings, two shortlists |
| AI-assessed edge precision | **193/200 = 96.50%**, Wilson 95% **92.95%–98.29%**; AI-only numeric checks pass |
| Historical v3 edge audit | 176/200 = 88.00% (Wilson 82.77%–91.80%); gates failed; preserved |
| Topic agreement (historical, AI references) | Embedding micro F1 .4667, phrase baseline .2301; both miss the .95 precision target |

**All evaluation is AI-assessed.** Human validation was not performed, and
evaluator independence and verified course accuracy are not established. Wilson
intervals exclude evaluator mistakes, shared-model bias and dependence on
construction sources. The v4 correction (removing OpenAlex IDs with conflicting
ORCIDs) was motivated by the failed v3 audit, so the v4 sample is not an untouched
independent experiment. The [v4 evaluation package](reports/release-v4/README.md)
gives the full method, exposure, overlap and evidence-depth disclosures.

## Reports

- **Course report (English and Vietnamese, LaTeX):** [`report/latex/`](report/latex/README.md)
- Measured report source and figures: [`reports/final-report/report.md`](reports/final-report/report.md), [v4 figures](reports/final-report/figures-v4/captions.md)
- v4 evidence: [graph summary](reports/release-v4/graph-summary.json), [analysis](reports/release-v4/analysis.json), [findings](reports/release-v4/findings.md), [edge audit results](reports/release-v4/audit-results-agent-v2.json), [change manifest](reports/release-v4/change-manifest.json)
- Historical v3 package: [`reports/release-v3/`](reports/release-v3/README.md)
- Public Explorer: <https://scientific-network-explorer.pages.dev/>

## Reproduce the local checks

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --group dev --extra analysis --extra report
uv run pytest
uv run research-network validate \
  --input data/processed/release-graph-v4/graph.json \
  --config configs/quality-release-v1.yaml \
  --require-size \
  --output reports/runs/manual-v4-validation.json
```

A fresh clone does not include the graph file or the OpenAlex cache (both are
ignored). Restore them from the original sources and check the recorded hashes
using the [v4 restoration and reproduction guide](docs/reproduce-remediation-v4.md).
Reacquiring from the API is not a byte-identical substitute. The release database
is the isolated `neo4j-five-year` service on Bolt port 7689. The pilot and extended
databases are separate and preserved.

Analysis writes to a new path, because committed outputs are frozen:

```bash
uv run research-network analyze \
  --input data/processed/release-graph-v4/graph.json \
  --config configs/analysis-release-v1.yaml \
  --quality-config configs/quality-release-v1.yaml \
  --output reports/runs/manual-analysis.json
```

## Graph model

The graph has five labels: `Researcher`, `Paper`, `Organization`, `Topic` and
`Venue`. Its ten predicates are:

- Observed: `AUTHORED`, `AFFILIATED_WITH`, `PUBLISHED_IN`, `CITES`
- Inferred from text: `HAS_TOPIC`
- Curated taxonomy: `SUBTOPIC_OF`
- Derived from accepted core-paper evidence: `COAUTHORED_WITH`, `COLLABORATED_WITH`, `RESEARCHES_TOPIC`, `CONTRIBUTES_TO_TOPIC`

The enriched graph v3 keeps these unchanged and adds a text-derived layer (D042):
`Method`, `Task` and `Dataset` entities and eight enrichment predicates (`USES_METHOD`,
`USES_DATASET`, `ADDRESSES_TASK`, `APPLIED_TO`, `EVALUATED_ON`, `PART_OF`, `MEMBER_OF`,
`RELATED_TO`).

Read the [graph schema](docs/graph-schema.md) for evidence, identity and weight
rules. Researchers are never merged on similar names alone. Affiliation triples
stay paper-specific before aggregation, and ambiguous claims stay in the review
queue.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/scientific_network/` | Python package, one subpackage per pipeline stage; CLI `research-network` |
| `tests/` | Test suite (`uv run pytest`) |
| `configs/` | Versioned corpus, quality, analysis and evaluation configs; earlier versions kept for reproducibility |
| `queries/` | Neo4j constraints, inventory, integrity and analysis Cypher |
| `apps/research-explorer/` | Research Explorer and Research Trend Navigator frontend and API; `ops/azure/` holds its deployment |
| `ops/llm/`, `ops/release/` | Local language-model server (llama.cpp) settings; data-release bundle builder |
| `reports/final-exam/`, `reports/enrichment-v*/` | Final-exam analysis, GraphRAG, QA and K1 evaluation results; enrichment quality |
| `reports/` | Measured results, receipts and figures, one folder per release |
| `report/latex/` | Course report sources |
| `docs/` | Requirements, design, workflows, decisions and the work log; start at [docs/README.md](docs/README.md) |

## Licences

- **Code:** [MIT License](LICENSE) (`Copyright (c) 2026 Research Trend Navigator contributors`).
- **Project-authored data** (enrichment triples not verbatim from external sources, resolved graph
  edges, analysis outputs, community reports and QA benchmark): **CC BY 4.0** — see
  [LICENSE-DATA.md](LICENSE-DATA.md).
- **Third-party sources** keep their own terms: OpenAlex metadata, ROR identifiers and Wikidata
  statements/IDs under **CC0 1.0**; Wikipedia lead summaries under **CC BY-SA 4.0** with
  attribution; AI-generated text is labelled and excludes third-party verbatim abstracts.

Raw downloads, graphs, models, credentials and database volumes are not tracked.
The repository is [github.com/HSandz/scientific-network](https://github.com/HSandz/scientific-network).
Its visibility and lecturer access are tracked in [status](docs/status.md).

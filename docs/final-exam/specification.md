# Research Trend Navigator — final exam specification

Working specification for the team and agents. It says what to build, the
default technical choices and how each part is accepted. The rubric and the
mapping from rubric items to sections are in [requirements.md](requirements.md).
Where this document fixes a default (a model, a threshold, a library), it can be
changed. Record the change in [decisions.md](../decisions.md) under D042 and
update this file.

Status: **draft, 23 November 2026.** Nothing in this document is implemented yet
unless §3.1 says so.

## 1. Product in one paragraph

**Research Trend Navigator** is a web application over a knowledge graph of the
13,617 AAAI and IJCAI 2021–2025 main-track papers. It answers three questions:
*what is trending* (topics, methods, tasks and datasets rising or falling, year by
year), *who is working on it* (organizations, well-known labs, collaboration
communities and the key researchers inside them), and *how things connect* (a chat
assistant that answers multi-hop questions over the graph, shows each hop on the
graph and cites papers). Every number on screen links to its definition, its
denominator and the graph version it came from.

Example questions the finished product must answer:

1. Which methods grew fastest in AAAI and IJCAI papers between 2021 and 2025, as a share of each year's papers?
2. Which organizations moved into large language models after 2022, and who do they collaborate with?
3. Which research communities work on reinforcement learning, and who are their hubs and bridges?
4. What datasets do the fastest-growing tasks of 2025 use, and which groups published on them first?
5. How is researcher A connected to researcher B, and what topics do the papers along that path share?

## 2. Users and use cases

| User | Need | Main screens (§6.4) |
| --- | --- | --- |
| Instructor or grader | See each rubric item demonstrated with real numbers | Network Science, Trends, Ask |
| Research planner (the course's business framing) | Spot emerging areas and potential partners | Trends, Topic pages, Groups |
| Student or researcher | Explore who does what and read the evidence | Ask, Node 360, Explorer |

Use cases to support end to end:

- **UC1 Trend scan:** pick a period and a level (topic, method, task, dataset) and get
  ranked rising, emerging and declining items with trend lines.
- **UC2 Topic deep-dive:** open one topic or method and see its trend, top
  organizations, communities, key researchers, related methods and datasets, key
  papers, and a generated summary with citations.
- **UC3 Group profile:** open an organization, lab or community and see its topic
  portfolio over time, specialization, partners, members and Wikipedia profile.
- **UC4 Ask:** ask a free-text question and get an answer grounded in the graph, with
  the reasoning steps, the subgraph used and the cited papers.
- **UC5 Network science:** see the small-world proof, the rankings and the
  community structure, with each calculation shown.

## 3. Starting point, constraints and architecture

### 3.1 What already exists (frozen, reused)

- Graph **v4 `release-d3c788c3114a`**: 47,875 nodes (32,189 researchers, 13,617
  papers, 2,047 organizations, 20 topics, 2 venues) and 225,731 edges over ten
  predicates. Details: [reports/release-v4/README.md](../../reports/release-v4/README.md).
- Text: titles and abstracts for 13,606 papers (11 have a title only), from cached
  OpenAlex works (`data/interim/release-v1/works.jsonl`, ignored).
- Organizations carry OpenAlex IDs, ROR IDs, country and sector.
- An embedding topic classifier (`all-MiniLM-L6-v2`, frozen thresholds, 20-topic
  taxonomy) covers 85% of papers.
- Analysis code (`src/scientific_network/analysis/`): five projections, PageRank,
  approximate betweenness, Louvain communities, robustness checks.
- Research Explorer (`apps/research-explorer/`): React 18, TypeScript, Sigma.js,
  ECharts frontend; FastAPI backend over Neo4j and SQLite artifacts; deployed to
  Cloudflare Pages and Azure ([ops/azure/README.md](../../ops/azure/README.md)).
- An agent evaluation workflow with frozen samples, ledgers and Wilson intervals
  ([agent-audit-workflow.md](../agent-audit-workflow.md)).

### 3.2 Constraints

- **Scope:** no new papers, venues or years. Enrichment adds entities and relations
  *about* the existing corpus only.
- **Frozen v4:** v4 graph, database, audit and reports are not modified. The
  enriched graph is a new version, **v5-enriched**, built from v4 plus the
  enrichment layer. It loads into a new isolated Neo4j service (default
  `neo4j-enriched`, Bolt port 7690). Pilot, extended and five-year services stay
  untouched.
- **Schema:** v4's five labels and ten predicates are kept unchanged inside v5. New
  labels and predicates (§4.4) form a separate, named enrichment layer, so v4 counts
  stay reportable on their own. D042 authorizes this extension.
- **Models:** pretrained or zero-shot only; no training or fine-tuning. Generative
  models must have ≤9B parameters. Encoders (embeddings, NER) are also small and are
  reported with their sizes.
- **Evaluation:** AI-assessed, labelled as such, with the integrity rules of
  `AGENTS.md`: frozen samples before review, no tuning on the test sample, real
  evaluator metadata, Wilson intervals that do not cover evaluator error.
- **Researcher identity:** enrichment never merges researchers on names. Researcher
  nodes come only from v4.

### 3.3 Architecture

```
 cached OpenAlex abstracts ─┐
 Wikipedia / Wikidata ──────┼─► enrichment pipeline ─► enrichment layer ─┐
 graph v4 (frozen) ─────────┘   (§4: extract, link,      (entities,       │
                                 relate, evaluate)        relations,      │
                                                          evidence)       ▼
                                                      graph v5-enriched (JSON)
                                                              │
                     ┌────────────────────────────────────────┼──────────────────┐
                     ▼                                        ▼                  ▼
            Neo4j neo4j-enriched                    analysis (§5): small     GraphRAG index (§6.2):
            (+ vector index)                        world, ranking,          community reports,
                     │                              communities, trends      entity and chunk embeddings
                     └──────────────┬──────────────────────┬──────────────────┘
                                    ▼                      ▼
                         FastAPI backend: graph API, trends API, Ask API
                         (retrieval + multi-hop planner + SLM client)
                                    │
                                    ▼
                    React frontend: Trends, Topics, Groups, Communities,
                    Network Science, Ask, Node 360, Explorer
```

**Platform decision:** extend the existing Research Explorer instead of starting a
new app. It already has the graph canvas, inspector, analytics charts, a
deployment and a test suite. New pages are added as routes; existing modes stay.

**Code layout** (follows `AGENTS.md`):

| Path | New content |
| --- | --- |
| `src/scientific_network/enrich/` | Source fetchers, entity extraction, linking, relation extraction, layer builder |
| `src/scientific_network/analysis/` | Small-world, ranking, community and trend modules |
| `src/scientific_network/rag/` | Community reports, embedding index, retrieval, multi-hop planner and tools, SLM client |
| `src/scientific_network/evaluation/` | Enrichment audit and QA benchmark scoring |
| `configs/*-enrichment-v1.yaml`, `configs/rag-v1.yaml` | Versioned configs |
| `apps/research-explorer/` | New backend routes and frontend pages |
| `reports/enrichment-v1/`, `reports/final-exam/` | Measured outputs and receipts |
| `report/arxiv/`, `slides/` | arXiv paper and presentation sources |

## 4. Data enrichment (E1–E4)

### 4.1 Sources and selection

| Source | What is used | Selection | Licence note |
| --- | --- | --- | --- |
| Paper abstracts (OpenAlex cache) | Title and abstract text of all 13,606 papers with abstracts | All core papers; the 11 title-only papers use titles | OpenAlex data is CC0. Check [source-policy.md](../source-policy.md) before redistributing abstract text; the public data release can ship IDs, spans and offsets instead of full text |
| Wikidata | Organization facts: type, parent organization (P749), part of (P361), country, inception, website, English Wikipedia sitelink | Organizations in v4, matched by ROR ID (Wikidata P6782); unmatched ones get a labelled name search with manual-style AI check | CC0 |
| Wikipedia (main text) | Lead section and infobox of each linked organization, topic, method, task and dataset; used for descriptions and as text for relation extraction | Pages linked in §4.2 only, not general crawling | CC BY-SA 4.0: attribute, keep the page revision ID |
| Wikidata for researchers (optional) | Notable researchers via ORCID (P496) or OpenAlex author ID (P10283) | Only exact ID matches; never names | CC0 |
| News or blogs (stretch) | Mentions of organizations and methods in AI news | Only if time allows after M3; same evidence rules | Per source |

Every fetched document is stored once, immutable, with URL, retrieval time,
revision ID and SHA-256 (`data/raw/enrichment-v1/`, ignored). The source manifest
(`reports/enrichment-v1/sources.json`) records counts per source and type and the
selection rules. That manifest is the E1 evidence.

**Splits (set before any prompt or threshold work):** a seeded, year-and-venue
stratified draw reserves **100 development papers** for prompt and threshold design
and **200 test papers** for the audit. Write both to
`data/manifests/enrichment-splits-v1/` and record their overlap with earlier audit
samples. Development decisions never look at test papers.

### 4.2 Entity extraction and linking (E2)

**New entity types** linked to the course topic, which is AI research:

| Label | Meaning | Examples |
| --- | --- | --- |
| `Method` | Model, algorithm, architecture or technique | transformer, graph neural network, PPO, diffusion model |
| `Task` | Problem addressed | image segmentation, link prediction, multi-agent path finding |
| `Dataset` | Named dataset or benchmark | ImageNet, COCO, MuJoCo, GLUE |

Organizations, topics and researchers already exist in v4. Enrichment adds
properties to them (Wikipedia description, organization type, parent) but no new
nodes of those labels.

**Pipeline** (no training):

1. **Mention detection:** a zero-shot, schema-driven encoder extracts entities and
   candidate relations from title and abstract sentences in one pass. The entity
   labels, relation labels and their descriptions are given at inference time.

   | Extractor | Size | Released | Role |
   | --- | --- | --- | --- |
   | `fastino/gliner2.5-base-v1` (GLiNER2.5) | 194M | Aug 2026, Apache-2.0 | **Default.** Joint entities and relations with schema constraints; boundary prediction, so long method names are not cut at a fixed span length |
   | `knowledgator/gliner-relex-large-v1.0` (GLiNER-Relex) | 467M | Mar 2026, Apache-2.0 | Comparison: joint NER and relation extraction |

   The development split picks the extractor and its thresholds. GLiNER2.5 loads
   through `gliner2[local]` (`AutoExtractor`); the older GLiNER loader does not
   read 2.5 checkpoints.
2. **Verification and typing:** the SLM (§6.1) receives the sentence and the
   candidate spans and returns JSON that keeps, drops or retypes each span.
   Dropped spans are kept with a reason. Encoder-only output is kept as the
   ablation baseline.
3. **Normalization:** lowercase and lemmatize; expand acronyms defined in the same
   abstract ("graph neural network (GNN)"); merge surface forms whose embeddings
   are close (cosine threshold set on development data) only within the same type.
4. **Linking:** search Wikipedia for each normalized entity and score candidate
   pages by embedding similarity between the abstract contexts and the page lead.
   Accept above a development-set threshold; otherwise keep the entity unlinked.
   A linked entity's canonical ID is its Wikidata QID; an unlinked one gets a
   deterministic ID from type and normalized name, marked `linked: false`.
5. **Node threshold:** an entity becomes a node only if it is supported by ≥3
   distinct papers. Rarer entities stay as mentions in the evidence store. The
   ≥3 default is tunable on development data only.

Every mention records paper ID, sentence offsets, extractor version and
confidence. Expected size: a few thousand `Method`/`Task`/`Dataset` nodes. That
is an estimate, not a target; report the measured count.

### 4.3 Relationship extraction (E3)

**New predicates.** "Extracted" means read from text with a sentence as evidence.
"Wikidata" means taken from a structured fact. "Aggregated" means counted over
extracted edges.

| Predicate | From → to | Origin | Rule |
| --- | --- | --- | --- |
| `USES_METHOD` | Paper → Method | Extracted | A paper's verified Method mention, where the abstract describes it as used or proposed |
| `ADDRESSES_TASK` | Paper → Task | Extracted | Verified Task mention the paper works on |
| `USES_DATASET` | Paper → Dataset | Extracted | Verified Dataset mention used for experiments |
| `APPLIED_TO` | Method → Task | Extracted | Same-sentence relation judged by the SLM as "method is applied to or solves task"; edge kept when ≥2 papers support it |
| `EVALUATED_ON` | Method or Task → Dataset | Extracted | Same-sentence relation "evaluated or benchmarked on"; ≥2 supporting papers |
| `PART_OF` | Organization → Organization | Wikidata | P749 or P361 between two organizations, or one in v4 and one added as a parent-only node |
| `RELATED_TO` | Method/Task → Method/Task | Wikipedia | A Wikipedia link between two linked entities' pages plus ≥3 co-occurring papers |

**Relation model.** The encoder (§4.2) proposes candidate `APPLIED_TO` and
`EVALUATED_ON` relations under the schema. For each sentence with two or more
verified entities, the SLM then receives the sentence, the typed entities, the
encoder's candidates and the closed list of relation types. It returns JSON with
`{head, relation, tail, confidence}` or `none`, and may add relations the encoder
missed. The output is
validated against the schema, and invalid JSON is retried once and then dropped.
Paper-to-entity edges come from the verified mentions in §4.2. Organization-level
interest ("organization X works on method Y") is **not** stored as an edge. It is
computed in queries from `AUTHORED`, `AFFILIATED_WITH` and `USES_METHOD`, so each
answer can be traced to papers.

Every edge carries `evidence_kind` (`extracted`, `wikidata`, `aggregated`),
`method_version`, `graph_version`, `support_count`, its supporting paper IDs and
sentence locators. For aggregated edges it also carries the raw and fractional
weights, following the v4 edge rules.

> **Note, 2026-11-25 (measured on graph `enriched-c0f7d1dd4abd`).** The extracted `APPLIED_TO` (32 edges) and
> `EVALUATED_ON` (4 edges) are sparse under the frozen rule: only 1,046 of 30,251 paper-level relations have both endpoints among
> the 1,991 entity nodes (most heads are a paper's own named method), and 909 of the remaining 943 node pairs have a single
> supporting paper. The application therefore answers method–task, method–dataset and task–dataset questions from **paper
> co-occurrence**: papers that carry both entities through `USES_METHOD`, `ADDRESSES_TASK` and `USES_DATASET`, with the shared
> papers as evidence (`enrich/cooccurrence.py`, `queries/enriched-method-task.cypher` and siblings; distribution in
> `reports/enrichment-v1/cooccurrence.json`). This adds no predicate and no threshold. A v2 relation rule (for example one paper when
> both endpoints share a sentence) is a separate, optional future decision: it would need tuning on development papers only, a dated
> D042 amendment and a new E4 sample.

> **Note, 2026-11-25 (enrichment v2, graph `enriched-827be09bc987`; D042 amendment "Enrichment v2: rules and acceptance criteria
> declared before measurement").** The optional v2 relation rule was tried and decided on development material, with criteria declared
> first. Single supporting paper, both endpoints in one sentence: **adopted for `EVALUATED_ON`** (23 of 24 correct on a supplementary
> development sample; 27 new edges, `support_rule: single_paper_same_sentence`) and **not adopted for `APPLIED_TO`** (same-sentence
> precision 0.452 against the frozen dev reference labels, declared 0.80), so `APPLIED_TO` stays at 32 edges and method–task questions
> keep using paper co-occurrence. The PART_OF rule (organization class filter, end dates, direction check) **failed its criterion**
> (kept precision 0.778, declared 0.85) and v1 `PART_OF` is unchanged; its consortium and association branch passed its own criterion
> and is added as the separate predicate `MEMBER_OF` (85 edges), so a pair can carry both. The reasons and figures are in
> `reports/enrichment-v2/`.

> **Note, 2026-11-25 (enrichment v3, graph `enriched-cb371912e308`; D042 amendment "Enrichment v3").** A reviewer judged the v2 absolute
> criteria badly chosen. On a **relative, post-hoc** criterion (decided after the v2 development results), the v2 `PART_OF` rule and the
> link guard are adopted unchanged: `PART_OF` 1,129 → 783, each organization pair carries one of `PART_OF` and `MEMBER_OF`, the 36, 14 and 2
> organizations under S&P 500, Dow Jones and Forbes Global 2000 are gone, and 43 of 287 raw links were removed by the guard (linked entities
> 261 → 231). Single-paper same-sentence `APPLIED_TO` is adopted after its criterion was re-declared on the audit scale (38 of 40 correct on a
> fresh sample labeled by a fresh evaluator context): `APPLIED_TO` 32 → 167. Development checks are not evidence for v3; the only accuracy
> claims are the fresh E4 v3 audit in §4.5.

### 4.4 Enriched graph schema and build

- v5-enriched = all v4 nodes and edges unchanged, plus the enrichment layer.
  Optional parent organizations from Wikidata are labelled `Organization` with
  `source: wikidata_parent` and `is_core: false`, so they never count toward core
  size gates.
- New labels: `Method`, `Task`, `Dataset`. New predicates: the seven in §4.3.
  Document them in [graph-schema.md](../graph-schema.md) as an "enrichment layer"
  section. The v4 sections stay as they are.
- The validator gains rules for the new types: endpoint labels, ID determinism,
  evidence present, support thresholds. A structural report is written next to the
  graph.
- Neo4j: load into `neo4j-enriched` (port 7690) with constraints and indexes for
  the new labels and a vector index for embeddings (§6.2). The loader refuses any
  other port for this graph version, as it does for v4.
- Summary counts are reported separately: v4 layer, enrichment layer by evidence
  kind, and the total.

### 4.5 Quality evaluation (E4)

Graph quality is measured on four axes. All accuracy figures are **AI-assessed**,
using the frozen-sample workflow of [agent-audit-workflow.md](../agent-audit-workflow.md).

| Axis | Measure | Sample |
| --- | --- | --- |
| Entity precision | Share of extracted mentions that are a real Method/Task/Dataset of the stated type | Up to 100 mentions per type from the 200 test papers |
| Entity recall (estimate) | The evaluator lists every Method/Task/Dataset in 50 test abstracts; recall = matched / listed | 50 test abstracts |
| Linking accuracy | Share of linked entities whose Wikipedia page is the right concept | 100 linked entities |
| Relation precision | Share of edges whose evidence sentence supports the predicate | 100 per extracted predicate, or all if fewer; 50 `PART_OF` |
| Structure | Validator rules, orphan nodes, duplicate entities (same Wikidata QID under two IDs), type conflicts | Whole graph |
| Coverage | Papers with ≥1 Method, Task and Dataset; organizations linked to Wikipedia | Whole graph |

Rules:

- Freeze the sample (IDs, seed, graph hash) before any judgment. The evaluator
  sees evidence sentences and the source page, not the extractor's confidence.
- Use a different model family from the extractor as evaluator. Default: the
  project's agent evaluator (a frontier model run in isolated contexts), with A/B
  overlap on 20% of items and Cohen's κ reported. Record the model, provider and
  run IDs as they actually were.
- Report point estimates with Wilson 95% intervals, per type and per predicate, and
  state that the intervals exclude evaluator error.
- **Ablation:** score three variants on the same frozen sample: encoder only, SLM
  only (extraction from the prompt) and encoder plus SLM verification (the
  default). This shows what each model adds.
- Targets (declared now, reported as pass or fail, not tuned against): entity
  precision ≥0.85, relation precision ≥0.80, linking accuracy ≥0.85. A miss is
  reported, not hidden.

> **Note, 2026-11-25 (E4 v2, graph `enriched-827be09bc987`).** Only the axes that v2 changed were re-audited, on fresh samples that
> exclude every v1-audited item, with the same A/B/C workflow (all items double-judged because each axis has 50 or fewer items): `EVALUATED_ON`
> single paper, all 27 new edges, 26 correct (0.963, Wilson [0.817, 0.993]); `MEMBER_OF`, 30 of 85, 29 of 29 decided with one unclear (0.967
> with unclear as incorrect). `MEMBER_OF` has no declared target, and its A/B agreement was low (kappa 0.144; most disputes were whether a
> partner of a consortium node counts as a member), so its figure carries that caveat. Axes whose rule was not adopted (`PART_OF` 0.69,
> linking 0.80, both below target) keep their v1 figures, labelled as carried over in `reports/enrichment-v2/quality.md`. These are
> AI-assessed figures; the Wilson intervals exclude evaluator error.

> **Note, 2026-11-25 (E4 v3, graph `enriched-cb371912e308`).** Fresh items only (not v1- or v2-audited, not in any development or informational
> sample); every item judged by A (`claude-opus-5-5`) and B (`gpt-6.2-sol`), disputes by a separate `gpt-6.2-sol` session as adjudicator C, which
> is a different family from A but the same model as B. Fewer fresh items existed than requested except for `PART_OF`. Point estimates with
> Wilson 95% intervals: `PART_OF` 0.951 (39/41 decided, 9 unclear; **0.78 with unclear counted as incorrect**), linking 0.895 (68/76), single-paper
> `APPLIED_TO` 0.983 (59/60), `MEMBER_OF` 13/13 decided but 13 of 26 unclear (sensitivity 0.50; the v2 `MEMBER_OF` figure drops from 0.97 to 0.63
> when the non-Claude adjudicator replaces the Claude one). Relation and linking targets are met on the primary rule; `PART_OF` meets 0.80 only
> when unclear is excluded. Evaluators are AI agents, so none of this is human annotation.

## 5. Social network analysis (S1–S3)

All analysis runs on fixed graph versions with seeds and writes versioned JSON
under `reports/final-exam/analysis/`. Computations use igraph (fast exact shortest
paths, Leiden) with NetworkX for checks. Every reported number keeps its
denominator and network name.

**Networks analyzed:**

| ID | Network | Nodes / edges |
| --- | --- | --- |
| N1 | Researcher co-authorship (`COAUTHORED_WITH`) | 32,189 researchers; largest component 20,776 |
| N2 | Organization collaboration (`COLLABORATED_WITH`) | 2,047 organizations |
| N3 | Paper citation (`CITES`, directed) | Core papers |
| N4 | Full enriched knowledge graph, undirected, all labels | v5-enriched |

### 5.1 Small world (S1)

For N1, N2 and N4, on the largest connected component:

- Exact average shortest path length **L** (BFS from every node), diameter, and the
  full path-length distribution (histogram: share of pairs at distance 1, 2, 3, …).
- Average clustering coefficient **C** and transitivity.
- Baselines: 20 Erdős–Rényi graphs G(n, m) and 20 degree-preserving rewired graphs
  (configuration model via double-edge swaps), same n and m. Report the means and
  standard deviations of L_rand and C_rand.
- Small-world coefficient **σ = (C / C_rand) / (L / L_rand)**. Small world holds
  when L is close to L_rand (similar order, ~ln n / ln⟨k⟩) and C ≫ C_rand, so σ > 1.
  Also report ω if the lattice baseline is computable in time; otherwise say why
  it was skipped.
- Evolution: L and C for the cumulative network at each year 2021…2025.
- Degree distribution on log–log axes, with a heavy-tail fit (fit statistics
  reported, no power-law claim without a test).

The app's Network Science page shows each formula, the inputs (n, m, ⟨k⟩), the
measured values and the baselines.

### 5.2 Node ranking (S2)

- Weighted **PageRank** (damping 0.85) on N1 (fractional weight), N2, N3 (directed;
  within-corpus influence) and N4.
- **Topic-personalized PageRank:** the restart vector is spread over the papers of
  one topic, method or task. This ranks the researchers and organizations most
  central *to that subject*, and feeds the Topic pages.
- Comparison: degree, strength, betweenness (exact on N2, sampled on N1 with the
  sample size reported) and eigenvector centrality. Report Spearman correlations and
  top-20 overlaps between measures.
- Robustness: top-20 stability under the strict evidence filter (support ≥2), as in
  v4.
- Output: top-k tables per network, with name, score, rank, degree and community.

### 5.3 Communities and key individuals (S3)

- **Leiden** (modularity objective) on N1 and N2 at resolutions 0.8, 1.0 and 1.2 and
  three seeds, with a hierarchical level for GraphRAG (§6.2). Louvain is a fallback
  and a cross-check. Report modularity, the number and size distribution of
  communities, and stability (NMI across seeds).
- **Community labels:** for each community, the top topics, methods and organizations
  by c-TF-IDF over member papers, plus a generated title (§6.2).
- **Key individuals** in each community:
  - *Hubs:* highest PageRank within the community.
  - *Brokers:* highest betweenness or participation coefficient across communities.
  - *Rising researchers:* largest paper growth in 2024–2025 compared with 2021–2023,
    with a minimum paper count.
- **Groups**, meaning "famous groups" in every sense:
  - organizations, with Wikipedia-notable ones flagged;
  - labs or research groups, approximated as an organization-anchored N1 community
    (most members share one organization);
  - Leiden communities of N1 and N2.

  The UI states which kind of group each one is.

> **Note, 2026-11-25 (presentation rules for groups, analysis config `analysis-final-exam-v1`).** Organizations are rolled up to parents along
> `PART_OF` only. `MEMBER_OF` is never used for a roll-up: its audit was ambiguous (reviewer A and B disagreed on whether membership of a
> consortium node is membership, see `reports/enrichment-v2/quality.md`). Parents whose name contains "ministry" are skipped, so a ministry never
> appears as the parent of a university. The reviewer counted 48 such `PART_OF` edges; the name rule reproduces that count, while a rule on the Wikidata
> class label would flag 78 (it also flags Tsinghua University and US federal departments), so the declared rule is the name rule (a disclosed change
> made before any roll-up was computed, recorded in the config). Community labels are c-TF-IDF terms only; generated titles stay in M3 (§6.2). The
> "lab" group kind is an organization-anchored N1 community under the thresholds in the config, an approximation and not a verified research group.

### 5.4 Trend metrics (feed the application)

For each topic, method, task and dataset, and each year:

- Paper count and **share** of that year's papers. AAAI and IJCAI grew from 2,240
  papers in 2021 to 4,042 in 2025, so raw counts mislead; share is the default.
- Growth: compound annual growth of share 2021→2025, the slope of a least-squares
  line of share against year, and a year-over-year change.
- Classes: **rising** (positive slope, significant at the stated level),
  **emerging** (low 2021–2022 base, high 2024–2025 share), **declining**, **stable**.
  Thresholds are fixed in config before results are inspected.
- Group interest: an organization's or community's share of papers in a subject,
  its specialization (revealed comparative advantage = its share ÷ corpus share),
  its first year active, and its growth.
- Caveats shown with trends: two venues only, venue size changes, topic labels
  come from a classifier with known precision limits (v4 topic evaluation), and
  2025 has the most papers.

## 6. Knowledge-graph application (K1–K3)

### 6.1 Language model selection (K1)

**Eligibility rule:** a model is eligible if the *total* parameter count of its
official checkpoint, as Hugging Face's safetensors metadata reports it, is ≤9.0B.
Counting the total, including any vision or audio encoder, is the strict reading;
it avoids an argument with the grader.

**Candidates** (generative; counts read from Hugging Face on 23 November 2026):

| Model | Total parameters | Released | Status |
| --- | --- | --- | --- |
| `google/gemma-4-E4B-it` (Gemma 4) | 8.00B (4B effective) | Apr 2026, Apache-2.0 | Eligible |
| `Qwen/Qwen3.5-4B` | 4.66B | Feb 2026, Apache-2.0 | Eligible |
| `Qwen/Qwen3.5-9B` | 9.65B (named 9B; the total includes its vision encoder) | Feb 2026, Apache-2.0 | Reference only, unless the exception below applies |

Excluded: TwIL-8B (8.8B, November 2026). It is a reasoning and coding fine-tune
with a non-commercial licence and self-reported benchmarks. Older models
(Qwen3-8B, Llama-3.1-8B) are superseded by the candidates above.

**Selection experiment** on the 100 development papers and a 20-question
development QA set (not the test benchmark):

- Extraction quality: agreement with the AI reference labels of the development
  set (precision, recall, F1).
- JSON validity rate, relation accuracy, and answer quality on the development
  questions.
- Latency (tokens per second), VRAM use and cost per 1,000 abstracts.
- Parameter scale: the 4.7B, 8B and 9.65B points show how quality changes with
  size. This is the "parameter scale" justification the rubric asks for.

**Decision rule:** pick the best eligible model on development F1 and answer
quality, within the runtime budget. Qwen3.5-9B may replace it only if it beats
the best eligible model by at least 5 F1 points on extraction or 10 points on
development answer accuracy, *and* the team accepts the "9B language model"
argument and records it in a D042 amendment. Report the full table as K1 evidence,
with the exact model ID, revision, quantization and provider. Check runtime
support (Ollama, llama.cpp, vLLM, hosted providers) for each candidate at M0;
Qwen3.5 uses a hybrid Gated DeltaNet and attention architecture, and Gemma 4 E4B
uses per-layer embeddings.

**Runtime:**
- *Development:* the local machine has an RTX 5060 Laptop GPU with 8 GB. Every
  candidate fits at 4-bit quantization with a modest context; Qwen3.5-9B is the
  tightest fit. The encoders (§4.2) run on the same GPU or on CPU.
- *Bulk extraction:* about 13.6k abstracts, roughly 2M output tokens. That takes
  hours locally, so a hosted OpenAI-compatible endpoint serving the *same* model is
  allowed.
- *Public demo:* the Azure VM is CPU-only, so the demo uses a hosted endpoint.

The client (`src/scientific_network/rag/llm.py`) takes one OpenAI-compatible base
URL and model name from config, so switching runtime changes no code. Every call
logs the model, provider, prompt version and hashes. Embeddings default to the existing
`all-MiniLM-L6-v2` (22M). Newer small encoders, such as `Qwen/Qwen3-Embedding-0.6B`
or `google/embeddinggemma-300m`, compete in the same experiment on linking accuracy
and retrieval quality; confirm their IDs and licences at M0.

### 6.2 GraphRAG index and retrieval (K2)

GraphRAG-style indexing over v5-enriched:

1. **Community hierarchy:** Leiden levels from §5.3 on the research graph (papers,
   researchers, organizations, methods, tasks, datasets).
2. **Community reports:** for each community at each level, the SLM writes a report
   from structured input only: top entities with metrics, top papers, trend
   figures and member organizations. A report has a title, a summary, key findings
   with cited paper IDs, and a rating of how central the community is to its
   topics. Reports are cached, versioned and embedded.
3. **Entity descriptions:** a short description per Method, Task, Dataset and
   Organization (Wikipedia lead when linked, otherwise generated from mentions and
   marked as such), embedded.
4. **Text chunks:** abstract sentences with entity annotations, embedded.

**Retrieval modes:**
- *Local search* (entity-centric): link the question's entities, collect their
  k-hop neighborhoods, related reports and top chunks, rank them, and fit them into
  the context budget.
- *Global search* (corpus-level questions such as "what are the main research
  directions in 2025?"): a map-reduce pass over community reports.
- *Graph query:* exact numbers come from deterministic Cypher or trend tools
  (§6.3), never from model memory.

**Vector store:** a Neo4j vector index in `neo4j-enriched` for development. The
deployed demo exports the vectors to the existing SQLite artifact store with an
in-process index, so the Azure VM does not need a second database.

**Visualization:** communities are shown on the graph as super-nodes, with an
icon, size and colour by level. A super-node expands to its members, and its
report opens in the inspector.

### 6.3 Multi-hop reasoning (K3)

The language model plans and the graph answers. The model never invents facts or
writes free-form Cypher.

1. **Parse and link:** extract the question's entities, time range and intent, then
   link them to graph IDs (exact, alias, then embedding match). Ambiguous names
   (two researchers with the same name) are shown to the user to choose from.
2. **Plan:** the SLM writes a plan of 1–4 steps using a closed tool set:

   | Tool | Does |
   | --- | --- |
   | `find(type, text)` | Entity lookup |
   | `neighbors(id, predicates, filters)` | One hop with year, venue and support filters |
   | `path(a, b, max_len, predicates)` | Shortest or constrained paths |
   | `papers(filter)` | Papers matching entity, year or venue conditions |
   | `aggregate(entity_set, by, metric)` | Counts, shares and growth over years |
   | `rank(network, scope, measure)` | PageRank or centrality, optionally topic-personalized |
   | `community(id)` / `community_report(cid)` | Community membership and report |
   | `trend(subject, period)` | §5.4 metrics |

3. **Execute:** each tool is a parameterized, read-only Cypher query or a lookup in
   precomputed artifacts, with limits and timeouts. Each step's output becomes the
   next step's input. If a step returns nothing, stop and say so instead of guessing.
4. **Answer:** the SLM writes the answer only from the collected results and cites
   paper IDs. Every number in the answer must appear in a tool result; a check
   rejects answers with numbers or entities that are not in the trace.
5. **Show:** the UI shows the plan, each step's result table, and the union
   subgraph highlighted on the canvas, hop by hop.

Worked example: "Which organizations collaborating with Tsinghua University increased
their share of large-language-model papers after 2022?" runs `find(Organization,
Tsinghua)`, then `neighbors(COLLABORATED_WITH)`, then `aggregate(by=year,
subject=LLM topic)`, then a filter on growth.

### 6.4 Product features

| Page | Contents | Rubric |
| --- | --- | --- |
| **Trends** | Topic/method/task/dataset trend lines (share per year), rising, emerging and declining leaderboards, topic × year heat map, venue toggle, period picker | K3, product |
| **Topic / Method page** | Trend, top organizations and groups (personalized PageRank and specialization), communities, key researchers, related methods, tasks and datasets, most-cited papers in the corpus, generated summary with citations | K2, K3, S2 |
| **Groups** | Organization × topic matrix, specialization, entry year, partners, Wikipedia profile (type, parent, country), labs, filter by sector and country | S3, K3 |
| **Communities** | Community map with super-nodes, report cards, hubs, brokers and rising researchers, topic profile over time | S3, K2 |
| **Network Science** | Small-world proof (L, C, σ against baselines, path-length histogram, degree distribution, evolution by year), centrality rankings and correlations, community statistics; each figure with its formula and inputs | S1–S3 |
| **Ask** | Chat with local, global and automatic modes; streaming answer; reasoning trace; highlighted subgraph; citations that open papers; suggested demo questions | K2, K3 |
| **Node 360** | Every node: properties, enrichment (Wikipedia, linked entities), metrics (PageRank, community, centralities), trend sparkline, neighborhood graph, evidence | K-app option "comprehensive node view", reused |
| **Explorer** | Existing five modes, extended with the new labels and predicates | Existing |
| **About the data** | Sources, counts, versions, evaluation results with intervals, AI-assessment statement | E1–E4 |

The interface is bilingual (English and Vietnamese) if time allows; English is
required.

### 6.5 Non-functional requirements

- **Clarity of numbers:** every metric has a tooltip with its definition,
  denominator, network and graph version. Generated text is marked "AI-generated
  from graph data".
- **Performance:** dashboards and tables load from precomputed artifacts in under
  2 s on the deployed site. Ask streams its first tokens within about 5 s and
  finishes typical questions within about 30 s on the hosted model.
- **Reliability for the demo:** cache the answers for the scripted demo questions,
  and give the demo a fallback recorded video and a local runtime.
- **Safety and integrity:** read-only database access, parameterized queries,
  timeouts and limits on result sizes; no API keys in the frontend or the
  repository.
- **Reproducibility:** configs, prompts and model IDs are versioned; LLM outputs
  for the graph build are cached by input hash so rebuilds are deterministic from
  the cache.
- **Quality bar for the UI:** consistent design system, responsive layout, accessible
  contrast and keyboard navigation, Playwright tests for every new page.

### 6.6 Question-answering evaluation

A benchmark gives K3 measured, not only demonstrated, results:

- About **80 questions**: 20 single-hop, 25 two-hop, 20 three-hop and 15 global or
  trend questions, written from templates over the graph. Reference answers are
  computed by deterministic Cypher, so they are exact for the factual questions.
  Freeze the questions and answers before system tuning; keep 20 separate
  development questions.
- Systems compared:
  1. SLM alone, without retrieval
  2. Vector RAG over abstracts
  3. GraphRAG local and global search
  4. The full multi-hop system
- Metrics:
  - Exact or set-F1 answer accuracy by hop count, for the factual questions.
  - Citation validity, meaning cited papers support the claim. AI-assessed.
  - Faithfulness, meaning no numbers outside the trace. Checked automatically.
  - Latency.
- Global questions have no single reference answer, so they are judged pairwise by
  the AI evaluator and labelled as such.

## 7. Deliverables (P1–P4)

| Deliverable | Specification |
| --- | --- |
| **arXiv report** | LaTeX in `report/arxiv/`, English, arXiv-compatible (standard article class with an arXiv-style template; PDF builds with pdfLaTeX; source tarball accepted by arXiv). Sections: abstract, introduction, related work (scholarly KGs, GraphRAG, SNA of co-authorship), data and enrichment, graph quality, network analysis, application and multi-hop reasoning, evaluation, limitations and ethics, conclusion, plus a reproducibility appendix and links. Suggested category **cs.SI** (cross-list cs.CL or cs.DL) |
| **Slides** | 20-minute talk of about 18–22 slides, one section per rubric block, real figures from the reports, a demo hand-off slide, backup slides for likely questions (evaluation validity, why ≤9B, small-world baselines, limitations) |
| **Demo (5 min)** | A script that covers a trend scan, a topic deep-dive, a group profile, one multi-hop Ask question with its trace, and the Network Science page. Cached answers plus a recorded fallback |
| **Q&A preparation** | A one-page sheet of likely questions with answers and the figures to show |
| **GitHub** | Public repository with code, configs, a data release (enrichment layer and analysis outputs, with licences respected) and a README with the system link, report link and quick start |
| **Submission** | Slides, the system URL, the GitHub URL and the arXiv link, resubmitted before **20 December 2026, 23:59** |

## 8. Delivery plan

Today is 23 November. arXiv submissions need moderation (often 1–2 working days)
and, for a first-time submitter, an endorsement. So the paper is submitted by
**15 December**, leaving a buffer.

| Milestone | Dates | Exit check |
| --- | --- | --- |
| M0 Set-up | 23–25 Nov | D042 recorded; splits frozen; LLM client and runtime working; model selection done (K1) |
| M1 Enrichment | 25 Nov–3 Dec | Sources fetched (E1); entities and relations extracted and linked (E2, E3); v5-enriched validated and loaded |
| M2 Quality and SNA | 1–6 Dec | Frozen audit run and scored (E4); small world, ranking, communities and trends computed (S1–S3, §5.4) |
| M3 Application core | 4–12 Dec | GraphRAG index; multi-hop engine; new backend routes; Trends, Topic, Groups, Communities, Network Science and Ask pages |
| M4 Evaluation and polish | 10–14 Dec | QA benchmark scored; UI polish and tests; deployment updated |
| M5 Report and arXiv | 8–15 Dec | Report complete; endorsement arranged; arXiv submission by 15 Dec |
| M6 Slides and rehearsal | 14–19 Dec | Slides, demo script, recorded fallback, Q&A sheet, two rehearsals |
| Submit | by 20 Dec 23:59 | Slides and links resubmitted |

Each milestone is a work-log entry and a local commit. Push when the user asks.

## 9. Acceptance checklist

- [ ] E1 source manifest with counts, licences and selection rules
- [ ] E2 entity pipeline run; per-type counts; ablation
- [ ] E3 relation pipeline run; per-predicate counts
- [ ] E4 frozen AI-assessed audit with Wilson intervals, recall estimate, linking accuracy, structure and coverage
- [ ] S1 L, C and σ against both baselines for N1, N2 and N4; path-length histogram; evolution by year
- [ ] S2 PageRank and personalized PageRank tables; correlation with other centralities
- [ ] S3 Leiden partitions with quality and stability; key individuals per community
- [ ] K1 model comparison table and model card
- [ ] K2 community reports, local and global retrieval, communities visible on the graph
- [ ] K3 multi-hop Ask with a visible trace; QA benchmark against three baselines
- [ ] Product: all §6.4 pages, tooltips on every metric, deployed URL working
- [ ] P1–P4 slides, demo script and fallback, arXiv listing, public repository, Q&A sheet

## 10. Risks and open questions

| Risk | Mitigation |
| --- | --- |
| arXiv endorsement or moderation delays, or rejection of a course report | Submit by 15 Dec; arrange an endorser early; write it as a research paper with real evaluation; keep a PDF on GitHub as fallback |
| GitHub repository is private today | Decide what can be public (source-policy check on abstracts and Wikipedia text) and make it public before submission |
| Local 8 GB GPU too slow for bulk extraction | Hosted endpoint with the same model; cache all outputs |
| Hosted model cost or rate limits during the demo | Cached demo answers; local fallback; recorded video |
| Entity noise (generic terms like "model", "framework") | Stop-list, SLM verification, ≥3-paper threshold, precision audit |
| Trend artifacts from venue growth or classifier error | Share-based metrics, stated caveats, confidence shown per trend |
| AI-only evaluation questioned by the instructor | Different evaluator family, A/B κ, exact Cypher-based QA references, clear labelling |
| Scope too large for four weeks | Order of cuts if late: news source, bilingual UI, ω coefficient, three-hop questions |

Open questions for the team:

1. Confirm the reading of "forum icons" as communities (see [requirements.md](requirements.md)).
2. Which hosted provider and budget to use for the SLM endpoint.
3. Who can endorse the arXiv submission in cs.SI.

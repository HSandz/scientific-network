# Final exam requirements and traceability

Received 23 November 2026. Deadline: **20 December 2026, 23:59** (slides and system
links resubmitted; report submitted to arXiv). The chosen application is
**research-trend analysis of scientific articles**. This replaces the earlier course
brief in [project-plan.md](../project-plan.md) as the grading target; the earlier
minimums (≥2,000 nodes, ≥5,000 edges, ten relationship types) are already met by
graph v4 and still hold.

## Rubric as given (10 points)

**Data enrichment and analysis (2.0).** Build a model that creates data-enriched
graphs by analyzing text data.

| Item | Points |
| --- | --- |
| E1. Collect and select data for enrichment (Wikipedia main text or other sources, e.g. newspapers) | 0.5 |
| E2. Model for identifying entities (nodes) linked to the topic of the major assignment | 0.5 |
| E3. Model for identifying relationships (edges) between entities | 0.5 |
| E4. Method for evaluating the quality of the built graph | 0.5 |

**Social network analysis (1.5).**

| Item | Points |
| --- | --- |
| S1. Prove the small-world property (average shortest distance across the entire network) | 0.5 |
| S2. Rank nodes with a graph ranking algorithm (e.g. PageRank) | 0.5 |
| S3. Detect communities and find individuals in the network | 0.5 |

**Knowledge-graph application (4.5).** One of five applications; we chose
"analyzing research trends in scientific articles: which topics are trending, which
well-known groups are interested in which issues".

| Item | Points |
| --- | --- |
| K1. Choose a small language model with ≤9B parameters for data analysis and processing | 1.0 |
| K2. Symbolic social network as a graph, knowledge visualization, and RAG; GraphRAG-style community-based RAG preferred | 0.5 |
| K3. Application using multi-hop reasoning over the graph and its communities | 3.0 |

The product must demonstrate social-media (social-network) analysis, have a
polished interface, and show clear data behind every analytical calculation.

**Slides, presentation and report (2.0).**

| Item | Points |
| --- | --- |
| P1. Clear slides with good-looking analysis | 0.5 |
| P2. Good presentation | 0.5 |
| P3. Clear, polished, complete report | 0.5 |
| P4. Answering the instructor's questions | 0.5 |

Format: 20-minute presentation, 5-minute application demo, 5-minute Q&A. Provide
GitHub links (code and data). Write the report to arXiv standards and submit it to
arXiv.

## Interpretation notes

The rubric reads as a translation, and three phrases are interpreted here. If the
original wording says otherwise, correct these notes first.

- **"Forum icons on graphs like GraphRAG"** is read as *communities*. GraphRAG
  retrieves over detected communities and their generated summaries, so K2 and K3
  are met by community-level retrieval and by communities shown as first-class
  objects (super-nodes) on the graph.
- **"A number of parameters less than or equal to 9 and a parameter scale"** is
  read as ≤9 billion parameters, counted as the total of the official checkpoint
  (vision or audio encoders included). The choice must be justified (K1), not only
  stated. Nominal "9B" models above 9.0B in total, such as Qwen3.5-9B at 9.65B, are
  reference points only unless the team records an exception.
- **"Multi-hop inference mechanism on a diagram"** is read as answering questions
  that need two or more traversals of the knowledge graph, with the hops shown.

## Project constraints (user decisions, 23 November)

- The data scope stays AAAI and IJCAI 2021–2025, 13,617 papers. Enrichment adds
  text-derived entities and relations about these papers and their existing
  organizations, researchers and topics; it does not add papers, venues or years.
- Any enrichment source is allowed.
- No model training or fine-tuning. Pretrained and zero-shot models only.
- Any suitable model ≤9B parameters; it does not have to run offline.
- Quality evaluation stays AI-assessed, labelled as such (as in D040).
- App scope can be large; aim for the best product we can ship.
- No task allocation in these documents.

## Traceability

Each rubric item, the specification section that satisfies it, and the artifact
that proves it at grading time.

| Item | Specification | Evidence at grading |
| --- | --- | --- |
| E1 | [§4.1 Sources and selection](specification.md#41-sources-and-selection) | Source manifest with counts, licences and selection rules; report §Data |
| E2 | [§4.2 Entity model](specification.md#42-entity-extraction-and-linking-e2) | Extraction method and per-type counts; entity precision table |
| E3 | [§4.3 Relationship model](specification.md#43-relationship-extraction-e3) | Relation method and per-predicate counts; relation precision table |
| E4 | [§4.5 Quality evaluation](specification.md#45-quality-evaluation-e4) | Frozen audit sample, AI-assessed precision with Wilson intervals, recall estimate, ablation |
| S1 | [§5.1 Small world](specification.md#51-small-world-s1) | L, C and σ against random baselines; path-length histogram; app Network Science page |
| S2 | [§5.2 Ranking](specification.md#52-node-ranking-s2) | PageRank tables per network and per topic; rank correlation with other centralities |
| S3 | [§5.3 Communities and key individuals](specification.md#53-communities-and-key-individuals-s3) | Partition quality and stability; community cards with hubs, brokers and rising researchers |
| K1 | [§6.1 Language model selection](specification.md#61-language-model-selection-k1) | Model comparison on the development set; chosen model card with exact ID and quantization |
| K2 | [§6.2 GraphRAG](specification.md#62-graphrag-index-and-retrieval-k2) and [§6.4 product](specification.md#64-product-features) | Community reports, retrieval modes, graph visualization in the app |
| K3 | [§6.3 Multi-hop reasoning](specification.md#63-multi-hop-reasoning-k3), [§6.4](specification.md#64-product-features) and [§6.6 QA evaluation](specification.md#66-question-answering-evaluation) | Live demo with a visible reasoning trace; benchmark accuracy by hop count against baselines |
| P1–P4 | [§7 Deliverables](specification.md#7-deliverables-p1p4) | Slides, demo script, arXiv report and listing, public GitHub repository |

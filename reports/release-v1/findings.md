# Phase 6 findings and investigation shortlists

**Graph:** `release-5d830ffcbdf4`

**Graph SHA-256:** `b79e456b22488ca8f753fb0884afd5c6a89afeeeaffec07d89ce83b2c5c141fb`

**Analysis method:** `named-projection-analysis-v2` plus `d040-release-metrics-v1`

**Scope:** core AAAI and IJCAI papers, proceedings years 2021–2025.

These are descriptive candidates from accepted graph records. Topic labels are
inferred and have not been independently reviewed. Organization sectors and
paper-specific affiliation links also remain subject to the planned human audit.
The results must not be read as evidence of current employment, contracts,
commercial readiness, or causal relationships.

## Findings

### 1. Academia–industry collaboration candidate in representation learning

The accepted graph contains **4,181 distinct academia–industry organization-pair
by core-paper supports** across the five-year corpus. The largest pair/topic
candidate is **Shanghai Jiao Tong University — Tencent (China)** in the inferred
**Representation learning** topic, supported by **14 distinct core papers**.
Examples include [*Exploiting Fine-Grained Face Forgery Clues via Progressive
Enhancement Learning* (2022)](https://doi.org/10.1609/aaai.v36i1.19954) and
[*DIRL: Domain-Invariant Representation Learning for Generalizable Semantic
Segmentation* (2022)](https://doi.org/10.1609/aaai.v36i3.20193).

This is a map of repeated co-publication evidence, not a measure of contract
volume or present-day partnership. Both the industry sector mapping and inferred
topic assignments require independent review; strict-evidence filtering retains
27.4% of organization-collaboration edges overall.

### 2. Researcher bridge candidate

**Dacheng Tao** ranks first in the configured approximate betweenness measure at
**0.05493** among **36,680 resolved researchers** in the researcher collaboration
projection. The configured Louvain partition places this researcher in a
**466-member** community with **231 distinct core papers**, of which **212** have
at least one inferred topic label. Its largest topic profile is Representation
learning: **63 papers**, or **50.0 fractional paper contributions** and **23.6%**
of the community's fractional topic mass. Two supporting core works in the graph
are [*BESA: BERT-based Simulated Annealing for Adversarial Text Attacks*
(IJCAI 2021)](https://doi.org/10.24963/ijcai.2021/453) and [*Deep Graph-neighbor
Coherence Preserving Network for Unsupervised Cross-modal Hashing* (AAAI
2021)](https://doi.org/10.1609/aaai.v35i5.16592).

Betweenness uses sampled NetworkX shortest paths with inverse fractional edge
strength as distance. Its top-20 overlap with the frozen stricter-evidence
projection is only **1 of 20**, with Spearman rank correlation **0.275** on
shared researchers. Treat the rank as a lead for inspection, not a stable
individual influence score. The community topics are unvalidated model outputs.

### 3. Organization topic portfolio comparison

For inferred Representation learning, **Zhejiang University** has **171 distinct
R10-supported papers among 527 organization-associated topic-labeled papers**;
**Peking University** has **149 among 420**. Under the schema's fractional
portfolio rule, which divides paper mass across both labels and supported
organizations, the corresponding shares are **26.0%** and **28.5%**. Supporting
examples include Zhejiang University's [*Multi-Scale Spatial Temporal Graph
Convolutional Network for Skeleton-Based Action Recognition* (2021)](https://doi.org/10.1609/aaai.v35i2.16197)
and [*Generalizable Representation Learning for Mixture Domain Face Anti-Spoofing*
(2021)](https://doi.org/10.1609/aaai.v35i2.16199), and Peking University's
[*Community-Aware Multi-Task Transportation Demand Prediction* (2021)](https://doi.org/10.1609/aaai.v35i1.16107)
and [*GRASP: Generic Framework for Health Status Representation Learning Based on
Incorporating Knowledge from Similar Patients* (2021)](https://doi.org/10.1609/aaai.v35i1.16152).

These denominators cover only papers with accepted organization alignment and at
least one inferred topic; they do not measure each institution's complete
research portfolio. Inferred topic accuracy is pending human labels, and the
fractional share is not the same as the raw R10 support fraction.

## Investigation shortlists

These are candidates for evidence review, not partner recommendations.

### Academia–industry topic pairs

Criterion: at least **8 distinct accepted core-paper supports** for one
organization pair within one inferred topic; ordered by support count, then topic
and stable organization IDs. Counts and topic labels should be checked before
making any business claim.

| Supported papers | Academia | Industry | Inferred topic |
| ---: | --- | --- | --- |
| 14 | Shanghai Jiao Tong University | Tencent (China) | Representation learning |
| 14 | Xiamen University | Tencent (China) | Representation learning |
| 14 | Zhejiang University | Alibaba Group (China) | Representation learning |
| 13 | Zhejiang University | Alibaba Group (China) | Multimodal learning |
| 11 | Tsinghua University | Tencent (China) | Representation learning |
| 10 | Shanghai Jiao Tong University | Tencent (China) | Multimodal learning |
| 9 | Zhejiang University | Alibaba Group (China) | Generative modeling |
| 9 | Xiamen University | Tencent (China) | Multimodal learning |

### Researcher bridge candidates

Criterion: top ten researchers by the frozen approximate betweenness score in
the full accepted researcher collaboration projection, ordered by descending
score with deterministic ID tie-breaking. The low strict-filter rank stability
above is a reason to review evidence before interpreting these candidates.

| Rank | Researcher | Approximate betweenness | Community | Community size |
| ---: | --- | ---: | --- | ---: |
| 1 | Dacheng Tao | 0.054933 | community 00017 | 466 |
| 2 | Zhe Chen | 0.033773 | community 00017 | 466 |
| 3 | Xiaochun Cao | 0.031548 | community 00148 | 542 |
| 4 | Shirui Pan | 0.022595 | community 00133 | 425 |
| 5 | Xinchao Wang | 0.021984 | community 00075 | 371 |
| 6 | Jing Zhang | 0.020476 | community 00017 | 466 |
| 7 | Lingjuan Lyu | 0.019239 | community 00071 | 432 |
| 8 | Peter J. Stuckey | 0.019002 | community 00009 | 340 |
| 9 | Wei William Wang | 0.018820 | community 00094 | 404 |
| 10 | Mingli Song | 0.017945 | community 00075 | 371 |

## Analysis notes

- All five annual core-paper counts sum to **13,617**. “New collaboration pairs” assigns each accepted researcher pair to the earliest year among its graph-supported core papers; these yearly counts sum to **112,042** distinct pairs in the cumulative graph.
- The largest researcher component has **26,990 of 36,680 researchers (73.6%)**; the graph also contains **193 isolates** and **2,278 components**.
- Topic coverage is **11,575/13,617 (85.0%)**. Venue-year coverage ranges from 81.9% to 87.9%. These are coverage measures, not accuracy.
- The in-scope citation ranking uses current captured OpenAlex references. It excludes external targets and does not correct for year-dependent exposure.
- All size gates passed: 52,415 domain nodes, 36,680 resolved core researchers, 124,619 unique R1–R4 factual edges, and all ten relation types. The graph remains **not certified** until independent review and audit scoring are complete.

## Figures and tables

Six PNG figures and their CSV source tables are in
[`reports/final-report/figures/`](../final-report/figures/). Captions beside the
figures record projection, filter, counting rule, and graph version.

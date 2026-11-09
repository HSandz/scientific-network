# Corrected-graph findings and investigation shortlists

Graph `release-d3c788c3114a`; graph SHA-256 `6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`.
Fresh analysis: [analysis.json](analysis.json), SHA-256 `580d1a6dbc21ef2ac17b820979830f3de157fc1b04d1c89f2580731f141701c9`.
Methods: `named-projection-analysis-v2` and `d040-release-metrics-v2`; frozen
`analysis-release-v1` configuration, seed 20261101. Scope: AAAI/IJCAI main-track
proceedings, 2021–2025. All five base projections and their stricter-evidence
counterparts were recomputed; these are measured descriptive results.

This separate correction follows the observed-ORCID omission found after the old
audit. It preserves that graph and its failed AI-assessed result, 176/200 (88%).
The new graph requires its own prospective audit; these findings do not establish
accuracy. Source checks below reuse construction sources. Human validation was
not performed, reviewer independence is not established and verified course
accuracy remains not established. Topic findings remain provisional: frozen
historical AI-reference micro F1 is .4667 for embedding and .2301 for the phrase
baseline, with test coverage 90% and 26%. The correction neither tunes the
classifier nor creates a new untouched topic holdout.

## What changed

| Projection | Nodes, previous → corrected | Edges, previous → corrected | Corrected isolates |
| --- | ---: | ---: | ---: |
| researcher collaboration | 36,680 → 32,189 | 112,042 → 80,482 | 414 |
| organization collaboration | 2,096 → 2,047 | 15,157 → 13,031 | 90 |
| core citations | 13,617 → 13,617 | 7,308 → 7,308 | 7,302 |
| paper topics | 13,637 → 13,637 | 14,222 → 14,222 | 2,046 |
| organization topics | 2,116 → 2,067 | 2,494 → 2,332 | 1,439 |

The researcher largest component falls from **26,990/36,680 (73.6%)** to
**20,776/32,189 (64.5%)**. Component count rises from **2,278 to 2,936** and
isolates from **193 to 414**. These changes follow global identity withholding;
they are not a change in the official paper population. The observed R1–R4 count
falls from **124,619 to 110,026**; all ten relation types remain present.

The [comparison artifact](analysis-comparison.json) records node/edge deltas,
rankings, communities, annual counts, full strict-filter comparisons and hashes.
It proves canonical equality of the entire citation and paper-topic projection
outputs, annual venue/topic shares and citation leader tables. All **13,617 core
papers**, **7,308 in-scope citations** and **14,222 HAS_TOPIC edges** remain.

## 1. Repeated academia–industry co-publication remains visible

The corrected graph contains **3,533 distinct academia–industry organization-pair
by core-paper supports**, down from **4,181** (648 fewer; 15.5%). This denominator
counts a pair once per supported paper; it is neither unique papers nor unique
partnerships. The leading pair/topic candidate remains **Shanghai Jiao Tong
University — Tencent (China)** in inferred **Representation learning**, with
**14 distinct papers**, tied with two other pairs. This stable local result
coexists with the broader reduction in accepted collaboration support.

Supporting examples are [*Exploiting Fine-Grained Face Forgery Clues via Progressive Enhancement Learning*](https://doi.org/10.1609/aaai.v36i1.19954) (2022) and
[*DIRL: Domain-Invariant Representation Learning for Generalizable Semantic Segmentation*](https://doi.org/10.1609/aaai.v36i3.20193) (2022). For both, original cached authorships
were hash-checked against immutable works; accepted observations align the two
organizations to distinct authors, with author-specific raw affiliation strings.
This supports co-publication under the release evidence rule. It does not show a
contract, current employment, commercial readiness or current partnership.
Institution sectors still come from OpenAlex. The frozen minimum-two-paper
sensitivity filter retains **26.1%** of organization-collaboration edges, versus
27.4% previously. Topic correctness is not established by this source alignment.

## 2. The bridge shortlist changes and remains sensitive

**Bo An** (`A5017743551`) ranks first by configured approximate weighted
betweenness, **0.042193**, among **32,189 researchers**. The selected Louvain run
(seed **17**, resolution **0.8**) places this identity in a **367-member**
community associated with **206 distinct core papers**, **180 topic-labeled**.
Its largest inferred topic is Representation learning: **63 papers**,
**52.3333 fractional contributions**, or **29.1%** of that community's fractional
topic mass. Community paper sets are deduplicated within a community and can
overlap across communities.

Two source-checked works with this author ID are [*GearNet: Stepwise Dual Learning for Weakly Supervised Domain Adaptation*](https://doi.org/10.1609/aaai.v36i8.20851) (2022;
byline position 4) and [*Partial-Label Regression*](https://doi.org/10.1609/aaai.v37i6.25871) (2023; position 5). Original cached
author objects, including retained ORCID arrays, exactly match immutable works.
These establish accepted participation, not that either paper causes bridge rank
or independently validates its inferred topic.

The previous leader was Dacheng Tao (**0.054933**). Only **3 of the previous
top 20** remain in the corrected top 20. Within the corrected graph, the
stricter-evidence researcher projection retains **7.78%** of collaboration edges;
its betweenness top 20 overlaps the base top 20 by **0/20**, with Spearman
correlation **0.1882** across all shared researchers, compared with 1/20 and
0.2750 previously. It fragments the largest component to **175/32,189 (0.54%)**.
Approximation samples 256 pivot nodes; removing researchers changes the pivot
population despite a fixed seed. Cross-version score changes therefore combine
network changes and sampling effects. Use this list to inspect bridges; it is
not a stable individual influence or hiring score.

## 3. Portfolio denominators change despite fixed topic predictions

For inferred Representation learning, **Zhejiang University** has
**156 supported papers among 489 organization-associated topic-labeled papers**,
versus 171/527 previously. **Peking University** has **139 among 381**, versus
149/420. Fractional portfolio shares are now **25.1% and 28.8%**, respectively,
versus 26.0% and 28.5%. Each topic-labeled paper first divides its mass across
supported organizations and then across its labels; these shares are not raw
support-count fractions. Exact fractional denominators are **270.4262** for
Zhejiang and **217.8357** for Peking.

Zhejiang examples: [*Multi-Scale Spatial Temporal Graph Convolutional Network for Skeleton-Based Action Recognition*](https://doi.org/10.1609/aaai.v35i2.16197) and
[*Generalizable Representation Learning for Mixture Domain Face Anti-Spoofing*](https://doi.org/10.1609/aaai.v35i2.16199), both 2021. Peking examples:
[*Community-Aware Multi-Task Transportation Demand Prediction*](https://doi.org/10.1609/aaai.v35i1.16107) and [*GRASP: Generic Framework for Health Status Representation Learning Based on Incorporating Knowledge from Similar Patients*](https://doi.org/10.1609/aaai.v35i1.16152),
both 2021. Each institution's involvement was checked in original authorship
institution IDs, author-specific raw affiliation strings and surviving graph
observations. Source reuse and provider errors remain limitations. Fixed labels
do not imply fixed organizational portfolios when identities/affiliations are
withheld. These denominators omit papers without accepted institution alignment
or inferred labels and cannot represent a complete institution research output.

## Investigation shortlist 1: academia–industry topic pairs

Criterion: **at least eight distinct core papers** supporting a pair within an
inferred topic. All ten qualifying candidates are shown, sorted by descending
support, then topic and stable organization IDs. These are leads for further
source review, with no contract or partnership recommendation implied.

| Papers | Academia | Industry | Inferred topic |
| ---: | --- | --- | --- |
| 14 | Shanghai Jiao Tong University | Tencent (China) | Representation learning |
| 14 | Xiamen University | Tencent (China) | Representation learning |
| 14 | Zhejiang University | Alibaba Group (China) | Representation learning |
| 13 | Zhejiang University | Alibaba Group (China) | Multimodal learning |
| 10 | Shanghai Jiao Tong University | Tencent (China) | Multimodal learning |
| 9 | Xiamen University | Tencent (China) | Multimodal learning |
| 8 | Zhejiang University | Tencent (China) | Generative modeling |
| 8 | Zhejiang University | Alibaba Group (China) | Generative modeling |
| 8 | Zhejiang University | Alibaba Group (China) | Natural language processing and language models |
| 8 | Harvard University | Google (United States) | Reinforcement learning |

## Investigation shortlist 2: researcher bridges

Criterion: top ten corrected-graph researchers by approximate weighted
betweenness, deterministic stable-ID tie-breaking. Community IDs belong only to
the selected corrected-graph Louvain run and are not persistent across versions.

| Rank | Researcher | OpenAlex ID | Betweenness | Community | Members |
| ---: | --- | --- | ---: | --- | ---: |
| 1 | Bo An | `A5017743551` | 0.042193 | 00126 | 367 |
| 2 | Lei Feng | `A5100682348` | 0.034010 | 00126 | 367 |
| 3 | Hau Chan | `A5046420136` | 0.021608 | 00000 | 687 |
| 4 | Shirui Pan | `A5008056593` | 0.020971 | 00043 | 481 |
| 5 | Chengjie Wang | `A5023834700` | 0.019882 | 00058 | 953 |
| 6 | Jianye Hao | `A5047509839` | 0.019694 | 00095 | 336 |
| 7 | Kui Jiang | `A5103140908` | 0.019523 | 00059 | 281 |
| 8 | Xiaokang Yang | `A5019708391` | 0.018851 | 00058 | 953 |
| 9 | Min-Ling Zhang | `A5079083101` | 0.018811 | 00126 | 367 |
| 10 | Xiaochun Cao | `A5068837264` | 0.018781 | 00136 | 407 |

## Evidence, robustness and figures

Eight supporting paper-case checks passed against immutable OpenAlex cache
objects and official roster cache hashes. The small source hashes/locators are
recorded in [analysis-comparison.json](analysis-comparison.json); full raw
alignments remain ignored under
`reports/runs/WORK-2026-11-09-012/findings-source-verification.json`. This is a
source-backed descriptive check, not independent semantic annotation or a new
audit. Original source text and raw affiliations are not redistributed here.

The minimum-support-two sensitivity rule removes every citation and paper-topic
edge because those base predicates lack the aggregate support counts used by the
filter. R10 organization-topic edges all remain because construction already
requires three distinct papers. Those mechanical results are not evidence about
citation or topic accuracy. Researcher/organization collaboration sensitivity
measures repeated co-publication support, with all versions and seeds retained
in the analysis artifact. Louvain is the NetworkX fallback; GDS was not used.

Topic coverage remains **11,575/13,617 (85.0%)**. Citation rankings use the captured
OpenAlex references within scope, without paper-age or exposure normalization.
Country unknowns remain unknown. Size gates pass for the corrected graph, but
size, structure and robustness do not certify scientific accuracy.

Six freshly generated PNG figures, CSV source tables and version-bound captions
are in [figures-v4](../final-report/figures-v4/captions.md). The paper-topic trend
and citation content remain unchanged; collaboration and community figures use
the corrected identities. See the analysis artifact for every numeric denominator
and the comparison artifact for precise unrounded before/after results.

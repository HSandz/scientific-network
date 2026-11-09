# AI Research Network: AAAI and IJCAI, 2021–2025

**Local report, 9 November 2026.** Source-backed AI evaluation is complete:
**176/200 edges correct (88.00%), Wilson 95% interval 82.77%–91.80%**.
The course point comparison and project precision checks **fail**. Human
validation was not performed; evaluator independence and verified course accuracy
are not established. Real team details and course disclosure/access facts remain
pending. This local submission draft has not been published or submitted.

## 1. Team allocation

Real human names, student IDs and actual human contributions remain **pending**
in [the team record](../../docs/team.md); no student identity is inferred from
repository accounts or illustrative role assignments.

| Recorded contributor | Actual work in this execution | Attribution scope |
| --- | --- | --- |
| Codex coordinator | Repository inspection, evaluator freeze, integration, validation, scoring/report/package preparation | AI-assisted project work |
| Isolated evaluator A | 30 blind topic judgments; assigned source-backed edge review | AI evaluator channel, not a student |
| Isolated evaluator B | 30 blind topic judgments; assigned source-backed edge review | AI evaluator channel, not a student |
| Scorer/renderer agent | Provenance-bound evaluation wrapper, regression tests and local rendering/package tooling | AI-assisted implementation |
| Human team | Names, IDs and actual individual contributions pending | Must be supplied from real records |

The contexts use the platform's inherited settings; precise provider/model/version
and sampling parameters are not exposed and are recorded as unknown. A/B received
no inherited coordinator conversation or other evaluator answers. The course's
specific AI-use disclosure/access requirements remain pending; this report openly
identifies AI work without asserting lecturer acceptance of AI-only judging.

## 2. Network rationale

This project models the research relationships visible in main-track AAAI and
IJCAI proceedings from 2021 through 2025. The business questions are: (1) which
researcher groups and organizations repeatedly collaborate, and where do
academia–industry links appear within research topics; (2) which researchers
connect otherwise separate collaboration communities; and (3) how do
organization topic portfolios and within-corpus citation patterns differ over
time? These views can help a research-program analyst identify partnership
patterns for further investigation, find possible connectors between groups, and
compare the subject mix represented in this selected publication corpus.

The graph records publication evidence. It does not measure current employment,
nationality, contract value, commercial readiness, or causal influence. A bridge
score is a structural property of the configured projection and distance rule;
it is not an assessment of a person's quality or importance.

## 3. Data and software stack

The release uses the final roster-v10 inclusion decisions for AAAI and IJCAI
main-track papers in 2021–2025. It contains **13,617 core papers**: AAAI has
1,654, 1,319, 1,578, 2,331, and 3,028 papers by year; IJCAI has 586, 678, 639,
790, and 1,014. These are the two selected series in this release, not the full
five-year discovery registry. The broader roster collection records 98 eligible
editions and 91,355 included papers; 62 additional candidates remain unresolved
or unavailable. This release selects AAAI and IJCAI because their official
records supply DOI routes that OpenAlex returns in batches. The other editions
are a coverage limit, not missing release papers silently filled from another
source. See the [v10 recovery report](../five-year-source-recovery-v10.md).

The acquisition stage (`release-openalex-v1`) derives DOIs from official paper
URLs and queries OpenAlex in DOI batches, with singleton retries for missing
batch results. A work is matched only when title and byline counts meet the
release rules. It matched **13,606/13,617 (99.92%)**; 11 papers remain in review,
zero were reported not found, and all 13,606 matched works have abstracts. Two
matches carry a title-similarity flag. Source responses and manifests are
hash-bound in the acquisition report; raw cached responses remain local and
ignored.

The implementation uses Python 3.12, Pydantic graph contracts, NetworkX for
projection analysis, Matplotlib for static figures, and Neo4j Community 5.26 as
the graph DBMS. Topic representations use the frozen
`sentence-transformers/all-MiniLM-L6-v2` model revision recorded in the topic
configuration. Dependency versions are locked in `uv.lock`.

## 4. Preprocessing and identity resolution

Official roster records define the paper, venue, edition year, byline order and
publication URL. DOI derivation is venue-specific. OpenAlex works must agree on
normalized title (similarity threshold 0.9, with flagged near matches) and
author count. Unresolved or ambiguous matches remain in the review queue instead
of being forced into the graph. Duplicate DOI records are resolved with the
official landing-page rule where possible; nine duplicate-DOI cases remain in
review, alongside two author-count mismatches.

For a matched paper, a Researcher is keyed by its OpenAlex author ID only at a
compatible byline position. ORCID is recorded when present, but is not required
for this release. Names alone never merge people. The scoped roster has 65,507
author positions, including 38 on unmatched papers. Of the 65,469 positions on
matched works, **59,159** were accepted as `AUTHORED` support and **6,310** were
withheld: 6,283 lack an OpenAlex author ID, 7 have incompatible names, 18 are on
papers with a repeated author ID, and 2 otherwise compatible positions were
withheld because multiple mismatches affected their paper. Five papers have all
authorship positions withheld. The seven incompatible-name positions are 0.011%
of the official positions; missing author IDs are a separate and much larger
coverage limit.

Affiliation evidence is retained as author–paper–organization triples from the
matched OpenAlex authorship, with raw affiliation strings. The paper's full
institution list is not copied onto each author. There are **56,633 supported
author–paper positions** with institution evidence (95.73% of accepted
authorships). The paper-level copied-affiliation guard withheld 147 patterns.
`AFFILIATED_WITH` aggregates the accepted observations only after these
triples are retained.

These figures describe implementation output, not a guarantee of the intended
identity rule. The audit found that resolver conflict handling reads singular
`author.orcid` but ignores multiple retained `author.observed_orcids` values.
Consequently some accepted researcher endpoints violate D040's conflicting-ID
withholding rule. Raw/full works retain the arrays; the projected review packet
also omitted them. Section 9 and the post-audit findings document this defect.
The frozen graph was preserved after discovery rather than corrected against its
audit sample.


The [first live diagnostic pilot](../pilot-v1.md), dated 3 November, used
ORCID-publication corroboration and exact printed institution matching. Among
100 processed 2023 papers it resolved 28/464 official authorship positions (6.03%)
and accepted affiliation evidence for 5/464 positions (1.08%). These are historical
pilot denominators, not release measurements. D040 replaced that restrictive
identity policy with compatible authorship-level OpenAlex IDs and author-specific
institution evidence while preserving ambiguity guards. The change improves
covered-network size but introduces dependence on OpenAlex identity resolution;
its coverage gain must not be called an accuracy gain.

Citation edges point from a citing paper to a deduplicated cited paper. The
acquisition scan found 378,360 reference targets: 370,831 targets outside the
release scope, 34 self-references, no ambiguous in-scope target mappings, and
7,308 accepted in-scope citation edges. External citations do not enter the
core citation projection.

## 5. NLP methods

The frozen topic taxonomy contains four parent topics and 16 leaf topics. A
phrase-based classifier supplied topics for graph v1. Graph v2 replaced those
labels with a sentence-embedding method using the frozen model revision and
development-calibrated thresholds `tau = 0.2708871365` and `delta = 0.02`.
The method compares title and abstract text against topic definitions and uses
an abstract sentence (or title for title-only text) as supporting evidence. It
assigns up to three leaf labels or abstains. Threshold calibration used
non-test papers; the test IDs were frozen before tuning. Model outputs were
generated only after the classifier freeze and are not shown in the prediction-blind
topic review sheet.

The corrected v3 graph has **11,575 topic-labeled papers** and **2,042 abstentions**, for
85.00% label coverage. This is coverage, not topic accuracy. Both isolated
reviewers completed their prediction-blind assignments before edge exposure:
30 papers each with ten shared, covering all 50 frozen tests. Each received 12
AAAI and 18 IJCAI papers. Their exports and evidence ledgers are hash-bound.
The embedding classifier achieves micro precision/recall/F1
**.6863/.3535/.4667** against these AI-assigned references; the phrase baseline
achieves **.9286/.1313/.2301**. Test coverage is 45/50 (90%) versus 13/50 (26%).
Embedding improves recall and F1 at lower precision; neither reaches the .95
precision target. Section 9 reports weighting, macro metrics and limitations.
Topic trends and topic-based business findings remain provisional given these
measured errors and source/evaluator dependence.

Earlier extraction diagnostics used GROBID 0.8.2 CRF-only PDF headers. In the
first pilot, all 100 TEI responses were valid XML but only 51 had affiliation
structures; valid parsing did not establish correct author alignment. A later
[frozen development diagnostic](../five-year-headers-v1.md) parsed 66/68 headers
and produced unaccepted affiliation candidates, not release edges. D040 makes
PDF/GROBID corroboration optional; this release uses the DOI-matched OpenAlex
source route and the frozen embedding classifier. Those historical diagnostics
were not rerun or pooled into the current evaluation.

## 6. Graph design and graph database

The property graph has five labels—Researcher, Paper, Organization, Topic and
Venue—and ten predicates. `AUTHORED`, `AFFILIATED_WITH`, `PUBLISHED_IN` and
`CITES` are observed facts; `HAS_TOPIC` is inferred from text; `SUBTOPIC_OF` is
curated taxonomy; `COAUTHORED_WITH`, `COLLABORATED_WITH`, `RESEARCHES_TOPIC` and
`CONTRIBUTES_TO_TOPIC` are derived from accepted core-paper support. Domain
nodes, evidence records and graph edges retain stable IDs and versioned
provenance. Unresolved evidence stays in review queues.

| Predicate | v3 edge count | Evidence class |
| --- | ---: | --- |
| AUTHORED | 59,159 | Observed |
| AFFILIATED_WITH | 44,535 | Observed |
| PUBLISHED_IN | 13,617 | Observed |
| CITES | 7,308 | Observed |
| HAS_TOPIC | 14,222 | Inferred topic |
| SUBTOPIC_OF | 16 | Curated taxonomy |
| COAUTHORED_WITH | 112,042 | Derived |
| COLLABORATED_WITH | 15,157 | Derived |
| RESEARCHES_TOPIC | 6,888 | Derived |
| CONTRIBUTES_TO_TOPIC | 2,494 | Derived |

The corrected frozen v3 graph (`release-9d4a6fb20f63`) has **52,415 nodes** and **275,438
edges**. The four observed predicates contain **124,619 unique factual edges**;
derived, inferred-topic and curated-taxonomy edges are counted separately.
Neo4j Community 5.26 was loaded in the isolated `neo4j-five-year` service on
`bolt://localhost:7689`. Fresh inventory and all six integrity queries passed for the corrected v3 graph;
replay reconciled counts without changing its inventory. The pilot and
extended databases were preserved.

## 7. Network statistics

Analysis uses separate researcher collaboration, organization collaboration,
core citation, paper-topic and organization-topic projections. Collaboration
edges are undirected, stored once in canonical endpoint order, and carry
fractional strength; weighted shortest-path distance is its inverse. Citation
edges remain directed, citing to cited. Topic portfolios fractionally allocate
each labeled paper across its accepted labels; organization portfolios also
divide a paper's contribution across its supported organizations.

The researcher projection contains **36,680 resolved researchers**,
**112,042 distinct coauthor pairs**, 193 isolates and 2,278 connected components.
The largest component contains **26,990 researchers (73.6%)**. Mean distinct
degree is 6.11 and the maximum is 108. Annual paper and active-researcher counts
are in the analysis JSON. New collaboration pairs are assigned to the earliest
year among their supported core papers, so yearly pair counts describe first
observed in-scope collaboration rather than an annual snapshot graph.

| Year | Core papers | Active resolved researchers | First observed coauthor pairs |
| --- | ---: | ---: | ---: |
| 2021 | 2,240 | 7,250 | 17,113 |
| 2022 | 1,997 | 7,038 | 14,640 |
| 2023 | 2,217 | 8,137 | 18,685 |
| 2024 | 3,121 | 10,810 | 24,208 |
| 2025 | 4,042 | 15,158 | 37,396 |

Researchers can appear in several years, so annual active-researcher counts must
not be summed into the cumulative unique population. These stored statistics are
reused from the corrected-graph analysis; no analysis or classifier was rerun for
the evaluator change.

Sector and country mixing count distinct accepted organization-pair by
core-paper supports, using the derived collaboration evidence. Unknown sector
or country is retained as its own category. Topic shares are available by both
venue and year; topic figure trends combine venues within a year and normalize
over labeled papers. The directed citation projection contains 7,308 in-scope
edges; its highest in-degree paper has 51 in-scope citing papers. Raw citation
counts are not adjusted for the unequal time papers have had to receive
citations.

The six static figures and their CSV data tables are in
[`figures-v3/`](figures-v3/), with graph version, projection, filter and counting
conventions in each caption. Three source-linked candidate findings and two
screening shortlists are in
[`reports/release-v2/findings.md`](../release-v2/findings.md). The strict-filter
sensitivity analysis materially changes researcher betweenness rankings and
retains only 8.0% of researcher collaboration edges; these comparisons are
robustness diagnostics, not semantic accuracy estimates.

### Figures

![Researcher collaboration degree complementary cumulative distribution](figures-v3/researcher-degree-ccdf.png)

*Figure 1. Researcher collaboration degree CCDF. Distinct coauthor neighbors;
denominator includes all resolved researchers, including isolates. Graph
`release-9d4a6fb20f63`.*

![Researcher collaboration connected component sizes](figures-v3/component-sizes.png)

*Figure 2. Connected researcher collaboration components, ranked by size. All
resolved researchers are included, so isolates are size-one components. Graph
`release-9d4a6fb20f63`.*

![Researcher community topic profiles](figures-v3/community-topic-profiles.png)

*Figure 3. Top researcher communities under Louvain seed 17 and resolution 0.8.
Each distinct labeled paper is fractionally allocated over its inferred topics.
Only stored top-five topics per community are shown; grey cells indicate topics
outside that stored profile, not measured zero support. Topic validity is limited
to the AI-assessed evaluation in section 9. Graph `release-9d4a6fb20f63`.*

![Organization collaboration by sector](figures-v3/sector-mixing.png)

*Figure 4. Organization collaboration sector mixing. Counts are distinct
organization-pair by core-paper supports on accepted `COLLABORATED_WITH` edges;
unknown sector remains visible. Graph `release-9d4a6fb20f63`.*

![Inferred topic portfolio trends by year](figures-v3/topic-trends.png)

*Figure 5. Topic portfolio trends in 2021–2025. Each labeled paper contributes
fractionally across its accepted inferred labels; the series combine AAAI and
IJCAI within each year. Topic validity is limited to the AI-assessed evaluation
in section 9. Graph
`release-9d4a6fb20f63`.*

![Most cited papers within the release corpus](figures-v3/top-cited-papers.png)

*Figure 6. Highest in-degree papers in the directed core citation projection.
Counts include only citing papers inside the release corpus and are not adjusted
for citation exposure time. Graph `release-9d4a6fb20f63`.*

## 8. Analysis and business findings

The collaboration network is highly connected at its largest scale but still
contains many small components: the largest component holds 73.6% of resolved
researchers, alongside 2,277 smaller components and 193 isolates. The unweighted
degree maximum is 108 distinct coauthors. This supports studying cross-group
connectors, while the small components caution against treating the graph as one
complete social system.

The sector matrix records 4,181 accepted academia–industry pair–paper supports.
The most frequent pair/topic candidate is Shanghai Jiao Tong University with
Tencent (China) in inferred Representation learning, supported by 14 distinct
core papers. Examples are [*Exploiting Fine-Grained Face Forgery Clues via
Progressive Enhancement Learning* (AAAI 2022)](https://doi.org/10.1609/aaai.v36i1.19954)
and [*DIRL: Domain-Invariant Representation Learning for Generalizable Semantic
Segmentation* (AAAI 2022)](https://doi.org/10.1609/aaai.v36i3.20193). This records
co-publication support in the selected corpus. It does not establish a present
partnership, commercial transaction or current employee relationship.

In the researcher projection, Dacheng Tao is the highest approximate-betweenness
candidate: score 0.05493 among 36,680 resolved researchers. The configured
Louvain community has 466 members and 231 distinct papers, 212 of which carry
inferred topics. Representation learning is the largest profile with 63 papers
and 23.6% of fractional topic mass. Supporting works include [*BESA:
BERT-based Simulated Annealing for Adversarial Text Attacks* (IJCAI
2021)](https://doi.org/10.24963/ijcai.2021/453) and [*Deep Graph-neighbor
Coherence Preserving Network for Unsupervised Cross-modal Hashing* (AAAI
2021)](https://doi.org/10.1609/aaai.v35i5.16592). Because the top-20 betweenness
overlap falls to 1/20 under the strict evidence filter and the rank correlation
is 0.275, this candidate is a lead for manual review rather than a stable
individual ranking.

For the inferred Representation learning topic, Zhejiang University has 171
R10-supported papers among 527 organization-associated topic-labeled papers;
Peking University has 149 among 420. Their fractional portfolio shares are
26.0% and 28.5%, respectively. Examples include Zhejiang University's
[*Multi-Scale Spatial Temporal Graph Convolutional Network for Skeleton-Based
Action Recognition* (AAAI 2021)](https://doi.org/10.1609/aaai.v35i2.16197) and
[*Generalizable Representation Learning for Mixture Domain Face Anti-Spoofing*
(AAAI 2021)](https://doi.org/10.1609/aaai.v35i2.16199); and Peking University's
[*Community-Aware Multi-Task Transportation Demand Prediction* (AAAI
2021)](https://doi.org/10.1609/aaai.v35i1.16107) and [*GRASP: Generic Framework
for Health Status Representation Learning Based on Incorporating Knowledge from
Similar Patients* (AAAI 2021)](https://doi.org/10.1609/aaai.v35i1.16152). These
denominators cover only accepted organization evidence in the topic-labeled
graph, not the organizations' complete research portfolios.

For investigation, the partner shortlist uses a threshold of at least eight
accepted pair–paper supports within one inferred topic. The leading candidates
are Shanghai Jiao Tong University–Tencent (14, Representation learning), Xiamen
University–Tencent (14, Representation learning), Zhejiang University–Alibaba
Group (14, Representation learning), Zhejiang University–Alibaba Group (13,
Multimodal learning), and Tsinghua University–Tencent (11, Representation
learning). This is a manual evidence-review queue, not a ranking of commercial
opportunity.

The bridge shortlist contains the top ten approximate-betweenness candidates
from the full researcher projection, including Dacheng Tao, Zhe Chen, Xiaochun
Cao, Shirui Pan and Xinchao Wang. The full list, scores and community IDs are in
[`findings.md`](../release-v2/findings.md). Selection requires a high configured
betweenness score with deterministic score/ID ordering; candidates should be
rechecked against accepted bylines and the strict-filter graph before use.

The within-corpus citation projection identifies *Informer: Beyond Efficient
Transformer for Long Sequence Time-Series Forecasting* (AAAI 2021) as the most
cited included target, with 51 in-scope citing papers. This is a count in the
captured OpenAlex snapshot. The graph omits out-of-scope citations, and the 2021
paper has more time to accumulate references than 2025 papers. PageRank and
in-degree rankings are descriptive and do not establish general scientific
impact.

## 9. Quality and robustness

### 9.1 Structural and coverage checks

| Measure | Observed | Interpretation |
| --- | ---: | --- |
| Domain nodes | 52,415 | Size gate passed (minimum 2,000) |
| Resolved core researchers | 36,680 | Size gate passed (minimum 2,000) |
| Unique R1–R4 factual edges | 124,619 | Size gate passed (minimum 5,000) |
| Nonempty relation types | 10/10 | Size gate passed |
| Matched works | 13,606/13,617 (99.92%) | 11 in review |
| Abstracts on matched works | 13,606/13,617 (99.92%) | Metadata coverage |
| Institution support on accepted authorships | 56,633/59,159 (95.73%) | Alignment coverage |
| Topic labels | 11,575/13,617 (85.00%) | Label coverage |

Fresh structural validation and size checks pass. A read-only check on the
isolated Neo4j service matches 52,415 nodes/275,438 edges; all six integrity queries
return zero rows. Sixty-six frozen content/evaluator file hashes were checked.
These checks do not establish semantic accuracy. Idempotent replay was performed
at the earlier corrected-graph checkpoint; this evaluation did not reload it.

### 9.2 Source-backed AI edge audit

The unchanged frozen recipe samples 200 edges uniformly without replacement
from all accepted edges, plus ten per relation as separate supplements. Fifty
global edges have both A/B reviews. All 350 assigned rows covering 300 unique
edges are complete, with zero missing reviews. A/B were separate fresh contexts
without inherited coordinator conversation or shared answers. Topic exports were
frozen before either context received edge predictions. Exact runtime model,
provider/version and sampling settings were unavailable and remain unknown.

The coordinator source-adjudicated all 11 actual overlap disagreements after
both edge exports were fixed. Nine identifier-policy disputes were resolved as
incorrect; two substantive-topic disputes as correct. Original votes and all
source-backed adjudications remain visible. Unverifiable edges count as incorrect.

| Global uniform sample | Measured AI-assessed result |
| --- | --- |
| Correct / planned | **176/200 = 88.00%** |
| Incorrect / unverifiable / missing | 23 / 1 / 0 |
| Wilson 95% interval | **82.7657%–91.8020%** |
| Course point comparison (>90%) | **FAIL** |
| Project point precision (≥95%) | **FAIL** |
| Project Wilson lower bound (>90%) | **FAIL** |
| Overlap agreement before adjudication | 39/50 = 78%; Cohen kappa .1851851852 |
| Verified course accuracy | **Not established** |

Global error categories are wrong identity 19, wrong topic four and unverifiable
one. Across all unique sampled edges, categories are wrong identity 27, wrong
topic 11, wrong affiliation one and unverifiable three. These latter counts
include supplements and are not a second global estimate.

Each row below is a **separate n=10 supplement**, never pooled with the global
sample. Small denominators produce wide Wilson intervals even at 10/10.

| Predicate | Correct/10 | Incorrect | Unverifiable | Wilson 95% interval |
| --- | ---: | ---: | ---: | --- |
| AFFILIATED_WITH | 9/10 | 1 | 0 | 59.58%–98.21% |
| AUTHORED | 7/10 | 3 | 0 | 39.68%–89.22% |
| CITES | 10/10 | 0 | 0 | 72.25%–100.00% |
| COAUTHORED_WITH | 6/10 | 4 | 0 | 31.27%–83.18% |
| COLLABORATED_WITH | 9/10 | 1 | 0 | 59.58%–98.21% |
| CONTRIBUTES_TO_TOPIC | 6/10 | 4 | 0 | 31.27%–83.18% |
| HAS_TOPIC | 9/10 | 1 | 0 | 59.58%–98.21% |
| PUBLISHED_IN | 10/10 | 0 | 0 | 72.25%–100.00% |
| RESEARCHES_TOPIC | 6/10 | 2 | 2 | 31.27%–83.18% |
| SUBTOPIC_OF | 10/10 | 0 | 0 | 72.25%–100.00% |

The leading identity finding is a resolver omission: raw/full work records retain
`author.observed_orcids`, but the singular-ORCID conflict pass ignores this array.
Reviewer A's separate source inventory binds 25 sampled edges with that conflict
to raw hashes and locators. The coordinator independently inspected the raw arrays
for the nine overlap identifier disputes. No graph-wide prevalence is inferred
from that targeted inventory. See [post-audit findings](../../docs/post-audit-findings.md).
Any correction needs a new graph version and new audit; these failed results stay
attached to the unchanged frozen graph.

Main evidence for the 350 assignments is primary for 123 and secondary-only for
227; 349 reuse construction sources and one uses an independent main source.
Taxonomy checks against the frozen config count as primary for the curated
hierarchy, not independent scientific corroboration. Additional sources are
recorded separately. The ledgers distinguish byline/author-specific institution
checks, citation records, topic evidence and distinct-paper derived support.
Reading the same OpenAlex snapshot cannot establish that snapshot's correctness.

### 9.3 Topic agreement with AI-assigned reference labels

The held-out set contains 20 AAAI and 30 IJCAI papers, selected before tuning.
All 60 assignments over 50 unique papers are reviewed; none is unreviewable.
One exclusive judgment has a considered empty leaf set. Each exclusive review
has weight one, and each of two overlap reviews has weight one half, so the
effective denominator is 50 papers. Reference disagreements would remain visible
rather than being converted into a synthetic consensus. Actual overlap exact-set
agreement is 10/10 and mean Jaccard is 1.0; agreement does not authenticate the
labels or establish independence. All topic evidence is secondary-only,
reconstructed OpenAlex title/abstract text from the construction source.

Both classifiers are evaluated on the same unchanged references and test IDs.
Metrics below are agreement with AI labels, not human gold accuracy.

| Frozen classifier | Test coverage | Micro P | Micro R | Micro F1 | Macro P | Macro R | Macro F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Phrase baseline | 13/50 (26%) | 0.9286 | 0.1313 | 0.2301 | 0.4167 | 0.0943 | 0.1473 |
| Embedding | 45/50 (90%) | 0.6863 | 0.3535 | 0.4667 | 0.4986 | 0.3066 | 0.3627 |

Weighted embedding TP/FP/FN are 35/16/64; phrase counts are 13/1/86. Neither
micro precision reaches the frozen .95 target. Embedding's broader coverage
increases recall/F1 but also introduces false positives; the results support
cautious exploratory use of topic portfolios. Macro scores give equal weight to
all 16 leaves, with the scorer's explicit undefined-label conventions. Full
per-label metrics and reviewer-specific results remain in
[topic-eval-agent.json](../release-v3/topic-eval-agent.json).

### 9.4 Robustness and evaluation limits

Every scored output records `evaluation_kind=ai_agent_review`,
`human_validation=not_performed`, `reviewer_independence=not_established` and
`verified_course_accuracy=not_established`. Separate contexts do not demonstrate
statistical independence or different models. Wilson intervals describe sampling
uncertainty conditional on judgments; they omit evaluator mistakes, shared-model
bias and source dependence. The audit measures accepted-edge precision, not
omitted-edge recall. No claim is made that the lecturer accepts AI-only evaluation.
The [evaluation limitations](../release-v3/evaluation-limitations.md) and
[completed source ledgers](../release-v3/completed/) give the scope and provenance.

The frozen strict-evidence filter retains 8.0% of researcher-collaboration
edges, 27.4% of organization-collaboration edges, no citation or paper-topic
edges, and all organization-topic edges. This is sensitivity analysis, not a
correctness estimate. Researcher bridge rankings are sensitive to support:
top-20 betweenness overlap is 1/20. Topic coverage varies by venue–year
(81.9%–87.9%), while the held-out AI agreement reveals semantic errors. Business
findings in section 8 remain candidates for source investigation rather than
validated recommendations.

## 10. Achievements and limitations

The release graph meets the course's node, factual-edge and ten-relation size
requirements, and it has passed structural validation, Neo4j inventory/integrity
checks and idempotent replay. Phase 6 now provides separate collaboration,
citation and topic projections, annual counts, partner/country mixing, topic
profiles, cited-paper rankings, sensitivity results, six figures and evidence
candidates. These are reproducible descriptions of the frozen artifact.

Several quality questions remain open. Eleven roster papers were not matched to
OpenAlex under the release rules. Thousands of official byline positions lack an
OpenAlex author ID and are withheld, so the researcher graph is a covered subset
of bylines rather than a complete author network. Agent evaluators checked the frozen sample, finding identity and topic errors;
the sample does not validate the complete graph. The 85.0% topic coverage is not topic accuracy. Country and sector
properties describe normalized organization metadata rather than researchers'
nationality or employment. Citation counts have unequal exposure time. The
release covers two conference series only, so claims do not generalize to all AI
research venues.

The project meets structural size requirements and produces reproducible social
network descriptions, but its AI-assessed edge precision is only 88.00% (Wilson
95% 82.77%–91.80%). Both course point and project precision checks fail. Embedding
micro F1 .4667 exceeds phrase .2301 against AI references but leaves substantial
topic error. Human validation and verified course accuracy remain unestablished.
These outcomes constrain the business interpretation; they are preserved rather
than hidden through post-audit tuning. A separately versioned correction should
first address observed-ORCID conflict handling, retain provenance and obtain a
new audit without reusing these test errors as independent evidence.

The pre-audit correction synchronizes all Topic metadata, hierarchy and evidence
with the frozen classifier taxonomy; the classifier, test membership, predictions,
excerpts, similarity scores, core facts and derived weights are unchanged.
[The correction summary](../release-v2/graph-summary.json) records equality hashes.
The analysis and figures were computed at the earlier corrected-graph checkpoint
and are reused here with their exact frozen bytes; they were not recomputed for
the evaluator change. New [caption version 1](captions-agent-v1.md) qualifies the
AI assessment without modifying the frozen figure/caption artifacts. Exact fractional accumulation (`d040-release-metrics-v2`) also corrects
floating-point order effects on tied community topic rankings; this changes no
graph facts or predictions. The old freeze and figure directory remain historical.
Execution follows [the agent workflow](../../docs/agent-audit-workflow.md).

## 11. Reproducibility and release state

The source repository is [HSandz/scientific-network](https://github.com/HSandz/scientific-network).
A read-only remote check on 9 November returned main
`05ac5d83922c54bd006034e5c7296de00e811f72` and no tags; local work is not pushed.
The GitHub HTTP check returned 504, so public lecturer access is not verified.
Eight DOI links in this report passed the recorded external-link check. No course
release/tag, Site update, invitation or submission was performed.
The frozen graph is
`release-9d4a6fb20f63`, SHA-256
`c23ef82c97fcb539b4b1c279e8ff42378bdb102e80fe851acf1a42e816a727b8`; the
release, quality, analysis and topic configuration hashes and review packet
hashes are recorded in [`freeze-v3.json`](../release-v2/freeze-v3.json).

The locked environment is restored with:

```bash
uv sync --locked --group dev --extra analysis --extra report
uv run pytest
uv run research-network schema
```

The frozen graph analysis is reproduced with:

```bash
uv run research-network analyze \
  --input data/processed/release-graph-v3/graph.json \
  --config configs/analysis-release-v1.yaml \
  --quality-config configs/quality-release-v1.yaml \
  --output reports/runs/manual-corrected-analysis.json
```

The committed fresh analysis is `reports/release-v2/analysis.json`. Use an unused
output path for each replay; do not overwrite the frozen analysis or graph. Source acquisition uses the official
roster manifest and OpenAlex cache described in `configs/release-v1.yaml`, with
an API key supplied via an ignored environment file. Raw downloads, graph JSON,
database volumes and paper files are not tracked in Git. The work logs record
the exact commands, input hashes, outcomes and local artifact paths for the
release stages. Independent reproduction should use the frozen configs and
confirm graph and summary hashes before comparing reports.

The real review exports, receipt, evaluator freeze and source ledgers are under
[`reports/release-v3/`](../release-v3/README.md). The supported `score-agent-review`
command validates bindings before writing AI-labelled results; its actual exit
code is 1 because numeric quality gates fail. The full suite passed 419 tests
with one existing empty-parameterization skip. These are software checks, not
semantic validation of the measured graph. Exact scoring/rendering commands and
host requirements are in [reproduction instructions](../../docs/reproduce-agent-evaluation.md).
The package excludes full graph/raw caches/models/credentials/database volumes;
a fresh clone cannot rescore without restoring original permitted ignored inputs
and verifying their hashes. Source ledgers permit traceability but do not
redistribute the complete third-party source cache.

## Remaining personal facts and external delivery

Agent annotation, scoring, report drafting and local rendering/package preparation
are complete or recorded in the current local package receipt. Human annotation
is optional. Real names, student IDs, actual human contributions, lecturer access
and course-specific AI-use rules remain explicitly pending from supplied records.
The local package is a submission draft until those facts are reflected in a new
render. A release tag/push, Site publication, invitations and submission require
separate authorization after this concrete local result is reviewed; follow
[the delivery checklist](../../docs/local-submission-checklist.md).

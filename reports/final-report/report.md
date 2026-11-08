# AI Research Network: AAAI and IJCAI, 2021–2025

**Draft status:** methodology and Phase 6 results written; team allocation and
independent evaluation still require human inputs. This is not the final report.

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
for this release. Names alone never merge people. Of 65,469 official author
positions, **59,159** were accepted as `AUTHORED` support and **6,310** were
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

Citation edges point from a citing paper to a deduplicated cited paper. The
acquisition scan found 378,360 reference targets: 370,831 targets outside the
release scope, 34 self-references, no ambiguous in-scope target mappings, and
7,308 accepted in-scope citation edges. External citations do not enter the
core citation projection.

## 5. NLP methods

The frozen topic taxonomy contains four parent topics and 16 leaf topics. A
phrase-based classifier supplied topics for graph v1. Graph v2 replaces those
labels with a sentence-embedding method using the frozen model revision and
development-calibrated thresholds `tau = 0.2708871365` and `delta = 0.02`.
The method compares title and abstract text against topic definitions and uses
an abstract sentence (or title for title-only text) as supporting evidence. It
assigns up to three leaf labels or abstains. Threshold calibration used
non-test papers; the test IDs were frozen before tuning. Model outputs were
generated only after the classifier freeze and are not shown in the human topic
review sheet.

The v2 graph has **11,575 topic-labeled papers** and **2,042 abstentions**, for
85.00% label coverage. This is coverage, not topic accuracy. Fifty frozen test
papers are ready for independent annotation with the 16 topic definitions; no
human test labels or classifier precision/recall/F1 are available yet. Topic
trends and topic-based findings below are therefore provisional until those
annotations are scored.

## 6. Graph design and graph database

The property graph has five labels—Researcher, Paper, Organization, Topic and
Venue—and ten predicates. `AUTHORED`, `AFFILIATED_WITH`, `PUBLISHED_IN` and
`CITES` are observed facts; `HAS_TOPIC` is inferred from text; `SUBTOPIC_OF` is
curated taxonomy; `COAUTHORED_WITH`, `COLLABORATED_WITH`, `RESEARCHES_TOPIC` and
`CONTRIBUTES_TO_TOPIC` are derived from accepted core-paper support. Domain
nodes, evidence records and graph edges retain stable IDs and versioned
provenance. Unresolved evidence stays in review queues.

| Predicate | v2 edge count | Evidence class |
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

The frozen v2 graph (`release-5d830ffcbdf4`) has **52,415 nodes** and **275,438
edges**. The four observed predicates contain **124,619 unique factual edges**;
derived, inferred-topic and curated-taxonomy edges are counted separately.
Neo4j Community 5.26 was loaded in the isolated `neo4j-five-year` service on
`bolt://localhost:7689`. Inventory and integrity queries passed for v1 and v2,
and replay reconciled counts without changing the v2 graph. The pilot and
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

Sector and country mixing count distinct accepted organization-pair by
core-paper supports, using the derived collaboration evidence. Unknown sector
or country is retained as its own category. Topic shares are available by both
venue and year; topic figure trends combine venues within a year and normalize
over labeled papers. The directed citation projection contains 7,308 in-scope
edges; its highest in-degree paper has 51 in-scope citing papers. Raw citation
counts are not adjusted for the unequal time papers have had to receive
citations.

The six static figures and their CSV data tables are in
[`figures/`](figures/), with graph version, projection, filter and counting
conventions in each caption. Three source-linked candidate findings and two
screening shortlists are in
[`reports/release-v1/findings.md`](../release-v1/findings.md). The strict-filter
sensitivity analysis materially changes researcher betweenness rankings and
retains only 8.0% of researcher collaboration edges; these comparisons are
robustness diagnostics, not semantic accuracy estimates.

## Sections still requiring human input

The task allocation, reviewer identities and contributions must be completed
from `docs/team.md`. Independent edge and topic annotations, their scoring,
quality conclusions, and the final limitations/results sections are pending.
No accuracy claim is made in this draft.

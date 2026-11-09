# Corrected release report — 9 November 2026

The release is **AAAI and IJCAI 2021–2025 main-track papers**, one cumulative
network. D040 supersedes the earlier 34-series implementation scope; the broader
registry remains long-term scope. The earlier pilot and source-diagnostic results
are historical. This page now uses corrected graph `release-d3c788c3114a`.

## What the network contains

The immutable corrected graph has **47,875 nodes and 225,731 accepted edges**:
32,189 researchers, 13,617 papers, 2,047 organizations, 20 topics and two venues.
There are **110,026 factual R1–R4 edges**; inferred topics, curated taxonomy and
derived collaboration/profile edges are counted separately. All ten predicates
are nonempty. Neo4j Community uses the isolated five-year service.

| Relationship | Accepted edges | Evidence class |
| --- | ---: | --- |
| AUTHORED | 50,437 | Observed authorship |
| AFFILIATED_WITH | 38,664 | Observed authorship-specific affiliation |
| PUBLISHED_IN | 13,617 | Official roster |
| CITES | 7,308 | Observed within-corpus reference |
| HAS_TOPIC | 14,222 | Inferred topic |
| SUBTOPIC_OF | 16 | Curated taxonomy |
| COAUTHORED_WITH | 80,482 | Derived distinct-paper support |
| COLLABORATED_WITH | 13,031 | Derived distinct-author paper support |
| RESEARCHES_TOPIC | 5,622 | Derived profile |
| CONTRIBUTES_TO_TOPIC | 2,332 | Derived profile |

The graph maps above are selected illustrations of this release. Researcher and
organization nodes are selected by full-projection fractional strength; papers by
within-corpus in-degree. Ties use stable IDs; all induced accepted edges are shown.
Layout seed is 42. Colors indicate stored Louvain membership (researchers; seed 17,
resolution 0.8, palette repeats), sector (organizations), or year (citations).
Positions are not geographic coordinates. Counts and filters in the explorer refer
to the displayed subset; full-projection counts are shown separately. Static maps,
node/edge CSVs and a public evidence-pointer payload are downloadable.

## Quality: numeric AI gates pass, limits remain

The prospective corrected-graph edge audit scored **193/200 = 96.5%**, with a
Wilson 95% interval of **92.95%–98.29%**. One edge was incorrect, six unverifiable,
and none missing; unverifiable outcomes count as failures. The configured AI
numeric thresholds pass. Across the supplementary checks all 350 assignments were
completed on 300 unique edges. Reviewer overlap agreement is 49/50; Cohen kappa
is 0.6598639456. The original v3 graph and failed **88%** audit remain preserved.

**These are source-backed AI assessments. Human validation was not performed;
evaluator independence and verified course accuracy are not established.** Wilson
intervals do not cover evaluator errors, shared source bias or model bias.
The correction was audit-motivated. Seven semantics repeat between audit samples;
24/516 supporting papers and 177/237 raw response hashes overlap earlier evidence
(the hash count is not a paper count). Two organization-topic aggregates inspected
10/35 and 17/107 supports, satisfying a minimum-three existence check, without
exhaustively validating aggregate support counts.

**Affiliation coverage fails its 80% gate:** 48,259/65,469 matched authorship
positions = **73.71%**. The 95.68% accepted-only diagnostic is conditional on
retained authorships and must not replace the main denominator.
The unchanged topic evaluation gives embedding/phrase micro-F1
**0.4667 / 0.2301**, and precision **0.6863 / 0.9286**; both miss the 95% precision
target. Its frozen test is small and IJCAI-heavy. These are AI-reference results,
not independent human gold labels.

## Read the statistical charts

The degree distribution and component chart describe collaboration structure;
community profiles show inferred topic mixes, not observed interests. Sector
mixing measures accepted organization links. Topic trends depend on classifier
coverage and thresholds. Citation rankings count references inside this corpus,
not global influence. Organization and researcher rankings are also conditioned
on the available OpenAlex identities and affiliations.

## Reproducibility and delivery

The corrected graph, source evidence, classifier, held-out memberships and
judgments were frozen before this presentation update. No graph reconstruction,
new judgments, threshold tuning or resampling was performed for these maps.
A fresh review reproduced the edge score exactly, checked all frozen artifact
bindings and the prior ZIP, and ran the configured tests. The updated local PDF
contains the three network maps plus the six statistical figures.

The Site is a published snapshot with native controls and SVG graphs. It does not
query a local database or automatically synchronize the repository. Source helper
publication preserves this existing project's ID, public audience and URL.
Personal student names/IDs/contributions, lecturer access and course AI-use
requirements remain pending; the course package is still a local draft. No
GitHub push, tag, invitation or course submission is implied by Site publication.

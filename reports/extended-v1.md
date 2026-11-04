# Expanded conference diagnostic results — 3 November 2026

Observed results from WORK-2026-11-03-006. This is an incomplete-scope diagnostic,
not a release or an independent semantic evaluation. The user authorized collection
under D015; legacy inputs and the original Neo4j database were preserved.

## Measured collection and graph

- Scope: **17 of 31 in-year editions** have rosters; 14 remain unresolved. Three
  series have no 2023 edition. The 17 include the two legacy venues.
- Roster: **15,738 records: 14,909 included and 829 excluded**. These are paper
  ledger counts, not resolved people, graph nodes, or an accuracy result.
- Freeze: **925 test / 470 development / 13,514 pool** assignments; all 5,046
  legacy assignments (including original120 test/60 dev) preserved. The250-paper
  sample contains old100 plus15×10 new diagnostics; held-out overlap is zero.
- Metadata: **245/250 acquired**,235 abstracts,145 strict OpenAlex matches. Five
  roster/detail byline conflicts remain withheld; no name-compatibility relaxation.
- Headers: **235 parsed PDFs**, ten MICCAI records without official PDF links,
  five acquisition failures;154 papers contain extracted affiliation structures.
- Neo4j: **399 nodes /533 edges**, including **369 factual R1–R4 edges**.
  Graph version: `pilot-topic-d512d7239923`. Eight predicates are nonempty.
  Browser: <http://localhost:7475>; Bolt: `bolt://localhost:7688`.
- Original database remains **154 nodes /211 edges**, version
  `pilot-topic-0bb7f11a404e`, on7474/7687. It was not replaced.

## Per-venue collection

All rows use2023; counts include legacy reuse. Unresolved/no-edition series are
listed separately below. Eligible roster counts follow the conservative track maps.

| Venue | Included | Excluded | Selected | Acquired | Abstracts | OpenAlex matches | Parsed headers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| neurips | 3218 | 322 | 50 | 50 | 50 | 32 | 50 |
| icml | 1828 | 0 | 50 | 50 | 50 | 29 | 50 |
| ijcai | 639 | 212 | 10 | 10 | 10 | 10 | 10 |
| mlsys | 46 | 0 | 10 | 9 | 9 | 1 | 9 |
| cvpr | 2353 | 0 | 10 | 10 | 10 | 6 | 10 |
| iccv | 2155 | 1 | 10 | 10 | 10 | 4 | 10 |
| miccai | 730 | 0 | 10 | 10 | 10 | 9 | 0 |
| acl | 1075 | 2 | 10 | 10 | 10 | 8 | 10 |
| emnlp | 1047 | 1 | 10 | 8 | 8 | 6 | 8 |
| eacl | 280 | 1 | 10 | 8 | 8 | 7 | 8 |
| aistats | 496 | 0 | 10 | 10 | 10 | 7 | 10 |
| uai | 243 | 0 | 10 | 10 | 10 | 3 | 10 |
| colt | 164 | 6 | 10 | 10 | 10 | 4 | 10 |
| rss | 112 | 0 | 10 | 10 | 10 | 3 | 10 |
| corl | 199 | 0 | 10 | 10 | 10 | 4 | 10 |
| aamas | 244 | 284 | 10 | 10 | 0 | 4 | 10 |
| kr | 80 | 0 | 10 | 10 | 10 | 8 | 10 |

## Node and edge inventory

| Node label | Count |
| --- | ---: |
| Organization | 32 |
| Paper | 245 |
| Researcher | 85 |
| Topic | 20 |
| Venue | 17 |

| Predicate | Count |
| --- | ---: |
| AUTHORED | 85 |
| AFFILIATED_WITH | 38 |
| PUBLISHED_IN | 245 |
| CITES | 1 |
| HAS_TOPIC | 108 |
| SUBTOPIC_OF | 16 |
| COAUTHORED_WITH | 36 |
| COLLABORATED_WITH | 4 |
| RESEARCHES_TOPIC | 0 |
| CONTRIBUTES_TO_TOPIC | 0 |

## Quality gaps and verification

Resolved authorships: **85/1185 (7.17%)**. Accepted affiliated author–paper
pairs: **36/1185 (3.04%)**, from38 observation triples.
Exact printed-institution and public-publication corroboration retain substantial
identity/affiliation review work. These coverage ratios are not precision estimates.

Topics: **85/245 papers (34.69%)**,108 assignments,160 abstentions. The draft
phrase taxonomy does not cover the expanded subfields well. No calibration or
independent semantic precision/recall/F1 was performed; thresholds were unchanged.
Neither size gates nor the ten-type gate is met. `--require-size` correctly fails.

**72 offline tests passed.** Schema/synthetic validation, locked environment checks,
graph structural validation, import/replay and six integrity queries passed.
All510 graph-referenced source objects passed SHA-256 checks; nine protected files
and all legacy split assignments were unchanged. No configured secrets were found
in Git-eligible files. An attempted import into the original database was rejected
before graph mutation. These checks do not establish semantic accuracy.

Referenced PDFs total820,060,996 bytes, median1,364,757 bytes. These include cached
legacy PDFs; they are not newly downloaded bytes. Final extraction elapsed2.881s
is a cache replay and must not be reported as fresh parser throughput. Earlier
v2 extraction recorded503.941s across cached/new records, not a controlled benchmark.

## Unresolved editions and source limitations

Public probes returned the following failures or required unimplemented source
handling; none was silently substituted with OpenAlex search results. Sources
can change, and these failures do not establish permanent publisher unavailability.

| Venue | Observed limitation |
| --- | --- |
| iclr | api.openreview.net: access/quota HTTP 403; collection stopped |
| aaai | ojs.aaai.org: RemoteProtocolError |
| acmmm | dl.acm.org: ConnectError |
| kdd | dl.acm.org: ConnectError |
| www | dl.acm.org: access/quota HTTP 403; collection stopped |
| sigir | dl.acm.org: access/quota HTTP 403; collection stopped |
| wsdm | dl.acm.org: access/quota HTTP 403; collection stopped |
| recsys | dl.acm.org: access/quota HTTP 403; collection stopped |
| cikm | dl.acm.org: access/quota HTTP 403; collection stopped |
| icdm | icdm2023.cloud: ConnectError |
| sdm | epubs.siam.org: access/quota HTTP 403; collection stopped |
| icra | www.icra2023.org: HTTP 400 |
| iros | ieee-iros.org: ConnectError |
| icaps | ojs.aaai.org: RemoteProtocolError |

ECCV, NAACL and COLING have no2023 edition. Source-specific details, exclusion
policies and complete source hashes are in the edition ledger/config. AAMAS keeps
regular research sessions; poster abstracts/special tracks are excluded. COLT keeps
Original Papers; front matter/Open Problems are excluded. MICCAI has accepted-title
rosters and detail bylines, but no official PDF links in the selected pages.

## Reproduction and next work

Use [the expanded workflow](../docs/extended-workflow.md); the active executable
config is `configs/corpus-extended-v2.yaml`, roster/splits v3, metadata/headers v3,
and final graph v1. Earlier discovery/metadata outputs remain preflight diagnostics.
[Machine-readable metrics](extended-v1.metrics.json) pin every input/method/code
hash and record per-venue coverage. Raw sources, graphs and console logs remain
local/ignored; no PDFs or credentials are published. No automatic commit/push.

Next: inspect the five official byline conflicts and affiliation/identity review
queue, annotate development topics for new subfields, and implement lawful source
routes for the14 unresolved editions. Confirm annotation capacity before expanding
beyond diagnostics. Preserve the untouched held-out sets; do not tune and reuse
them as independent evaluation. `analyze` and `evaluate` remain placeholders.

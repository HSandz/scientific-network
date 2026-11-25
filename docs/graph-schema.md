# Graph schema

Node IDs are stable, namespaced internal IDs, such as `researcher:<internal-id>`.
Provider identifiers are crosswalks, not authority to silently recluster people.
Neo4j uses `id` on every node. `name` is the human display value (the title for a
Paper); paper exports may additionally retain `title` as a source field.

| Label | Meaning | Required domain properties |
| --- | --- | --- |
| Researcher | One resolved person | name, resolution_status, identity evidence/crosswalk |
| Organization | Defined institution/corporate entity | name, sector, normalization policy; optional ROR/location |
| Paper | One deduplicated work, selected proceedings version | name/title, year, official_url, track, is_core |
| Topic | Frozen project vocabulary concept | name, level (parent/leaf), taxonomy_version, definition |
| Venue | Conference series | name; edition year is on Paper |

Not all release-required properties are enforced by the initial JSON validator.
Unresolved mentions, raw responses, files and evidence records stay outside domain
node totals. A year/country is a property unless a later analysis justifies a node.

| ID | Predicate | Source → target | Class | Meaning/support rule |
| --- | --- | --- | --- | --- |
| R1 | AUTHORED | Researcher → Paper | observed | Resolved identity on official byline; retain position |
| R2 | AFFILIATED_WITH | Researcher → Organization | observed | Accepted author–paper–organization observations; not employment duration |
| R3 | PUBLISHED_IN | Paper → Venue | observed | Official main proceedings, one primary series/core paper |
| R4 | CITES | Paper → Paper | observed | Explicit reference, verified deduplicated target; citing → cited |
| R5 | HAS_TOPIC | Paper → Topic | inferred_topic | 1–3 supported leaf labels or abstain |
| R6 | SUBTOPIC_OF | Topic → Topic | curated_taxonomy | Approved leaf → parent; frozen and fully audited |
| R7 | COAUTHORED_WITH | Researcher ↔ Researcher | derived | Distinct resolved people share accepted core paper |
| R8 | COLLABORATED_WITH | Organization ↔ Organization | derived | Same core paper, two distinct authors with aligned affiliations to two organizations |
| R9 | RESEARCHES_TOPIC | Researcher → Topic | derived | ≥2 distinct accepted core papers with that leaf topic |
| R10 | CONTRIBUTES_TO_TOPIC | Organization → Topic | derived | ≥3 distinct accepted core papers with that leaf and paper-specific organization support |

The Venue label applies to all series in [the expanded scope](archive/scope/conference-scope.md),
not just the two legacy pilot venues. Planned scope is **2021–2025** (D018);
existing artifacts cover 2023 only. The year remains the conference edition year
on Paper. No sixth label or extra predicate is introduced. Expanding venue
coverage does not add entity labels or predicates; verified cross-venue work
versions must be reconciled with the one-primary-venue invariant before release.

## Identity, evidence and counting

One semantic edge has key `(predicate, source_id, target_id)`. Store symmetric
pairs once in lexicographic ID order and analyze them as undirected. The code's
`edge_id()` hashes a compact JSON array containing that key using SHA-256; sources
and graph version do not create additional semantic edges.

Every accepted edge records `edge_id`, endpoints, predicate, `evidence_kind`,
`evidence_ids`, `method_version`, `graph_version`, and accepted status. Source
evidence resolves to URL/record, timestamp, raw hash, locator and permitted excerpt.
Derived evidence resolves to exact accepted base-edge IDs and distinct supporting
core-paper IDs. For scale, use ledger partitions instead of enormous Neo4j arrays.
Do not mix unlike rule/model scores as calibrated probabilities.

R2 is a single researcher–organization edge aggregated over canonical affiliation
triples. Store observed years and support counts; use the triple table for precise
paper/year filtering. Every triple must align one byline researcher to that
organization on that exact paper. Unknown affiliation/sector remains unknown.

For the release, at least 5,000 unique core-supported **R1–R4** edges must exist
before counting inferred, taxonomy and derived relationships. Report all four
classes separately. Reverse copies and source confirmations do not increase size.

## Derivation weights

- R7: each core paper with `k > 1` official byline authors contributes `1/(k-1)`
  to each pair of resolved authors. Unresolved authors remain in the denominator
  to avoid inflating accepted pairs; see D012 in [decisions](decisions.md).
  Save distinct shared-paper count and summed fractional weight.
- R8: enumerate eligible distinct-organization pairs supported by distinct authors.
  A sole author with two affiliations creates none. If the paper supports `q > 0`
  pairs, contribute `1/q` per pair. Deduplicate support by paper.
- R9/R10: threshold by distinct canonical work IDs, not alternate versions or
  repeated labels. A below-threshold contribution remains visible through base edges.
- Topic portfolios: with `L` accepted labels a paper contributes `1/L` to each;
  organization portfolios additionally divide by `m` supported organizations.
  Portfolio fractions do not replace R9/R10 raw-paper thresholds.

Never add supervision, funding, current employment or method-use predicates
without explicit source evidence and a separate annotation policy.

## Construction and analysis

Freeze accepted entities/support; load nodes and R1–R6; recompute R7–R10; verify
keys, support, weights and DBMS reconciliation; repeat import to prove idempotence.
Keep review candidates outside the released graph. The pilot materializer
recomputes R7–R10 and the validator checks their support and weights. The Neo4j
loader reconciles counts in its transaction and rejects conflicting graph versions.

Named projections: researcher collaboration, organization collaboration, core
citations, paper topics and organization topics. Use inverse positive strength
for weighted shortest-path distance when intended. Report direction, isolates,
counting, seeds, algorithm versions and corpus boundary for every result.

## Enrichment layer (v5-enriched, D042)

Added for the final exam. The sections above describe the frozen v4 graph and are
unchanged: v5-enriched carries every v4 node, edge, evidence record and affiliation
observation as is (a canonical hash of that layer is recorded in the artifact and
checked by the validator) and adds a separate enrichment layer. The artifact is
`schema_version: 0.2.0-enrichment` with the v4 keys plus `base_graph_version`,
`base_layer_sha256`, `enrichment_version` and `node_enrichments`.

**New labels.** `Method`, `Task`, `Dataset`. Properties: `name`, `key` (normalized
form), `paper_count` (distinct supporting papers, at least 3), `linked`,
`wikidata_qid`, `wikipedia_title`, `wikipedia_url`, `wikipedia_revision_id`,
`link_score`, `surfaces`, `enrichment_version`. A linked entity's ID is
`<label>:<QID>` (for example `method:Q42`); an unlinked one gets a deterministic ID
from label and normalized name (`method:<16 hex>`) with `linked: false`.

**Added Organization nodes.** Parents named by Wikidata P749 or P361 that are not v4
organizations are `Organization` nodes with `source: wikidata_parent`,
`is_core: false` and `wikidata_qid`. They never count toward core size gates.
Existing v4 organizations gain properties only through `node_enrichments`
(`wikidata_qid`, `wikidata_description`, `wikidata_types`, `wikidata_country`,
`wikidata_inception`, `wikipedia_url`, `wikipedia_revision_id`), stored under those names in Neo4j.

**New predicates.**

| Predicate | From → to | Evidence kind | Rule |
| --- | --- | --- | --- |
| `USES_METHOD` | Paper → Method | `extracted` | verified Method mention in the paper's title or abstract |
| `ADDRESSES_TASK` | Paper → Task | `extracted` | verified Task mention |
| `USES_DATASET` | Paper → Dataset | `extracted` | verified Dataset mention |
| `APPLIED_TO` | Method → Task | `extracted` | stated in the abstract; at least 2 distinct supporting papers, or (enrichment v3) one paper whose two endpoints sit in one sentence (`support_rule`) |
| `EVALUATED_ON` | Method or Task → Dataset | `extracted` | stated in the abstract; at least 2 distinct supporting papers |
| `PART_OF` | Organization → Organization | `wikidata` | Wikidata P749 or P361; from enrichment v3 only for a parent that passes the `part_of_v2` rule (an organization of an allowed kind, no index, list or ranking, statement not end-dated, plausible direction) |
| `MEMBER_OF` | Organization → Organization | `wikidata` | enrichment v2 only: Wikidata P749 or P361 whose parent's direct instance-of class is a consortium, association, alliance, network or group (class list in `configs/enrichment-v2.json`); a member of the second organization, not a unit of it; from v3 a pair carries this edge **instead of** `PART_OF` |
| `RELATED_TO` | Method or Task → Method or Task | `aggregated` | Wikipedia link between the two linked pages in either direction and at least 3 shared papers; source ID sorts before target ID |

Every enrichment edge has `edge_id` (SHA-256 of relation, source, target and method
version), `evidence_ids` that resolve in the evidence list, `method_version`,
`graph_version` (the enriched version) and `validation_status: accepted`.
Extracted evidence stores the paper ID, a hash of the title-and-abstract text, character
offsets and sentence indices, the extractor and confidence, and **not** the abstract text
(`docs/source-policy.md`). Aggregated edges carry `support_count` and `support_paper_ids`;
`APPLIED_TO` and `EVALUATED_ON` also count the papers whose two endpoints sit in one sentence.

**Enrichment v2 (`schema_version: 0.3.0-enrichment`, D042 amendment 2026-11-25).** Adds the `MEMBER_OF`
predicate above and the optional edge property `support_rule` on `APPLIED_TO` and `EVALUATED_ON`:
`two_or_more_papers` (the v1 rule) or `single_paper_same_sentence` (one supporting paper whose two endpoints the extractor found in one
sentence; `support_count` 1; adopted only for `EVALUATED_ON`). `MEMBER_OF` is **additional**: the v1 `PART_OF` edges are unchanged
because the PART_OF v2 rule failed its declared criterion, so a pair that is a consortium membership can carry both a `PART_OF` edge
(known to be weak, see `reports/enrichment-v2/quality.md`) and a `MEMBER_OF` edge. Consumers that roll organizations up to parents should
prefer `MEMBER_OF` for such pairs and should not treat `PART_OF` targets that are indices or lists as organizations.

**Enrichment v3 (`schema_version: 0.4.0-enrichment`, D042 amendment 2026-11-25, graph `enriched-cb371912e308`).** No new predicate. Three
rules were adopted post hoc or on a re-declared criterion (see the amendment; the reviewer judged the v2 absolute criteria badly chosen): the
`part_of_v2` rule now filters `PART_OF` (783 edges instead of 1,129; the dropped statements are end-dated, point to an index, list or
non-organization, run in the wrong direction or put a university under a faculty or institute), so **each organization pair carries exactly one of
`PART_OF` and `MEMBER_OF`** (the validator checks it, and every `PART_OF` evidence record names the rule); the narrower-page link guard unlinks
an entity whose best Wikipedia page is narrower than its name; and single-paper same-sentence `APPLIED_TO` edges are admitted (`support_rule`
`single_paper_same_sentence`, `support_count` 1). The v1 and v2 graphs keep their own schema versions and stay loadable.

Organization-level interest ("organization X works on method Y") is not an edge; it is
computed from `AUTHORED`, `AFFILIATED_WITH` and `USES_METHOD` so every answer traces to papers.

Counts are reported by layer (v4, enrichment by evidence kind, total). The R1-R4 factual-edge
gate of D040 applies to the v4 layer only. Structural validation (`enrich.graph5.validate_enriched`)
checks endpoint labels, deterministic IDs, evidence resolution, support thresholds, the node
threshold, paper-count consistency, parent-node rules and the v4 layer hash, and re-runs the frozen v4
validator on the v4 layer. It does not establish semantic accuracy.

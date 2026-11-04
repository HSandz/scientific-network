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

The Venue label applies to all series in [the expanded scope](conference-scope.md),
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

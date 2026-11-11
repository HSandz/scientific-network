# Task2B — identity recovery, evaluation and recommendation

Final isolated candidate: **`release-identity-v5-503aafe10a31`**, method `identity-candidate-v5.5` / `paper-mention-identity-v5.3`, config `configs/identity-candidate-v5-release-v4-final.yaml`. Graph SHA256 `85ff09d0a5e6a42160a3c98fad3f63941a2b412213490f4c7f744ed5e2ba4d4e`. Implementation checkpoint `eab4dce`. Frozen v4 remains production; both v3 and intermediate Task2B checkpoints are preserved.

This session implements and executes bounded identity recovery, an exact abstention/source inventory, prospective evaluation sampling/scoring, a new graph build, structural validation, deterministic replay and three-way network comparison. It does not establish independent semantic precision or recall.

## What was recovered

- **253 additional accepted positions versus candidate-v3**, with zero v3 accepted positions lost or reassigned: 185 formatting positions on 37 stable provider IDs, 50 positions on five provider IDs with publicly declared ORCID aliases, and 18 missing-provider-ID positions supported by exact-DOI cached duplicate work records.
- The 235 formatting/alias positions were already accepted by v4. They restore coverage lost to v3's global name-variant guard. The 18 alternate-source positions are newly accepted relative to both checkpoints.
- Relative to v4: 33 gains (18 new plus the 15 retained v3 gains), 470 withheld positions (448 unresolved name-variant positions, 21 DOI disagreements and one raw-name incompatibility), and zero retained-position reassignment.
- No new cross-provider merge or provider split is made. The previous paper-specific raw-ORCID mechanisms remain; no observed-array ORCID is converted into paper ownership.
- The seven DOI cases remain ambiguous. No corrected work snapshot or source-corrected graph is fabricated. Construction aliases are evidence, not independent ground truth.

## Three-way measured comparison

All positions use the same **65,469 matched / 65,507 official** denominator. Researchers and edges are graph censuses, not sample estimates. Collaboration component/isolates denominators are the researcher count in the same column. Largest-component fractions use that denominator.

| Measurement | Frozen v4 | Candidate-v3 | Revised candidate |
| --- | ---: | ---: | ---: |
| Resolved researchers | 32,189 | 32,023 | 32,077 |
| Accepted authorships | 50,437 | 49,747 | 50,000 |
| Authorship coverage / matched positions | 77.04% | 75.99% | 76.37% |
| Affiliated positions | 48,259 | 47,586 | 47,833 |
| Affiliation coverage / matched positions | 73.71% | 72.68% | 73.06% |
| Affiliation coverage / official positions | 73.67% | 72.64% | 73.02% |
| Affiliated / accepted positions | 95.68% | 95.66% | 95.67% |
| Affiliation ceiling / matched positions | 77.04% | 75.99% | 76.37% |
| Total nodes | 47,875 | 47,704 | 47,758 |
| Total edges | 225,731 | 222,599 | 223,730 |
| Coauthorship pairs | 80,482 | 78,694 | 79,389 |
| Collaboration components | 2,936 | 3,069 | 3,032 |
| Researcher isolates | 414 | 452 | 440 |
| Largest researcher component | 20,776 (64.54%) | 20,191 (63.05%) | 20,414 (63.64%) |

Affiliation support improves **247/65,469 = 0.3773 percentage points** over v3, while remaining below frozen v4. This comes entirely from accepting supported identity positions, with the original institution mapping/copy guard. Retained-position organization sets are identical; no Task3 affiliation repair is included.

### Relationship and ranking changes

Compared with v3, the revision gains 695 coauthorship pairs, 46 organization collaboration pairs, 51 researcher-topic aggregates and one organization-topic aggregate. There are no lost relation keys. Eighty-five new researcher–organization aggregate edges reflect the recovered paper triples; support counts/weights can also change on retained aggregates. All four derived predicates are rebuilt using the existing materializer.

All 49,747 retained AUTHORED edges receive new decision IDs/method provenance. The comparison counts these property changes; they are not 49,747 new or reassigned scientific relationships. Citation (7,308), topic prediction (14,222), publication (13,617) and taxonomy (16) claims remain exact apart from graph-version tags. Protected paper/venue/topic metadata and original nonderived evidence are hash-checked; enumerated authorless-paper reasons may change. New external/alternate identity evidence is additive.

The same 256 common-node pivots and inverse positive fractional-weight distances are used for all three checkpoints. Revised versus v3 top-20 overlaps are degree **19/20**, strength **17/20**, betweenness **18/20**; Spearman correlations over 32,023 common researchers are .998270, .995693 and .995383. Versus frozen v4 they are 20/20, 19/20 and 12/20; correlations .996763, .988938 and .993427. These are paired descriptive approximations, conditional on the pivot set, not semantic correctness or reproduction of the historical release ranking. Full ranks/scores and support deltas are linked below.

## What remains unresolved

- **15,507/65,507 official positions** remain outside the canonical graph: 9,206 ambiguous and 6,301 unresolved (including 38 positions on unmatched works). See exact reason counts and venue/year denominators in the comparison JSON.
- Of the 170 targeted IDs / 683 positions, **128 IDs / 448 positions** still lack adequate name-variant corroboration. Classification distinguishes observed name patterns from proven causes; 20 prioritized IDs received new public ORCID review, all 170 received cached inventory.
- All 4,492 historically ORCID-conflicting provider IDs retain their global ambiguity. The preexisting single raw-ORCID recovery is not extrapolated to other papers. New recovery does not solve this dominant population.
- Of the original **6,285 matched positions missing IDs**, 19 now resolve (18 new alternate-source plus one prior raw-ORCID case); 6,263 remain unresolved and three ambiguous (two raw-name mismatches, one raw-ORCID crosswalk collision).
- All seven DOI discrepancies / 21 positions remain ambiguous mixed-version records. Crossref establishes separate DOI registrations and matching bylines, not an explicit proceedings/journal identity or affiliation crosswalk.

## Independent evaluation

The frozen probability draws contain 200/65,507 official positions and 200/146,065 pairs in a declared provider/name blocked frame; 111 diagnostic positions are separate. Blinded evidence packets, A/B assignments, annotation rubric, adjudication requirements, inverse-probability scoring and paired bootstrap are implemented. References and decisions remain separate from construction evidence. Outside-block pairwise recall is not estimable from this design.

The actual three-way scorer was executed with **zero independent adjudicated references** and correctly returned null semantic precision, recall, F1, true false merge/split rates and confidence intervals. No humans or independent gold labels are fabricated; no AI semantic votes substitute for gold. The synthetic scoring tests only validate implementation. Historical edge-audit labels were not reused. New ORCID/Crossref evidence used in development cannot become an untouched evaluation set.

Coverage and source availability improved. **Whether identity precision improved: unknown. Whether identity recall improved: unknown.** Declared aliases and exact-DOI alternate records provide new construction support, but provider/ORCID ownership, undetected overmerges and false splits still require independent references. The increased accepted count is not a measured recall estimate. Selective coverage policies and null precision columns are supplied; confidence intervals remain unavailable without valid references.

## Recommendation and Task3 dependency

Use this as the next evidence-supported **development** candidate while preserving candidate-v3. **Do not promote it as an independently validated replacement** for v3 or frozen v4: a better semantic precision/recall tradeoff has not been demonstrated. There is no scientific basis to claim a quality threshold passed merely because more positions resolve.

The Task3 interface is technically ready (paper-specific triples, exclusions, explicit unresolved mentions and evidence), but the **80% end-to-end affiliation target is not feasible** with this identity population: even 50,000/65,469 affiliated positions would be only **76.37%**. At least 52,376 accepted positions would be needed at this denominator, 2,376 more than currently accepted, even assuming perfect affiliation availability. This is a dependency calculation, not a recovery target or reason to relax identity evidence. Task3 can be investigated separately after authorization; this candidate is not ready for a target-compliant promoted Task3 baseline. No Task3 work was started.

## Deliverables and validation

- [DOI reconciliation](doi-reconciliation.md) and [seven-case ledger](investigation/doi-ledger.json).
- [Abstention analysis](identity-abstention-analysis.md), [170-ID CSV](investigation/provider-classification.csv), [evidence inventory](investigation/provider-ledger.json), [paper-specific context](investigation/provider-context.json).
- [Evaluation protocol](evaluation-protocol.md), [sample freeze](evaluation/freeze.json), [actual null scoring results](comparison-final/semantic-evaluation.json).
- [Final graph manifest](candidate-v4-final/candidate-manifest.json), [v4 comparison](candidate-v4-final/comparison.json), [v3 comparison](comparison-final/versus-candidate-v3.json), [three-way summary](comparison-final/comparison-summary.json), [rankings](comparison-final/three-way-rankings.json), [253 recovered positions](comparison-final/recovered-versus-v3.jsonl).
- [Validation report](validation-report.md), [hash/replay/preservation receipt](validation-receipt.json), [reproduction and artifact inventory](README.md).

Focused suite: **115 passed**. Full suite: **603 passed, one existing skip**. Structural CLI: zero errors, all size checks pass, derived support/weights validated. Original source objects and added public evidence are hash-checked. Final replay verifies deterministic outputs and protected file preservation; exact outcomes are in the receipt. Neo4j integration was not run because no load/query/service code changed; no infrastructure was altered.

# Targeted ten-relation audit — AI assessment only

Graph `release-d3c788c3114a`, unchanged frozen v4. Sample method
`sprint-relation-audit-release-v1`, seed `2026111107`: eight accepted edges per
relation, deterministic hash-ranked draw using the existing sampling helper.
The new sprint draw is supplemental and does not replace the historical global
200-edge release audit or certify the course accuracy requirement.

| Relation | Population | Inclusion probability | Supported | Unsupported | Unknown | Conditional Wilson 95% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AFFILIATED_WITH | 38,664 | 0.00020691 | 8/8 | 0 | 0 | 67.6–100.0% |
| AUTHORED | 50,437 | 0.00015861 | 7/8 | 0 | 1 | 52.9–97.8% |
| CITES | 7,308 | 0.00109469 | 8/8 | 0 | 0 | 67.6–100.0% |
| COAUTHORED_WITH | 80,482 | 0.00009940 | 8/8 | 0 | 0 | 67.6–100.0% |
| COLLABORATED_WITH | 13,031 | 0.00061392 | 8/8 | 0 | 0 | 67.6–100.0% |
| CONTRIBUTES_TO_TOPIC | 2,332 | 0.00343053 | 7/8 | 1 | 0 | 52.9–97.8% |
| HAS_TOPIC | 14,222 | 0.00056251 | 8/8 | 0 | 0 | 67.6–100.0% |
| PUBLISHED_IN | 13,617 | 0.00058750 | 8/8 | 0 | 0 | 67.6–100.0% |
| RESEARCHES_TOPIC | 5,622 | 0.00142298 | 6/8 | 2 | 0 | 40.9–92.9% |
| SUBTOPIC_OF | 16 | 0.50000000 | 8/8 | 0 | 0 | 67.6–100.0% |

Each denominator is eight, including unknowns as nonsupport. Wilson intervals
are descriptive sampling approximations conditional on AI judgments, without
finite-population correction; the taxonomy sample covers half its frame. No
multiplicity adjustment. These very small strata cannot establish high precision.
No raw pooling, overall graph accuracy estimate or population-weighted claim is
made. The hash-permutation recipe assumes pseudorandom sampling within relation.

Two separate fresh contexts, `/root/luna_edges_1` and `/root/luna_edges_2`,
reviewed disjoint 40-case packets, requested model `gpt-6-luna`, reasoning `high`.
Actual output attribution uses these supported environment identifiers. Provider
build/version, temperature and underlying request IDs were not exposed. No overlap
or inter-rater agreement is estimated. Fresh contexts do not establish statistical
independence; both use OpenAlex/official construction caches. Human validation:
**not performed**. Reviewer independence: **not established**.

Reviewers checked relation semantics against positional authorship, paper-specific
institutions, accepted base support, citation target IDs and frozen taxonomy.
Topic support was interpreted from full titles/abstracts. Each derived packet
shows up to three paper witnesses and declares its full support count. This checks
bounded semantic witnesses, not every support paper, derived weight or researcher
identity. Existing structural validation separately recomputes support and weights.
The initial extractor omitted abstracts because it looked for an inverted-index
field; a hash-bound plain-abstract supplement was supplied to all reviewers before
final judgments. The frozen sample did not change. Replay preparation now directly
includes the original work records and their plain abstracts.

## Flagged cases and coordinator disposition

- `edge:b8ad1484fd0d7a0fb87280461e102431358e8cff5157ccb90323457ef2052e43` (RESEARCHES_TOPIC, **unsupported**): Both support witnesses are present: paper:aaai:2021:16100 contributes an early-stopping MCTS method for NoGo/AlphaZero, with RL only as application context; paper:aaai:2024:29154 substantively studies PPO-Clip. Of the total two support papers, only one meets the RL topic rule.
- `edge:cc8efc4bdc585fe23bd723a4bb5b30395ef2efe664366ba82d4330631e24113e` (AUTHORED, **unknown**): The official byline gives Kairong Yu at position 1, while the matched OpenAlex authorship at that position is named Ke Yu; no evidence in the packet resolves this name mismatch.
- `edge:26b2191684c60e3b1bd58b1f690620b61168c2d3eb5020f4a89bd6482a685db6` (RESEARCHES_TOPIC, **unsupported**): Only one of the two distinct-paper supports substantively fits Representation learning: PointRWKV develops hierarchical point-cloud feature learning, while Density Matters selects samples using an existing feature space and does not claim to learn transferable or structured representations; R9 therefore falls below two papers.
- `edge:6e05724228b61bdc1ae5bf917cc0937bc6cfd6296ea8e24eaba915368d25d857` (CONTRIBUTES_TO_TOPIC, **unsupported**): The three supplied papers include only two substantive Efficient machine learning systems contributions: EG-NAS addresses low-cost search and FedET reduces communication cost, while Curriculum-Meta Learning addresses order robustness and relation representations without a computation, memory or systems-efficiency contribution. The R10 threshold of three is not met.

The coordinator reread all four flagged packets and full paper abstracts. The
three topic challenges each have complete two- or three-paper witness sets; they
are AI semantic disagreements with frozen inferred labels, not materializer bugs.
The authorship's raw name **Kairong Yu** matches the official byline, but its
canonical provider display name is **Ke Yu**. This is unresolved identity evidence,
not a proven incorrect author and not a reason to merge or rename researchers.
All raw judgments are preserved. No post-review graph or classifier repair occurred.
These exposed examples are future development diagnostics, never a new untouched test.

## Optional human packet

Each member receives their own `human-member-{1,2}.html` plus matching CSV. Both
forms retain the same prespecified 20-case pseudorandom draw and six risk
diagnostics, and add all four IDs from the issue ledger. Three flagged cases
overlap the random subset, producing 27 unique cards; overlapping tags remain
visible. Only IDs carrying the `random` tag have probability-based inclusion. The
conditional probability stays 20/80; marginal population probability for a random
case is `(8 / relation population) * (20/80)`. Risk and diagnostic-only flagged
cases are not a probability sample and must not enter the random estimator. Do not
pool relation strata unweighted.

The form groups the flagged cases in a dedicated section and provides their source
evidence without showing Luna's concern. Separate member-specific post-blind HTML
views contain the concerns and source locators; reviewers should export their
initial decisions before opening those pages. The form retains `correct`,
`incorrect`, `unverifiable`. Its rubric distinguishes source consistency from
independent semantic verification; official byline/provider-ID alignment alone
does not establish researcher identity, and derived claims inherit input identity
uncertainty. See the [rubric amendment](review-protocol.md#optional-human-packet-rubric-and-allocation-amendment).
Export original CSVs separately before comparing answers. Member labels do not
fabricate identities or participation. Human metrics remain unavailable until
actual submissions exist; no completed human annotations were produced.

# V5 identity audit and candidate implementation report

Completed 11 November 2026. Implementation checkpoint: `18f98d0`.
Final candidate: **`release-identity-v5-7e6b1a34ffa2`**, an isolated development
candidate. It is not a final v5 release or a replacement for frozen v4.

## Executive findings

The audit confirms the current builder's dictionary/string state bug and fixes
it for future builds. Frozen v4 was produced through a different historical path
and shows no accepted conflicting provider IDs. The cached dataset has severe
identifier missingness and little paper-specific ORCID evidence. An evidence-aware
resolver recovers 15 positions while quarantining 705 previously accepted positions.
It preserves explicit unresolved mentions and source contradictions rather than
increasing graph size at the expense of evidence.

This implements a stricter, more explainable policy. **Improved semantic precision
or recall has not been measured.** No independent identity references exist here.
The candidate has lower coverage, and the new abstentions may include valid aliases.
Historical AI edge precision does not transfer to this candidate.

## Task 1: established baseline

The [baseline audit](baseline-audit.md), [machine census](baseline-audit.json),
[issue inventory](issue-inventory.csv), and [identity analysis](identity-error-analysis.md)
were committed as `bc783e8` before resolver implementation. The later additive
[pipeline inventory](pipeline-inventory-v1.json) supplies exact historical guard
counts, DOI anomalies with source locators, and topic/citation venue-year summaries.

- All 13,606 matched works' retained authorship/reference arrays equal 341 original
  hash-verified cached responses. Source equality is not source correctness.
- The [official input binding](official-input-bindings-v1.json) confirms the frozen
  roster hash and every retained byline/title/source field and derived DOI against
  the existing works rows. This is a copy-consistency check, not a new roster audit
  or independent validation of the official parser.
- 6,285 matched positions have no provider author ID. Of 15,032 absent v4 positions,
  primary reasons are 8,722 ORCID conflicts, 6,283 missing IDs, and 27 byline rejects.
- All 4,492 conflicting IDs repeat their observed ORCID set across works; none
  changes its selected singular ORCID. Only one conflicting position has a paper
  raw ORCID. The arrays cannot establish paper-specific identities or true splits.
- Seven returned work DOIs differ from their official requested DOIs, affecting
  21 positions. The singleton retry path lacks the batch path's DOI check. These
  could be provider version merges; they are not seven proven false matches.
- Original copy guard: 147 papers / 609 positions before correction. Exactly
  525 surviving v4 positions have source institutions but no affiliation triples;
  all 525 are explained by that original guard. The earlier baseline's 146/560
  figure is a different, explicitly labeled surviving-team pattern diagnostic.
- No unsupported source-institution triples, accepted conflicting provider
  positions, provider/position disagreements, or source-filtered core citation
  inventory differences were found. These are source-consistency checks.
- Institution metadata is internally stable across all 2,153 source IDs; all
  74,485 assignments have ROR and mapped strings. This does not verify institution
  identity, historical affiliation correctness, or organizational hierarchy.

The shadowing bug triggers after either a multi-name rejection or repeated usable
ID. A subsequent matched paper checks IDs against a reason string and bypasses
global withholding. Both paths have cross-paper regression tests. Builder method
is now `release-openalex-graph-v1.3`; the historical correction's method and shared
ORCID collector remain unchanged. No frozen build was regenerated with this code.

## Task 2: resolution strategy

[mentions_v5.py](../../src/scientific_network/resolve/mentions_v5.py) writes one
decision for each of the 65,507 official mentions, including papers without an
accepted work match. It uses the same complete-source ORCID collector as the
builder and v4 correction, then adds paper-specific evidence and consistency checks.
There are no identity decisions hidden inside graph-count adjustments.

1. Require accepted work status, valid work identifier, matching DOI, title
   similarity at least the unchanged .9 threshold, and byline count agreement.
2. Compare official and paper raw names at the same position. Unicode, diacritics,
   hyphens and token-order normalization support equivalent representations.
   Initials require equal token counts, a full-token anchor and unique alignment.
   Alternate full spellings are not fuzzily merged or guessed.
3. A nonconflicting provider ID plus supported raw position may resolve without
   ORCID, as allowed by the release standard. Incompatible names across publications
   quarantine the provider ID; the algorithm does not split it by names.
4. Profile ORCID conflicts remain global ambiguity. A direct checksum-valid paper
   raw ORCID with compatible names may independently anchor one position. The
   conflicted provider ID supplies no canonical person ID for that recovery.
5. A raw ORCID may crosswalk multiple provider IDs only through direct paper
   observations and compatible names, with collision checks. A different existing
   identity's profile-only ORCID claim requires review. Neither profile arrays
   nor coauthor/affiliation similarity create crosswalks.
6. Multiple raw ORCIDs with compatible names on one provider ID remain ambiguous:
   accounts do not prove distinct people. Separate raw identifiers and incompatible
   independently aligned bylines can support separate identities. No such actual
   split was made in this corpus.
7. Repeated provider/canonical positions, missing or malformed identifiers,
   incompatible names and ambiguous alignments stay outside the canonical graph.
   Unique exact raw positions may recover beside other bad positions; the resolver
   never guesses a byline permutation.

The middle-name expansion exception requires direct paper raw ORCID, unchanged
full tokens in order, identical endpoints, and canonical/official name agreement.
It supports the one source conflict/raw case described in the identity analysis.
It does not recover other papers on that provider ID or independently verify
ownership of the ORCID account.

Each deterministic decision includes mention/decision IDs, paper and position,
provider/work IDs, canonical ID or null, state, method, reason, source URLs,
timestamps, hashes, exact authorship locators, raw/profile ORCID observations,
contradictions and review requirements. A separate index retains the shared
collector's complete provenance and additional name/crosswalk conflicts.
Ordering and IDs depend on evidence and method, not output directory or run time.

## Candidate materialization and preserved components

[candidate_v5.py](../../src/scientific_network/resolve/candidate_v5.py) consumes
the frozen v4 graph and original works. It verifies input/freeze/audit hashes and
original cache bytes, rebuilds R1/R2 and affiliation triples, then calls the existing
materializer for R7–R10. No model inference, topic tuning, citation rematching,
corpus expansion or database import occurs.

For every retained position, its exact original organization set and exclusions
are preserved. Only newly accepted positions may add affiliations from their
cached authorship mappings, subject to copy guards. Unchanged R2 aggregates are
reused. An assertion checks all 49,732 retained positions; no affiliation repair
is bundled into this phase.

Canonical hashes prove unchanged publication, citation, taxonomy and topic edges,
non-derived source evidence, and protected paper/venue/topic metadata. The only
paper exceptions are 25 enumerated unresolved-reason changes: four recovered
previously authorless papers lose a stale reason; 21 newly authorless papers gain
one. Frozen topic labels, scores, excerpts and evidence remain unchanged.

Initial candidate-v1 exposed a materialization attribution problem: rechecking the
full-source copy guard changed existing affiliation support. It remains a diagnostic
under source commit `dfaa01b`. Candidate-v2 (`a3d4dd8`) fixed that. The final v3
adds the multiple-account ambiguity regression; its real identity counts equal v2.
All prior candidate artifacts are preserved. No numeric quality threshold was
loosened or tuned to raise a score.

## Before/after: v4 versus final identity candidate

Counts are from [comparison.json](candidate-v3/comparison.json); denominators and
rates are in [quality-summary.json](candidate-v3/quality-summary.json).

| Measurement | Frozen v4 | Final candidate |
| --- | ---: | ---: |
| Core papers | 13,617 | 13,617 |
| Nodes | 47,875 | 47,704 |
| Resolved researchers | 32,189 | 32,023 |
| Total edges | 225,731 | 222,599 |
| Unique factual R1–R4 edges | 110,026 | 109,071 |
| Accepted positions / 65,469 matched positions | 50,437 (77.04%) | 49,747 (75.99%) |
| Affiliated positions / 65,469 matched positions | 48,259 (73.71%) | 47,586 (72.68%) |
| Author–paper–organization triples | 56,273 | 55,489 |
| Coauthorship pairs | 80,482 | 78,694 |
| Organization collaboration pairs | 13,031 | 12,797 |
| Researcher components | 2,936 | 3,069 |
| Researcher isolates | 414 | 452 |
| Largest researcher component | 20,776 | 20,191 |

The 15 gained positions consist of 13 byline-policy recoveries and two raw-ORCID
recoveries. Of the latter, one had no provider ID and one was globally withheld
for ORCID conflict. The [recovery ledger](candidate-v3/recovered-authorships.csv)
binds each case to its decision and exact cached source locator. Recovery of the
historically removed population is **1/8,722 = .0115%**. Across all matched source
positions with conflicting provider IDs, one resolves and 8,726 remain withheld;
five of those source positions were already absent before the v4 correction.
An additional unmatched official position shares a conflicting ID; it is outside
the matched denominator and remains unresolved.

Of 705 lost positions, 683 are on 170 previously represented IDs with incompatible
name variants, 21 are on DOI-disagreement works, and one lacks compatible raw-name
support. Those three effects are reported separately. They are stricter evidence
decisions, not independently verified corrections of 705 false authorships.
There are eight gained and 174 lost canonical researcher nodes, zero reassigned
retained positions, zero actual corroborated provider merges and zero actual splits.

The final ledger has **49,747 resolved, 9,441 ambiguous and 6,319 unresolved**
mentions. These sum to all 65,507 official positions. Of 6,319 unresolved mentions,
38 belong to the 11 unmatched papers; 6,281 lack provider ID or usable paper raw
ORCID. Ambiguity counts and all ten venue/year strata are in the comparison JSON.
Acceptance is neither authorship precision nor recall.

R7 gains 18 and loses 1,806 pairs. R8 loses 234 pairs; R9 loses 145 researcher-topic
edges; R10 gains one and loses 11 organization-topic edges. Their support and
weights are recomputed, not manually adjusted. Affiliation triples gain 13 and
lose 797 solely through changed positions. Conditional affiliation support is
47,586/49,747 = 95.66%; this does not rescue the failed overall 80% coverage target.

## Centrality and scientific limitations

[Paired network diagnostics](candidate-v3/network-comparison.json) use identical
256 SHA256-ranked common-node pivots, seed 20261101, all nodes as targets, and
inverse positive fractional strength for weighted paths. This controls pivot
selection between the graphs. It is a descriptive sensitivity calculation
conditional on surviving common pivots, not a new unbiased centrality study or a
reproduction of the historical v4 approximate scores.

Top-20 overlap: degree 19/20, strength 16/20, betweenness 11/20. Spearman correlations
on common nodes are .99544, .98546 and .98965 respectively. High overall correlation
coexists with meaningful changes in the bridge shortlist. Neither rank is a
verified real-world influence measure.

Researcher pairwise precision/recall/F1, authorship acceptance precision/recall,
and true false-merge/split counts are **null**, not zero. Tests prove specified
synthetic behavior; source conformance proves consistency with construction
evidence. Neither provides independent semantic truth. Valid aliases may be
quarantined, same-name conflations may remain undetected, provider/raw ORCIDs may
be wrong, and source affiliation/citation errors remain possible. No independent
gold, human validation or verified course accuracy is claimed. Historical
193/200 AI edge precision applies only to frozen v4 and was not reused as labels.

## Remaining work and Task 3 readiness

1. Review the seven DOI disagreements and legacy singleton acceptance before
   future enrichment. Candidate identity claims abstain; protected historical
   citation/topic claims on these works were deliberately not rewritten here.
2. Obtain independently supported identity crosswalks for missing/conflicting IDs
   and name variants. Reserve new references prospectively before future tuning.
   Avoid counting this exposed development population as independent test gold.
3. Task 3 can consume the exact paper triples, preserved exclusion ledger, 525
   historical copy-guard positions, and explicit identity states. Keep unresolved
   mentions outside canonical collaboration; do not loosen affiliations to recover
   identity-related coverage. No Task 3 implementation was performed.
4. Independent semantic evaluation is needed before candidate promotion. The
   candidate reduces coverage and does not demonstrate improved measured accuracy.
   Existing topic-quality and affiliation-coverage failures remain visible.

No push, deployment, public Explorer change, external collection or Neo4j write.
Detailed [validation](validation-report.md), [reproduction commands](README.md)
and [artifact inventory](artifact-inventory.md) complete this handoff.

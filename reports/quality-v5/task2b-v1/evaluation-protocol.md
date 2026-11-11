# Prospective identity evaluation protocol v1

Frozen draw: [evaluation/freeze.json](evaluation/freeze.json), seed 2026111104.
Sampling occurred before recovery implementation and external evidence review.
No independently adjudicated identity references were available or created in this
session. All semantic precision, recall, F1, true merge/split rates and their
intervals remain unavailable. Historical AI edge labels are not reused.

## Frames and estimands

The assignment frame contains all 65,507 official byline positions, including
unmatched papers and abstentions. A simple random sample without replacement of
200 has inclusion probability 200/65,507 per position. Assignment precision is
correct accepted assignments / accepted sampled assignments; identity recall is
correct accepted assignments / sampled positions with an independently established
reference identity. Report both denominators and the count with unknown reference.
Coverage is accepted / all sampled positions. Correct rejection requires affirmative
evidence of an invalid identity claim, not simply absence of sufficient evidence.
Unverifiable references remain unknown; do not turn them into negative identities.

The pair frame is the **union**, deduplicated, of all unordered pairs sharing a
provider ID or the existing exact normalized-name block. It contains 146,065 pairs;
a separate SRSWOR of 200 has probability 200/146,065. Include accepted and rejected
mentions. Pairwise precision/recall/F1 and false merge/split estimates apply **only
to this blocked frame**. Outside-block aliases and splits are not sampled, so no
global pairwise recall is identifiable. Name blocking creates the evaluation frame,
never an identity acceptance rule. Pairwise false splits include a same-person pair
not joined by the candidate, including either-endpoint abstention; report these
separately from two accepted canonical IDs when references eventually exist.

The 111 diagnostic positions are separate, up to 30 sampled per prior name-variant,
ORCID-conflict, missing-provider and DOI-disagreement category (21-position DOI
census). Category precedence and population sizes are in the frozen JSONL. They
are not pooled into the population estimator; their unit probabilities apply only
to their category frames. Common names, provider splits and overmerges are also
represented by pair blocking; evidence packets can document secondary risk tags.
No resampling or threshold search is permitted after reference review.

## References, reviewers and evidence packets

`evidence-packets.jsonl` includes official byline positions and construction-source
locators/hashes. Predictions and acceptance states are omitted. These are starting
packets, not independent evidence or gold. Public ORCID declarations and duplicate
OpenAlex responses used for recovery are construction evidence and cannot become
independent test references merely because they came from another endpoint.

`blank-reviewer-assignments.jsonl` allocates every unique selected unit to A and B.
No reviewers have been impersonated and all labels are blank. Human reviewers are
optional: source-backed agent assessments may be stored separately as AI-assessed,
with actual model/run and isolation metadata, but cannot satisfy the independent
reference gate. No agent review scores are substituted for missing gold here.

Reviewers must work independently without seeing candidate predictions, development
certificates or each other's labels. Obtain paper-specific authoritative evidence
(e.g. printed byline identifiers, publisher-linked researcher record, a signed
academic publication list with persistent paper IDs). Record URL, timestamp, hash,
exact locator, claim, source owner and whether it shares upstream construction data.
Names, current institution and coauthors alone do not prove equivalence. Conflicting
ORCID accounts do not prove distinct people. Absence of a public ORCID work does
not prove non-authorship. Preserve contrary evidence and unknown cases.

Pair labels are `same`, `different`, or unknown. Assignment labels are `identity`
(with a reference identity and independently justified `accepted_canonical_ids`
crosswalk) or `unresolvable` only with affirmative evidence. Each reviewer records
justification, evidence and independence. An independent adjudicator resolves
conflicts without tuning the resolver; unresolved disagreement remains unknown.
Bind adjudicated files to this frozen manifest and retain both original reviews.

## Deterministic scoring

`scientific_network.quality.identity_evaluation.score` refuses incomplete, AI-only,
non-adjudicated or unevidenced references. It reports null semantic metrics rather
than a complete-case estimate with unknown selection bias. `paired_score` applies
the same references/units to all graph checkpoints, computes inverse-probability
ratio estimates, and offers a deterministic paired SRS percentile bootstrap for
precision/recall/F1 differences. No Wilson interval is applied to weighted totals.
Bootstrap intervals omit finite-population correction and reference/evaluator error;
valid replicate counts are disclosed, especially when positive denominators vanish.

Candidate predictions are canonical IDs (or null), with pair acceptance true only
when both mentions have the same non-null canonical ID. Use the same frame for v4,
v3 and revised graphs. Diagnostic strata remain separate. Selective precision uses
explicit method strata (`baseline`, formatting, declared alias, alternate-source),
not fabricated confidence probabilities: recompute coverage and precision of each
nested predeclared policy subset from the same labeled assignment sample. Report
all denominators, missing-reference counts and paired intervals. This session
executes the missing-reference path; synthetic scorer tests are not measured results.

No final independent reference labels were consulted during development. Construction
metadata was inspected across the corpus, so this is a prospective reference study,
not a claim that its papers or provider records were unseen. A future adjudication
must additionally disclose overlap with exposed historical audit papers/sources.

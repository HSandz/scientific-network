# Evaluation scope and limitations — agent release v1

```text
evaluation_kind: ai_agent_review
human_validation: not_performed
reviewer_independence: not_established
verified_course_accuracy: not_established
numeric_gate_scope: ai_assessed_only
```

The evaluation freeze predates all judgments. A/B are separate fresh contexts,
without inherited coordinator conversation or shared answers. Both blind topic
exports were completed and hash-frozen before either context opened edge packets.
This is context isolation, not evidence of statistical independence, different
models, human validation or independently validated gold labels. Precise runtime
provider/model/version and sampling settings were not exposed and remain unknown.
Run IDs, context identities, actual timezone timestamps and sources are recorded.

All 60 topic assignments cover the frozen 50-paper test set; none is unreviewable.
A considered empty topic set remains a reviewed judgment. The 10 overlapping
papers retain both answers, each with weight one half. Exclusive papers have
weight one, giving total effective weight 50. Agreement is measured on the actual
overlap only. The phrase baseline and frozen embedding classifier use the same
AI-assigned references. Their precision/recall/F1 describe agreement with those
references, not human gold accuracy. Neither classifier was tuned or rerun from
these results. The restricted 16-leaf taxonomy and evaluator interpretation can
limit both reference completeness and model agreement.

Title/abstract evidence for every topic judgment is reconstructed OpenAlex text,
classified secondary_source_only and same_source_as_construction. Re-reading
OpenAlex can assess extraction from that snapshot; it is not independent
corroboration of the source's correctness. Original PDFs were not required under
D040. The edge ledgers distinguish primary, secondary-only, internal-only and
unavailable main evidence. Normative taxonomy checks against the frozen config
are primary evidence for the curated hierarchy; they do not independently
corroborate observed scientific claims. Additional sources, when actually read,
remain recorded separately. Main-evidence counts describe assignment rows, not
unique independent sources or a census of paper evidence.

Identity review distinguishes a compatible stable ID on a sampled work from a
full author-profile merge-history investigation. Historical affiliations use the
paper-specific author/institution/raw-string mapping, never current employment.
Citations sourced only from OpenAlex remain same-source reference checks. Derived
edge review inspects the distinct-paper/author supports required by its relation;
this does not independently audit every historical support or every weight.
The structural validator separately recomputes support/weights and does not
establish semantic source accuracy. Inaccessible/internal-only edge evidence is
unverifiable and counted as incorrect. Incorrect/unverifiable verdicts and all
initial overlap disagreements are retained; the graph remains unchanged.

The global uniform sample and relation-specific supplements are separate. Do not
pool supplement rows into the global precision estimate, or treat overlap rows
as independent additional sampled edges. Wilson 95% intervals describe sampling
uncertainty conditional on these judgments; they exclude evaluator mistakes,
shared-model/source bias and correlated errors. Small per-type samples have wide
intervals. Numeric course/project comparisons are explicitly AI-assessed; a
passing comparison cannot establish verified course accuracy or lecturer acceptance
of AI-only evaluation. Failed checks remain reported results.

The graph covers two conference series, with unresolved work/author coverage and
source limitations documented in the report. The audit is a sample of accepted
edges: it does not measure omitted-edge recall or validate all source records.
Topic-dependent business findings remain conditional on inferred labels and the
measured agreement, while bridge rankings also show support-filter sensitivity.
Real team identities, student IDs, actual human contributions, lecturer access and
course-specific AI-use rules remain pending when unavailable in supplied records.
No external delivery follows automatically from local scoring or packaging.

## Measured outcome

Global AI-assessed precision is 176/200 (88%), Wilson 95% 82.7657%–91.8020%:
23 incorrect and one unverifiable, no missing assignments. All frozen edge
precision gates fail. Overlap agreement is 39/50 (78%), kappa .1851851852.
Main evidence is primary for 123 and secondary-only for 227 assignment rows;
349 reuse construction sources and only one has an independent main source.
All 11 actual overlap conflicts were source-adjudicated with original votes kept.

Embedding topic micro F1 is .46666667 at 90% test coverage; phrase micro F1 is
.23008850 at 26% coverage. There are no unreviewable references; one reviewed
exclusive paper has a considered empty leaf set. Topic overlap agreement 10/10
is conditional on common sources/rubric and cannot demonstrate independence.

The resolver reads singular `author.orcid` but ignores retained multiple
`author.observed_orcids` values. The same array was absent from the projected
source packet, though raw/full works preserve it. The source-bound conflict
inventory and `docs/post-audit-findings.md` document this omission. No graph
correction or claim about the complete error population follows from these
sampled findings; this frozen graph and its failed results remain preserved.

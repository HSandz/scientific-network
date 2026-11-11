# Candidate decision — defer scientific promotion

**Retain Task2B `release-identity-v5-503aafe10a31` as the experimental development
foundation; retain frozen v4 in production.** Neither v5 candidate has demonstrated
scientifically superior identity accuracy. This decision is a documented continuation
of an experimental line, not an accuracy-based promotion or a claim that v4 is correct.
No production graph, Neo4j data, service, Explorer, classifier or corpus was changed.

| Decision factor | Evidence available | Implication |
| --- | --- | --- |
| Identity precision / recall / F1 | No independently adjudicated references | No candidate wins on measured quality |
| False merges / splits | Frame and scorer ready; semantic labels absent | Residual risk cannot be ranked quantitatively |
| Coverage | Task2B recovers 253 positions over v3 without losing/reassigning v3 positions; remains 437 below v4 | Useful engineering tradeoff, not demonstrated recall |
| Source quality | Bounded public paper/owner leads; crosswalks still pending | More evidence is available for review, not independent gold |
| Topology stability | Degree broadly stable; bridge top-20 membership sensitive | Avoid unqualified bridge/influence conclusions |
| Reproducibility | Bound immutable graphs/sample; deterministic workspace/scoring/reports | Appropriate isolated development input |
| Unresolved population | Explicit unresolved ledger and affiliation ceiling | Do not relax acceptance for target compliance |

Selecting v3 for lower accepted counts would not prove higher precision; selecting
v4 for more coverage would not prove higher recall. Promoting Task2B for more
construction evidence would also be unsupported. Keep all three for adjudicated
comparison. Current new sources do not justify a targeted resolver change; uncertain
ownership must be resolved before adding another recovery rule.

The next quality decision should use independently anchored authorship references,
completed candidate-person crosswalks, pair judgments inside the stated frame,
measured missingness, and paired uncertainty. Project targets do not replace these
identity estimands. If adjudication remains partial, report subset diagnostics and
keep promotion deferred. Any rule tuned after seeing these cases must declare that
exposure and obtain fresh untouched evaluation for a new independent claim.

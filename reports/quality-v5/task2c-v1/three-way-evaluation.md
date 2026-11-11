# Three-way identity evaluation

All three SHA-256-bound graphs were read in Task2C. Membership in the original
200-position assignment draw, 200-pair blocking-frame draw and 111 separate
diagnostics is unchanged. Exact graph versions/hashes are in
[checkpoint-bindings.json](checkpoint-bindings.json); scoring method and limitations
are in [evaluation-audit.md](evaluation-audit.md).

| Census measure | Frozen v4 | Candidate-v3 | Task2B candidate-v4 |
| --- | ---: | ---: | ---: |
| Accepted authorships | 50,437 | 49,747 | 50,000 |
| Official positions | 65,507 | 65,507 | 65,507 |
| Matched positions | 65,469 | 65,469 | 65,469 |
| Matched-position coverage | 77.04% | 75.99% | 76.37% |
| Official-position abstentions | 15,070 | 15,760 | 15,507 |
| Assignment probability sample | 200 | 200 | 200 |
| Blocked pair probability sample | 200 | 200 | 200 |
| Independent adjudicated references | 0 | 0 | 0 |
| Assignment precision / recall / F1 | null | null | null |
| Within-frame pair precision / recall / F1 | null | null | null |
| True false merge / split rates | null | null | null |
| Semantic confidence intervals / paired differences | null | null | null |

The evaluator was executed with an actually empty independent reference dataset.
All 511 review cases are pending, not reviewed-unknown or incorrect. No verified
subset metrics are available yet; the implementation will emit descriptive subset
results when genuine partial references arrive. Unknown or invalid references are
counted explicitly and never silently interpreted as negatives. The 111 diagnostic
units remain separate by their frozen categories. Recovered diagnostic evidence
cases do not enter population quality estimators by selection convenience.

The machine report includes all sample acceptance/coverage denominators, pair
prediction states, per-mechanism population counts and probability-sample presence.
Task2B's predeclared nested mechanism policies remain available in its preserved
comparison summary: v3; v3 plus formatting; plus aliases; plus alternate works.
Their precision values remain unavailable. Mechanism coverage changes are not
measured recall improvements. A small or empty mechanism subsample cannot support
an independent mechanism precision claim.

Future runs use the same references for all candidates. A wrong accepted identity
counts as FP and FN; a valid identity omitted everywhere still counts as FN.
Partially verified subsets yield descriptive paired differences only, with explicit
selection and missingness bias. Full references permit weighted frame estimates
and deterministic paired SRS bootstrap intervals. Outside-block identity pairs
remain unidentifiable even if all 200 sampled pairs are adjudicated. Complete-case
scores cannot certify the course accuracy requirement.

Source retrieval, byline confirmation and graph integrity are useful diagnostics;
none is a substitute for the independent person identity and crosswalk judgments.

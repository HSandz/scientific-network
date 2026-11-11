# Task2C evaluation framework audit

Inspected HEAD `ac5883e` (Task2B implementation `eab4dce`). This audit supersedes
the scorer limitations in Task2B without editing its frozen protocol, samples,
blank reviewer forms or historical results. No resolver thresholds were changed.

## Sampling and estimands

The assignment frame is every official byline position, including unmatched works
and candidate abstentions: 65,507 units. The frozen SRSWOR has 200 units, inclusion
probability 200/65,507. Precision is correct accepted assignments / accepted
assignments. Recall is correct accepted assignments / independently established
reference people at those positions, including people omitted by every candidate.
These are authorship-position estimates, not recall over unique real people.

The deduplicated pair frame is the union of same-provider-ID and exact normalized
name blocks: 146,065 unordered pairs, 200 SRSWOR units, probability 200/146,065.
Precision, recall, F1 and merge/split rates refer **only to this blocking frame**.
Outside-block false splits and global person-clustering recall are unidentified.
A pair is predicted positive only if both endpoints have the same non-null
canonical ID. Same-person pairs predicted negative include endpoint abstention
and two accepted different IDs; these prediction states are reported separately.

The 111 diagnostic positions have category precedence frozen by v3 decisions and
up to 30 units per category (21-case DOI census). They are not pooled with the
assignment or pair estimators. Their inclusion probabilities describe their own
frames only. Reordering input decisions reproduces the draw in regression tests;
the actual frozen draw is replayed and hashes compared in the validation receipt.

## Corrected implementation

| Finding | Correction |
| --- | --- |
| Zero TP with FP/FN returned null F1 | Compute `2TP/(2TP+FP+FN)`; zero is a valid result |
| Empty accepted-ID crosswalk invalidated a real person missing everywhere | Explicit `crosswalk_complete=true` permits an empty crosswalk and retains that person in recall |
| Missing references hid all verified-case information | Preserve population metrics as null; emit descriptive verified-subset metrics and paired differences without inferential intervals |
| Coverage used unweighted counts despite weighted ratio claims | Compute inclusion-weighted coverage; disclose full census denominators separately |
| Missing predictions/probabilities could evade checks with partial labels | Validate sampling and candidate predictions before reference completeness |
| Pair strings could be interpreted as booleans | Require actual boolean pair predictions; assignments are nonempty canonical ID or null |
| AI provenance could pass if mislabeled independent | Explicit AI kind fails reference gate; strict compiler separates AI assessments |
| Paired bootstrap accepted unequal-probability frames | Refuse unequal probabilities and mixed frames for SRS resampling |
| Marginal uncertainty absent; boundary bootstrap could collapse | Add candidate paired-bootstrap intervals and count-based conditional Wilson precision/recall intervals for equal-weight complete references; disclose bootstrap degeneracy |
| Original evidence packets contain provider IDs/ORCIDs | Preserve originals; generate separate blind bundles containing official paper context only |

A wrong accepted identity is both an FP and an FN when a valid person reference
exists. A correct affirmative abstention is TN, whereas an unnecessarily rejected
valid person is FN. An unknown reference is neither. Assignment `unresolvable`
requires affirmative evidence; missing identifiers, name mismatch or failed
retrieval alone never justify it.

Pair false merge rate is `FP/(TP+FP)` and false split rate is `FN/(TP+FN)`, with
explicit weighted totals and zero-denominator nulls. The former is a false-discovery
rate, not `FP/(FP+TN)`; neither is a population rate of erroneous researcher nodes.

## References and statistical limits

Independent references require actual separate reviewer A/B submissions, source
records, source independence rationale, original-file hashes and explicit consensus
or adjudication. No third reviewer is fabricated: the two teammates can document
consensus after freezing their independent answers. Disagreement can remain unknown.
The compiler rejects mixed reviewer files, duplicate/out-of-frame units, inconsistent
case labels, unsupported crosswalks and conflicting canonical-to-person crosswalks.
Human attribution cannot be authenticated by a local tool; the actual person must
supply their own judgment. AI adjudication is retained separately even if both
initial judgments are human.

Every accepted canonical ID in a crosswalk needs person-specific corroboration.
A provider label or repeated name is not a sufficient bridge. Empty crosswalks are
allowed only after considering all three candidates. Unknown mapping is not an
empty completed crosswalk: leave that case unknown. Positive pair judgments alone
do not establish an assignment crosswalk.

Complete frame references permit inverse-probability ratio estimates. The paired
bootstrap resamples the same units for every candidate, with deterministic seed,
valid replicate counts, and no finite-population correction. Conditional Wilson
marginal intervals use **actual unweighted counts**, never expanded weighted totals;
without FPC they are conservative approximations under this SRS design. F1 and
paired-difference percentile intervals can degenerate at boundaries and with rare
positives. A zero-width difference interval does not establish candidate equivalence.
No interval includes evaluator error, shared-source bias or an unmodeled reference
missingness process. With partial labels all population quality estimates and their
intervals remain null; verified-subset diagnostics disclose selection/missingness
bias even when inverse sampling weights are retained.

The 200 draws may be inadequate to distinguish rare errors or small differences.
A complete study still requires reporting positive denominators and effective
precision; no minimum power claim is made. Population coverage is directly measured
from graph ledgers and does not need semantic labels. No threshold selection,
resolver development, source-driven recovery or resampling follows reference review
in this task. Subsequent remediation must label these exposed cases as development
and cannot reuse them as fresh independent certification.

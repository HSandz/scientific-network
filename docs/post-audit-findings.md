# Frozen-graph audit findings — 9 November 2026

These findings describe the unchanged graph `release-9d4a6fb20f63`, assessed under
D040. They do not authorize a graph correction, new sample or threshold change.
The initial A/B judgments, evidence and adjudications remain in the versioned
agent evaluation package. Numeric outcomes are AI-assessed only.

## Conflicting identifier evidence ignored by the resolver

The raw source and `works.jsonl` retain `authorships[].author.observed_orcids`.
The resolver's first pass in `src/scientific_network/resolve/release.py` reads only
singular `author.orcid` across matched works. Multiple values in the separate
observed array therefore escape the D040 conflicting-ID withholding rule. The
resulting researcher endpoint and its derived edges can remain accepted despite
that evidence. This is an implementation/source-evidence omission, not evidence
that any named researcher actually has multiple identities.

For example, the Gradient Based Activations work W4283803512 has author
A5101407551 with one selected ORCID plus three distinct entries in
`author.observed_orcids`; the accepted graph node retains only the selected value.
The exact raw cache hash/array locator is in
`reports/release-v3/completed/A-orcid-conflict-provenance-v1.jsonl` and the
adjudication ledger. Reviewer A recorded 25 sampled edges with this issue and a
separate name mismatch; the supplemental inventory binds every claimed conflict
to actual source values. The coordinator independently read the raw observed
arrays in the nine overlap identity disputes before adjudicating them.

A coordinator check initially examined only singular `orcid` and did not reproduce
the lists. Reading the separate `observed_orcids` field corrected that incomplete
check; no unsupported-evidence accusation or graph modification followed. The
normalized source-presentation packet also omitted the array; original raw records
and full works remained available. This demonstrates why a projected packet or
same-source summary cannot replace full relevant source inspection. Initial
reviewer disagreements remain visible rather than being silently rewritten.

A future correction requires a separately versioned graph, preserved conflicting
observations, validation/reload and a new audit. Do not apply it to this frozen
graph after seeing its audit errors or reuse this audit as independent evidence
for a corrected version. No estimate of the complete graph-wide error population
is inferred from the targeted source inventory.

## Other sampled limitations

Source review also records incompatible given-name endpoints, insufficient
identity evidence, incorrect topic predicates and derived topic-support failures.
The exact cases and error categories remain in the completed ledgers and scored
results. The audit is not a census of all records or omitted-edge recall.

A sampled organization collaboration uses the official GEONet record
(`paper:aaai:2025:32924`), which is marked RETRACTED. The recorded byline and aligned
institutions support the historical collaboration predicate under the frozen
rubric; that verdict does not endorse the paper's scientific results. No new
retraction-exclusion policy or roster audit was introduced. Any later scope policy
change needs its own explicit decision and versioned analysis.

Topic interpretations can differ even with identical full abstracts and a frozen
leaf definition. Both blind topic references and initial edge disagreements are
retained. Report the actual AI agreement and failed checks, not a claim of human
validation, independent gold labels or verified course accuracy.

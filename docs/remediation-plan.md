# Plan after the agent-release review — 9 November 2026

Status: **proposed; planning only**. Basis: [WORK-007](work-log/2026-11-09-007-agent-release-review.md).
Read the current [status](status.md) and D040 [release plan](release-plan.md)
first. This is a bounded continuation of the existing release phases, not a new
readiness framework. Human annotation remains optional; agents perform feasible
implementation, source review, scoring, analysis and packaging.

The immediate next task is **step 1**. Steps 2–5 describe the recommended separate
correction release. This plan does not change the frozen graph or enact a D040
amendment. When that track is adopted, record the dated decision before execution:
permit a new graph/evaluator version for the confirmed implementation omission,
while retaining every old graph, audit, failed result and receipt. D040 currently
prohibits changing the frozen graph after its audit; no in-place correction is allowed.

## 1. Close the scorer validation gap first

Change `src/scientific_network/evaluation/agent_review.py` and
`tests/test_agent_review.py`. Require an explicit `labels` list on **every topic
ledger row**, including considered empty and unreviewable rows. Retain the
existing type, uniqueness, CSV agreement and unreviewable-empty checks. Apply
this topic requirement without imposing it on edge ledgers.

Add synthetic regressions for a missing key, wrong type and the reviewed/unreviewable
empty-set cases. Update the shared fixture to satisfy the actual frozen rubric;
do not weaken legacy scoring or rewrite real completed records.

**Acceptance:** `uv run pytest` and an offline CLI check pass. Re-run the documented
`score-agent-review` command into unused ignored paths; both real JSON outputs
must remain equal to the existing results. Its exit 1 for failed numeric gates
is expected. Commit this focused checkpoint locally. No graph rebuild is needed.

## 2. Correct ORCID conflict handling in a new graph version

Use `resolve/release.py`, `tests/test_release_graph.py`, the graph contracts and
`graph/materialize.py`. Collect the union of normalized valid singular `orcid`
and `observed_orcids` values per OpenAlex author ID across matched works. Deduplicate
equivalent values. Withhold the ID everywhere when that union has multiple values;
retain exact conflicting values and source locators/hashes in the review queue.
Missing ORCID alone remains acceptable. Do not merge people by name.

Test array-only conflicts, singular-versus-array conflicts, conflicts across papers,
equivalent duplicates, malformed/missing values, unaffected same-name people and
propagation through affiliations and derived support. Malformed input handling
must be explicit and conservative, never silently converted into identity evidence.
Bump the method version so corrected output cannot reuse the old graph identity.

Implement an explicit, versioned correction path from immutable works and the
frozen v3 graph. The implementation must apply the rule to the complete source
population, not only sampled failures. Remove withheld researchers' authorships
and affiliation observations, reconcile affiliation aggregates, and regenerate
all R7–R10 from surviving support. Report any unsupported organization nodes and
their retention/removal policy; keep denominators consistent. Preserve all core
papers and official byline denominators.

Reuse the frozen embedding predictions and taxonomy, including their evidence,
excerpts and scores. `resolve/release_topics.py` performs model inference: do not
rerun that builder to obtain a correction that should preserve predictions.
Do not substitute the phrase baseline for the frozen embedding output. Select
unused graph/report paths; a prospective name is `release-graph-v4`, not an
assertion that this output already exists. Refuse overwrites.

**Acceptance:** suite/offline correction CLI pass; structural and size gates are
measured; old hashes remain unchanged. A machine-readable before/after diff
accounts for removed endpoints, observations and every changed derived edge,
support count and weight. Paper/venue/citation claims, taxonomy and paper-topic
predictions must be semantically unchanged. No new collection, threshold tuning
or source/roster audit. Commit code and measured receipts locally.

## 3. Recompute the affected database and analysis

Freeze/hash the corrected graph before evaluating it. Use only the isolated
`neo4j-five-year` service; preserve the pilot and extended databases. Keep old
graph/load receipts recoverable. Because the loader rejects conflicting graph
versions, use the supported explicit reset/import procedure for this service;
do not assume importing v4 over v3 is an idempotent update.

Verify inventory, all integrity queries and repeat-import reconciliation. Re-run
the five named projections, robustness checks, figures and candidate business
findings into new outputs; identity removals can change communities, affiliations,
rankings and portfolio denominators even with unchanged paper-topic predictions.

**Acceptance:** graph/Neo4j inventories reconcile, integrity checks pass, replay
does not change inventory, and each new figure/finding binds the corrected graph.
Record unavailable integration checks honestly. Commit the checkpoint locally.

## 4. Freeze and execute one prospective agent audit

Create a new evaluator protocol/config, rubric, quality config, sample packets and
receipts in unused paths. Preserve the existing numeric targets, global/per-type
sample sizes and A/B overlap design. A new draw needs a newly documented seed;
freeze it before drawing, after the construction rule is fixed. Record the dated
D040 amendment covering new graph bindings and this prospective audit. Do not
retry seeds, change sampling after seeing results or reuse old verdicts.

Sample uniformly from **all accepted edges of the corrected graph**. Do not
exclude previously reviewed IDs and then describe the remainder as a full-frame
sample. Record semantic overlap with previous samples and source/paper exposure;
repeated units are not new independent evidence. Explicitly disclose that the
correction was motivated by the earlier audit. A fresh probability draw and fresh
contexts do not prove independent validation or eliminate source/model bias.

Use isolated fresh A/B contexts with no inherited coordinator conversation or
shared answers. Supply complete raw relevant evidence, including observed ORCID
arrays; fix the source-packet omission as well as the resolver. Inspect every
assigned claim, retain original votes, and adjudicate actual conflicts only after
exports are frozen. Bind source hashes, run/model metadata and timestamps.

Keep both classifiers and the existing topic test/reference package frozen.
Its scores remain historical measured evidence for unchanged predictions; reuse
them with explicit provenance rather than pretending to obtain a fresh topic
test. Do not retune topics from these exposed errors. Repeated reference judgments,
if needed, are repeat assessment, not an untouched holdout. Any future classifier
improvement needs a separate development/test design established before tuning.
For edge-only new reviewer contexts, declare that design in the new protocol and
add a tested provenance-bound edge-only scoring mode. The current combined
wrapper binds A/B topic-first completion and must not be made to imply those new
contexts produced historical topic judgments. Keep its existing behavior intact.

**Acceptance:** provenance/assignment checks pass, every assigned claim has a
verdict or explicit missingness, and results report global k/n, Wilson intervals,
per-type supplements, agreement, exposure and source/evaluator limitations.
Keep AI-assessed qualifiers and all failed gates. Commit once; do not repeat the
audit until it passes. Precision improvement is an outcome to measure, not a promise.

## 5. Produce a new report and local submission draft

Update the report, README, status and reproduction instructions to distinguish
the original 88% audit from the corrected graph's actual results. Explain changed
coverage and business findings, unchanged topic limitations and the correction's
origin. Preserve the original report/package through versioned artifacts and Git.

Render a new PDF/HTML/ZIP using `reporting/release_package.py`. Verify at least
the required report length, headings, figures, tables, fonts, local links, member
hashes, privacy exclusions and representative rendered pages. Record the exact
source commit and actual byte hashes. Do not publish or submit as part of this plan.

Real student identities/contributions and unavailable course AI-use/access facts
come from supplied records; keep clearly pending fields while agents complete
other work. Follow [the delivery checklist](local-submission-checklist.md) for
separately authorized external actions.

## Deadline and stopping rule

Recommended sequence: scorer fix and bounded correction on **9 November**;
analysis, prospective audit and replacement package on **10 November**. These
are targets, not measured runtime promises. Use the existing internal packaging
target in the team record; the exact 11 November course submission time is unknown.
Checkpoint each step so partial progress remains reviewable.

If the correction/audit cannot finish, retain the verified original submission
draft and its disclosed failed gates; do not present an unaudited replacement as
validated. If the new audit also fails, report it and finish the package. Do not
start deadline-driven topic tuning, broaden scope, lower thresholds or seek human
annotations merely to obtain a passing number.

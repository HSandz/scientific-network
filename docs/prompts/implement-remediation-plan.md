# Fresh-session prompt — implement the remediation plan

Paste the entire text block into a fresh agent session in this repository.
This prompt supersedes the older pre-evaluation execution prompt for this task.

```text
Work in /home/san/Code/scientific-network. Implement all five steps of
docs/remediation-plan.md, continuing through a corrected, source-audited graph,
updated analysis/report and verified local submission package. Execute the work;
do not stop after planning, fixing only the scorer, or creating empty scaffolding.

I adopt the plan's separate correction track. This message explicitly authorizes
a NEW version of the graph to fix the observed-ORCID conflict omission, one
prospective agent audit of that corrected graph, and the necessary local database,
analysis, report and packaging work. Preserve the old frozen graph and all its
failed audit results. Record this dated D040 amendment in docs/decisions.md and
the new versioned protocol before graph correction/sampling. This is a bounded
exception to the old prohibition on post-audit graph changes: no in-place edit,
classifier tuning, lowered threshold or audit-driven iteration is authorized.
Do not ask me to reconfirm work already authorized here.

Agents perform all feasible work. Human annotation is optional. Use human input
only for genuinely unavailable personal/private/course facts or demonstrated
tool/access limits; continue independent work while those remain pending.
No push, release tag, Site publication, invitation or submission is authorized.

Start by reading, in order:
1. AGENTS.md
2. docs/release-plan.md
3. docs/status.md and its latest work-log entry
4. docs/remediation-plan.md
5. docs/work-log/2026-11-09-007-agent-release-review.md
6. docs/agent-audit-workflow.md, docs/reproduce-agent-evaluation.md,
   docs/post-audit-findings.md and reports/release-v3/reviewer-rubric-v1.md
Before graph changes read docs/project-plan.md and docs/graph-schema.md. Inspect
actual code/configs/tests/artifacts before edits; historical logs are not proof.
Keep frozen/hash-bound instructions, configs and completed receipts unchanged;
record the new amendment separately and bind it into the new evaluator freeze.
Do not edit those old files merely to make their future-tense wording current.

At handoff the source checkpoint was 934759b, followed by the prompt/documentation
commit. Inspect current HEAD and Git status; do not reset to a historical SHA.
If some work is already done, verify it and resume the first incomplete step.
Preserve unrelated edits. Check regular files and symlinks before replacing files.

Known artifact anchors (verify hashes locally):
- Frozen graph: data/processed/release-graph-v3/graph.json
  graph version release-9d4a6fb20f63
  SHA256 c23ef82c97fcb539b4b1c279e8ff42378bdb102e80fe851acf1a42e816a727b8
- Content receipt: reports/release-v2/freeze-v3.json
- Original agent evaluation/results/ledgers: reports/release-v3/
- Full immutable works: data/interim/release-v1/works.jsonl
- Frozen taxonomy: configs/topics-release-v1.yaml
- Historical topic test/references/allocation: data/manifests/release-v1/topic-test.jsonl,
  reports/release-v1/audit/, reports/release-v3/completed/
- Report/figures: reports/final-report/report.md and figures-v3/
- Existing local package: reports/release-v3/local-package-receipt-v1.json
- Historical baseline: 419 tests passed, one existing skip. Original AI-assessed
  precision 176/200 = 88%, gates failed; embedding/phrase micro F1 .4667/.2301.
  These are historical results, not targets or new validation.

Run uv sync --locked --group dev --extra analysis --extra report and uv run pytest.
Use unique Asia/Bangkok work entries and ignored reports/runs/<work-id>/ directories.
Run relevant tests/offline CLI checks and commit locally at meaningful checkpoints;
update the work-log index and replace status (under 60 lines). Continue after each
checkpoint. Keep evidence of failures, actual commands/exits, hashes and next steps.

A. Fix and validate the topic-ledger guard
- Inspect evaluation/agent_review.py, CLI routes and tests/test_agent_review.py.
- Require a labels list on every topic ledger record. Preserve existing element
  type/uniqueness/CSV agreement rules. Explicit [] distinguishes considered empty
  and unreviewable records via their decisions; unreviewable cannot contain labels.
  Edge ledgers do not require topic labels. Update the synthetic fixture to conform
  to the rubric; add meaningful missing-field/type/empty-set regressions.
- Preserve legacy behavior. Run the suite and relevant offline CLI. Rescore the
  ORIGINAL review using the documented command with new ignored output paths:
  both result JSON objects must remain equal to existing results; exit 1 for
  failed numeric gates is expected, not a provenance failure. Commit this step.

B. Implement and build the separately versioned identity correction
- Inspect resolve/release.py, resolve/release_taxonomy.py, graph/materialize.py,
  graph contracts/validation and tests/test_release_graph.py.
- Union normalized valid author.orcid and author.observed_orcids values per
  OpenAlex author ID across ALL matched works. Withhold IDs with multiple distinct
  values everywhere. Missing ORCID remains allowed. Handle malformed source values
  explicitly and conservatively; keep conflicting values and exact raw locators/
  hashes in the review queue. Never merge on names or special-case sampled IDs.
- Add regressions for array-only/singular-array/across-paper conflicts, equivalent
  duplicates, absent/malformed values, same-name people, affiliation observations
  and derived support propagation. Bump the resolver/correction method version.
- Implement an explicit CLI correction from immutable works plus frozen v3 into
  unused versioned outputs. Remove withheld researchers/authorships/observations,
  reconcile affiliation aggregates and regenerate all R7–R10. Preserve official
  byline denominators, stable surviving IDs and all core papers. Document handling
  of organizations left without support; keep all counts/denominators consistent.
- Reuse frozen embedding labels, scores, excerpts and evidence and the corrected
  taxonomy exactly. resolve/release_topics.py invokes model inference: do NOT rerun
  it merely to carry predictions forward. Do not replace topics with the phrase
  baseline, recalibrate, retrain, download models or reacquire the corpus.
- Preserve old configs/graphs/receipts; choose unused paths (v4 is a candidate,
  not proof that it is unused). Emit a complete before/after change manifest and
  new content freeze. Validate all size/structure/support gates and explain every
  changed edge, observation, weight and endpoint. Prove unchanged paper/venue/
  citation claims, taxonomy and paper-topic predictions. Commit the checkpoint.

C. Load and analyze the corrected graph
- Use only neo4j-five-year on Bolt port 7689. Verify service identity before any
  write. Keep the old graph recoverable from its immutable files/receipts. Use
  the supported release-service reset/import procedure needed for a new graph
  version; never prune global volumes or touch pilot/extended databases.
- Verify Neo4j inventory, all integrity queries and idempotent repeat import.
  Record genuine service limitations without claiming unavailable checks passed.
- Recompute all five projections, sensitivity results, figures/tables and business
  findings into new paths. Even unchanged topic labels can have changed researcher/
  organization portfolios. Bind every output to actual corrected graph/method/
  config versions. Do not relabel old analysis as recomputed. Commit the checkpoint.

D. Freeze and perform ONE prospective source-backed agent audit
- Implement/test a provenance-bound edge-only scoring mode while preserving the
  combined scorer. New edge contexts did not produce historical topic references;
  do not invent topic-completion records or pass old identities as new reviewers.
- Create a new protocol/rubric/quality config, packets and evaluator freeze. Retain
  numeric targets and the default 200-global, 10-per-type, 50-overlap design. Fix
  the construction rule first; choose/document/commit a new seed before drawing
  the sample. Sample all accepted corrected-graph edges uniformly. Do not retry
  seeds or exclude previously reviewed IDs then claim a full-frame sample.
- Record semantic-ID/sample and paper/source overlap with the old audit and the
  fact that its errors motivated this correction. Do not reuse old verdicts or
  describe repeated units as new independent evidence.
- Explicitly delegate A/B judgments to separate fresh contexts with no inherited
  coordinator history or shared answers (fork_turns=none where supported). Supply
  only each reviewer's assignments/rubric and source evidence. Do not share old
  verdicts or suggest answers. Source packets must include observed_orcids arrays
  and full relevant underlying support; verify actual caches, not summaries alone.
- Each assigned edge needs a source-backed judgment, exact locator/hash/depth,
  construction-source reuse disclosure, actual evaluator/run/model metadata and
  timezone timestamp. Unknown metadata remains unknown. Structural agreement or
  a programmatic conflict flag cannot substitute for source review of all claims.
- Freeze A/B exports before separately source-adjudicating actual disagreements.
  Preserve original votes. Unverifiable counts incorrect; missingness is explicit.
- If context isolation is genuinely unavailable, select the documented single-agent
  variant before judging, implement/test its new provenance-bound path and disclose
  unavailable agreement. Never impersonate two evaluators. Complete other work
  despite a demonstrated evaluator/tool blocker and report exactly what is unrun.
- Keep historical topic references/scores frozen and attribute them correctly.
  Confirm semantic prediction equality before reuse. No classifier tuning or new
  claim of an untouched topic holdout. A new edge audit does not resolve topic error.
- Score once and retain actual pass/fail, global k/n/Wilson interval, separate
  per-type supplements, agreement/errors and exposure/source limitations. A
  failed numeric gate does not authorize another correction/sample cycle. Commit.

E. Update and verify the local submission draft
- Update report/README/reproduction instructions/status with the new measured
  graph and results, before/after coverage, changed findings and historical failed
  audit. Keep topic limitations visible. No invented improvements or course claims.
- All evaluation remains evaluation_kind=ai_agent_review,
  human_validation=not_performed, reviewer_independence=not_established,
  verified_course_accuracy=not_established. Wilson intervals exclude evaluator
  error and source/model bias, even with fresh contexts and a new draw.
- Commit the report/source checkpoint before building a NEW local PDF/HTML/ZIP
  with reporting/release_package.py. Verify report length, text, figures, tables,
  glyphs, links, actual archive CRC/member hashes, source commit and privacy
  exclusions. Inspect representative rendered pages. Preserve old package bytes.
- Never include credentials, raw caches, full graph JSON, models or DB volumes
  in Git/submission artifacts. Preserve historical CSV byte/line-ending differences.
- Real student names/IDs/contributions and unavailable course AI-use/access facts
  remain clearly pending; do not infer them from Git accounts or agent channels.
  Finish independent work and list the exact missing facts/external actions.

Before finishing, finalize all work entries and status, run applicable checks and
commit locally. Report findings fixed, actual corrected graph/version/counts,
before/after scope, audit and unchanged topic results, failed/unrun checks, artifact
paths/hashes, local commits and exact remaining blockers. A fresh clone cannot
rescore without permitted ignored inputs; document restoration/hash checks.

Use the plan's deadline targets without inventing a submission time. If a corrected
release cannot be completed and audited, retain the verified original draft with
its honest failures; do not replace it with an unaudited success claim. If the new
audit also fails, preserve that outcome and finish the local package. Do not seek
human annotations or tune/resample merely to obtain a passing number.
```

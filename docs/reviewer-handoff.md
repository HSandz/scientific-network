# Reviewer handoff — corrected release, 9 November 2026

> **Superseded execution instructions:** the user selected agent-led evaluation on
> 9 November. Use [the agent audit workflow](agent-audit-workflow.md) and
> [fresh-session prompt](prompts/agent-release-completion.md). Do not wait for
> human A/B identities or annotations. The remainder preserves the optional human
> workflow and its frozen packet paths; it does not govern current execution.

The active package is [release-v2/freeze-v3.json](../reports/release-v2/freeze-v3.json),
for graph `release-9d4a6fb20f63` at
`data/processed/release-graph-v3/graph.json`. It supersedes the v2 graph's old
freeze and edge packets; preserve those historical files and do not review them.
No human quality result exists yet. The [correction summary](../reports/release-v2/graph-summary.json)
records source hashes and equality checks for all preserved facts and predictions.

## Before beginning

The user must map real people to A and B in [team.md](team.md), confirm they can
review independently, and give each person only their own packets. The normal
A/B design remains selected. If only one reviewer is available, explicitly choose
the separate fallback below before beginning edge review. Do not label the topic
test with a model, inspect its predictions, or tune the frozen classifier.
Names, student IDs, actual contributions and course AI-use disclosure belong to
the user; software cannot authenticate reviewer identity or independence.

## Current packets

| Reviewer | Edge packet | Prediction-blind topic packet |
| --- | --- | --- |
| A | [HTML](../reports/release-v2/audit/edge-review-sheet-v2-reviewer-A.html#reviewer=A) · [blank CSV](../reports/release-v2/audit/edge-review-sheet-v2-reviewer-A.csv) | [HTML](../reports/release-v1/audit/topic-label-sheet-reviewer-A.html) · [blank CSV](../reports/release-v1/audit/topic-label-sheet-reviewer-A.csv) |
| B | [HTML](../reports/release-v2/audit/edge-review-sheet-v2-reviewer-B.html#reviewer=B) · [blank CSV](../reports/release-v2/audit/edge-review-sheet-v2-reviewer-B.csv) | [HTML](../reports/release-v1/audit/topic-label-sheet-reviewer-B.html) · [blank CSV](../reports/release-v1/audit/topic-label-sheet-reviewer-B.csv) |

Open the HTML locally in a modern browser, or serve the repository locally. The
form itself works offline; public source links require network access. Keep the
repository's relative paths when using the frozen taxonomy config link. The
complete source locators/hashes, excerpts, definitions, supporting edges/papers
and affiliation observations are under each edge's expandable evidence context.
Those strings are not clipped. Paper/DOI/PDF/OpenAlex links provide source access.

For edges, decide **correct**, **incorrect** or **unverifiable** from the evidence.
Unverifiable counts as incorrect in precision. For an error, choose a category and
write a reason. Edge answers persist in that browser; export frequently with
**Export my reviews (CSV)** and keep a backup. The downloaded filename is
`edge-review-A.csv` or `edge-review-B.csv`. Complete every assigned row for the
normal audit. The HTML deliberately exports only completed edge rows; a partial
export is not a completed audit.

For topics, choose up to three leaf IDs from the supplied frozen definitions.
If none applies, leave all labels empty and explain “no applicable leaf” in Notes.
Keep this tab open until **Download completed CSV** succeeds: topic sheets do not
save draft answers across reloads. Downloads are
`topic-label-sheet-reviewer-A-completed.csv` and the corresponding B file.
Every assigned paper must be considered; blank packets cannot be scored.

Preserve all blank originals. Save and return completed downloads under these
**separate, currently absent** paths (rename the downloaded files):

```text
reports/release-v2/completed/edge-A.csv
reports/release-v2/completed/edge-B.csv
reports/release-v2/completed/topic-A.csv
reports/release-v2/completed/topic-B.csv
```

Do not edit IDs, hashes, assigned reviewer letters, titles, abstracts or catalogs.
Do not open/save CSVs through a tool that reformats their frozen fields. Return
separate UTF-8 CSVs; no manual concatenation or spreadsheet merge is needed.
Keep the independent exports unchanged after returning them.

## Compare and adjudicate returned edge conflicts

Run from the repository root, after the real exports exist:

```bash
uv run research-network prepare-edge-adjudications \
  --reviews reports/release-v2/completed/edge-A.csv reports/release-v2/completed/edge-B.csv \
  --output reports/release-v2/completed/edge-adjudications.csv
```

This copies provenance and returned conflicting judgments into a **blank** joint
form. It creates no judgments and does not validate the graph assignment; the
final scorer does that. Only disagreements between two returned verdicts need a
row. A and B jointly inspect each conflict, fill `adjudicator_id` (for example
`A+B`, mapped to real people in team.md), `decision`, `reason` and `reviewed_at`
with a timezone (for example `2026-11-10T10:00:00+07:00`). Use the actual time.
Set `error_category` for incorrect/unverifiable; leave it blank for correct.
Categories: `wrong_identity`, `wrong_affiliation`, `wrong_citation`, `wrong_topic`,
`unverifiable`, `other`. Preserve the copied binding columns and edge ID.
An unresolvable conflict can be adjudicated **unverifiable** with a reason;
it cannot be silently discarded. Agreed or singly reviewed edges need no
adjudication. A header-only form is valid when there are no conflicts.

## Score the normal completed edge audit

```bash
uv run research-network score-edge-audit \
  --input data/processed/release-graph-v3/graph.json \
  --config configs/quality-release-v1.yaml \
  --reviews reports/release-v2/completed/edge-A.csv reports/release-v2/completed/edge-B.csv \
  --adjudications reports/release-v2/completed/edge-adjudications.csv \
  --output reports/release-v2/audit-results.json
```

Each export is parsed separately, then combined as CSV rows in memory. The normal
sample has 200 uniform global edges and a separate ten-per-relation supplement;
50 global edges are shared. Only the uniform sample estimates global precision.
All frozen assignments and returned conflicts must be resolved. The course gate
is point precision >90%; the project target is ≥95% with Wilson lower bound >90%.
A computed failed gate exits 1 **with** a result; malformed/incomplete inputs exit
1 **without** a result. No command certifies independence or a submission.

## Score the unchanged topic test against the replacement freeze

```bash
uv run research-network score-topic-review \
  --graph-v1 data/processed/release-graph-v1/graph.json \
  --embedding-graph data/processed/release-graph-v3/graph.json \
  --embedding-summary reports/release-v2/graph-summary.json \
  --topic-test data/manifests/release-v1/topic-test.jsonl \
  --taxonomy configs/topics-release-v1.yaml \
  --allocation reports/release-v1/audit/topic-review-allocation.json \
  --master-sheet reports/release-v1/audit/topic-label-sheet.csv \
  --freeze reports/release-v2/freeze-v3.json \
  --reviewer-a reports/release-v2/completed/topic-A.csv \
  --reviewer-b reports/release-v2/completed/topic-B.csv \
  --output reports/release-v2/topic-eval.json
```

The topic master, allocation and A/B sheets are reused by exact-byte reference,
because their content already matches the frozen classifier taxonomy. They have
no graph-dependent prediction content. Their old paths are intentional; the new
freeze binds them. Do not regenerate the test or reassign papers. The allocation
remains 50 unique papers, 30 per person, ten shared; each reviewer has 12 AAAI and
18 IJCAI, and the overlap four AAAI/six IJCAI. Each paper contributes total weight
one, including two half-weight judgments on shared papers. Preserve independent
topic disagreements; topic scoring does not require a manufactured consensus.

## Optional fallbacks — prepared, not selected

**One edge reviewer:** use only
[the separate single-reviewer HTML](../reports/release-v2/audit-single-reviewer/edge-review-sheet-v2.html#reviewer=A)
and [its freeze](../reports/release-v2/audit-single-reviewer/freeze-v3.json).
This uses 200 uniform edges plus five per relation, no overlap, assigned only to
A. It cannot produce agreement statistics. Save its export separately as
`reports/release-v2/completed/edge-single-A.csv`; do not mix it with the A/B forms.
The topic test still requires its agreed A/B allocation; this edge fallback does
not change the topic protocol.

```bash
uv run research-network score-edge-audit \
  --input data/processed/release-graph-v3/graph.json \
  --config configs/quality-single-reviewer-release-v1.yaml \
  --reviews reports/release-v2/completed/edge-single-A.csv \
  --output reports/release-v2/audit-results-single.json
```

**Incomplete edge audit:** only when explicitly chosen under D040 §4, add
`--allow-partial` to the appropriate edge-scoring command and choose a new output
such as `reports/release-v2/audit-results-partial.json`. Supply only completed
export rows; blank/malformed rows remain fatal. Omit an entirely absent export
path. Returned overlap conflicts still require joint adjudication. The output
reports actual global n/planned n, every missing assignment, completed overlap
pairs and relation coverage. Agreement uses only returned pairs; supplements are
never pooled. Missing reviews are not correct and unverifiable decisions remain
incorrect. Partial results explicitly warn about nonresponse bias and cannot
claim the planned audit was completed. A real partial result exits 1 after
writing the partial result. Neither fallback is activated by its implementation.

Stop after returning/scoring real reviews for a separate report decision. This
handoff authorizes no Site publication, release tag, push or submission.

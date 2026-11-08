# Agent-led evaluation and release preparation

Active under the user's **9 November 2026 D040 amendment**. The agent performs
all feasible evaluation, report and local packaging work. Human annotation is
optional; it is no longer a prerequisite. This replaces the human-execution
requirements in [the older handoff](reviewer-handoff.md). The course brief recorded
in [project-plan.md](project-plan.md#course-brief) does not explicitly prescribe
human reviewers. This amendment does not assert lecturer acceptance of AI judging.

The contract is [evaluation-agent-release-v1.yaml](../configs/evaluation-agent-release-v1.yaml).
It is a declared protocol, **not implemented evaluation support or a completed
audit**. First implement the minimum provenance/binding/scoring changes below.
Use [the fresh-session prompt](prompts/agent-release-completion.md) to execute it.

## Preserve the scientific artifact

Keep the current graph and its [source freeze](../reports/release-v2/freeze-v3.json),
classifier, taxonomy, thresholds, held-out membership, old quality configs,
allocation and blank review packets unchanged. The existing freeze remains the
graph/content receipt; its human-review plan is a historical protocol snapshot.
New evaluation artifacts belong under `reports/release-v3/`, without overwriting
anything already present. This evaluation change does not require a graph reload,
new predictions, corpus collection, a roster audit or a new graph version.
Human-review wording in hash-bound findings/analysis/figure captions describes
their original protocol snapshot. Qualify it in the new evaluation/report rather
than editing frozen bytes; any necessary replacement caption/figure gets a new
version with its actual computation/reuse provenance stated.

## 1. Implement and freeze the evaluator before judging

- Inspect `evaluation/edge_audit.py`, `evaluation/topic_eval.py`, their CLI routes
  and tests. Preserve legacy behavior. Add explicit agent-provenance and receipt
  validation, using narrow CLI options or a dedicated wrapper; a post-hoc disclaimer
  attached to unqualified human-style results is insufficient.
- Create `configs/quality-agent-release-v1.yaml` from the selected immutable
  sampling config. Retain its seed, size/coverage/precision thresholds and selected
  design. Declare the agent reviewer kind; do not overwrite either source config.
  Changing quality bytes changes audit bindings: generate new blank edge forms
  and prove sampled semantic IDs, global/type flags and assignments match the
  selected source design. Do not relabel hashes in the old packets.
- Default to two isolated fresh agent contexts, A and B, using the existing edge
  design and topic allocation. These letters denote evaluator channels, not team
  members. Each context receives only its own prediction-blind topic packet and
  the frozen rubric. Do not fork the coordinator's conversation or pass graph,
  prediction, analysis, findings or other reviewer's answer files.
- If isolated reviewer contexts are genuinely unavailable, select the declared
  single-agent variant **before labels are generated**. Use the existing
  single-reviewer edge sampling recipe; assign each frozen topic-test paper once.
  Implement and test this explicit topic design, with weight one per paper and
  unavailable overlap statistics. Never duplicate one context's answers as A/B.
  A fresh top-level session may serve as the single topic reviewer only if it has
  not inspected item-level predictions. Otherwise create a clean context. If no
  clean context is available, record topic evaluation as not run with that specific
  blinding blocker and continue edge/report/package work; do not invent blind labels.
- Write `reports/release-v3/evaluation-freeze-v1.json` before judging. Bind graph
  and source-freeze hashes, this protocol/config, runtime quality config, exact
  reviewer prompts/rubric, topic/test/allocation/packet hashes, selected design and
  evaluator identities. Record actual provider/model/version when exposed, run
  and session IDs, tools/settings that are available, start times and context
  isolation. Unavailable metadata is explicitly `unknown`, never invented.
  Preserve the pre-review freeze; add completion receipts with output hashes later.
- Add meaningful synthetic regressions for wrong/missing evaluator provenance,
  bindings, duplicate/copied reviewer runs, single-agent topic weighting, partial
  or unreviewable topics, and honest AI result labels. Run `uv run pytest` and a
  relevant offline CLI check before real scoring. Fixtures remain invented.

## 2. Label topics before exposing edge predictions

Reviewers first label only their assigned titles/abstracts against the frozen
leaf definitions. They must not inspect classifier predictions, scores, excerpts
selected by the classifier, graph files or the report's item-level findings.
Finish and hash the topic exports and evidence ledger before those same contexts
perform edge review. The coordinator must not supply suggested labels.

For each paper, record up to the allowed number of leaf IDs, a concise rationale,
supporting text location, evaluator run and timestamp. A considered empty set
means **no applicable leaf**; inaccessible or insufficient evidence means
**unreviewable**, recorded separately. Do not fabricate empty gold labels to
complete a CSV. Report planned/reviewed/unreviewable counts, actual denominators
and missingness. Preserve A/B disagreements and the existing paper-normalized
weighting in the default design; never tune the classifier from these results.

## 3. Review sampled edges against sources

Inspect every assigned edge, not a convenient subset. Use the relation-specific
rubric in release plan §5, checked against the D040 evidence standard in §2.2.
Read actual cached source records or accessible official pages/PDFs; paper-level
source verification for sampled claims is permitted and is not a new roster or
source-route audit. Fetch only what the sampled claim needs. Never upload private
files or spend on new services without authorization.

- Identity: byline position, compatible name, stable author ID and conflicting
  identifiers; normalized-name equality alone cannot establish a person.
- Affiliation: author–paper–institution mapping and raw affiliation evidence;
  never copy paper-level institutions to every author or use current employment
  as historical evidence. PDFs can corroborate; D040's OpenAlex rule still applies.
- Citations/publication: verify the cited target or official venue/year claim in
  the underlying source, rather than trusting a generated summary.
- Taxonomy/topics: hierarchy must match the frozen taxonomy; a predicted topic
  must have substantive paper support. Classifier confidence is not correctness.
- Derived edges: inspect the required distinct-paper/author supports and counting
  rule; structural recomputation alone does not validate the underlying facts.

Each judgment needs a resolvable URL/local cache locator, source hash, evidence
depth, concise finding, actual agent run ID and timezone timestamp. Record whether
the source is the same source used to construct the graph. Source-backed checking
can verify extraction from that source, but cannot be called independent external
corroboration when it repeats OpenAlex. Keep primary-source and secondary-only
counts visible. Internal-only checks or unavailable evidence are **unverifiable**,
counted as incorrect. Access failures do not automatically require human review:
record the limitation, complete other rows, and continue.

Process bounded batches and checkpoint completed rows so context limits do not
lose work. Read full required fields programmatically; do not judge from truncated
console output. Batch/session IDs must remain mapped to actual per-unit evaluator
runs, with A/B overlap answers separated. Automation can extract/format evidence
and score decisions; it must not bulk-fill verdicts from predictions or structural
checks in place of the declared source review.

After A/B exports are frozen, the coordinator may adjudicate actual edge conflicts
from source evidence in a separately recorded agent adjudication. An unresolved
conflict becomes unverifiable, not an assumed correct verdict. Do not alter the
frozen graph in response to audit errors or silently discard difficult units.

## 4. Score and report what was measured

Every result must bind the graph, configs, evaluator receipt, actual review files
and evidence ledgers. Validate the ledger-to-assignment joins and evaluator IDs;
do not score blank templates, test fixtures or mechanically copied predictions.

Use explicit metadata throughout JSON, README, report, tables and captions:

```text
evaluation_kind: ai_agent_review
human_validation: not_performed
reviewer_independence: not_established
```

Report **AI-assessed edge precision** (global k/n, Wilson 95% interval, per-type
results kept separate) and **topic agreement with AI-assigned reference labels**
(both frozen classifiers, micro/macro P/R/F1, coverage, actual reviewed n and
agent agreement where defined). Preserve incorrect/unverifiable decisions, error
categories, failed numeric thresholds and partial results. Existing thresholds
remain unchanged, but their outcomes must be explicitly **AI-assessed numeric
checks**. Verified course accuracy remains `not_established`; do not assert that
an AI point estimate certifies the assignment's accuracy requirement.

Wilson intervals describe sampling uncertainty conditional on supplied judgments.
They do not cover evaluator mistakes, shared-model bias or correlated judgments.
Two fresh contexts, even on different models, do not establish statistical or human
independence. Report these limitations alongside the scores, not only in a log.

## 5. Complete the remaining local release work

Finish report/README results and limitations, render the report to a local PDF
of at least the required length, inspect the rendered text/figures, run applicable
tests and integrity checks, and prepare the local submission bundle and exact
remaining-action list. Preserve graph/figures unless a separately justified fix
needs a new version. Record actual results, never prefill planned scores.

Ask for human input only for unavailable personal/private facts (real names, IDs,
actual contributions, course-specific disclosure/access rules), necessary actions
that available tools demonstrably cannot perform, or external actions requiring
authorization. Continue all independent work while those items remain missing.
Team placeholders may remain clearly marked in a draft; do not claim a final
submission-ready team section until real details exist. No push, tag, Site
publication, invitation or submission is authorized by this protocol change.
Prepare those actions for review without performing them.

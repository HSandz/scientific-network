# Actual review instructions and execution record

The coordinator explicitly requested `gpt-6-luna`, reasoning effort `high`, with
`fork_turns: none` for all three runs. Tool-accepted task names:
`/root/luna_edges_1`, `/root/luna_edges_2`, `/root/luna_diagnostics`.
The environment exposes the selected model identifier/effort and task names;
provider build/version, temperature and request identifiers remain unknown.
No reviewers were presented as people. No A/B agreement was estimated.

The following records the operational rubric supplied to the actual runs (not
a retrospective claim of independent gold). Both edge reviewers received the
same rubric with only their own 40-row packet path and output filename changed:

- Work only on the bounded packet, do not modify code, graphs, sources or other
  reports and do not spawn agents. Read relation semantics in `docs/graph-schema.md`
  and frozen taxonomy `configs/topics-release-v1.yaml` as needed.
- Read complete evidence fields programmatically in manageable batches. Review
  subject/object IDs and names, source links/hash/locators, base support edges,
  affiliation observations and up to three source-paper witnesses.
- Decide `supported`, `unsupported`, or `unknown`. Raw-name similarity alone
  cannot prove identity. Compatible positional authorship plus OpenAlex ID is
  release construction evidence, not independently verified identity.
- Derived claims require accepted authorship, paper-specific organizations,
  distinct authors for organization collaboration, substantive paper-topic support,
  and two/three distinct-paper thresholds for researcher/organization topics.
- Citation support requires the actual target in `referenced_works`. Paper-topic
  claims need substantive title/abstract support rather than classifier scores.
  Taxonomy edges must match the frozen config. Unknown means evidence insufficient.
- Record witness depth and total support count; bounded witnesses cannot validate
  all weights. Do not infer failure of an entire aggregate from an incomplete
  witness subset. The coordinator explicitly reminded reviewer 1 of this rule;
  the challenged R9 was confirmed to have exactly two total papers, both inspected.
- Emit one JSONL row per assigned edge with decision, strength, evidence IDs,
  source locators, concise evidence-specific finding, issue, AI kind, actual model,
  reasoning effort, evaluator run, evidence depth and construction-source overlap.
- All three contexts received the hash-bound plain-abstract supplement before
  finalizing judgments; the first packet extractor used a nonexistent inverted-index
  field. No source bytes or frozen sample IDs changed.

The diagnostic reviewer received all seven prior DOI investigation records and
exactly eight sampled HAS_TOPIC packets. Its rubric required authoritative
replacement evidence before proposing any correction, distinction between likely
version links and verified equivalence, title/full-abstract topic assessment,
missing-leaf/overlap/abstention diagnostics and critique of analytical claims.
Predictions were exposed; this was explicitly not a blind topic test or relabeling
instruction. Crossref source records were reused; no collection was requested.

No reviewer received another reviewer's answers. Review batches were disjoint;
the diagnostic reviewer independently saw the same eight paper-topic cases.
The coordinator later reviewed all flagged packets. Shared models and construction
sources mean statistical/evaluator independence is not established. Per-run output
hashes are preserved in `review-completion.json`.

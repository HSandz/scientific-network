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

## Optional human packet rubric and allocation amendment

The human packet keeps the existing CSV vocabulary and `correct_when` field; it
does not add an annotation schema. It makes two evidence states explicit:

- **Source-consistent relationship:** the claim agrees with official publication
  metadata and accepted provider records, at the evidence depth shown.
- **Independently verified relationship:** appropriately independent evidence
  establishes the claim's semantic correctness, including the mapping of a
  canonical researcher ID to the real person where relevant.

An official byline aligned with an OpenAlex author ID is a construction-consistent
authorship record, but does not alone independently establish person identity.
`AFFILIATED_WITH` also depends on that identity mapping. `COAUTHORED_WITH`,
`COLLABORATED_WITH`, `RESEARCHES_TOPIC`, and `CONTRIBUTES_TO_TOPIC` inherit the
identity uncertainty of their researcher inputs; mechanical support thresholds
or correct aggregation do not remove it. If only source consistency is established
and the semantic claim remains unresolved, reviewers can record `unverifiable`
and explain the evidence in the existing reason field. A `correct` response is
not separately coded as independently verified; readers must inspect the evidence
and the reviewer's stated basis. This is a known limit of the existing form.

Each member receives their own `human-member-{1,2}.html` plus matching CSV. Both
forms show the same 20-case prespecified random subset, six existing risk
diagnostics, and all four IDs in `issues.json`. Three flagged cases overlap the
random subset. The 27 unique displayed cases retain every selection tag; flagged
cases appear once in a dedicated section. Only the `random` tag contributes to
probability-based calculations. The random conditional probability remains 20/80;
its marginal population probability is `(8 / relation population) * (20/80)`.
Risk and diagnostic-only flagged cases are not a probability sample and must not
enter that estimator. Do not pool relation strata unweighted.

The initial packet includes the cases' source evidence but withholds Luna's concern.
Each reviewer has a separate `human-member-{1,2}-flagged-post-blind.html` with the
issue-ledger concerns and source locators. Reviewers should record and export their
initial CSV before opening that page. Open each local form in a separate browser
profile; source links require Internet. Export original CSVs separately before
comparing answers. Member labels do not fabricate identities or participation.
Human validation remains **not performed** until actual submissions exist; both
members' metrics remain unavailable.

# Contributor and agent instructions

## Project boundary

Read `README.md`, `docs/project-plan.md`, `docs/graph-schema.md`, and the relevant
configuration before editing. This is a course project for **Social Media Network
Analysis for Business**, not a general research search engine.

- Target release: major AI and related flagship conference editions in **2021–2025**
  (D018), listed in `docs/conference-scope.md`, `docs/five-year-scope.md` and the
  planning-only `configs/conference-scope-2021-2025.yaml`. NeurIPS/ICML and all
  current 2023 artifacts are historical diagnostics, not five-year coverage.
  Exclude non-main research material under the venue-specific track policy; keep
  no-edition, exclusion and unresolved-source records in the ledger.
- **Planning/documentation/Site updates only as of 2026-11-04 (D018). Do not
  implement pipeline changes, discover sources, collect/enrich papers, create new
  splits or import graphs until a later explicit instruction.** D015 authorized
  historical 2023 staging; it does not override this current pause. Preserve all
  legacy and expanded inputs/test IDs. Future executable configs need new versions,
  cross-year leakage protection and honest per-edition availability ledgers.
- Preserve `configs/corpus.yaml`, `configs/quality.yaml` and frozen pilot artifacts
  for reproducibility. The scope registry is not an executable pipeline config.
  Expanded adapters/splits/venue handling are not implemented by listing venues.
- Use Neo4j Community as the graph DBMS. Keep optional GDS compatibility work
  separate from the working base service.
- Preserve the five entity labels and ten predicates in `docs/graph-schema.md`.
  Change semantics, corpus boundaries, or release thresholds only with an explicit
  documented decision. The five years are core planned scope; prediction and
  years outside 2021–2025 remain optional after the core release.
- The existing public Site is **AI Research Network — Plan & Report (2021–2025)**,
  with Plan and Report tabs (D019/D020). Report visualizations and controls must
  be native Site components, never an iframe embedding the standalone HTML.
  Preserve its project ID, URL and audience.
  Read `docs/sites-workflow.md`; refresh its Report snapshot after material
  finalized project iterations, using permitted measured artifacts and clear dates.
  Publish through Sites; do not claim unattended/live synchronization. Preserve
  historical snapshots under `docs/reference/` and record publication receipts.

## Evidence and scientific integrity

- Never merge researchers on normalized names alone. Preserve stable internal IDs,
  external-ID crosswalks, conflicting evidence, and reversible resolution decisions.
- Store author–paper–organization triples before aggregating affiliations. Do not
  assign a paper's entire institution list to every author or use current profiles
  as historical affiliation evidence.
- Every accepted edge needs deterministic identity, resolvable evidence, method and
  graph versions, and accepted status. Ambiguous claims belong in a review queue.
- Derive social/profile edges only from accepted core-paper support. A sole
  dual-affiliated author cannot establish organization collaboration. Count distinct
  papers, use canonical pair orientation, and preserve raw and fractional weights.
- Keep observed, inferred-topic, curated-taxonomy, and derived counts separate.
  R1–R4 alone count toward the 5,000 factual-edge gate. Technical records, context
  papers, and unresolved people must not rescue the core size targets.
- Synthetic fixtures are invented examples. Never report fixture counts, computed
  audit examples, or planned targets as measured project results.
- Structural validation is not semantic accuracy. Release claims require the
  frozen independent audit in `docs/evaluation.md`, plus recall and coverage.
- Reserve held-out IDs before tuning; keep all versions of those papers out of
  development. Do not tune thresholds against test/audit errors and reuse that test
  as independent evidence.

## Repository workflow

- Keep Python code under `src/scientific_network/`; organize by pipeline stage.
  Keep standalone project documentation under `docs/`, results/report material
  under `reports/`, and runnable Cypher under `queries/`.
- Keep changes focused and preserve unrelated user edits. Check regular files and
  symlinks before replacing instructions or other existing content.
- Raw downloads are immutable and ignored. Track small manifests, configuration,
  synthetic/permitted fixtures, source code, and reproducibility instructions.
- Do not commit `.env`, credentials, large models, database volumes, or paper PDFs.
  Do not assume code licensing grants redistribution rights to third-party data.
- Install with `uv sync --locked --group dev`; update dependencies through
  `pyproject.toml` and `uv lock`. Keep `uv.lock` in sync. Do not download models or
  collect the full corpus as part of ordinary tests.
- Use explicit config, input, and output paths. Planned stages must exit nonzero
  until implemented; do not replace them with empty successful outputs.
- For code changes run `uv run pytest` and a relevant offline CLI check. For data
  semantics include meaningful cases such as same-name people, duplicate versions,
  multi-affiliation mappings, topic abstention, and repeated support records.
- If changing import/query code, verify against Neo4j when available and report
  when integration validation was unavailable. Never claim services or benchmarks
  ran if they did not.
- Record material choices in `docs/decisions.md` and measured outputs with graph,
  config, source, and method versions. Update the roadmap/status when behavior is
  implemented. Never invent names, student IDs, a GitHub URL, or measured scores.

## Task history and session handoff

- At the start of substantive project work, read `docs/status.md`,
  `docs/work-log/README.md`, and the latest relevant work entries, then verify the
  actual files and Git state. Logs are context, not proof that older checks still
  pass. Read the task's code/configuration as required above.
- Create a work entry from `docs/templates/work-log.md` under `docs/work-log/`,
  using an unused `YYYY-MM-DD-NNN-short-slug.md` filename and matching
  `WORK-YYYY-MM-DD-NNN` ID. Use Asia/Bangkok dates and explicit timezone offsets
  for recorded times. Never overwrite another task's entry.
- Record the objective and `in_progress` state early; checkpoint meaningful
  findings or a long-running command before an interruption can lose the handoff.
  Use one entry per task or meaningful iteration, not per tool call. Follow-up
  work after a finalized entry gets a new entry linked to its predecessor.
- Before the final response, finalize the entry with changes, exact checks and
  outcomes, artifacts, decisions, limitations/blockers, and a concrete next step.
  Log incomplete/blocked work too. Mark unrun checks and distinguish historical
  results from checks performed in this task. Record failures and partial results.
- Update the index in `docs/work-log/README.md` and the short current handoff in
  `docs/status.md`. Update `docs/roadmap.md` when a capability changes; keep durable
  design rationale in `docs/decisions.md` and link it from the entry.
- Keep finalized records stable. Add dated corrections with evidence or link a
  superseding entry rather than silently rewriting the original outcome.
- Keep concise work records ready for Git alongside the related changes. Raw
  console logs and run artifacts go in a unique `reports/runs/<work-id>/` directory
  and remain ignored. Summarize commands, exit codes and key results in the work
  entry so the handoff works without local-only artifacts. No automatic commit or
  push is required by this logging rule.
- Do not save credentials, private source text, hidden reasoning or full chat
  transcripts in the journal. Record useful observations, decisions and evidence.
  A conversational reply with no project work or state change needs no new entry.

## Current implementation

`schema`, structural `validate`, and the audit-interval utility work offline.
`discover`, `split`, `acquire`, `extract`, `resolve`, `classify`, and `build` implement
the historical 2023 staged workflow. Five-year execution is not implemented or authorized.
Read `docs/extended-workflow.md` for the historical extended config,
roster, split and separate Neo4j instance; `docs/pilot-workflow.md` records historical
two-venue paths. Not all registry venues have working source adapters/access.
`analyze` and `evaluate` remain nonzero placeholders. Resolution requires public
ORCID publication corroboration; affiliations require exact printed-institution
and authorship-specific metadata alignment. Shared provider-work/version conflicts
are withheld. Uncorroborated records remain in review. Topics are an uncalibrated
phrase baseline using a draft taxonomy, with explicit paper-text evidence separate
from roster evidence. Do not equate staged collection with release-quality coverage
or independent accuracy. Read current status/work logs before rerunning.

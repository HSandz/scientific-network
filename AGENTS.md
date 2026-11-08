# Contributor and agent instructions

## Current release plan — read first

Until the 11 November 2026 submission, all work follows
[`docs/release-plan.md`](docs/release-plan.md) under D040. Where older plans,
decisions or gates conflict with it (the P00–P10 sequence, gates G01–G12, the P02
enrichment no-go, D022–D039 source holds, readiness receipts), the release plan
wins. At session start read, in order: this file, `docs/release-plan.md`,
`docs/status.md` (phase checklist) and the latest work-log entry. Open other
documents only when a task needs a specific fact from them.

**9 November user amendment:** agents perform all feasible audit, scoring, report
and local packaging work. Human annotation is optional, not a prerequisite.
Follow [the agent audit workflow](docs/agent-audit-workflow.md) and its frozen
protocol config. The fresh-session prompt is under `docs/prompts/`. Old human
handoffs and frozen receipts remain historical; do not wait for A/B human exports.

## Project boundary

Read `docs/project-plan.md` (course brief and business questions) and
`docs/graph-schema.md` before changing graph semantics. This is a course project
for **Social Media Network Analysis for Business**, not a general research search
engine.

- Release scope (D040): AAAI and IJCAI 2021–2025 main-track papers from roster v10
  (13,617 papers), one cumulative graph. Roster v10 is final for this release: do
  not run edition, roster, source-route or rights audits. The other eligible
  editions and the 62 unresolved or unavailable candidates are reported as coverage
  limits. The 34-series 2021–2025 registry (D018) stays the long-term scope.
- Preserve `configs/corpus.yaml`, `configs/quality.yaml`, earlier roster versions,
  frozen splits and pilot artifacts for reproducibility. New behaviour gets new
  config and output versions (`*-release-v1`).
- Use Neo4j Community as the graph DBMS. The release graph goes in the isolated
  `neo4j-five-year` service; never modify the pilot or extended databases. Keep
  optional GDS compatibility work separate from the working base service.
- Preserve the five entity labels and ten predicates in `docs/graph-schema.md`.
  Change semantics, corpus boundaries, or release thresholds only with an explicit
  documented decision. Prediction and years outside 2021–2025 remain optional.
- The existing public Site is **AI Research Network — Plan & Report (2021–2025)**,
  with Plan and Report tabs (D019/D020). Report visualizations and controls must
  be native Site components, never an iframe embedding the standalone HTML.
  Preserve its project ID, URL and audience. Publish once, after the final graph
  and audit exist (release plan phase 9), with no intermediate publications. Read
  `docs/sites-workflow.md` at that point; record the receipt under `docs/reference/`
  and do not claim unattended or live synchronization.

## Evidence and scientific integrity

- Never merge researchers on normalized names alone. Preserve stable internal IDs,
  external-ID crosswalks, conflicting evidence, and reversible resolution decisions.
- Release evidence standard (D040): match official roster papers to OpenAlex works
  by the DOI derived from the official URL, with title and author-count agreement.
  A researcher is the OpenAlex author ID on a matched, name-compatible authorship
  (ORCID recorded when present, not required). Affiliation triples come from that
  authorship's OpenAlex institutions, with raw affiliation strings as evidence.
  PDF/GROBID checks are optional. The release plan lists the withholding rules.
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
- Structural validation is not semantic accuracy. Accuracy claims come from the
  frozen edge audit defined in the release plan (D040), reported with Wilson
  intervals, together with measured coverage and the topic evaluation.
- Agent judgments must be source-backed and explicitly identified as AI-assessed.
  Never present them as human annotations, independently validated gold labels or
  verified course accuracy. Wilson intervals do not cover evaluator errors.
  Record actual evaluator/model/run metadata, evidence depth and source overlap.
- For agent evaluation, delegate A/B judgments to separate fresh contexts without
  inherited conversation or shared answers when supported. Freeze blind topic
  answers before edge review exposes predictions. If isolation is unavailable,
  use the documented single-agent variant; never impersonate two reviewers.
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
  config, source, and method versions. Never invent names, student IDs, a GitHub
  URL, or measured scores.
- Commit locally at each release-plan checkpoint with a descriptive message; push
  only when the user asks.

## Task history and session handoff

- At the start of substantive project work, read the files listed under "Current
  release plan" above, then verify the actual files and Git state. Logs are
  context, not proof that older checks still pass.
- Create a work entry from `docs/templates/work-log.md` under `docs/work-log/`,
  using an unused `YYYY-MM-DD-NNN-short-slug.md` filename and matching
  `WORK-YYYY-MM-DD-NNN` ID. Use Asia/Bangkok dates and explicit timezone offsets
  for recorded times. Never overwrite another task's entry.
- Use one entry per release-plan phase or session, about one page. Record the
  objective and `in_progress` state early; checkpoint meaningful findings or a
  long-running command before an interruption can lose the handoff.
- Before the final response, finalize the entry with changes, exact checks and
  outcomes, artifacts, decisions, limitations/blockers, and a concrete next step.
  Log incomplete/blocked work too. Mark unrun checks and distinguish historical
  results from checks performed in this task. Record failures and partial results.
- Update the index in `docs/work-log/README.md`, and replace `docs/status.md`
  rather than appending to it: keep it under 60 lines and tick its phase checklist.
  Do not restate roster or assignment totals across files. Update `docs/roadmap.md`
  only when a capability changes; keep durable rationale in `docs/decisions.md`.
- Keep finalized records stable. Add dated corrections with evidence or link a
  superseding entry rather than silently rewriting the original outcome.
- Keep concise work records ready for Git alongside the related changes. Raw
  console logs and run artifacts go in a unique `reports/runs/<work-id>/` directory
  and remain ignored. Summarize commands, exit codes and key results in the work
  entry so the handoff works without local-only artifacts.
- Do not save credentials, private source text, hidden reasoning or full chat
  transcripts in the journal. Record useful observations, decisions and evidence.
  A conversational reply with no project work or state change needs no new entry.

## Current implementation

- Working offline: `schema`, structural `validate`, `audit-precision`, `analyze`
  (named projections), `freeze-audit-sample` / `score-edge-audit`, `evaluate`
  (component scoring) and `report` (standalone HTML).
- Historical diagnostics, preserved and not to be rerun: the 2023 pilot/extended
  stages (`discover`, `split`, `acquire`, `extract`, `resolve`, `classify`, `build`;
  see `docs/pilot-workflow.md` and `docs/extended-workflow.md`) and the five-year
  roster v1–v10, diagnostics, corroboration and pregraph stages (D022–D039; see
  `docs/five-year-collection.md`). Their ORCID-only identity rule was a pilot
  policy (D009) and is not the release standard.
- Current roster: `configs/corpus-five-year-v10.yaml` →
  `data/manifests/five-year-roster-v10/`. Frozen held-out assignments:
  `data/manifests/five-year-splits-v1/membership.jsonl`.
- Release-plan phase 1 tooling fixes are done (WORK-2026-11-08-026): the validator
  is indexed, the loader uses labeled `MATCH` and 5,000-row transactions and refuses
  to put a release graph anywhere but port 7689, `analyze` and the audit commands need
  no readiness receipt and record the size gates, and `audit.review_design:
  split_with_overlap` writes a review CSV plus an HTML sheet.
- OpenAlex DOI acquisition, OpenAlex-based resolution, embedding topics, the
  isolated Neo4j load and release analysis are
  already completed for the corrected graph. Do not rebuild them for an evaluator
  change. Agent provenance/ledger support and real agent evaluation are the next
  implementation/execution task; the new protocol config alone implements none.

# Decision register

| ID | Date | Decision/status | Reason |
| --- | --- | --- | --- |
| D001 | 2026-11-02 | Retain original Sites corpus, five labels, ten predicates and stronger size targets | Scaffold follows the existing plan |
| D002 | 2026-11-02 | Use `src/scientific_network/<stage>/` Python package layout | Keeps planned stage boundaries with installable/importable code |
| D003 | 2026-11-02 | Pin Python 3.12, package lock and explicit Neo4j/GROBID tags | Reproducible starting environment; service runtime still needs host validation |
| D004 | 2026-11-02 | Leave real pipeline stages explicitly pending | A scaffold must not fabricate acquisitions, graphs or scores |
| D005 | 2026-11-02 | GDS/model revision, calibrated thresholds and code license pending pilot/owner selection | Compatibility, evidence and rights have not yet been established |
| D006 | 2026-11-02 | Lecturer interpretation of accuracy and heterogeneous/derived predicates pending | Course-specific acceptance must be recorded in week one |
| D007 | 2026-11-03 | Use a short current-status page and dated per-task Markdown work records; keep raw command output under ignored `reports/runs/<work-id>/` | Humans and future agents need a portable progress history, exact verification outcomes and a concrete handoff; see [logging workflow](work-log/README.md) |
| D008 | 2026-11-03 | Freeze official roster and deterministic title-leakage groups before acquisition; pilot excludes all test groups | Live reconciliation found 5,046 eligible main papers; normalized-title grouping prevents leakage without asserting work identity. Implementation: Codex; independent review pending |
| D009 | 2026-11-03 | Pilot accepts public-publication-corroborated ORCID identities and exact printed institution plus authorship-specific provider matches; withhold other claims | Stable IDs alone can contain provider errors. Conservative corroboration and PDF-nested triples trade recall for inspectability; this is a pilot policy, not a release-quality claim. Review pending |
| D010 | 2026-11-03 | Replace GROBID 0.8.1 with pinned `0.8.2-crf`; disable external header consolidation | Official Docker documentation and registry inspection showed the original image was 12.51 GB compressed versus 536.79 MB for the CRF image. `/api/isalive` succeeded; parser method/cache version changed. Corpus/schema unaffected |
| D011 | 2026-11-03 | Load only validated, versioned pilot artifacts transactionally; refuse foreign/different-version entity IDs | Prevents silently replacing a previous graph. Replay is supported; cross-version migration needs a separate reviewed procedure. GDS compatibility remains separate |
| D012 | 2026-11-03 | Clarify R7 denominator as full official byline size, while emitting pairs only for resolved people | Using only resolved authors inflates weight on incompletely resolved papers. This explicitly supersedes the earlier resolved-author denominator wording; raw support counts, predicates and release gates stay unchanged. Offline four-author case verifies the distinction. Review pending |
| D013 | 2026-11-03 | Use an uncalibrated literal-phrase topic baseline with explicit abstention for the first pilot | Keeps evidence inspectable without downloading a model or consulting held-out papers. Draft taxonomy, exclusions/context rules and substantive-label accuracy require development annotation before freezing. No semantic accuracy claim |

| D014 | 2026-11-03 | Expand the target from the NeurIPS/ICML examples to the explicit flagship AI/related venue registry, retaining 2023; planning only, collection paused | Explicit user correction authorizes a scope change. 34 series / 31 planned editions; ECCV, NAACL and COLING have no 2023 edition. Supersedes D001's venue boundary only; five labels, ten predicates and release gates remain. Preserve legacy configs/data/splits/reports; new adapters, cross-venue leakage controls, annotation budget and resource estimates precede a separately authorized run. See [scope policy](conference-scope.md). |

Add the rationale, evidence, scope impact and reviewer to subsequent material
decisions. Preserve original requirements and old frozen audit results.

## D015 — Authorized additive expanded collection (2026-11-03)

The user explicitly requested implementation and collection, superseding D014's
collection pause. Preserve all legacy configs, 5,046 eligible roster records,
120 test / 60 development assignments and 100 diagnostic papers. New executable
`configs/corpus-extended-v2.yaml` is separate from the historical planning registry.
Every one of the 34 series gets an edition ledger status; inaccessible, unverified
and no-edition cases do not masquerade as collected. Public official proceedings
remain track authority; do not bypass access restrictions.

Freeze supplemental samples before detail/API/PDF enrichment: 60 test / 30 dev
groups for editions with at least 100 independent eligible groups; otherwise
reserve floor(20%) test (minimum 1) and max(10, floor(10%)) development. Add ten
diagnostic papers from development per available new edition. This is a staging
and annotation allocation, not a changed release gate or completed audit. Reserve
all title-matched versions of old test papers; quarantine other cross-venue/version
collisions from acquisition rather than treating normalized titles as work identity.
Old exposed pool/development IDs never become new independent test examples.

Use a separate Neo4j Community service/volume on localhost:7475/7688 for the
expanded graph. Retain the original database; no destructive migration. Keep
conservative ORCID and printed authorship-specific affiliation acceptance, draft
topics and all release thresholds. Large rosters alone cannot establish accuracy.
Implementation/review: Codex; independent human review remains pending.

D015 implementation details: COLT retains Original Papers, excluding front matter
and the Open Problems section; AAMAS retains regular research sessions, excluding
Blue Sky, Innovative Applications, poster extended abstracts, demonstrations and
doctoral material. These are conservative explicit track maps; exclusions remain
visible for review. MICCAI's accepted-title roster has no bylines: freeze title
groups first, then require an authoritative detail byline before work matching or
accepting a core paper. Failure is explicit, not inferred authorship. CoRL repeats
two identical official records under presentation headings; collapse only identical
rows, reject any conflicting title/byline/track. RSS XIX→2023 is corroborated by
the publisher's master volume page, whose hash and required text are pinned.

D015 provenance/version safeguards: R3 points to the official roster; topic spans
point to the actual detail/title/abstract source, with a separate evidence ID and
versioned classifier method. A shared matched provider work across two official
records blocks both from core graph admission pending version review; it does not
silently merge publications or inflate paper/citation counts.

## D016 — Standalone read-only visual report (2026-11-03)

The user requested HTML visualization of the existing output. Provide an offline,
self-contained report generated from a versioned graph, matching recorded metrics
and hashed quality/scope configs. No collection, database writes or semantic
threshold changes are needed. Preserve all input artifacts and refuse existing
output paths. Separate global snapshot statistics from filtered graph counts;
conference filters follow supporting papers and exact affiliation triples. Keep
social weights as stored and disclose that filtering does not recompute them.
Use seeded NetworkX/NumPy coordinates only for display, preserving typed isolates
in social views. NumPy is explicit in the locked core dependencies.

Embed public entity metadata, evidence references and short topic phrases; omit
full abstracts and arbitrary node properties. Embed licensed fonts and include
SIL OFL text. Distinguish freshly checked structure/hashes from historical source
and database checks; the report does not measure accuracy or replace the final
course report. Implementation/review: Codex; independent semantic audit pending.
See [report documentation](visual-report.md) and
[task 007](work-log/2026-11-03-007-html-report.md).

## D017 — Input-bound development source review (2026-11-04)

Use the ACL article's unique visible publication byline when it agrees in full
order with the frozen roster; retain citation-export name differences as separate
evidence. Preserve Unicode letter tokens during name comparison. This fixes
erased Chinese-script names without creating transliteration aliases or permitting
name-only identity merges. Keep complete ordered OpenAlex matching and public
ORCID publication corroboration unchanged. Resumable acquisition may reuse only
successful records bound to the same frozen manifest, membership and roster.

PDF inspection can still contradict an HTML byline. The reviewed diagnostic set
has three retained papers and two withheld core records: EACL 2023 main 280 has
a different printed author order; the MLSys record has nine PDF authors versus
eight in HTML. Preserve these conflicts and all original files. A source-parser
recovery is not automatic core admission or researcher identity acceptance.

Allow explicitly reviewed printed author–paper–organization observations only
after identity acceptance, with exact institution agreement on that author's
matched provider authorship. Bind decisions to the full input, individual record
and cached PDF hashes; require byline position, printed locator and decision ID.
Merge support for an existing deterministic triple rather than duplicating it.
Do not expand aliases, assign other authors' institutions, or relax thresholds.
The five reviewed observations in this task corroborate existing triples: GROBID
repeated combined institution lists under several authors, but the provider
intersection had already retained their correct organizations. Triple totals
remain 38. The review ledger adds direct printed-source support.

The offline `review` utility preserves every original queue row and source hash;
its decisions are technical triage, with no graph overrides. Accepted-claim checks
test stored byline/ORCID/TEI consistency, not independent semantic correctness.
The input-bound source ledger separately records the agent's development review.
No held-out papers, release gates or database version policies change. Candidate
outputs remain separate from loaded graphs until a safe migration is implemented.
Implementation/review: Codex; independent human adjudication remains pending.
See [review results](../reports/evidence-review-v1.md) and
[task 008](work-log/2026-11-04-001-evidence-review.md).

## D018 — Five-year core scope, planning only (2026-11-04)

The user extends the core release to **2021–2025**, retaining 34 flagship series.
This supersedes D014/D015's 2023 release boundary. The current request pauses
further pipeline implementation/collection despite historical D015 authorization;
documentation and Site presentation work are authorized. No new discovery,
academic API/PDF request, split, pipeline feature or graph import.

Preserve old configs, frozen inputs/memberships, measured artifacts and reference
snapshots. Add `configs/conference-scope-2021-2025.yaml` as a non-executable planning
registry. Its 170 venue–year candidates are review slots, not confirmed editions.
Verify each edition/year/track/access, including series with no 2023 edition;
do not infer five editions per series or substitute years. Keep five labels,
ten predicates and release thresholds. Deduplicate works/people over the union;
recompute annual/cumulative support within explicit windows. Protect cross-year
versions of old tests, budget annotation prospectively and disclose citation-age/
snapshot bias. No 2023 count becomes a five-year result. Re-estimate resources,
schedule and samples before a later implementation instruction.
See [temporal design](five-year-scope.md). Requested by user; documented by Codex.

## D019 — Existing Site for Plan and evolving Report (2026-11-04)

Retain project `appgprj_6ae7698b8b2881919d49df2426c517a2`, current public audience
and URL. Rename it **AI Research Network — Plan & Report (2021–2025)**. Preserve
the full Plan; add a dated Report combining measured progress and the existing
2023 HTML explorer. Separate loaded graph (399/533), local candidate (402/538),
Plan targets and historical checks.

Refresh/publish Report after material project iterations from permitted versioned
evidence. Preserve Site source history, dated snapshots and receipts. This is
task-driven publication, not unattended sync or authorization for research
collection. Do not create a schedule, change audience or replace the required
final ≥10-page report. [Workflow](sites-workflow.md). These presentation changes
are authorized; pipeline changes remain paused by D018.


## D020 — Native Report integration in the existing Site (2026-11-04)

The user explicitly rejects embedding the standalone HTML report. Clarify D019:
merge graph visualization, projections, conference/name filters, charts, coverage,
evidence inspection and exports directly into the Site's Report DOM. Share its
editorial palette, typography, Plan/Report navigation and publication history.
Use namespaced IDs and scoped styles/scripts; preserve the full 20-section Plan.
Remove the iframe, separate deployed explorer page and its open-separately flow.

Reuse the exact permitted payload of the 399-node / 533-edge historical report,
`pilot-topic-d512d7239923`, without recollection or scientific recomputation.
Keep the separate 402/538 candidate clearly labeled, and preserve the original
standalone offline HTML and historical receipts/logs. Report hash and structure
checks as their original task 007 results, not newly rerun scientific checks.
The current five-year target remains planning-only under D018. Task-driven Site
updates remain required; no live Neo4j connection or background synchronization.
See [Site workflow](sites-workflow.md) and
[WORK-2026-11-04-003](work-log/2026-11-04-003-native-site-report.md).

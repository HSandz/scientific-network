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
| D032 | 2026-11-07 | Add count-reconciled MICCAI 2021/2023/2025 rosters; hold 2022/2024 unresolved | Preserve source/index counts separately, retain D015 byline requirements, do not redistribute per-record metadata; no scope, threshold, split or enrichment change |
| D035 | 2026-11-07 | Keep ACM Multimedia 2024 unavailable pending complete roster and track/proceedings reconciliation | Official ID file has 1,149 unique numeric values while the research-track statistics report 1,150 acceptances; do not infer the missing record or track boundary. No roster, split, enrichment or graph change |
| D036 | 2026-11-07 | Keep ICDM 2021 unresolved pending proceedings reconciliation and reuse authorization | The official list has 197 IDs and the schedule's 42 additional IDs are in separately named workshop/PhD Panel events; IEEE Xplore returned HTTP 418 and source ownership/reuse terms remain unclear. No roster or frozen assignment change |
| D037 | 2026-11-08 | Keep ICDM 2025 unresolved pending final proceedings reconciliation and reuse status | The hash-bound accepted list has 105 Regular and 70 Short entries, but the CFP's no-short-track language, incomplete program join, unavailable publisher index and unclear metadata reuse status leave final main-proceedings membership unresolved. No roster or frozen assignment change |
| D038 | 2026-11-08 | Keep ACM Multimedia 2024 unavailable after browser-source follow-up | The official call clarifies length-neutral regular-paper review and says BNI acceptances appear in main proceedings, but the 1,149/1,150 count conflict, incomplete program join and unknown metadata reuse terms still prevent roster closure. No roster or frozen assignment change |
| D040 | 2026-11-08 | Release reset for the 11 Nov submission: AAAI + IJCAI 2021–2025 graph from roster v10 with DOI-matched OpenAlex evidence, embedding topics and a feasible frozen audit; source closure stops | P01 cannot close by the deadline, the D009 pilot rules yield too little to form a network, and no release graph or report exists. See [D040](#d040--release-reset-for-the-11-november-submission-2026-11-08) and the [release plan](release-plan.md) |

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


## D021 — Deadline-driven execution readiness, planning only (2026-11-06)

The user accepted the proposed execution-plan task and confirmed **11 November
2026** as the deadline, asking to ignore the remaining capacity/lecturer questions.
Do not make those answers prerequisites or infer committed reviewer hours. Keep
existing proposed accuracy interpretation and release gates; no new thresholds.
Use internal cutoff proposals on 8–10 November, protect writing/evaluation time,
and disclose partial delivery if independent evidence is insufficient. No claim
that the five-year release or audit fits the remaining calendar.

Produce a 170-row **planning** queue from the unchanged registry, with every
candidate pending new-scope verification. Historical 2023 roster statuses remain
context only. Estimate resources with explicitly hypothetical paper counts and
review-time ranges; cached extraction timings are not cold benchmarks. Preserve
all historical inputs/configs/splits/graphs and earlier reference snapshots.

The user's “proceed” authorizes this plan and native Site updates, not E01–E09
execution. D018's source-discovery/collection/pipeline/split/import pause remains.
Future work needs a later explicit instruction. Use proposed new versions and
isolated Neo4j storage rather than overwriting current snapshots. See
[execution plan](five-year-execution-plan.md) and
[WORK-2026-11-06-001](work-log/2026-11-06-001-five-year-execution-plan.md).

## D022 — Authorized five-year staged collection (2026-11-06)

The user explicitly requested “now start data collecting, based on the plan”.
This supersedes D018's execution pause for necessary implementation and staged
2021–2025 collection under the existing scope and gates. D018 remains the scope
and reproducibility decision; the unchanged planning registry is a historical
snapshot, not an executable config. No paid services, threshold relaxation or
historical database replacement is authorized or required.

Start E01–E03 with `configs/corpus-five-year-v1.yaml`, additive official catalog/
roster adapters and `data/manifests/five-year-roster-v1/`. Every one of the 170
candidates must retain a ledger record, including blocked sources, unsupported
layouts, nonresearch exclusions and unresolved/missing routes. Missing links or
HTTP failures do not prove that no edition existed. A retrieved catalog does not
establish an eligible edition. Partial multi-page editions cannot enter sampling.
Official year/track routes, hashes, retrieval dates and unknown rights stay explicit.

This first executable version is **roster-only**. Cross-year/version and exposure
reconciliation, a prospective frozen sampling design, new enrichment contracts,
isolated graph import and independent evaluation remain required ordered work
before their respective stages. Do not apply the historical split/acquisition
implementation to the new config. Preserve all original IDs and frozen memberships;
no names are merged and no new graph/release-quality claims follow from rosters.
See [collection work entry](work-log/2026-11-06-002-five-year-collection.md).

## D023 — Corrected roster contracts and prospective five-year diagnostics (2026-11-06)

Continue D022 under the user's “proceed” instruction. Preserve roster/reconciliation
v1 and every original/expanded assignment. Create roster v2 for source-layout fixes:
NeurIPS position-track papers are outside main research; ECVA eligibility requires
the edition accordion and paper path to agree; RSS years require official catalog
edition/date evidence plus matching Roman numeral on the proceedings page. KR
Full/Short Papers (2021) and Main Track count; named special/application tracks are
excluded under the existing main-track policy. Unknown tracks still require review.
These mappings implement the existing boundary, without relaxing gates.

Freeze a bounded **development diagnostic** design before enrichment. Strata are
source-adapter family × conference year among eligible, new, unexposed singleton
leakage candidates. Reserve five test groups then two development diagnostics per
stratum by a recorded seeded uniform permutation, or fail if a stratum cannot
support it. All other new independent groups enter pool. Preserve the complete
14,909 historical assignments unchanged; previously reserved/exposed records are
not eligible for fresh tests. Quarantine ambiguous/changed/mixed-exposure groups.
Record population, selection probabilities, manifest/config/ledger/triage hashes
and seed. This is a layout/year coverage diagnostic with a reserved component test,
not the final 600-edge audit or a representative all-venue semantic accuracy claim.

Title similarity guards leakage but never proves a canonical merge. Preserve a
provisional identity per official record and review same-title/identifier versions.
Later provider-ID/version conflicts trigger quarantine, never a new test allocation
or development exposure of old tests. Canonical work resolution and independent
human scientific evaluation remain incomplete; disclose alternate-title detection
limits. Metadata acquisition is bounded to the frozen development IDs and existing
free API allowance, with immutable evidence and explicit failures. No graph import
or historical DB replacement in this iteration. See task WORK-2026-11-06-003.

## D024 — Frozen development PDF headers and source candidates (2026-11-06)

Under D022 and the user's next “proceed”, implement bounded PDF/header extraction
for exactly the 68 D023 development records, with every frozen input hash and
held-out group checked before source access. Use a separate extraction config;
do not modify the frozen sampling/metadata config. Preserve original acquisition
and legacy PDF/TEI artifacts. Disable GROBID external consolidation and keep PDFs,
TEI, full abstracts and source review observations local/ignored. Unknown rights
do not grant redistribution; only aggregate measurements go to the public Site.

A withheld metadata record may have its official PDF inspected for source-review
evidence, without changing acquisition status, accepting aliases or admitting graph
support. Record PDF/header title and complete ordered byline agreement separately.
Header author names must be unique within the paper before proposing positional
affiliation bindings. Exact printed institution matches may use only that author's
complete matched provider authorship; never the paper-wide institution union.
Deduplicate repeated printed observations and preserve every TEI locator.

All resulting author–paper–organization records remain **review candidates**.
GROBID nesting and metadata agreement are development evidence, not a verified
printed-marker mapping, accepted person identity, independent semantic audit or
graph edge. Public ORCID publication corroboration, canonical work/version review
and source-specific marker verification are still required before acceptance.
No model thresholds, edge semantics or release gates change. No new graph/import
in this iteration. See WORK-2026-11-06-004.

## D025 — Reviewed source overlays and public identifier corroboration (2026-11-06)

Continue D022 under the user's “proceed” instruction with Docker restored. Keep
the original 68 metadata/header records, two GROBID failures, every frozen test
assignment and both databases unchanged. Create source corrections as explicit,
input/PDF-hash-bound review records, never a global author alias or parser-score
override. The printed COLT author blocks exclude the labelled editors; the RSS
headers/markers are available through reviewed rendered pages despite unavailable
machine-readable text. Label these as **printed-source reviews**, not successful
GROBID/OCR parses. The MLSys printed byline corroborates the roster while its
citation export abbreviates a name; preserve the original failed metadata status
and attach the reviewed bibliographic observation in a new staging version.

For the frozen development sample only, stage person/publication support using
complete ordered provider authorships plus unambiguous stable ORCID/OpenAlex IDs
and public ORCID work corroboration. A typed DOI match or Unicode-preserving exact
title with publication-year corroboration is required; no name-only clustering.
Quarantine shared provider works, historical/test version links, conflicting
provider–ORCID crosswalks and contradictory source bylines. Preserve stable
internal researcher IDs and all rejected/uncorroborated mentions with reasons.

Accepted affiliation support additionally requires reviewed printed author/marker
evidence and an exact institution match within that same provider authorship.
Other TEI/metadata candidates remain review. Deduplicate support by paper and
canonical institution; store triples before any aggregation. Accepted here means
the implemented development evidence contract, not independently measured semantic
accuracy. Global canonical work resolution, final human audit, graph materialization
and isolated DB import remain subsequent work; no DB writes in this iteration.
No release threshold, predicate, corpus boundary or model threshold changes.

## D026 — Pregraph evidence closure without graph construction (2026-11-06)

The user requests finishing remaining preparation before building the graph.
Continue source inspection on the already frozen development sample, add
input/PDF-bound reviewed bylines and author-specific printed affiliation mappings,
and preserve all original failures, conflicts and frozen tests. Do not force
acceptance when a source is missing or contradictory. A final withheld disposition
closes a development triage action; it does not improve coverage or satisfy a gate.

Stage canonical work crosswalks, citations, organization crosswalks and topic
candidates before graph construction, with immutable input/output hashes, complete
claim dispositions and explicit readiness gates. Shared provider/DOI/version links
must be quarantined across the whole known roster, including reserved IDs, without
acquiring held-out content. Title matches can guard leakage but never merge works.
An accepted diagnostic singleton means no conflicting version in the known frame,
not exhaustive global canonical identity or complete five-year coverage.

Freeze a reproducible pregraph bundle only for the actual inspected population.
Keep full-scope edition, enrichment, canonical-work and independent annotation gaps
explicit and return nonzero for unmet full pregraph gates. No new graph JSON,
node/edge materialization, derivations, Neo4j services/imports or DB writes in this
task. Existing schema, release thresholds and ORCID/publication requirements stay
unchanged. Topic phrase outputs remain uncalibrated review candidates; no independent
accuracy, recall or F1 can be inferred from agent review or software tests.

## D027 — Bounded official OJS source recovery with frozen leakage guards (2026-11-06)

Under the user's instruction to proceed with source/evidence recovery, add a new
roster-only v3 overlay for AAAI and ICAPS. Inherit the other 160 edition observations
from the input-hashed v2 baseline without re-dating or retrying unavailable hosts.
Preserve every prior manifest, development/test membership, reviewed support table,
pregraph freeze and loaded graph. Do not expand enrichment or construct a graph.

Follow the official journal's linked archive pages until the 2021 boundary is
crossed or the archive ends, within a fixed page budget. Require monotonic year
evidence, unique official issue URLs, complete AAAI technical/publication issue
sequences, exact archive/issue heading agreement and complete article sections.
Any missing page/issue, access failure or unknown track prevents edition eligibility.
Stop journal retrieval after an access failure; do not bypass restrictions.

AAAI main technical issues/sections qualify under the existing main-only policy;
special/IAAI/EAAI/student/demo issues are recorded as excluded catalog routes and
are not fetched. Their unobserved article counts remain unknown. ICAPS's explicit
Main Track qualifies; separately labelled special/application tracks and editorial
or position material are excluded. Unknown 2025 research categories remain review
until official main-track corroboration; do not relabel them from their names alone.
This operationalizes the existing boundary and does not expand eligible tracks.

Run roster-only leakage triage using the union of historical and five-year roster
evidence plus the current frozen membership (including all 170 new test groups).
Hash-check every frozen input and verify earlier assignments match before source
access. Equal titles quarantine candidate versions, never merge papers or people.
No new split, canonical merge, accepted researcher/affiliation/topic, independent
semantic score, graph artifact or DB write is produced by this recovery.

Source inspection in this iteration identified four literal main-technical heading
variants within archive-verified AAAI Technical Tracks issues: three 2021
`AAAI Technical Track Focus Area on ...` sections (Neuro-Symbolic AI; AI Responses
to the COVID-19 Pandemic; AI for Conference Organization and Delivery) and 2024's
`Intelligent Robots (ROB)`. V5 recognizes only these exact edition-bound headings,
retains their source/section locators and never repairs missing bylines this way.
V3's older-archive-title failure and v4's conservative unknown-section results
remain immutable. V4 stops after the first corroborated pre-2021 issue, avoiding
parsing irrelevant older titles without guessing the year of any target issue.

## D028 — Complete pregraph prerequisite plan; documentation only (2026-11-06)

The user requested a Markdown plan for everything remaining before final graph
construction and explicitly deferred implementation. The
[pregraph completion plan](pregraph-completion-plan.md) organizes P00–P10 and
twelve preparation gates around official scope closure, resource feasibility,
prospective leakage-safe sampling, calibrated methods, population evidence,
independent component review and reproducible accepted support tables/tooling.
This records a planning sequence, not a newly implemented or passed capability.

Retain D018/D022's 2021–2025 scope, existing schema, acceptance thresholds,
corroboration rules and every historical/new frozen assignment. No source access,
implementation, collection, new split, annotations, service operation, graph build
or Site publication is authorized by this document-only iteration. Existing
execution decisions remain historical context; a later instruction must initiate
execution of this plan.

An operationally closed access/review item is not successful scientific coverage.
Diagnostic preparation v3 stays input-bound and not ready; a future release needs
a genuine population-capable readiness evaluator and immutable new artifacts,
not manually changed flags. Unmet evidence, resources or independent-review gates
must be recorded as no-go, even if the deadline arrives. Actual final graph/import,
uniform-edge audit, graph statistics/findings and final report results necessarily
follow construction; prepare their tooling/protocols without claiming results now.

## D029 — ICAPS 2025 roster correction and enrichment no-go (2026-11-07)

Use a new roster-only v6 to resolve ICAPS 2025 using the official main technical
call, the conference's topic-based track policy, and its accepted-paper page. The
48 theoretical/algorithmic/modelling/tools OJS records match accepted publisher
IDs and qualify as main research papers under the existing scope. Keep the three
position papers excluded under the existing main archival research rule, and keep
front matter excluded. Do not change the five-year boundary, schema, thresholds,
or any older roster/config/frozen assignment. V1–v5 and the v2-bound diagnostic and
pregraph artifacts remain unchanged.

P01 remains incomplete with 81 edition gaps. For P02, do not begin broader paper,
ORCID, PDF, model, or annotation enrichment until the canonical population, P03
prospective frame, live free-resource limits, storage budget, and actual reviewer
capacity can be measured. This is a current no-go, not a full-release cost estimate
or a decision to reduce the release scope. See the [source triage](five-year-source-triage.md),
[v6 measured report](../reports/five-year-source-recovery-v6.md), and
[P02 feasibility checkpoint](../reports/five-year-pregraph-feasibility-v1.md).

## D030 — Official route closure and COLING joint-edition mapping (2026-11-07)

Apply authoritative edition-history evidence to the 11 previously unverified
routes. Record ICCV 2022/2024, ECCV 2021/2023/2025, NAACL 2023, EACL 2022/2025,
and COLING 2021/2023 as verified no-edition candidates. Add the complete official
LREC-COLING 2024 proceedings roster to the in-scope COLING series. Every joint
paper receives one primary series (`venue:coling`) and a crosswalk to the joint
event and LREC co-host; do not duplicate LREC papers or add LREC as a new series.
One volume-frontmatter record remains excluded. The edition evidence and source
hashes are in [source corrections v5](../data/manifests/five-year-source-corrections-v5.json).

This applies the current 34-series boundary and existing one-primary-venue rule;
it does not change conference scope, track thresholds, graph semantics, or quality
gates. Roster v7 remains roster-only: 30 unsupported-adapter editions and 40
publisher-access editions remain gaps. Do not begin broader enrichment or graph
construction; P02/P03 gates remain open. See the [v7 source report](../reports/five-year-source-recovery-v7.md)
and [current source triage](five-year-source-triage.md).

## D031 — AAMAS official roster closure and 2023 reconciliation hold (2026-11-07)

Create a new roster-only v8 overlay for AAMAS 2021, 2022, 2024 and 2025. Apply
D015's existing regular-research policy to the explicit official sections: Main
Track (2021: 151; 2022: 166), Full Research Papers (2024: 230), and Research Paper
Track (2025: 260). Keep other identified sections excluded. This is an application
of the existing venue policy, not a track/scope or quality-threshold change.

Keep AAMAS 2023 unresolved. Its official news page announces 237 full papers and
221 extended abstracts, while the accepted-paper page lists 237 full papers and
219 extended abstracts. A bounded exact-title reconciliation maps 225 of 237 full
paper titles to the proceedings contents; 12 titles remain unmatched, and 35 of
the exact-title matches have different author strings. Session/poster contents do
not provide a reconciled boundary. Do not infer stable publication IDs, fill title
differences, or promote the year from these partial joins.

The IFAAMAS notices allow limited personal/classroom copying with attribution and
require prior permission or a fee for republication/redistribution. Keep detailed
rosters in the ignored local cache/output; publish only credited aggregate counts.
No PDFs, enrichment requests, new splits, canonical merges, graph construction or
database writes are part of v8. Preserve all v1–v7 outputs and the v2-bound
diagnostic/pregraph artifacts. See [source correction v6](../data/manifests/five-year-source-corrections-v6.json),
[v8 recovery report](../reports/five-year-source-recovery-v8.md), and
[current source triage](five-year-source-triage.md).

## D032 — MICCAI roster closure and unresolved edition counts (2026-11-07)

Create a new roster-only v9 overlay on the immutable v8 baseline. Add MICCAI 2021
(531), 2023 (730), and 2025 (1,027) from captured official conference/Society
accepted-paper lists that match the year-specific Springer full-paper descriptions.
The 2025 Society final acceptance update also reports 1,027. The 2021 and 2023
lists expose titles and record identifiers without bylines; 2025 provides BibTeX
names. Under D015, names/roster presence alone do not establish person identities
or accepted graph claims, and authoritative detail bylines remain required before
work matching or core-paper acceptance.

Keep MICCAI 2022 unresolved: the official accepted-paper route returned HTTP 522;
the Springer volume describes 574 revised full papers while its series index
displays 576. Keep MICCAI 2024 unresolved: the Society list has 856 numbered
records while Springer reports 857 accepted full papers. The series index also
displays 857 for 2024. These catalog counters remain separate from accepted-paper
counts; do not infer missing records or expand track scope. Source responses and
aggregate dispositions are hash-bound in [source corrections v7](../data/manifests/five-year-source-corrections-v7.json).

Captured pages establish official source/count findings, not permission to
redistribute per-record roster metadata. Keep the detailed source captures and
full rosters in ignored local storage; publish aggregate counts and official links
only. Download no PDFs. Do not change the 2021–2025 boundary, existing track
policy, schema, thresholds, frozen assignments, D022 collection gates, P02 no-go,
or the v2-bound diagnostic/pregraph inputs. V9 adds 2,288 roster observations;
the ledger has 97 eligible editions / 10 verified no-edition findings / 23
unresolved roster/adapter editions / 40 access-unavailable editions. All 76,629
frozen assignments, including 1,095 tests, remain guarded. See the [v9 recovery
report](../reports/five-year-source-recovery-v9.md), [edition ledger](../reports/five-year-edition-ledger-v9.csv),
and [source triage](five-year-source-triage.md). Requested by user; implemented by Codex.


## D033 — MICCAI 2024 full-proceedings reconciliation (2026-11-07)

Create a roster-only v10 overlay on immutable v9. The official MICCAI Society
accepted-paper list contains 856 unique numbered research records. Reconcile it
one-to-one against all 12 Springer main-proceedings volumes: 49 captured contents
pages contain 857 unique chapters. The complete matching comprises 836 exact-title
matches and 20 unique title-and-byline matches; the one remaining publisher chapter
is a correction notice linked to an already-listed accepted paper. Exclude that
nonresearch correction and include the 856 Society research records under the
existing D015 policy. No guessed paper or new track is added.

Bind the official pages, hashes, per-volume counts, rights caveat and matching
metrics in [source corrections v8](../data/manifests/five-year-source-corrections-v8.json).
Keep full captures and per-record rosters local and ignored; publish aggregate
counts and official links only. Preserve all prior roster versions, the 76,629
frozen assignments (including 1,095 tests), and the v2-bound diagnostic/pregraph
inputs. V10 has 98 eligible editions, 10 verified no-edition findings, 22 unresolved
roster/adapter editions and 40 access-unavailable editions; its 94,857 observations
include 91,355 and exclude 3,502. P01 remains incomplete and P02 remains no-go for
broader enrichment. No splits, enrichment, PDF downloads, graph writes or DB
operations are part of D033. See the [v10 report](../reports/five-year-source-recovery-v10.md),
[ledger](../reports/five-year-edition-ledger-v10.csv), and [source triage](five-year-source-triage.md).
Requested by user; implemented by Codex.

## D034 — MICCAI 2022 official route follow-up (2026-11-07)

Keep MICCAI 2022 unresolved and ineligible under P01. The direct official Society
accepted-paper index has 573 unique paper-detail records (the topic-category page
has 572); the eight official Springer main-volume tables contain 576 chapter DOI
records, while their set description states 574 revised full papers and the series
index displays 576. A normalized-title join finds 558 unique exact-title pairs;
15 accepted-index records and 18 publisher chapters remain outside that join,
including three publisher correction titles. No byline adjudication was completed
for the title differences, and the official program documents do not resolve the
one-record count discrepancy. Do not infer a missing/duplicate paper, change track
scope, or promote the edition from these counters.

Hash-bind the official route and volume-page captures in [source corrections v9](../data/manifests/five-year-source-corrections-v9.json).
Keep raw pages and program PDFs ignored; do not publish the per-record listings or
download paper PDFs. Preserve v10 as the current roster, all frozen assignments,
and the v2-bound diagnostic/pregraph inputs. P01 remains failed and P02 remains
no-go for broader enrichment. See [source triage](five-year-source-triage.md)
and [WORK-007](work-log/2026-11-07-007-miccai-2022-source-followup.md).
Requested by user; implemented by Codex.

## D035 — ACM Multimedia 2024 official-source hold (2026-11-07)

Keep ACM Multimedia 2024 `access_unavailable` in roster v10. The locally captured
official `accepted_papers.txt` contains 1,149 unique numeric values (5,497 bytes,
SHA-256 `00441e7cd5f52a8030d6b5d316c66bae7707021fddb2a3647c3dd1e0d2c25fc2`).
The official ACM Multimedia research-track statistics page reports 4,385
submissions and 1,150 acceptances (26.20%) for 2024; its captured page is 43,256
bytes, SHA-256 `1b3428b0a898f66dc92a5bd517f882d06dada0164d805cabae627107cda05a47`.
The conference-hosted regular-papers URL returns a 7,508-byte JavaScript shell
(SHA-256 `24131a90c6f898357a100157e932bbc6e8d2c0651c6075207bcad09e71eae544`)
without the accepted records. The official file index also lists the full program
and a separate Brave New Ideas call; Search-rendered text says BNI papers appear
in the main proceedings, but those views are not locally hash-bound.

The source does not explain the one-record difference, define the numeric-ID
schema, resolve whether a separate archival track belongs in this roster, or
provide a complete official accepted-to-proceedings crosswalk. Bulk metadata reuse
terms are unverified. Do not guess a missing record, include or exclude a track
from counts alone, or promote the edition. Keep the captures ignored under
`reports/runs/WORK-2026-11-07-017/`; publish aggregate counts and official links
only. All 42 v10 output hashes and all five configured frozen-input hashes were
verified. The 76,629 assignments, including 1,095 tests, remain unchanged. P01
still has 62 incomplete candidates; P02 remains no-go with one reviewer of
unknown hours and a second independent reviewer unconfirmed. No scope, threshold,
split, enrichment, PDF, graph or database change. See [source triage](five-year-source-triage.md#
acm-multimedia-2024-official-source-follow-up-work-017) and
[WORK-017](work-log/2026-11-07-017-p01-acmmm-2024-source-closure.md).
Codex recorded this source hold; the user authorized continuation under D022.

## D036 — ICDM 2021 official-source hold (2026-11-07)

Keep ICDM 2021 unresolved and ineligible in roster v10. The official accepted list
contains 197 unique DM IDs (98 Regular and 99 Short); all occur in the official
schedule. The schedule contains 239 unique IDs, with the additional 42 occurring
in separately named workshop events (40) and a separate PhD Panel event (2).
The conference call states that accepted conference papers appear in IEEE
Computer Society proceedings. The separate PhD Forum call accepts doctoral
submissions and says those accepted papers appear in IEEE proceedings, but no
record-level link was established between its proceedings and the two PhD Panel
items. The direct local IEEE Xplore proceedings request returned HTTP 418; no
bypass was attempted, and no complete proceedings crosswalk was captured.

The University of Auckland copyright page distinguishes University-owned from
third-party material. The captured conference pages do not state who owns or may
authorize bulk reuse of the accepted-paper metadata, so reuse permission is not
established. Do not infer a permission grant from hosting domain or public
accessibility. Preserve the official counts and named event distinctions, but do
not add the records to v11 or publish per-record metadata. Keep the 76,629 frozen
assignments and all v10 artifacts unchanged. P01 remains partial; P02 remains
no-go with one reported reviewer of unknown hours and a second independent
reviewer unconfirmed. See [source triage](five-year-source-triage.md#icdm-2021-official-accepted-list-follow-up-work-018)
and [WORK-018](work-log/2026-11-07-018-icdm-2021-source-closure.md). The
source hold is recorded by Codex under the user's D022 continuation instruction.

## D037 — ICDM 2025 accepted-list audit (2026-11-08)

Keep ICDM 2025 unresolved in roster v10. Fresh direct captures of the official
accepted-page, main call, BlueSky call and program routes returned HTTP 200 and
are hash-bound in [source corrections v10](../data/manifests/five-year-source-corrections-v10.json).
The accepted page has two complete, sequential tables with 105 Regular and 70
Short entries (175 unique IDs). The main CFP says accepted conference papers go
to IEEE Computer Society proceedings, conditions inclusion on registration and
presentation, and states there is no separate short-paper submission track; the
accepted-page Short Papers heading leaves the classification of those 70 entries
unclear. The BlueSky call says its accepted papers appear in separate workshop
proceedings.

The official program capture contains 97 distinct DM IDs, 95 also on the accepted
page; 94 accepted titles match program text after normalized exact-title
comparison. This is not a complete publication crosswalk. The candidate IEEE
Xplore proceedings route returned HTTP 418 to a direct HEAD request. No bypass was
attempted. The captured pages provide no metadata license or bulk-reuse grant; a
generic footer link points to University of Auckland copyright terms without
establishing ownership or permission for this page's content. Keep detailed data
in ignored local captures; publish only aggregate counts and official links.

No v11 config or roster was created. V10 remains at 98 eligible / 10 verified
no-edition / 22 unresolved / 40 access-unavailable editions, with 94,857
observations (91,355 included; 3,502 excluded). All 76,629 frozen assignments,
including 1,095 tests, remain unchanged. P01 remains incomplete and P02 remains
no-go: one reviewer is reported, exact hours are unknown, and no second
independent reviewer is confirmed. No split, enrichment, paper PDF, graph or
database operation occurred. See [source triage](five-year-source-triage.md#icdm-2025-official-accepted-list-audit-work-020)
and [WORK-020](work-log/2026-11-07-020-icdm-2025-offline-source-audit.md).
This is a year-specific 2025 finding; D036 remains specific to ICDM 2021.
Recorded by Codex under D022 and the user's proceed instruction.

## D038 — ACM Multimedia 2024 browser-source follow-up (2026-11-08)

Keep ACM Multimedia 2024 `access_unavailable` in roster v10 after WORK-021. The
connected browser retrieved the conference-hosted accepted-ID file; its decoded
5,497-byte body exactly matches WORK-017's hash
`00441e7cd5f52a8030d6b5d316c66bae7707021fddb2a3647c3dd1e0d2c25fc2` and still
contains 1,149 unique numeric IDs. A current local `curl` request failed with
exit 6 because the host did not resolve.

The official [regular-paper call](https://2024.acmmm.org/regular-papers) says
there is no long/short distinction and all regular papers undergo the same review
process. The separate [Brave New Idea call](https://2024.acmmm.org/files/MM24_BNI.pdf)
says accepted BNI papers are full papers in the main proceedings, with a separate
committee and review criteria. These call pages and the five-page
[full program](https://2024.acmmm.org/files/MM24-Full_Program.pdf) were available
as connected-browser/Search/MarkItDown rendered views, not locally hash-bound
source captures. A diagnostic parse found only 63 explicit `Paper <id>` labels in
the rendered program and did not produce a complete accepted-paper crosswalk.

The existing research-track statistics still report 1,150 acceptances. The
program and call views do not reconcile that count to the 1,149 accepted-ID file,
and no applicable bulk metadata reuse terms were found. Do not infer the missing
record, treat the program's visible labels as a complete roster, or create a new
roster version. Preserve D035's original hold, v10, and all frozen assignments.
No split, enrichment, paper PDF, graph or database operation occurred. See the
[source triage](five-year-source-triage.md#acm-multimedia-2024-browser-source-follow-up-work-021)
and [WORK-021](work-log/2026-11-08-021-acmmm-2024-browser-source-review.md).

## D039 — CIKM 2025 browser-source audit (2026-11-08)

Keep CIKM 2025 `access_unavailable` in roster v10 after WORK-022. Hash-bound browser
captures cover the official accepted-paper page, proceedings page, and Full,
Short, and Applied Research calls. The accepted page contains 827 unique IDs:
436 Full Research, 185 Short Research, 93 Applied Research, 52 Resource, 37
Demo, 11 PhD Symposium, and 13 Industry Day entries. The Full and Short
categories are 621 candidate main-research records under the existing policy;
the separate Applied Research call says it is unlike the Research Track, but no
project-specific inclusion decision was made.

The official proceedings page links to 852 unique ACM Digital Library records
under one DOI collection. Normalized title comparison matches 789 accepted
entries; exact title plus author-set comparison matches 697 overall and 531
Full/Short entries. The proceedings page does not expose accepted-list IDs,
38 accepted entries have no exact normalized proceedings title, and 63 publisher
records have no exact normalized accepted title. Fuzzy/title/byline candidates
were not adjudicated, so this is not a complete crosswalk. The Full and Short
calls require an author to register and present accepted work on-site for
proceedings inclusion. Their footer says all rights reserved; the captured pages
do not provide a metadata license or bulk-reuse authorization.

Do not create a roster v11 or change CIKM's disposition. Keep raw captures in
ignored run artifacts and publish aggregate counts and official links only.
Preserve v10, all 76,629 frozen assignments including 1,095 reserved tests, and
the P02 no-go. No split, enrichment, PDF, graph, or database operation occurred.
See [source corrections v12](../data/manifests/five-year-source-corrections-v12.json),
[source triage](five-year-source-triage.md#cikm-2025-browser-source-capture-work-022),
and [WORK-022](work-log/2026-11-08-022-cikm-2025-browser-source-capture.md).
This year-specific finding does not change earlier CIKM editions. Recorded by
Codex under D022 and the user's proceed instruction.

## D040 — Release reset for the 11 November submission (2026-11-08)

Requested by the user after an independent review of the project state
([WORK-2026-11-08-024](work-log/2026-11-08-024-release-plan-reset.md)); drafted by
Claude. It applies until submission, and the [release plan](release-plan.md) holds
the operational detail. The user may amend the defaults below before release-plan
phase 1; record any amendment here with its date.

- **Scope:** AAAI and IJCAI 2021–2025 main-track papers from roster v10 (13,617),
  as one cumulative graph. Roster v10 is final and P01 source closure stops. Other
  editions and the 62 incomplete candidates are reported as collected data and
  coverage limits. D018's 34-series registry stays the long-term scope.
- **Evidence:** works are matched by the DOI derived from the official URL, with
  title and author-count agreement. A researcher is the OpenAlex author ID on a
  name-compatible authorship (ORCID recorded, not required). Affiliation triples
  come from that authorship's OpenAlex institutions with raw strings as evidence;
  papers showing a paper-level institution list go to review. Citations link only
  matched in-scope works. PDF/GROBID checks are optional. For this release this
  supersedes D009's pilot identity and affiliation rule.
- **Topics:** a frozen embedding classifier with abstention, compared with the
  phrase baseline on 50 papers frozen before tuning (30 reserved IJCAI tests and
  20 newly reserved AAAI papers).
- **Audit:** `quality-release-v1`: 200 uniform edges plus 10 per relation type.
  Each edge gets one review, split between two reviewers, plus a 50-edge overlap
  both review. Report Wilson 95% intervals against the course requirement (>90%)
  and the project target (≥95% with lower bound >90%). Size and coverage targets
  are unchanged.
- **Gates and process:** P00–P10, G01–G12, the P02 enrichment no-go (D029),
  D022's enrichment preconditions and readiness receipts no longer block release
  work; gates are reported as measured pass/fail. The Site is updated once, after
  final results. All other integrity rules in `AGENTS.md`, historical artifacts
  and held-out IDs are kept.
- **Evidence for the change:**
  - On the 2023 candidate, D009's rules resolved 85 of 1,206 author positions (7%)
    and 36 affiliated author–paper pairs (3%); no researcher appeared on two papers.
  - Thirteen source tasks after roster v10 changed no roster.
  - Access issues block 40 ACM/SIAM, 15 IEEE and 5 ICLR candidates.
  - Keyless OpenAlex checks on 8 Nov returned 24 of 24 derived AAAI/IJCAI DOIs,
    with author IDs, institutions, raw affiliation strings and abstracts. Sampled
    ICML papers were indexed only as arXiv records.
- **Risks, disclosed in the report:** OpenAlex author disambiguation and
  institution assignment errors (measured by the audit), the single-review design,
  and the narrower venue coverage.

### D040 amendments

- **2026-11-08 — tooling choices in phase 1
  ([WORK-2026-11-08-026](work-log/2026-11-08-026-release-phase-1-tooling.md)).**
  These implement the release plan; none changes a §2 default.
  - A graph versioned `release-…` can only be imported into bolt port 7689 (the
    isolated `neo4j-five-year` service), and a non-release graph cannot use that
    port. `.env` points `NEO4J_URI` at the pilot service, so a forgotten override
    would otherwise write the release graph into the pilot database.
  - `analyze`, `freeze-audit-sample` and `score-edge-audit` no longer require a
    readiness receipt (one is still verified when supplied) and record each size
    gate as passed or failed. A relation with no edges no longer aborts the audit
    freeze; the empty relation shows up as a failed `required_relation_types` gate.
  - The audit error categories are the five in release plan §5 plus `other`, so a
    wrong `PUBLISHED_IN` or `SUBTOPIC_OF` edge has a valid category. `double_review`
    stays the default when `audit.review_design` is absent, so older configs and
    fixtures behave as before.
- **2026-11-08 — duplicate OpenAlex records for one DOI
  ([WORK-2026-11-08-027](work-log/2026-11-08-027-release-phase-2-openalex-acquisition.md)).**
  In the full acquisition 330 of 13,617 DOIs returned two works: one crawled from the
  official page and one merged from Crossref and arXiv. Among duplicates that pass the
  title (at least 0.9) and author-count checks, the single record whose landing page equals
  the roster official URL is chosen; the others are kept as alternates and whether their
  author IDs agree is recorded. Any other duplicate stays in review (9 papers). The
  OpenAlex `select` gained `type` and `primary_location` to make this possible, which
  extends the field list in release plan section 8.2. Alternate IDs also resolve CITES
  targets, so a reference to the merged record still reaches the paper.
- **2026-11-08 — topic-review allocation for the frozen test set (user decision).**
  The D040 workload estimate of 25 papers per reviewer with 10 overlapping covered
  only 40 of the 50 frozen papers. The user selected 30 papers each with 10 shared,
  covering all 50 in 60 judgments. The deterministic venue-stratified allocation
  gives each reviewer 12 AAAI and 18 IJCAI papers; the overlap contains four AAAI
  and six IJCAI papers. The graph, test membership and classifier are unchanged.
  The allocation manifest and reviewer sheet hashes are recorded in
  [`freeze.json`](../reports/release-v1/freeze.json).
- **2026-11-08 — topic metrics for the partial-overlap allocation.** Each of the
  50 frozen papers contributes equal total weight to model metrics: a single
  annotation has weight one and each annotation on a shared paper has weight one
  half. This keeps all 50 papers in the estimate without treating repeated labels
  on the overlap as extra papers. Reviewer labels on overlap papers remain
  separate; exact-set agreement and per-topic Cohen's kappa are reported on those
  ten papers. An empty label set requires a note confirming that no leaf applies.
  This is an evaluation-weighting choice, not an accuracy threshold or a license
  to tune on the reserved test set.

# Scientific Network Explorer implementation and verification

WORK-2026-11-10-011. Local implementation only, 10 November 2026 (+07:00).
The broad audit is **substantially implemented, with explicit remaining gaps**
below; this receipt does not claim every requested feature or test contract is done.

## Source and production identity

Started from clean `main`, `f259353bbe1efff0b181fd1bbad8abf35f2b5ef8`.
`git ls-remote origin refs/heads/main` still matched that commit during verification.
No unrelated edits existed at startup; no reset/clean or push was performed.

Read AGENTS, release plan, status/latest logs, project plan/schema, both Explorer
plans and operations review, frozen v4 README/findings/summary/analysis/comparison,
quality/analysis configs, final-report captions, Explorer README, Azure runbook,
frontend components/store/API/types/E2E, backend routes/service/repositories/tests,
and analysis/release_metrics implementation. Historical records informed scope;
current files and live read-only checks provided evidence.

Read-only deployment checks established:

- Pages project `scientific-network-explorer`, deployment
  `22a38c01-b890-46e0-a3c4-8c54accaada2`, successful source commit
  `f259353bbe1efff0b181fd1bbad8abf35f2b5ef8` (13:12:47Z).
- Azure `.ci-deployment.json`: source
  `b25f0267bfab7147e0491d591cf4f4a3ab083c2f`, image
  `sha256:59c983a7128d15c8572b8fdcc50727d4b6e50f817614583ccc9a9350decf6481`,
  verification 10:06:51Z. API health reported the corrected graph inventory.
- VM snapshot: 3856 MiB total RAM, 1793 used, 2063 available; swap 0/4095 MiB.
  API 136.8 MiB / 0.08% CPU, Neo4j 993.2 MiB / 0.34%, Caddy 13.01 MiB.
  These are point-in-time observations, not load/capacity benchmarks.

The frontend and API production commits differ legitimately because deployment
triggers are separate. Existing backend Actions automation was inspected and left
unchanged. **No production resource, data, deployment or course Site was modified.**

## Implementation

- `viewSpec.ts`, Zustand and App: schema v2 validates/clamps full view filters,
  projection/layout/edge filter/selection and Ego/Path request parameters; legacy
  migration, localStorage bookmarks and explicit transient-overview notices.
  Bounded API hydration reconstructs actual Ego and directed Path graphs.
- `effectiveGraph.ts` is the shared effective slice for canvas, counters, inspector
  and exports. Repeated-paper filtering applies to R7/R8 only; unique neighbors,
  incident semantic edge degree and fractional collaboration strength are separate.
  Repository support/weight filtering also preserves non-collaboration facts.
- `exportGraph.ts` and header: effective JSON with view/method/quality/time/caveats,
  separate nodes/edges CSV, IDs/endpoints/direction/support/evidence class. Clipboard
  reports success only after successful write and otherwise provides selectable text.
- App expansion cancels/rejects stale requests before state application and preserves
  the previous graph on error. Relevant year/venue constraints resolve immutable
  paper evidence; weights keep frozen full-period meanings.
- Backend quality and metadata derive from artifacts; missing summary/analytics
  returns 503. Generic caveats never manufacture numeric PASS/count fallbacks.
  Classifier metadata comes from frozen summary, independently of identity correction.
- Analytics is lazy-loaded into five sections. Modular ECharts instances survive
  option changes, resize and obey reduced motion. Exact-value tables offer keyboard
  alternatives and entity/topic/community actions. Back returns to the finding.
- Sigma/Graphology persist through ordinary updates; keyed coordinates, identity
  and camera survive selection/expansion. Parallel and reciprocal semantic edges
  have distinct selectable offset lanes/arrows. Evidence colors, lane patterns and
  metric/coordinate legends explain the encodings. Heterogeneous sizes are fixed;
  homogeneous sizes use fractional strength or citation in-degree as labeled.
- `explorer_derived.py`, new config and separate small JSON add deterministic
  citation cohorts, organization support persistence and component representatives.
  Graph/config/method hashes and explicit definitions accompany the output. The Azure
  preparer retains compact strict summaries and embeds this extension in new immutable
  runtime packages; old packages honestly show missing optional analyses.

## Measured scientific results and limits

Frozen release remains `release-d3c788c3114a`:
47,875 nodes / 225,731 edges; R7 80,482, R8 13,031, R4 7,308,
R5 14,222; factual R1–R4 110,026. Researcher isolates: 414.
Graph SHA-256 remains
`6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`.
Tracked release-v4 results, final report/package sources, manifests and frozen
quality/analysis configs have no diff from starting HEAD.

Frozen researcher sensitivity: 6,260/80,482 edges survive (7.7781367262%);
base largest component 20,776/32,189, strict 175/32,189. Components 2,936→28,163;
isolates 414→26,946. Top-20 approximate betweenness overlap 0/20.
Methods: 256 pivots, inverse positive fractional-strength distance, random seed
20261101; Louvain seed 17/resolution .8. The historical 73.6% component belongs
to another graph version; the identity amendment is not a controlled accuracy trial.

Topic heatmaps use frozen fractional topic mass divided by labeled-paper count,
with raw/fractional counts, labeled/all denominators, coverage, abstentions and
percentage-point changes available together. Sector cells count pair-paper support,
include unknown and use their actual maximum. Annual counts use separate scales;
CCDF uses numerical degree and the complete tail, including isolates.

Separate [descriptive extension](explorer-analysis-release-v1/README.md): ten
venue/year citation cohorts cover 13,617 papers, including 10,140 with zero incoming
in-corpus citations. Informer has in-degree 51 within the 1,654-paper AAAI 2021
cohort; empirical upper-tie percentile 1.0 is not global impact. The highest-support
organization pair has 303 distinct core papers and observed annual support
49/52/43/58/101. Reproduction to a second unused path is byte-identical.

Unchanged quality: AI-assessed 193/200 = 96.5%, Wilson 95% CI 92.95–98.29%;
no independent human validation, reviewer independence or verified course accuracy.
Wilson intervals exclude evaluator error. Affiliation 48,259/65,469 = 73.71%,
below 80%; topic coverage 11,575/13,617 = 85% is not accuracy. Historical weighted
topic precision 35/51 = 68.63%, F1 .4667 versus .2301 phrase baseline. Unknown
sector/affiliation is not absence; inferred topics and in-corpus citation limits
remain visible in UI and exports.

## Verification and performance

Raw logs/screenshots are ignored under `reports/runs/WORK-2026-11-10-011/`.
| Check / exact command | Fresh result |
| --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report` | Passed (initial environment sync) |
| `uv run pytest` | 527 passed, 1 existing empty-parameter skip; exit 0 |
| `PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -q` | 25 passed, including real read-only Neo4j integration; exit 0; one existing Starlette/httpx deprecation warning |
| `VITE_API_BASE_URL=http://127.0.0.1:8001/api npm --prefix apps/research-explorer/frontend run build` | TypeScript + Vite passed; exit 0; large-chunk warning remains |
| `PLAYWRIGHT_BASE_URL=http://127.0.0.1:5174 npm --prefix apps/research-explorer/frontend run test:e2e` | 16 passed; final scope guard acceptance recorded in `e2e-scope-acceptance.log` |
| `PLAYWRIGHT_BASE_URL=http://127.0.0.1:4174 npm --prefix apps/research-explorer/frontend run test:e2e -- tests/explorer.spec.ts` | Five UI suites against production build; final result in `e2e-preview-scope.log` |
| `uv run research-network schema` | Passed; exit 0 |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json --config configs/quality.yaml` | Passed; exit 0; invented fixture is not measured accuracy |
| `python ops/azure/scripts/prepare-artifacts.py --root . --output reports/runs/WORK-2026-11-10-011/runtime-final` | Immutable SQLite roundtrip/integrity and source/output hashes passed; extension bytes match final derived artifact |
| `python ops/azure/scripts/smoke-api.py --base-url http://127.0.0.1:8011/api` | Production-mode API with compact SQLite/analysis: 28 passed; exit 0 |
| Derived replay command in extension README + `cmp` | Byte-identical; exit 0 |
| `git diff --check` and frozen-path comparison to starting commit | Passed; original release/report/manifests/configs unchanged |

Browser assertions include effective JSON/CSV field parity, versioned filter/schema
validation, clipboard denial, honest missing-artifact recovery, filtered Overview,
Ego and **directed citation Path** share/reload ID parity, persisted bookmarks,
late-response rejection, 503 preservation, reciprocal-edge lanes/identity, topic
cell → correct nonempty year/venue/topic paper graph, responsive reduced motion,
coordinate preservation, and renderer listener removal on unmount. Coordinate
persistence test applies the same Graphology update as dragging; it is not a
hardware touch-drag fidelity test. Four contract tests execute pure transforms;
twelve tests exercise the browser. Full production-build run covers the five
UI suites; development-only instrumentation is not shipped.

Failures were retained in earlier logs: HMR/test-store identity, a real export-menu
stacking collision, slash-spacing assertion, resize-observer timing, API preflight
rate-limit exhaustion and an initial smoke startup race. Fixed code/harness issues
were rerun. GET requests no longer send unnecessary JSON content-type/preflight;
API limits were not weakened. Logs distinguish earlier failures from acceptance.

`design-taste-frontend` source lint: 0 FAIL / 36 monospace warnings (stable IDs/code
retain mono). Production browser inspection: 0 FAIL / 1 small-text warning at
1440/768/390. No full WCAG certification is claimed. Baseline and final screenshots
at 390/768/1024/1440 in both themes, plus selected-edge drawers and all five analytical
sections, were inspected manually. Visual review fixed the inventory grid, restored
bounded per-type overview labels, and corrected taxonomy support/weight units.

Screenshot groups: `baseline-visual/graph-*-*.png`, `after-accepted/graph-*-*.png`,
`after-accepted/edge-*-*.png`, `after-accepted/{robustness,topics,communities,sectors,trajectories}-*.png`.
An additional live read-only browser check at 1440/390 in both themes loaded
111 nodes / 166 edges with zero page errors (`live-readonly.log`, `live-final-*.png`).
This confirms the existing deployment only; it does not deploy or validate local
new features in production. Initial before captures caught loading states; the
completed `baseline-visual/` captures supersede them for comparisons.

Reproducible profiler: `node apps/research-explorer/frontend/scripts/profile.mjs BASE_URL UNIQUE_OUTPUT_DIRECTORY`.
Chromium 153.0.8010.52, Linux/WSL, 1440×900, no throttling; local Vite dev + FastAPI
and the same Neo4j, warm server caches. Baseline code extracted from starting HEAD
uses isolated Vite cache on 5175/API8000; implementation uses 5174/API8001. One cold
browser navigation + warm reload; 12 selections to two animation frames, 120 idle
rAF intervals; expansion response plus two frames. These are single descriptive
runs, not statistical or production capacity claims; idle rAF is not canvas FPS.

| Measure | Before | Implementation |
| --- | ---: | ---: |
| Cold browser graph ready (ms) | 2384.454 | 2349.496 |
| Warm reload graph ready (ms) | 781.580 | 699.218 |
| Median selection → two frames (ms) | 184.4 | 50.0 |
| Canvas insertions across 12 selections | 84 | 0 |
| Idle rAF p95 interval (ms) | 16.7 | 16.8 |
| Expansion response + two frames (ms) | 697.411 | 535.895 |
| JS heap snapshot (bytes) | 23,085,179 | 24,811,607 |

Raw precision is retained in `profile-baseline-final/profile.json` and
`profile-accepted/profile.json`. Snapshot heap increased; no retained-memory growth
or local CPU benchmark claim is made. Final source adds only deterministic curated
query tie-breaks/scope rejection and Retry after this renderer profile; these do
not change the measured researcher projection's renderer behavior.

Baseline single JS chunk: 1,580.92 kB (486.11 kB gzip). Implementation initial JS
533.01 kB (142.50 kB gzip), lazy Analytics 576.09 kB (191.55 kB gzip);
see final build log for exact bytes. The initial graph no longer loads all ECharts.
Both remaining JS chunks still exceed Vite's 500 kB warning threshold.


## Explicit remaining gaps

- Community/country/topic/cross-sector constrained expansions are blocked with a
  retryable explanation. Filtered overviews work. This avoids silently dropping
  constraints but does not implement every paper-specific neighbor join.
- Narrowed year/venue/topic requests on full-period curated presets return 422
  with guidance to choose Researcher → Paper → Topic. That filtered preset works;
  arbitrary narrowed variants of every curated preset are unimplemented. Ranking
  ties now use stable IDs.
- Full unique-versus-shared paper/neighbor comparison sets are unimplemented.
  Existing shared-neighbor list is capped at 30; accepted R8 supporting papers at
  100. Organization topic portfolios are normalized frozen profiles; researcher
  comparison does not gain a new full topic profile.
- Component actions show actual representative bounded neighborhoods, not full
  component membership. Stored community profiles contain top five topics only;
  absent topics are explicitly not zero.
- Single straight edges use evidence colors, not all four dash patterns. Parallel
  lanes have patterns and individual selection. No configurable size metric chooser,
  staged neighbor fade-in or interpolated hover animation. Camera/chart easing and
  reduced-motion support work; no perpetual simulation is added.
- No sector opportunity/null model or assortativity claim; no new venue/year
  affiliation-missingness analysis using a different denominator. Frozen topic
  coverage/abstention by venue/year is exposed.
- No arbitrary JSON file import, exact sharing of manually appended expansions,
  cross-browser certification, full automated WCAG contrast audit, sustained memory
  leak/capacity test or production load benchmark. JSON/CSV identity parity and one
  renderer unmount/listener cleanup are tested.
- Vite still warns about chunks above 500 kB; charts are lazy/modular but not fully
  split below the warning threshold. Phone density remains a documented design warning.

## Authorized next steps

Local code and evidence are reviewable; pushing or deployment needs separate user
authorization. Do not rebuild/import the graph. For eventual complete rollout:

1. Review the local commits/diff and these gaps; rerun the commands below.
2. After authorization, push the tested commit through existing main CI. Check
   the existing Deploy Azure API workflow; do not replace it or bypass approval pins.
3. To enable strict/extension charts, prepare a **new immutable artifact directory**
   with `prepare-artifacts.py` and use the runbook's coordinated image/artifact
   update. The old directory/image and rollback selectors must remain available.
   Review the new manifest and compatibility fingerprint before operator approval.
4. Verify API `/ready`, exact inventory, immutable hashes, 28-check smoke, actual
   source/image receipt and database preservation; separately verify the canonical
   Pages deployment source commit and desktop/mobile behavior. No graph restore is
   needed for this application-only change.

See [Azure runbook](../ops/azure/README.md) for precise update/rollback commands.


## Local checkpoints and operator commands

Implementation: `494b3420ac267bc420e1a722f952d5c1e1d8ce17`.
Scope/determinism/Retry acceptance: `b6d8dde`.
The subsequent documentation checkpoint contains this receipt and finalized log.
All commits remain local; production identities above are unchanged.

From the repository root, reproduce acceptance with the existing local Neo4j and
configured immutable artifacts available:

```bash
uv sync --locked --group dev --extra analysis --extra report
uv run pytest
PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -q
npm --prefix apps/research-explorer/frontend run build
npm --prefix apps/research-explorer/frontend run test:e2e
uv run research-network schema
git diff --check
```

Default E2E configuration uses ports 5173/8000; ensure those run the tested source.
This session used isolated 5174/8001 and preview 4174 as recorded above, preserving
pre-existing servers. Set `VITE_API_BASE_URL` at build time for the intended API.
Only after separate authorization: `git push origin main`; observe the existing
Pages/backend workflows and approval compatibility gate, then follow the Azure
runbook for the new immutable artifact directory. A successful code push alone
does not enable extension data in an old artifact package.

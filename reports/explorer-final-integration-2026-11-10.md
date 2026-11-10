# Explorer final integration — 10 November 2026

Status: locally verified; **not deployed or pushed**. WORK-2026-11-10-012.
This supersedes the implementation limitations in the earlier
[Explorer receipt](research-explorer-implementation-2026-11-10.md) where stated below.

## Outcome and production diagnosis

Initial local and remote main were `4a432d60fe7a1a012029de86b7ce06e66b358ca2`.
Read-only Actions/SSH/public checks confirmed:

- Run [42838707362](https://github.com/HSandz/scientific-network/actions/runs/42838707362)
  failed in `stable_services()` before image delivery or selector updates.
  Missing guest receipt was a consequence, not the original failure.
- Caddy Docker health commands could not exec (`procReady not received`). Its
  container had 88 zombie `ssl_client` children plus eight Caddy threads, near
  `pids_limit: 100`; PID-limit events numbered 9,371. BusyBox HTTPS wget probes
  orphan TLS helper processes; Caddy PID 1 did not reap them. Public HTTPS still
  worked. Available memory/disk did not explain the failure.
- `compose.yaml` now enables `init: true` on Caddy, preserving the PID cap,
  trusted HTTPS probe and deployment health gate. Isolated real probes reproduced
  16 zombies without init versus zero with init over 20 seconds; restart passed.
  This is a short reproduction, not a sustained leak benchmark.
- Activation checks stable services before updating API. The failed production
  run therefore preserved the last healthy backend. A real isolated Docker health
  failure also verified exact API selector rollback. Neo4j was never modified.

| Production identity observed | Value |
| --- | --- |
| Pages source | `4a432d6` |
| Pages deployment | `9a9fa4b6-6436-4998-8f6f-46b0ffd62468` |
| API source | `b25f0267bfab7147e0491d591cf4f4a3ab083c2f` |
| API configuration digest | `sha256:59c983a7128d15c8572b8fdcc50727d4b6e50f817614583ccc9a9350decf6481` |
| Runtime artifacts | `/opt/scientific-network/artifacts/azure-20261110-v1` |
| Manifest SHA-256 | `958be6e9493eb6b0255ad36939a96fb901dd7bd7e64cdb9634649139a105ef0f` |

The old API image and old compact artifacts lack the extension and strict
projections. Deploying the frontend alone cannot enable those charts. New code
loads a separately versioned, graph-bound `explorer_derived` extension alongside
frozen analytics. Missing or incompatible optional data remains explicitly
unavailable. A new immutable package supplies both strict projections and derived
analytics without rerunning analysis or changing the frozen release.

## Implementation and scientific semantics

- `backend/services/explorer_service.py`, `repositories/neo4j_repo.py`, routes and
  schemas filter collaboration views and bounded expansions by distinct accepted
  support papers satisfying year, venue and inferred topic together. Organization
  country/sector apply to both endpoints; community means the frozen partition.
  Citation paper filters apply to both endpoints. Unsupported combinations return
  422. Restricted heterogeneous paper windows require the supported
  researcher–paper–topic preset; taxonomy remains timeless context.
- Original full-period weights, thresholds and node rankings remain unchanged.
  `in_window_support_count`, `in_window_support_paper_ids` and `weight_scope`
  distinguish filtered support from full-period metrics, including CSV exports.
  Candidate selection is bounded and can omit other matching entities.
- Expansion forwards community/country/topic/cross-sector constraints and discards
  stale requests. A selected non-paper Ego center can remain contextual with zero
  matching links. A paper center violating its window is rejected.
- Comparison computes complete distinct paper/neighbor counts before limiting
  deterministic shared/unique previews. Organization shared papers require R8
  support, excluding sole dual affiliation. Comparisons and Paths disclose their
  full-period scope; Paths suspend overview filters and restore them on Back.
- Saved Graph/Table/Analytics views restore workspace, layout, scope, selection,
  filters, analytical section/controls and Table queries/sort/page. Legacy views
  migrate safely, disclosing cleared unsupported controls or transient expansions.
  Finding→chart→graph→evidence→Back retains analytical controls.
- Persistent Sigma, graph coordinates/camera and reciprocal/parallel edge identities
  are preserved. Evidence classes and provenance remain distinct in UI/exports.
- Ops preparation rejects existing outputs including symlinks. Readiness checks
  enforce complete strict/derived analytics when declared in the manifest.
  Idempotent CI verification refreshes the actual active artifact path in its
  receipt after a coordinated switch with an unchanged image.

The frozen graph and release evidence are unchanged: see
[release-v4 inventory and limitations](release-v4/README.md).
Graph version is `release-d3c788c3114a`, source SHA-256
`6f665a946cec7473889a09e883a3ef88469de867cb1054d6a3b145239ea59c90`.
AI-assessed precision is not human accuracy; topic coverage is not classification
accuracy; within-corpus citations are not global impact; co-publications do not
establish commercial partnerships. Historical failed quality gates remain failures.

## Verification evidence

Raw logs/screenshots are ignored local artifacts under
`reports/runs/WORK-2026-11-10-012/`; their absence from Git is intentional.

| Check | Result / log |
| --- | --- |
| `uv sync --locked --group dev --extra analysis --extra report` | Passed |
| `uv run pytest` | 530 passed, 1 existing empty-parameter skip; `pytest-release.log` |
| `PYTHONPATH=apps/research-explorer:src uv run pytest apps/research-explorer/backend/tests -q` | 32 passed, including live read-only Neo4j; `backend-acceptance.log` |
| `npm --prefix apps/research-explorer/frontend run build` (local API base configured) | TypeScript/Vite passed; `build-final.log`; chunk-size warnings remain |
| Browser suites | 22 passed in final full run; 5 production-preview suites passed; `e2e-final.log`, `e2e-preview-final.log` |
| Real packaged API container | 28 smoke checks plus complete strict/derived assertions; restart ready; `container-runtime.log` |
| Image without data/network | Readiness correctly unavailable; `ci-image-smoke.log` |
| Caddy probe/restart reproduction | Passed; `caddy-reaper-accepted.log` |
| Real isolated Docker rollback | Exact old config restored; `rollback-docker.log` |
| Deployment regression | 19 passed; `deployment-regression.log` |
| Offline schema and synthetic validation | Passed; `schema.log`, `validate.log` |
| Production-build visual capture | 32 screenshots; no unexpected console/page errors, alerts or horizontal overflow; `visual-preview/verification.json` |

Visual contact sheets were manually inspected: `graphs-contact.jpg`,
`charts-contact.jpg`, `mobile-charts-contact.jpg`. Captures cover all four
projections, all five analytics sections, both themes, 390/768/1024/1440 widths
and reduced motion. DOM assertions alone were not treated as scientific validation.
Synthetic fixtures discriminate year/venue/topic, duplicate support, affiliations,
unsupported filters and truncation; actual read-only queries verify window support.
Initial failed browser checks/logs are retained. Two intermittent failures in the
Table follow-up rerun passed isolated diagnosis; subsequent full-run outcome is
recorded separately, without claiming a proven cause or deleting failure evidence.

## Immutable package and exact version binding

[Machine-readable readiness receipt](explorer-runtime-readiness-2026-11-10.json)
contains all output bytes/hashes, ledger totals and tested image identity.

- Local directory: `reports/runs/WORK-2026-11-10-012/runtime-explorer-v2`.
- Proposed VM directory: `/opt/scientific-network/artifacts/explorer-20261110-v2`.
- Manifest SHA-256: `3b188311e1daefd2083100957f5bc488dc5309b4966b2359136ddd0246ab5820`.
- Derived SHA-256: `bb0da2d2d2f9b23cec053ceb3cc31514a614b7a85b7672d38791e409d93eb37d`.
- Runtime contract: `6ca14fb8375af8d2e0e66c82634f0251141f5fa702b841dd5497e6170e5615ec`.

The tested API image is labeled with application commit `75f55e2`; later commits
change operations, Table frontend state and documentation. The actual CI image
must be labeled with the **final approved pushed HEAD**, not relabeled as the
locally tested image. Pages and API must both resolve to that final source SHA.
Image configuration digests are distinct from archive/registry hashes.

## Release procedure — separate authorization required

No commands below have been performed against production in this task.
Approve the final local commit range `origin/main..HEAD` as one coordinated release.
It includes `75f55e2cf06f13ce33ebb0b7af650d9006d15c6f` (main fixes),
`78485e87a099ea87af0f6d7d675d5d8bd822ba89` (receipt follow-up),
`a26dce56b05c0ed8f301294eb2c35e83a87e607c` (Table state) and final handoff
documentation at approved HEAD. Obtain exact full SHAs with
`git log --format='%H %s' origin/main..HEAD`; pin `RELEASE_SHA=$(git rev-parse HEAD)`
at approval. Do not push or trigger Actions before approval.

1. Reconfirm remote HEAD, live selectors/approval, service IDs and graph identity.
   Save root-only copies of Compose, `.env`, `.ci-approval.json` and installed CI
   scripts. Preserve existing image, certificates and artifact directory.
2. Copy reviewed Compose to `/opt/scientific-network/ops/azure/compose.yaml`.
   Under the runtime maintenance lock, run only
   `docker compose --env-file .env -f compose.yaml up -d --no-deps --no-build --pull never --force-recreate --wait --wait-timeout 120 caddy`
   from that directory. This is a brief HTTPS interruption requiring approval.
   Verify public certificate/health, Caddy init process, no accumulating zombies,
   and API/Neo4j health. Do not restart the database or API for this probe fix.
3. Run `bash ops/azure/scripts/install-ci-vm.sh azure_scientific-network` from the
   approved checkout. It verifies the existing contract/manifest approval before
   installing reviewed root-owned scripts; it does not authorize a new manifest.
4. Copy the prepared package into the **unused** proposed VM directory. Refuse any
   pre-existing directory/symlink. Verify manifest hash, every output hash, graph
   binding and read-only permissions. Do not edit active files or selectors yet.
5. Push the approved HEAD to main. This separately authorized action triggers Pages
   and Azure. Backend CI first activates matching code using the still-approved old
   artifacts. Optional charts may temporarily show unavailable states. Verify actual
   source/image identity and public health, not merely a green workflow.
6. With that exact image present, run from the VM ops directory:
   `sudo scripts/update.sh scientific-network-api:sha-<RELEASE_SHA> /opt/scientific-network/artifacts/explorer-20261110-v2`.
   Keep the exact rollback snapshot printed by the command. **Do not pre-edit
   ARTIFACT_DIR**: the old image/old artifact selectors must remain the snapshot
   until the coordinated transaction. No dump restore or graph-volume change.
7. After successful verification, atomically update the root-owned approval's
   manifest pin to the reviewed new hash, retaining the same approved contract and
   previous approval backup. Rerun the workflow at the same source SHA; its
   idempotent verification must record the actual artifact directory/service IDs.
8. Run `python ops/azure/scripts/smoke-api.py --base-url https://scientific-network-api.eastasia.cloudapp.azure.com/api --require-explorer-analytics`.
   Verify exact inventory/graph SHA, Caddy/API/Neo4j health, manifest, API source and
   `.ci-deployment.json`, canonical Pages source, real `explorer_derived`, strict
   summaries, all five sections, narrowed support, evidence, exports and bookmarks.
   Observe Caddy PID/zombie counts over repeated probe intervals and API restart
   readiness. Record public browser screenshots and receipt independently of CI.

Rollback: `sudo scripts/rollback.sh .env.rollback-<exact-printed-filename>` restores
only API image/artifact selectors and verifies health. Restore the corresponding
root-owned approval backup, verify public API and the guest receipt, and retain
new artifacts for diagnosis. For a failed CI activation use its recorded rollback
mechanism/receipt. Caddy recovery is separate: restore backed-up Compose and
recreate **only Caddy** if needed; the original probe configuration will still
have its known leak. No database rollback is appropriate for these changes.
A frontend rollback requires separately approved Pages deployment promotion/revert.

## Remaining limitations

Production health-probe recovery, new API/analytics activation and production
restart/rollback remain **unverified live**, awaiting authorization. Arbitrary
narrowed heterogeneous presets are explicitly unsupported. Bounded candidates and
previews can omit matching items; full-period comparisons/Paths do not implement
arbitrary constrained traversal. Appended expansions cannot be reconstructed as
an exact shared overview and are disclosed. Dense labels/small phone text, bundle
warnings, straight-edge dash/size controls and sustained load/leak, cross-browser
and WCAG certification remain incomplete. No scientific score was improved by
changing thresholds, suppressing failures or fabricating unavailable chart values.

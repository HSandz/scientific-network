# WORK-2026-11-03-005 — Expand conference scope and publish the revised Sites plan

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-03, Asia/Bangkok (UTC+07:00); started after task 004 |
| Finalized | 2026-11-03 09:35 +0700 (Asia/Bangkok) |
| Work performed | 2026-11-03 |
| Contributor | Codex |
| Related task | [Historical pilot implementation](2026-11-03-004-discovery-pilot-graph.md) |
| Scientific repo Git state | `main`; no commits or remote; existing scaffold/pilot and this revision uncommitted |
| Sites source state | Separate source repo; commit `532bf27a85185a1a4ad847dc872aa500f4f2ddbf` published as version 3 |

## Objective

The user clarified that NeurIPS and ICML were examples, not the course project's
intended limit. Expand the plan to major flagship AI/related research conferences,
update the existing Sites plan and related repository docs, and **do not start
collecting new research data**. This task is scope planning, documentation and
publication only.

## Changes and decisions

- Added [conference scope](../conference-scope.md) and planning-only
  `configs/conference-scope.yaml`: **34 series / 31 planned 2023 editions**, across
  seven areas. ECCV, NAACL and COLING have no 2023 edition and remain explicit
  no-edition entries; no neighboring year is substituted.
- Operationalized “all large, top conferences” as a curated, versioned flagship
  roster, including major specialized fields. No universal ranking, verified CORE
  classification, expanded completeness or new corpus size is claimed. Official
  catalog URLs are leads; edition sources, tracks and rights remain to be verified.
- [D014](../decisions.md) supersedes D001's venue boundary only. Five labels, ten
  predicates, 2023 baseline and release thresholds remain. Added full/short main
  research-paper policies, source-family plans, Findings/workshop exclusions,
  KDD Research Track and no-edition/access-state handling.
- Updated README, AGENTS, local project plan, schema context, source/data contracts,
  annotation/evaluation, setup, roadmap, docs index, status and final-report outline.
  Historical pilot commands are labeled and collection is explicitly paused.
- Preserve the old 120 test / 60 development IDs. Plan supplemental cross-venue
  work/version leakage controls before future acquisition. Unchanged per-venue
  defaults imply **1,860 test / 930 development papers** as arithmetic workload
  scenarios, not new frozen samples. Finalize allocation and reviewer hours first.
- Staged diagnostic scenario: 10 papers per 29 newly active venues plus the
  existing 100, **390 cumulative**, only after a later collection instruction.
  The old equal-quota splitter does not yet implement this staged design.
- Require resource/schedule re-estimation. The two-person/eight-week baseline and
  old two-venue size estimates do not size the expanded release. Generalized
  adapters, IDs, venue labels, year windows, taxonomy and sampling remain future work.
- Used the [Sites skill](/home/san/.codex/plugins/cache/openai-curated-remote/sites/1.1.2/skills/sites/SKILL.md)
  to open the existing public Site, preserve its identity/audience, edit canonical
  `source-plan.md`, rebuild and publish **version 3**. Kept the 20-section visual
  layout, five illustrations, relation guide, search and browser-local checklist.
  Updated hero/date, scope/source/sampling/schedule sections and Markdown download.
- Saved the [revised 20-section source snapshot](../reference/sites-project-plan-2026-11-03.md)
  separately from the unchanged original 2026-11-02 snapshot, plus a small
  [publication receipt](../reference/sites-plan-publication-2026-11-03.json).

## Verification

Repository commands ran from `/home/san/Code/scientific-network` unless noted.
Raw/local artifacts are under ignored `reports/runs/WORK-2026-11-03-005/`.

| Command or concrete check | Outcome and exit | Evidence |
| --- | --- | --- |
| `uv run pytest` | **48 passed**, exit **0**; 0.51 s test time | `pytest.log` |
| `uv run research-network schema` | Ten predicates, exit **0** | `schema.json` |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json --config configs/quality.yaml --output reports/runs/WORK-2026-11-03-005/synthetic-validation.json` | Structural pass, exit **0**; synthetic only | `synthetic-validation.json` |
| `uv lock --check` | Passed, exit **0**; no dependency changes in scientific repo | Tool result |
| `uv run python reports/runs/WORK-2026-11-03-005/verify-plan.py` | Passed, exit **0**: 34 unique series, 31 planned editions, collection disabled, source snapshot/download match | `planning-validation.json`, `planning-validation.log` |
| Data-file inventory and size/mtime comparison | **1,438 existing data files unchanged**, no additions/deletions | `before-files.json`, `planning-validation.json` |
| SHA-256 of frozen corpus/quality configs and original snapshot | All unchanged | `protected-hashes.json`; full hashes below |
| Local Markdown target/whitespace check | Zero missing local links / unintended trailing spaces, exit **0**; original-style Markdown hard breaks in source snapshot preserved | `docs-validation.json` |
| Configured-secret scan of Git-eligible files | Zero matches, exit **0** | `secret-boundary.json`; no credentials printed |
| Site build from isolated source checkout | Exit **0**; **20 sections, 26 tables**, 132,287-byte HTML | Build tool result; `site-build-environment.log` |
| Browser checks at **1440×1000** and **390×844** | No page overflow; tables scroll; 29 references, no missing anchors or duplicate IDs; conference search and download pass; 10 relation tabs / 12 checks retained | `site-qa.json`, browser tool results |
| Sites helper source commit/push/package | Exit **0** after credential renewal; isolated checkout clean | Source commit in publication receipt; `sites-deploy.tar.gz` |
| Native Sites save/deploy | **Version 3, status succeeded**, same public audience and URL | Version/deployment IDs in publication receipt |
| Published-page and Markdown-download check | New roster/pause/hero visible; 20 sections / 29 references; no page overflow; console has zero errors/warnings | `site-qa.json`, browser tool results |
| Temporary local preview shutdown | Only this task's server stopped (SIGTERM; exit **143** expected) | Server session completion |

The Site source checkout is `/tmp/scientific-network-sites-2mqKzB`, isolated from
scientific data. Pandoc was absent. An ephemeral **software build dependency**
`pypandoc-binary` (32.9 MiB) supplied Pandoc; no project lock/dependency files changed
and no research corpus was downloaded. The build command from that checkout was:

```bash
uv run --no-project --with pypandoc-binary python - <<'PYBUILD'
import os, sys, subprocess
from pathlib import Path
import pypandoc
os.environ['PATH'] = str(Path(pypandoc.get_pandoc_path()).parent) + os.pathsep + os.environ['PATH']
subprocess.run([sys.executable, 'build_site.py'], check=True)
PYBUILD
```

Sites source helper: `node /home/san/.codex/plugins/cache/openai-curated-remote/sites/1.1.2/scripts/site-workflow.mjs --project-id appgprj_6ae7698b8b2881919d49df2426c517a2`.
Opening/packaging credentials were passed through hidden stdin only, never files,
arguments or journal. Packaging reused the complete opening result and `commands: []`
because the unchanged build had passed. Archive path is the ignored run directory's
`sites-deploy.tar.gz`. Only the separate Sites source was committed/pushed; the
scientific repository was not committed or pushed.

### Failures and corrections within the task

- A helper was initially started in the scientific repo but cancelled before
  credentials/input; no Git source mutation occurred. Reopened correctly in an
  empty isolated directory (cancelled helper exit **1**).
- Initial inspection used the wrong skill reference path (exit **1**); read the
  actual `skills/sites/references/preview/local.md` before browser QA.
- First packaging attempt exited **1** because the short-lived source credential
  expired. Renewed credentials for the same Site, reused source/ID, and completed
  packaging/publication. No new Site, access-policy change or force-push was used.
- An atomic documentation patch had a mismatched heading and applied nothing;
  reapplied against inspected context. Fixed a new source-reference table break
  before the successful build and browser checks.

### Versions and hashes

- Registry: `conference-scope-v1`, decision D014; SHA-256
  `5f636e144900ebe1b78dc181eb66ce30d6945c9fbbd26e1ce939ab9893ff1862`.
- Revised Sites source SHA-256:
  `f9e7fc4abdb29c5dd60c0a4863fc05140817974e4bfd930def8fe6a04504eb92`.
- Legacy corpus config SHA-256, unchanged:
  `35d32b64f1d611d991d79267ddb7ce5c80912fe1b229627a4211ccf4894d0361`.
- Quality config SHA-256, unchanged:
  `fd37163b6d8cd7302b1b1fcee128b97d8c32f059fd9f4126de37405f2ce65deb`.
- Sites source commit: `532bf27a85185a1a4ad847dc872aa500f4f2ddbf`.
- Saved version: `appgprj_6ae7698b8b2881919d49df2426c517a2~appgver_dc845e124e8481919a70b754f9856173` (number **3**).
- Deployment: `appgdep_6ae94768ec5c8191a299a7acfdd99c5b`, **succeeded**, `2026-11-03T02:31:20.022494+00:00`.
- URL: https://ai-research-network-plan.hazy-tern-8113.chatgpt.site.

## Open issues and limitations

No collection/discovery/enrichment/PDF/new split/graph-write command ran. No Neo4j
integration or service health check was needed or rerun; previous task 004 results
remain historical and no semantic accuracy was measured. All source-family
edition IDs, tracks and rights need verification during a later authorized task.
The new roster does not implement adapters, revised quotas or complete taxonomy
coverage. Workload scenarios are calculations, not fresh samples or measured
resource estimates. Deadline, names/IDs, code license and lecturer interpretations
remain unspecified. No universal top-conference ranking or new paper count is
claimed. The current pilot remains only NeurIPS/ICML. No jobs/server for this task
remain running; native Site deployment is terminal success.

## Next step

Review the explicit roster/track rules and feasible annotation budget, then design
and implement generalized adapters/edition IDs/venue handling and staged splits
with **offline** fixtures. Preserve old held-out IDs and draft supplemental
cross-venue leakage exclusions. Do not start collection until a later instruction
explicitly authorizes it; use fresh executable configs/output versions then.

## Corrections

None. Future corrections should be dated or linked through a new work entry.

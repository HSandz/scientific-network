# WORK-2026-11-03-003 — Next steps and setup readiness

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-03 07:45 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-03 |
| Contributor | Codex, responding to the user's next-task/setup question |
| Related task | [Progress logging](2026-11-03-002-progress-logging.md) |
| Git state | `main`; no commits or remote; existing scaffold uncommitted |

## Objective

Verify current local prerequisites and recommend the next bounded tasks, separating
what is needed for corpus discovery from later database/PDF/model requirements.

## Changes and findings

- Read the current handoff, task history, setup/roadmap, project/schema documents
  and relevant corpus/quality configuration before assessing readiness.
- Python 3.12.3 virtual environment and uv 0.9.28 are available.
- Docker is now available: Engine/client 29.7.2, Compose v5.4.0, reachable daemon.
  The daemon reports 32 CPUs and 12,536,893,440 bytes of memory (about 11.7 GiB).
  This supersedes the historical unavailable-Docker limitation; it does not verify
  Neo4j/GROBID service startup or suitability for a full run.
- `.env` has not been created. Git has no commit or remote backup.
- The next code milestone remains official main-track roster discovery; Docker,
  API credentials, models and a GPU are not prerequisites for that stage.
- Refreshed [current status](../status.md) and the history index with the new
  readiness evidence. No application code, configuration or dependencies changed.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `docker --version` | passed, exit 0; Docker 29.7.2 | Read-only inspection in this task |
| `docker compose version` | passed, exit 0; v5.4.0 | Read-only inspection in this task |
| `docker info --format 'Server={{.ServerVersion}}; CPUs={{.NCPU}}; MemoryBytes={{.MemTotal}}'` | passed, exit 0; daemon reachable | Read-only inspection in this task |
| `uv run pytest` | passed, exit 0; 32 tests | Local ignored `reports/runs/WORK-2026-11-03-003/pytest.log` |
| `uv run research-network validate --input tests/fixtures/synthetic_graph.json --config configs/quality.yaml --output reports/runs/WORK-2026-11-03-003/synthetic-validation.json` | passed, exit 0; structural only, synthetic and release-ineligible | Local ignored JSON report and `validate-console.log` in the same run directory |
| `uv lock --check` | passed, exit 0; lock consistent | Tool output in this task |
| `docker ps --all --filter 'label=com.docker.compose.project=scientific-network' --format 'table {{.Names}}\t{{.Status}}'` | passed, exit 0; header only, no matching project containers | Read-only inspection in this task |
| Repository-root Python check of Markdown links, trailing whitespace and finalized entry status | passed, exit 0; 20 Markdown files | Local ignored `reports/runs/WORK-2026-11-03-003/documentation-checks.log` |

The fresh validation used graph `synthetic-v1`, input SHA-256
`fde1dc302d66ee28e045cd4ae9d74238315f631ade95932cdaef91453d14dc2c` and quality-config
SHA-256 `fd37163b6d8cd7302b1b1fcee128b97d8c32f059fd9f4126de37405f2ce65deb`.
Semantic accuracy remains `not_measured`. These checks establish scaffold readiness,
not real corpus size or model/service correctness.

## Decisions

None. Recommendations follow the existing plan and stage contracts.

## Open issues and limitations

No services were started, no credentials configured, no data acquired and no
models downloaded. Real pipeline stages remain placeholders. Service startup,
resource use and NLP/semantic accuracy remain unverified. OpenAlex access/quota
rules need checking before bulk enrichment; no API key is required for writing
the official-roster collector.

## Next step

1. Checkpoint the scaffold/work records in Git and configure a real remote for
   backup when available. Fill member/deadline fields and confirm the proposed
   accuracy/heterogeneous-predicate interpretation with the lecturer in week one.
2. Implement official NeurIPS/PMLR discovery into a reconciled corpus manifest
   with stable official IDs, explicit exclusions and unknown-track review. Add
   offline parser fixtures/tests; this stage needs no running DBMS or PDF parser.
3. Freeze held-out IDs (120 papers, 60 per venue) before tuning and keep development
   labels separate (60 papers, 30 per venue). Select the approximately 100-paper
   balanced pilot outside the held-out set.
4. Before DBMS/PDF pilot work, create `.env` from the example, set the Neo4j password,
   validate Compose configuration, and smoke-test Neo4j/GROBID. Defer GDS/model
   installation until the corresponding stage. Verify OpenAlex access/quota rules
   before enrichment at scale.
5. Acquire pilot metadata, selectively parse PDFs, inspect at least 20 affiliation
   mappings and difficult identities, and measure coverage/runtime/review effort.
   Then implement canonical resolution, supported topic baseline and a small
   repeatable Neo4j import before scaling.

## Corrections

None.

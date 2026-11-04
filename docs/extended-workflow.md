# Expanded 2023 collection workflow

**Historical 2023 execution instructions.** D018 extends the planned release to
2021–2025 and pauses pipeline implementation/collection. Do not rerun these commands
under the planning-only request. See [five-year scope](five-year-scope.md).

The user authorized expanded implementation and acquisition on 2026-11-03 (D015).
Run from the repository root after `uv sync --locked --group dev`. Credentials stay
in ignored `.env`; existing process variables take precedence. No model is required.
Read [current status](status.md) for measured results and remaining source gaps.

The commands below preserve the first expanded run. The subsequent
[evidence-review workflow](evidence-review.md) documents recovered metadata v4,
headers v5, source-review v2 and the separate graph-v2 candidate. Current loaded
databases and HTML remain graph-v1 until an explicit migration.

## Configurations and immutable outputs

`configs/corpus.yaml` and `configs/quality.yaml` remain unchanged. The scope registry
is the historical planning snapshot, not a runnable corpus config. The executable
config is **`configs/corpus-extended-v2.yaml`**. Its 34 entries distinguish verified
source adapters, unresolved sources and three no-2023-edition cases.

The first extended config/discovery were preflight attempts. The v2 discovery
corrected no-edition statuses, exact repeated CoRL entries, ACL front matter and
RSS year corroboration. **`extended-corpus-v3` is the active roster**: its correction
preserves `?day=all` in CVF evidence URLs. v2 and v3 memberships are identical;
the manifest/config signatures are separately frozen. Keep earlier artifacts as
diagnostics, not competing current releases. Metadata passes v1/v2 exposed
source-specific author/abstract layouts; v3 incorporates those corrections and
leaves genuine roster/detail byline conflicts withheld. Always use a fresh output version
when source/config/method inputs change; never overwrite frozen legacy outputs.

```bash
uv run research-network discover --config configs/corpus-extended-v2.yaml --output data/manifests/extended-corpus-v3
uv run research-network split --input data/manifests/extended-corpus-v3/corpus_manifest.jsonl --corpus-config configs/corpus-extended-v2.yaml --output data/manifests/extended-splits-v3
uv run research-network acquire --config configs/corpus-extended-v2.yaml --input data/manifests/extended-corpus-v3/corpus_manifest.jsonl --splits data/manifests/extended-splits-v3/membership.jsonl --output data/interim/extended-acquired-v3
```

Discovery writes JSONL/Parquet rosters and an **edition ledger for all 34 series**.
It returns **1** when editions remain unavailable/unreviewed, while retaining valid
rosters. An HTML response alone does not establish a valid roster. One failed page
blocks the entire edition from new sampling; do not treat a partial page as complete.
No-edition cases are explicit and do not count as source failures. To retry a blocked
edition after correcting access/config, use a new discovery output version.

New source families: PMLR, CVF, ACL Anthology, MLSys, IJCAI, RSS, KR, AAMAS and
MICCAI accepted-title lists. Only identical official record repetitions collapse;
conflicting titles/bylines/tracks fail. COLT uses Original Papers; AAMAS uses regular
research sessions, excluding poster abstracts and special/nonresearch material.
The edition ledger retains exclusions. MICCAI bylines must be obtained from the
official detail only after split freezing; absent authoritative bylines fail acquisition.
Unverified publisher catalogs and access failures stay unresolved. Do not bypass them.

## Held-out protection and staging

Preserve **all 5,046 legacy assignments**, including 120 test, 60 development and
100 diagnostics. New papers sharing an old test title group remain held out; other
duplicate/version title candidates are quarantined. Grouping prevents leakage and
does not merge work identities. Titles alone cannot detect every alternate version:
later identifier/content evidence must trigger review and leakage disclosure.

Before detail/API/PDF enrichment, new editions with ≥100 independent eligible groups
reserve 60 test / 30 development. Smaller editions reserve floor(20%) test (minimum
one) and max(10, floor(10%)) development, or fail if infeasible. Select ten new
diagnostics from development. Seed and all input/membership hashes are recorded.
Samples remain unannotated; per-venue quotas need population weights for global
component estimates and do not replace the independent uniform edge audit.

Acquisition reuses the old 100 metadata records only after verifying the protected
file hash and exact roster equality. Other matches require title, edition-relative
year window and full ordered byline agreement. Roster/detail byline conflicts are
withheld. Official 401/402/403 failures are recorded per paper; rate limits and
OpenAlex access/quota failures stop the run, retaining successful records for resume.

## PDF extraction and graph construction

```bash
docker compose --profile nlp up -d grobid
uv run research-network extract --config configs/corpus-extended-v2.yaml --input data/interim/extended-acquired-v3/papers.json --output data/interim/extended-headers-v3
uv run research-network resolve --config configs/corpus-extended-v2.yaml --input data/interim/extended-headers-v3/papers.json --output data/processed/extended-resolved-v1
uv run research-network classify --config configs/topics.yaml --quality-config configs/quality.yaml --input data/processed/extended-resolved-v1/graph.json --output data/processed/extended-graph-v1.json
uv run research-network validate --input data/processed/extended-graph-v1.json
```

The shared content-addressed cache reuses old PDF/TEI bytes. Extraction retains
per-paper failures and missing affiliations. Resolution still requires public
ORCID publication corroboration and exact printed, authorship-specific institutions.
The taxonomy remains a draft phrase baseline with abstention. Larger venue coverage
does not improve or establish semantic accuracy by itself.

Keep the original database on **7474/7687**. The additive service uses independent
volumes on **7475/7688**:

```bash
docker compose --profile extended up -d neo4j-extended
NEO4J_URI=bolt://localhost:7688 uv run research-network build --input data/processed/extended-graph-v1.json --output reports/runs/WORK-2026-11-03-006/import-v1.json
NEO4J_URI=bolt://localhost:7688 uv run research-network build --input data/processed/extended-graph-v1.json --output reports/runs/WORK-2026-11-03-006/import-replay-v1.json
```

Choose **new report paths** for later imports/replays. The loader refuses an existing
report path and rejects foreign graph versions sharing entity IDs. No automatic
database replacement or migration occurs. Integration checks must reconcile counts,
prove replay, and verify the old database remains unchanged. `analyze`/`evaluate`
remain nonzero placeholders. Size, independent accuracy and coverage gates remain
unchanged and must be reported separately from software tests and collection counts.

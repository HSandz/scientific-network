# Development setup

The current release plan covers [2021–2025](five-year-scope.md) (D018). Existing
services/configs support historical 2023 work; no additional setup, collection or
pipeline changes are authorized by this planning-only revision.

## Offline Python workflow

Use Python 3.12 and uv from the repository root:

```bash
uv sync --locked --group dev
uv run research-network --help
uv run research-network schema
uv run research-network validate --input tests/fixtures/synthetic_graph.json
uv run pytest
```

The lockfile is the reproducible dependency source. Optional analysis dependencies:
`uv sync --locked --extra analysis --group dev`. The optional app uses
`uv sync --locked --extra app --group dev` then `uv run streamlit run app/main.py`.
An embedding runtime/model is deliberately not selected yet; pin its package and
model revision after the pilot and record the decision.

If uv is unavailable, this installs compatible packages without the exact lock:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e . pytest
.venv/bin/research-network schema
.venv/bin/python -m pytest
```

## Scope and authorized collection

D015 records the user's authorization for expanded collection.
`configs/conference-scope.yaml` remains a non-executable historical planning
registry; `configs/corpus.yaml` retains the old pilot. Use the separately versioned
`configs/corpus-extended-v2.yaml` and [expanded workflow](extended-workflow.md).
A separate Neo4j service on 7475/7688 protects the old database. Some sources remain
unavailable; consult the edition ledger instead of assuming full-scope coverage.

## Command status

| Command | Current behavior |
| --- | --- |
| `schema` | Print five endpoint labels and ten predicate contracts |
| `validate --input GRAPH --config configs/quality.yaml [--output SUMMARY]` | Parse the small JSON contract; check structural invariants; report counts and size targets |
| `validate ... --require-size` | Additionally return nonzero on the implemented size checks; still no release certification |
| `audit-precision --correct N --total M` | Wilson interval for supplied counts only; performs no sampling/review |
| `discover`, `split`, `acquire`, `extract`, `resolve`, `classify`, `build` | Implemented pilot stages; see [exact commands and limitations](pilot-workflow.md) |
| `analyze`, `evaluate` | Stage contracts only; exit 2, no output file |

Pending stages accept `--config`, `--input`, and `--output`; these define the future
interface. A run on a placeholder is not an acquisition, build or evaluation.
Successful validation includes input/config hashes, timestamp and graph version.
`reports/runs/` is ignored; only reviewed permitted summaries belong in a release.

## Neo4j and GROBID

Install Docker Engine with the Compose plugin separately. Then:

```bash
cp .env.example .env
# Replace NEO4J_PASSWORD in .env with a local password of at least 8 characters.
docker compose config --quiet
docker compose up -d neo4j
docker compose ps
docker compose --profile nlp up -d grobid
```

Current pinned images are `neo4j:5.26.12-community` and
`grobid/grobid:0.8.2-crf`. The CRF-only image is a documented CPU alternative to
the much larger full image; parser method/version and external-consolidation
settings are recorded in extraction artifacts. See the latest work log for actual
host verification. Measure the pilot rather than assuming a full-run resource budget.

Neo4j is exposed only on localhost: Browser at <http://localhost:7474>, Bolt at
`bolt://localhost:7687`. Log in as `neo4j` with the `.env` password, then run
`queries/00_constraints.cypher` in Browser. Mounting the query directory alone does
not execute the constraints. Existing database credentials are not reset by
editing `.env`. `docker compose down` stops services and preserves named volumes.

GROBID is at <http://localhost:8070>. The pilot extractor explicitly disables
external consolidation, negotiates XML and retains PDF/TEI evidence locators.
The explicit `extract` stage acquires pilot PDFs into ignored immutable storage;
ordinary tests and service startup do not download the corpus.

GDS is not downloaded automatically. Select a compatible Community GDS version
against the actual Neo4j version, pin that artifact, verify `RETURN gds.version()`,
and record resource limits before implementing projections. NetworkX is installed
for algorithm checks/fallback; Neo4j remains the required stored graph.

## Verification boundaries

Offline tests cover contracts, roster/split rules, secret-safe cache behavior,
matching, author-specific TEI alignment, topic abstention, derived weights and
audit math. Record actual service/import verification in the current work log.
Independent accuracy, full-corpus coverage, final report and full rebuild remain
release tasks. The pilot is not a semantic-quality certification.
CI uses the same synthetic offline check and does not contact sources or run models.

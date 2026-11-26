# Research Trend Navigator — Azure VM & Hosted SLM Deployment Preparation (D042 / M4)

> [!IMPORTANT]
> **Status: Prepared locally ONLY — NOT deployed, signed up, paid, or published.** Do not execute deployment steps until the user selects a hosted SLM provider/budget (or `$0` cached-demo mode) and explicitly authorizes production changes.

## 1. Architecture on the Existing Azure VM + Cloudflare Pages

Preserves the single-VM budget architecture (existing Ubuntu 24.04.5 LTS VM: 2 vCPU, 3.8 GiB RAM, 4 GiB swap) without adding a second database or GPU instance:

1. **Frontend (Cloudflare Pages)**: Build `apps/research-explorer/frontend` with `VITE_API_BASE_URL` pointing to `https://scientific-network-api.eastasia.cloudapp.azure.com/api` (same security/CSP headers as v4 Explorer, exposing all Navigator tabs alongside Explorer).
2. **Single Neo4j Community 5.26.12 Container (`enriched-cb371912e308`)**: Load `enriched-cb371912e308` (contains both the frozen v4 `release-d3c788c3114a` subgraph and the D042 enrichment layer — **no second Neo4j container required**; memory footprint stays inside the VM's 2 GiB Neo4j limit).
3. **Immutable Navigator Artifact Bundle (Read-Only Mount)**: Built locally via:
   ```bash
   uv run python ops/azure/scripts/prepare-navigator-artifacts.py \
     --root . \
     --output /tmp/navigator-artifacts-v1
   ```
   Packages `vectors.sqlite` (~27 MB CPU SQLite vector index), `analysis-v2/*.json`, `rag-v1/*.json` (reports, entity descriptions, cached scripted demos, **excluding full-abstract `chunks.json`**), `enrichment-v3/*.json`, `enrichment-v1/cooccurrence.json`, `qa-eval-v1/results.json`, and `configs/rag-v1.yaml` with SHA-256 `manifest.json`.
4. **Hosted OpenAI-Compatible SLM (≤9B) + Graceful Cached-Demo Fallback**:
   `apps/research-explorer/backend/config.py` reads optional env vars so switching LLM providers needs zero code changes:
   - `EXPLORER_LLM_BASE_URL` (e.g., `https://openrouter.ai/api/v1`)
   - `EXPLORER_LLM_MODEL` (e.g., `qwen/qwen3.5-4b` or provider-specific ID)
   - `EXPLORER_LLM_PROVIDER` (e.g., `openrouter`)
   - `EXPLORER_LLM_API_KEY_ENV` (name of env var holding the API key, e.g. `OPENROUTER_API_KEY` — stored only in VM `.env` `chmod 0600`, never echoed in API responses)
   - **Fallback behavior**: If the hosted LLM endpoint is unconfigured, unreachable, or fails with `LLMError`, `/api/ask` (both JSON and SSE) automatically serves the cached scripted demos (`fallback_reason="llm_unavailable_served_cached_demo"`) and returns a structured HTTP 200 `status="llm_unavailable"` notice for custom uncached questions.

## 2. Hosted SLM Provider Options & Cost Estimates (Verification Required Before Signup)

For an interactive course demo / marking traffic (~500–2,000 Ask queries; ~2,500–4,000 prompt tokens + ~500 completion tokens per multi-hop Ask query ≈ 1.5M–8M input tokens and 0.25M–1M output tokens total over Dec 2026):

| Option | Endpoint / Setup | Approx Pricing (verify current pricing before signup) | Estimated Monthly Demo Cost (500–2k queries) | Tradeoff |
| --- | --- | --- | --- | --- |
| **Option A: Cached-demo mode only (`$0`)** | Leave `EXPLORER_LLM_BASE_URL` unset or point to disabled endpoint; keep `Use demo cache` enabled | **$0** | **$0** | Zero ongoing spend & sub-second cached Ask demos; custom uncached Ask questions return graceful `llm_unavailable` |
| **Option B: Serverless OpenAI-compatible small Qwen endpoint** (e.g., OpenRouter / DeepInfra / Together / Fireworks serverless API when ≤9B Qwen3/3.5 tier is hosted) | `EXPLORER_LLM_BASE_URL` + `EXPLORER_LLM_API_KEY_ENV` | ~\$0.05–\$0.20 / 1M tokens (verify exact model availability & rates) | ~**\$0.10 – \$2.00 total** | Pay-per-token, zero idle GPU cost; requires confirming exact ≤9B Qwen3.5-4B model availability at chosen provider |
| **Option C: Hugging Face Inference Endpoints (dedicated T4 / L4 GPU)** | Dedicated OpenAI-compatible vLLM/llama.cpp container for `Qwen/Qwen3.5-4B` | ~\$0.50–\$0.80 / hr while running | ~\$5–\$20 if scaled to zero when idle; \$360+/mo if left 24/7 | Exact pinned GGUF/HF checkpoint match, higher idle cost unless paused outside demo |

## 3. Deployment Checklist (Do Not Execute Without User Approval)

1. Export immutable v4+Navigator artifact directories with `prepare-artifacts.py` and `prepare-navigator-artifacts.py` and verify `manifest.json` hashes + absence of `chunks.json`.
2. Build production API image (`ops/azure/scripts/build-image.sh <tag>`) including `src/scientific_network/rag/` dependencies (and `sentence-transformers` CPU weights or precomputed query embedder check) and transfer to VM via `docker save | gzip -1 | ssh azure_scientific-network 'sudo -n docker load'`.
3. Create Neo4j 5.26.12 dump of `enriched-cb371912e308` (`neo4j-admin database dump`) and restore into an unused production volume on VM, keeping the frozen v4 `neo4j-five-year` backup intact outside VM.
4. Set VM `/opt/scientific-network/ops/azure/.env` (`chmod 0600`) with new production Neo4j password + `EXPLORER_LLM_*` vars + `EXPLORER_NAVIGATOR_ARTIFACT_DIR`.
> **Open packaging gap (2026-11-27):** the artifact bundle does not yet include the organization
> index (`data/processed/navigator-affiliations-v1/index.json.gz`, built by
> `apps/research-explorer/backend/scripts/build_affiliation_index.py`). Add it, and set
> `affiliation_index_path` for the container, before deploying; otherwise organization pages list no
> papers. The frontend now uses real paths, so the host must serve `index.html` for unknown paths.

5. Run read-only API health + Navigator smoke checks (`/api/trends`, `/api/groups`, `/api/communities`, `/api/network-science`, `/api/about-data`, `/api/ask/demos`), then build & deploy frontend to Cloudflare Pages.

# WORK-2026-11-24-001 — Local LLM server and extraction encoders

| Field | Value |
| --- | --- |
| Status | completed |
| Recorded | 2026-11-24 11:00 +07:00 (Asia/Bangkok) |
| Work performed | 2026-11-24 |
| Contributor | Claude Code agent (claude-opus-5-5), at the user's request |
| Related task | [WORK-2026-11-23-002](2026-11-23-002-final-exam-specification.md); specification §6.1, milestone M0 |
| Git state | `main` at `3489d5b`; new files under `ops/llm/` and this entry, uncommitted |

## Objective

Set up a local, controllable runtime for the ≤9B language model on the 8 GB GPU,
using a Q4 quantized model, and test it with Qwen3.5-4B only. Then, on request,
set up and test the two extraction encoders (GLiNER2.5-base, GLiNER-Relex-large).
This is the "runtime working" part of M0, not the model-selection experiment.

## Changes and findings

- Added [`ops/llm/`](../../ops/llm/README.md): a compose service for llama.cpp
  `llama-server` (CUDA image pinned by digest), a model env file with the pinned
  GGUF source and hash, a standard-library smoke test, and a README.
- Runtime choice: llama.cpp rather than Ollama (Windows-side install, not running,
  less control over offload, context and constrained output) or vLLM (reserves
  GPU memory up front; GGUF support experimental).
- Model file `~/models/gguf/Qwen3.5-4B-Q4_K_M.gguf`, outside the repository:
  `unsloth/Qwen3.5-4B-GGUF` revision `e87f176479d0855a907a41277aca2f8ee7a09523`,
  2,740,937,888 bytes, SHA-256
  `00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4` (verified).
  Chosen over bartowski's build (3.01 GB) as the most-downloaded Q4_K_M; the
  quantizer choice is not a quality comparison.
- Image `ghcr.io/ggml-org/llama.cpp@sha256:f8e7c336e3660804f6bc35a4147dbfdf1ddae9b7c3c50d412fab49b323e28fea`
  (created 2026-11-23), server build `b12648-44d50873b`. Qwen3.5's hybrid Gated
  DeltaNet architecture loads and runs fully on the RTX 5060 (Blackwell) GPU.
- Qwen3.5 thinks by default. With thinking on, a two-hop toy question took 2,928
  reasoning tokens (~43 s) before answering correctly; at a 2,048-token budget it
  never answered. Default to thinking off; test thinking only where it helps.

- Added [`ops/extract/`](../../ops/extract/README.md): an isolated uv project
  (PyTorch 2.11.0+cu128, `gliner2[local]==2.2.0`, `gliner==0.2.30`, own `uv.lock`;
  main project lock unchanged) and a smoke test. Pinned revisions:
  `fastino/gliner2.5-base-v1` @ `07d99c0b…`, `knowledgator/gliner-relex-large-v1.0`
  @ `4aedc922…`. Loading GLiNER2.5 through `JointIE` (typed endpoints) needed
  `device=` rather than `map_location` alone; the first run failed on a
  parameter-count bug in the test script, fixed and rerun.
- On three synthetic abstracts both encoders produce plausible entities and
  relations. GLiNER2.5 JointIE is type-consistent but missed some relations and
  mistyped two baselines; GLiNER-Relex found more but duplicates per mention and
  allowed one type-violating edge. Three examples cannot rank them.

## Verification

| Command/check | Outcome and exit code | Evidence/artifact |
| --- | --- | --- |
| `docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi -L` | passed; GPU visible in containers | console |
| `sha256sum` of the downloaded GGUF | passed; matches Hugging Face LFS hash | above |
| `docker compose -f ops/llm/compose.yaml --env-file ops/llm/qwen3.5-4b-q4km.env up -d` | passed; healthy in ~17 s, 2 slots × 16,384 tokens | `docker logs sn-llm` |
| `python3 ops/llm/smoke_test.py` run 1 | failed, exit 1: four checks passed; thinking mode hit the 2,048-token limit with no answer | `reports/runs/WORK-2026-11-24-001/smoke-test-qwen3.5-4b-q4km.json` (ignored) |
| Same, run 2, thinking budget 8,192 | passed, exit 0: health, plain chat, JSON-schema extraction, tool call, thinking (42.9 s) | `…/smoke-test-qwen3.5-4b-q4km-run2.json` |
| Load test, first attempt with ~16k-token prompts | failed: HTTP 400, prompt longer than the 16,384-token slot | console |
| Load test, two parallel 11.9k-token prompts, then two parallel 400-token generations | passed; peak 5,747 MiB of 8,151 (baseline ~1.6 GB); ~2,000 tok/s prompt, ~44 tok/s per stream in parallel, ~67–70 tok/s single | `…/load-test.json` |
| `uv lock && uv sync` in `ops/extract/`; `torch.cuda.is_available()` | passed; capability (12, 0) | console |
| `ops/extract/smoke_test.py --device cuda`, run 1 | failed, exit 1: `JointIEEngine` has no `parameters` (test-script bug) | console |
| Same, run 2 | passed, exit 0: GLiNER2.5 107 ms/abstract, peak 0.8 GB; Relex 20 ms/abstract, peak 1.8 GB; GPU total 7.35 of 8.15 GB with the LLM server loaded | `…/extract-smoke-cuda.json` |
| `ops/extract/smoke_test.py --device cpu --repeat 3` | passed, exit 0: GLiNER2.5 125 ms, Relex 147 ms per abstract (~28 and ~33 min for 13,606) | `…/extract-smoke-cpu.json` |
| `uv run pytest` | not run; no package code changed | — |

All inputs were synthetic. These are runtime checks, not extraction quality.

## Decisions

None. Runtime and quantization defaults are recorded here and in
[`ops/llm/README.md`](../../ops/llm/README.md); the model choice stays with the
§6.1 experiment.

## Open issues and limitations

- The `sn-llm` container was left running at the end of this task; stop it with
  `docker compose -f ops/llm/compose.yaml --env-file ops/llm/qwen3.5-4b-q4km.env down`.
- Gemma-4-E4B and Qwen3.5-9B are not downloaded or tested. Q8_0 comparison not run.
- Encoders ran in fp32 and unbatched for GLiNER2.5; fp16 and batching are untested.
  Extraction quality is unmeasured until the development-split experiment.
- The client `src/scientific_network/rag/llm.py` (with call logging and caching)
  does not exist yet.
- The server has no API key; it is safe only because the port is bound to localhost.

## Next step

Freeze `data/manifests/enrichment-splits-v1/` (100 development, 200 test papers),
then write the LLM client against `http://127.0.0.1:8080/v1` and run the first
extraction prompts on development papers only.

## Corrections

None.

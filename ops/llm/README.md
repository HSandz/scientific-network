# Local language-model server

Runs one quantized GGUF model with llama.cpp `llama-server` (CUDA) in Docker, for
the final-exam model experiments ([specification §6.1](../../docs/final-exam/specification.md#61-language-model-selection-k1)).
It serves an OpenAI-compatible API at `http://127.0.0.1:8080/v1`, bound to
localhost only. Model files are kept outside the repository in `~/models/gguf/`
(override with `LLM_MODEL_DIR`) and are never committed.

## Files

| File | Purpose |
| --- | --- |
| `compose.yaml` | The `llm` service; image pinned by digest |
| `qwen3.5-4b-q4km.env` | Qwen3.5-4B Q4_K_M: pinned source, revision, size, SHA-256 and server settings |
| `smoke_test.py` | Health, plain chat, JSON-schema extraction, tool call, thinking mode, speed and GPU memory |

## Set up and run

Requires Docker with the NVIDIA runtime (`docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi -L` lists the GPU).

```bash
# Download the pinned model and check its hash (2.74 GB).
mkdir -p ~/models/gguf && cd ~/models/gguf
curl -L --fail -o Qwen3.5-4B-Q4_K_M.gguf \
  https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q4_K_M.gguf
echo "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4  Qwen3.5-4B-Q4_K_M.gguf" | sha256sum -c
cd -

# Start, test, stop.
docker compose -f ops/llm/compose.yaml --env-file ops/llm/qwen3.5-4b-q4km.env up -d
python3 ops/llm/smoke_test.py --output reports/runs/<work-id>/smoke-test.json
docker compose -f ops/llm/compose.yaml --env-file ops/llm/qwen3.5-4b-q4km.env down
```

To try another model, add an env file with its pinned source and hash, bring the
service down, and bring it up with the new file. Only one model is loaded at a time.

## Settings and why

- `--n-gpu-layers 99`: all layers on the GPU. Lower it only if a larger model runs
  out of memory.
- `--ctx-size 32768 --parallel 2`: two slots of 16,384 tokens each. A request
  longer than its slot is rejected with HTTP 400.
- `--cache-type-k/v q8_0` and `--flash-attn on`: halve KV-cache memory.
- `--jinja`: uses the model's chat template, needed for tool calls and
  `chat_template_kwargs`.

## Request conventions

- Send `temperature: 0` and a fixed `seed` for repeatable runs.
- Qwen3.5 thinks by default. Send `"chat_template_kwargs": {"enable_thinking": false}`
  for extraction and tool planning. With thinking on, even a two-hop toy
  question used about 2,900 reasoning tokens (~43 s), so give thinking requests a
  budget of 8k tokens or more and use them only where they measurably help.
- Use `response_format: {"type": "json_schema", ...}` for structured output; the
  server constrains generation to the schema.

## Measured on this machine (WORK-2026-11-24-001)

RTX 5060 Laptop GPU, 8,151 MiB, about 1.6 GB already used by Windows; llama.cpp
build `b12648-44d50873b`; Qwen3.5-4B Q4_K_M. Runtime checks only, not quality.

| Check | Result |
| --- | --- |
| GPU memory, idle after load (32k context, 2 slots) | ~3.6 GB above baseline |
| Peak, two parallel 11.9k-token prompts | 5,747 MiB total (~4.1 GB above baseline) |
| Generation speed | ~67–70 tok/s single request; ~44 tok/s each with two in parallel |
| Prompt processing | ~2,000 tok/s on long prompts |
| JSON-schema extraction, tool call, thinking answer | pass (synthetic inputs) |

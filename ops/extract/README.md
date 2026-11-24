# Extraction encoder runtime

An isolated uv environment for the zero-shot extraction encoders in
[specification §4.2–4.3](../../docs/final-exam/specification.md#42-entity-extraction-and-linking-e2).
It is kept apart from the main project because it needs a CUDA build of PyTorch
(the main `nlp` extra pins a CPU build) and recent `transformers`; the main
`uv.lock` is unchanged. Model weights download to the Hugging Face cache
(`~/.cache/huggingface/`) and are never committed.

| Model | Role | Repository and pinned revision | Parameters | Licence |
| --- | --- | --- | --- | --- |
| GLiNER2.5-base | Default (spec) | `fastino/gliner2.5-base-v1` @ `07d99c0ba5d15cb3b24e0a236fa99bdd4ef87a5c` | 193,581,591 | Apache-2.0 |
| GLiNER-Relex-large | Comparison | `knowledgator/gliner-relex-large-v1.0` @ `4aedc9226a5ac9e2f6b5ea3e91c1ee577c88a290` | 466,576,896 | Apache-2.0 |

Packages: `gliner2[local]==2.2.0` (loaded with `JointIE`, which enforces typed
relation endpoints) and `gliner==0.2.30` (`GLiNER.inference(..., return_relations=True)`).
Locked versions in `uv.lock`: PyTorch 2.11.0+cu128, transformers 5.22.2.

## Run

```bash
uv sync --project ops/extract
uv run --project ops/extract python ops/extract/smoke_test.py \
  --device cuda --output reports/runs/<work-id>/extract-smoke-cuda.json
# CPU only:
CUDA_VISIBLE_DEVICES= uv run --project ops/extract python ops/extract/smoke_test.py \
  --device cpu --repeat 3 --output reports/runs/<work-id>/extract-smoke-cpu.json
```

The test uses three synthetic abstracts, schema `method` / `task` / `dataset`,
and relations `applied_to` (method→task), `evaluated_on` (method→dataset) and
`part_of` (method→method).

## Measured on this machine (WORK-2026-11-24-001)

RTX 5060 Laptop (8 GB), 32 CPU threads, fp32, with the Qwen3.5-4B server
([`ops/llm/`](../llm/README.md)) running at the same time. Runtime checks on
synthetic text, not quality.

| | GLiNER2.5-base (JointIE, beam 32) | GLiNER-Relex-large (batched) |
| --- | --- | --- |
| GPU, per abstract | 107 ms (~24 min for 13,606) | 20 ms (~4.5 min) |
| CPU, per abstract | 125 ms (~28 min) | 147 ms (~33 min) |
| Peak PyTorch GPU memory | 0.8 GB | 1.8 GB |
| GPU total with LLM server loaded | 6.2 of 8.15 GB | 7.35 of 8.15 GB (tight) |

Observations from the three examples, which are too few to rank the models:

- GLiNER2.5 JointIE keeps relation endpoints type-correct, but it missed
  `GraphMix evaluated_on OGB-MolHIV/Tox21`, typed the baselines ReAct and
  Reflexion as datasets, and emitted one relation twice.
- GLiNER-Relex found more of the expected relations, but it repeats relations per
  mention and produced one type-violating edge (`offline reinforcement learning`,
  a task, `applied_to` a task), since it does not enforce endpoint types.
- Both need de-duplication and type filtering before the language-model check (§4.3).

## Resource guidance

- Run the encoders on the CPU during bulk extraction (about 30 minutes for the
  corpus) to keep the GPU for the language model, or stop the LLM server and use
  the GPU.
- Do not run GLiNER-Relex on the GPU next to a model larger than Qwen3.5-4B.

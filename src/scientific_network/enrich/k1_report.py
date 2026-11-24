"""Assemble the K1 model-selection evidence from development-run outputs into reports/enrichment-v1/k1-*."""

import json
from pathlib import Path

from scientific_network.enrich.k1 import summarize_runs

MODELS = {
    "qwen4b": {"model": "Qwen3.5-4B Q4_K_M", "hf": "Qwen/Qwen3.5-4B", "total_parameters_b": 4.66, "eligible": True,
               "gguf": "unsloth/Qwen3.5-4B-GGUF@e87f176479d0855a907a41277aca2f8ee7a09523",
               "sha256": "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4"},
    "gemma": {"model": "Gemma-4-E4B-it Q4_K_M", "hf": "google/gemma-4-E4B-it", "total_parameters_b": 8.00, "eligible": True,
              "gguf": "unsloth/gemma-4-E4B-it-GGUF@bfc15c382204943c3a8fff0c750b94ae2364d7a3",
              "sha256": "85a896a047553e842f25297ee5b031d64ff30147d9c4af17b1e4b394cd1fab87"},
    "qwen9b": {"model": "Qwen3.5-9B Q4_K_M (reference only)", "hf": "Qwen/Qwen3.5-9B", "total_parameters_b": 9.65, "eligible": False,
               "gguf": "unsloth/Qwen3.5-9B-GGUF@3885219b6810b007914f3a7950a8d1b469d598a5",
               "sha256": "03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8"},
}
VARIANTS = (
    ("SLM only (extract-v2)", "extract2"),
    ("GLiNER-Relex candidates + SLM verify-v5 + relations-v1", "verify7-relex"),
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _gpu(path: Path):
    return int(path.read_text().split()[0]) if path.exists() else None


def build(runs: Path) -> dict:
    entries = []
    for key, meta in MODELS.items():
        for variant, suffix in VARIANTS:
            score = _load(runs / f"score-{key}-{suffix}.json")
            if score is None:
                continue
            entries.append({"name": f"{meta['model']} | {variant}", "model": meta["model"], "variant": variant,
                            "score": score["slm"], "run": _load(runs / f"run-{key}-{suffix}.json"),
                            "gpu_mib": _gpu(runs / f"gpu-{key}-busy.txt") or _gpu(runs / f"gpu-{key}.txt"),
                            "total_parameters_b": meta["total_parameters_b"], "eligible": meta["eligible"]})
    table = summarize_runs(entries)
    table["models"] = MODELS
    return table

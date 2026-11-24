"""Smoke test for the extraction encoders (specification §4.2–4.3).

Loads pinned revisions of GLiNER2.5-base (default) and GLiNER-Relex-large
(comparison), extracts Method, Task and Dataset mentions and the relations
APPLIED_TO, EVALUATED_ON and PART_OF from synthetic abstracts, and records
load time, latency, throughput and GPU memory. Inputs are invented examples, not
corpus papers; outputs are runtime checks, not quality measurements.

    uv run --project ops/extract python ops/extract/smoke_test.py \
        --device cuda --output reports/runs/<work-id>/extract-smoke.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import torch
from huggingface_hub import snapshot_download

MODELS = {
    "gliner2.5-base": ("fastino/gliner2.5-base-v1", "07d99c0ba5d15cb3b24e0a236fa99bdd4ef87a5c"),
    "gliner-relex-large": ("knowledgator/gliner-relex-large-v1.0", "4aedc9226a5ac9e2f6b5ea3e91c1ee577c88a290"),
}

ENTITY_TYPES = {
    "method": "A named model, algorithm, architecture or technique proposed or used in the paper",
    "task": "A research problem or application the paper addresses",
    "dataset": "A named dataset, benchmark or corpus used for training or evaluation",
}
# (name, head type, tail type, natural-language label for GLiNER-Relex)
RELATIONS = [
    ("applied_to", "method", "task", "applied to"),
    ("evaluated_on", "method", "dataset", "evaluated on"),
    ("part_of", "method", "method", "part of"),
]

SYNTHETIC_ABSTRACTS = [
    "We propose GraphMix, a contrastive pre-training method for graph neural networks, "
    "and apply it to molecular property prediction. On the OGB-MolHIV and Tox21 "
    "benchmarks GraphMix improves ROC-AUC over GraphCL by 2.1 points.",
    "Long-horizon planning remains hard for language agents. We introduce TreePlan, which "
    "combines Monte Carlo tree search with a learned value model, and evaluate it on "
    "ALFWorld and WebShop, where it outperforms ReAct and Reflexion.",
    "We study offline reinforcement learning for robotic manipulation. Our method, CQL-Aug, "
    "extends conservative Q-learning with data augmentation and is evaluated on the D4RL "
    "benchmark and on the RoboMimic dataset.",
]


def gpu_used_mib() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, check=True).stdout
        return int(out.strip().splitlines()[0])
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def load(name: str, device: str):
    repo, rev = MODELS[name]
    path = snapshot_download(repo, revision=rev)
    if name == "gliner2.5-base":
        from gliner2.joint_ie import JointIE
        model = JointIE.from_pretrained(path, device=device, map_location=device)
        model.eval()
    else:
        from gliner import GLiNER
        model = GLiNER.from_pretrained(path).to(device)
        model.eval()
    return model


def run_gliner25(model, texts: list[str]) -> list[dict]:
    from gliner2.joint_ie import JointIEConfig
    schema = model.create_schema().entities(ENTITY_TYPES)
    for rel, head, tail, _ in RELATIONS:
        schema = schema.relation(rel, head, tail)
    schema = schema.no_self_loops()
    out = []
    for text in texts:
        res = model.extract(text, schema, config=JointIEConfig(optimizer="beam", beam_size=32))
        d = res.to_dict()
        by_id = {e["id"]: e for e in d["entities"]}
        out.append({
            "feasible": res.feasible,
            "entities": [(e["type"], e["text"], round(e["confidence"], 3)) for e in d["entities"]],
            "relations": [(by_id[r["head"]]["text"], r["type"], by_id[r["tail"]]["text"],
                           round(r["confidence"], 3)) for r in d["relations"]],
        })
    return out


def run_relex(model, texts: list[str]) -> list[dict]:
    label_to_name = {label: name for name, _, _, label in RELATIONS}
    with torch.no_grad():
        ents, rels = model.inference(
            texts=texts, labels=list(ENTITY_TYPES), relations=list(label_to_name),
            threshold=0.4, adjacency_threshold=0.55, relation_threshold=0.7,
            flat_ner=True, return_relations=True)
    return [{
        "entities": [(e["label"], e["text"], round(e["score"], 3)) for e in te],
        "relations": [(r["head"]["text"], label_to_name.get(r["relation"], r["relation"]),
                       r["tail"]["text"], round(r["score"], 3)) for r in tr],
    } for te, tr in zip(ents, rels)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    ap.add_argument("--models", nargs="+", default=list(MODELS))
    ap.add_argument("--repeat", type=int, default=10, help="timed passes over the abstracts")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    results = {"device": args.device, "torch": torch.__version__, "cuda": torch.version.cuda,
               "gpu_used_before_mib": gpu_used_mib(), "models": {}}
    if args.device == "cuda":
        results["gpu"] = torch.cuda.get_device_name(0)
    ok = True
    for name in args.models:
        if args.device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
        t0 = time.perf_counter()
        model = load(name, args.device)
        load_s = time.perf_counter() - t0
        runner = run_gliner25 if name == "gliner2.5-base" else run_relex
        outputs = runner(model, SYNTHETIC_ABSTRACTS)  # warm-up and recorded output
        t0 = time.perf_counter()
        for _ in range(args.repeat):
            runner(model, SYNTHETIC_ABSTRACTS)
        n = args.repeat * len(SYNTHETIC_ABSTRACTS)
        per_doc = (time.perf_counter() - t0) / n
        entry = {
            "repo": MODELS[name][0], "revision": MODELS[name][1],
            "parameters": sum(p.numel() for p in getattr(model, "model", model).parameters()),
            "device_dtype": str(next(getattr(model, "model", model).parameters()).dtype),
            "load_seconds": round(load_s, 1),
            "ms_per_abstract": round(per_doc * 1000, 1),
            "abstracts_per_second": round(1 / per_doc, 1),
            "est_minutes_13606_abstracts": round(13606 * per_doc / 60, 1),
            "outputs": outputs,
        }
        if args.device == "cuda":
            entry["torch_peak_allocated_mib"] = round(torch.cuda.max_memory_allocated() / 2**20)
            entry["gpu_used_loaded_mib"] = gpu_used_mib()
        entry["pass"] = all(o["entities"] and o["relations"] for o in outputs)
        ok &= entry["pass"]
        results["models"][name] = entry
        del model
        if args.device == "cuda":
            torch.cuda.empty_cache()
    results["all_pass"] = ok
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

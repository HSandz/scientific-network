"""Run a zero-shot extraction encoder over a JSONL of texts (specification §4.2).

Runs inside the ``ops/extract`` environment (CUDA PyTorch, gliner2, gliner), which the
main project environment does not have. Input rows: ``{"id": ..., "text": ...}``.
Output rows: ``{"id", "extractor", "entities": [{text, label, start, end, score}],
"relations": [{head, relation, tail, score}]}`` with character offsets into ``text``.
Entity types, descriptions and thresholds come from a JSON config, so prompts and
thresholds are versioned with the run and tuned on development papers only.

    CUDA_VISIBLE_DEVICES= uv run --project ops/extract python ops/extract/run_encoders.py \
        --extractor gliner2.5-base --config configs/enrichment-v1-encoders.json \
        --input texts.jsonl --output mentions.jsonl --device cpu
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from huggingface_hub import snapshot_download

MODELS = {
    "gliner2.5-base": ("fastino/gliner2.5-base-v1", "07d99c0ba5d15cb3b24e0a236fa99bdd4ef87a5c"),
    "gliner-relex-large": ("knowledgator/gliner-relex-large-v1.0", "4aedc9226a5ac9e2f6b5ea3e91c1ee577c88a290"),
}


def load(name: str, device: str):
    repo, revision = MODELS[name]
    path = snapshot_download(repo, revision=revision)
    if name == "gliner2.5-base":
        from gliner2.joint_ie import JointIE
        model = JointIE.from_pretrained(path, device=device, map_location=device)
    else:
        from gliner import GLiNER
        model = GLiNER.from_pretrained(path).to(device)
    model.eval()
    return model


def find_span(text: str, surface: str, taken: set[int]) -> tuple[int, int] | None:
    low, needle = text.lower(), surface.lower()
    start = low.find(needle)
    while start != -1:
        if start not in taken:
            return start, start + len(needle)
        start = low.find(needle, start + 1)
    return None


def run_gliner25(model, rows: list[dict], cfg: dict) -> list[dict]:
    from gliner2.joint_ie import JointIEConfig
    schema = model.create_schema().entities(cfg["entity_types"])
    for relation, head, tail, _label in cfg["relations"]:
        schema = schema.relation(relation, head, tail)
    schema = schema.no_self_loops()
    options = dict(optimizer="beam", beam_size=32, **cfg.get("gliner2.5-base", {}))
    out = []
    for row in rows:
        result = model.extract(row["text"], schema, config=JointIEConfig(**options)).to_dict()
        by_id = {e["id"]: e for e in result["entities"]}
        entities = []
        for e in result["entities"]:
            start, end = e.get("start"), e.get("end")
            if start is None or end is None:
                span = find_span(row["text"], e["text"], set())
                start, end = span if span else (-1, -1)
            entities.append({"text": e["text"], "label": e["type"], "start": start, "end": end,
                             "score": round(e["confidence"], 4)})
        relations = [{"head": by_id[r["head"]]["text"], "relation": r["type"], "tail": by_id[r["tail"]]["text"],
                      "score": round(r["confidence"], 4)} for r in result["relations"]]
        out.append({"id": row["id"], "extractor": "gliner2.5-base", "entities": entities, "relations": relations})
    return out


def run_relex(model, rows: list[dict], cfg: dict) -> list[dict]:
    label_to_name = {label: name for name, _h, _t, label in cfg["relations"]}
    options = {"threshold": 0.4, "adjacency_threshold": 0.55, "relation_threshold": 0.7, "flat_ner": True,
               **cfg.get("gliner-relex-large", {})}
    out = []
    batch = 8
    for index in range(0, len(rows), batch):
        chunk = rows[index:index + batch]
        with torch.no_grad():
            ents, rels = model.inference(texts=[r["text"] for r in chunk], labels=list(cfg["entity_types"]),
                                         relations=list(label_to_name), return_relations=True, **options)
        for row, te, tr in zip(chunk, ents, rels):
            out.append({
                "id": row["id"], "extractor": "gliner-relex-large",
                "entities": [{"text": e["text"], "label": e["label"], "start": e.get("start", -1),
                              "end": e.get("end", -1), "score": round(e["score"], 4)} for e in te],
                "relations": [{"head": r["head"]["text"], "relation": label_to_name.get(r["relation"], r["relation"]),
                               "tail": r["tail"]["text"], "score": round(r["score"], 4)} for r in tr],
            })
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extractor", choices=list(MODELS), required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--stats", type=Path)
    parser.add_argument("--resume", action="store_true", help="append, skipping ids already in the output")
    parser.add_argument("--chunk", type=int, default=64, help="documents per flushed chunk")
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    with args.input.open(encoding="utf-8") as handle:  # not splitlines(): abstracts may contain U+2028
        rows = [json.loads(line) for line in handle if line.strip()]
    done: set[str] = set()
    if args.resume and args.output.exists():
        with args.output.open(encoding="utf-8") as handle:
            done = {json.loads(line)["id"] for line in handle if line.strip()}
    todo = [row for row in rows if row["id"] not in done]
    started = time.perf_counter()
    model = load(args.extractor, args.device)
    load_s = time.perf_counter() - started
    started = time.perf_counter()
    run = run_gliner25 if args.extractor == "gliner2.5-base" else run_relex
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.output.open("a" if args.resume else "w", encoding="utf-8") as handle:
        for index in range(0, len(todo), args.chunk):
            for record in run(model, todo[index:index + args.chunk], cfg):
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                count += 1
            handle.flush()
            if args.progress:
                print(f"{len(done) + count}/{len(rows)} documents", flush=True)
    run_s = time.perf_counter() - started
    stats = {"extractor": args.extractor, "repo": MODELS[args.extractor][0], "revision": MODELS[args.extractor][1],
             "device": args.device, "torch": torch.__version__, "documents": len(rows), "newly_processed": count, "resumed_from_disk": len(done),
             "load_seconds": round(load_s, 1), "run_seconds": round(run_s, 1),
             "ms_per_document": round(run_s / max(count, 1) * 1000, 1),
             "peak_cuda_mib": round(torch.cuda.max_memory_allocated() / 2**20) if args.device == "cuda" else None}
    if args.stats:
        args.stats.parent.mkdir(parents=True, exist_ok=True)
        args.stats.write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

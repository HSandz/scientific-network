"""Development-set experiment runner for model selection (K1) and threshold tuning.

Runs only on the 100 development papers. Variants scored on the frozen AI-assessed
reference labels: encoder only, SLM only, encoder + SLM verification.
"""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time

from scientific_network.enrich.candidates import merge_entities, merge_relations
from scientific_network.enrich.scoring import score_entities, score_relations
from scientific_network.enrich.slm import slm_extract, slm_relations, slm_relations_text, slm_verify, slm_verify_batch
from scientific_network.rag.llm import LLMClient, LLMConfig


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:  # not splitlines(): abstracts may contain U+2028
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def client_from_config(path: Path, *, log_path: Path | None = None) -> LLMClient:
    data = json.loads(path.read_text(encoding="utf-8"))
    if log_path is not None:
        data["log_path"] = str(log_path)
    return LLMClient(LLMConfig.from_mapping(data))


def encoder_candidates(encoded: dict, text: str, *, entity_threshold: float, relation_threshold: float) -> tuple[list[dict], list[dict]]:
    entities = merge_entities(encoded, text, threshold=entity_threshold)
    relations = merge_relations(encoded, entities, text, threshold=relation_threshold)
    return entities, relations


def run_slm(mode: str, client: LLMClient, texts: list[dict], output: Path, *, encoder_path: Path | None = None,
            entity_threshold: float = 0.3, relation_threshold: float = 0.3, workers: int = 2) -> dict:
    encoded = {r["id"]: r for r in read_jsonl(encoder_path)} if encoder_path else {}

    def one(row: dict) -> dict:
        started = time.perf_counter()
        if mode == "extract":
            result = slm_extract(client, row["text"])
        else:
            entities, relations = encoder_candidates(encoded[row["id"]], row["text"], entity_threshold=entity_threshold,
                                                     relation_threshold=relation_threshold)
            cands = [{"id": e["id"], "text": e["text"], "type": e["type"]} for e in entities]
            if mode == "verify-pairs":
                result = slm_verify_batch(client, row["text"], cands, relations, enumerate_pairs=True)
            elif mode == "verify-gen":
                result = slm_verify_batch(client, row["text"], cands, [])
                rels, pt, ct = slm_relations(client, row["text"], result["entities"], relations)
                result["relations"], result["prompt_tokens"], result["completion_tokens"] = rels, result["prompt_tokens"] + pt, result["completion_tokens"] + ct
            elif mode == "verify-text":
                result = slm_verify_batch(client, row["text"], cands, [])
                rels, pt, ct = slm_relations_text(client, row["text"], result["entities"], relations)
                result["relations"], result["prompt_tokens"], result["completion_tokens"] = rels, result["prompt_tokens"] + pt, result["completion_tokens"] + ct
            elif mode == "verify-batch":
                result = slm_verify_batch(client, row["text"], cands, relations)
            else:
                result = slm_verify(client, row["text"], cands, relations)
            result["candidates"] = len(cands)
        result["id"] = row["id"]
        result["seconds"] = round(time.perf_counter() - started, 2)
        return result

    done: dict[str, dict] = {}
    if output.exists():  # resume: keep finished papers, redo nothing that is already on disk
        with output.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:  # a write cut short by a crash: that paper is redone
                        continue
                    done[record["id"]] = record
    todo = [row for row in texts if row["id"] not in done]
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    with output.open("a", encoding="utf-8") as sink, ThreadPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(one, todo):
            sink.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
            sink.flush()
            done[result["id"]] = result
    wall = time.perf_counter() - started
    results = [done[row["id"]] for row in texts]
    # rewrite in input order so the file is a clean, ordered artifact
    write_jsonl(output, results)
    fresh = [done[row["id"]] for row in todo]
    completion = sum(r["completion_tokens"] for r in fresh)
    return {"mode": mode, "papers": len(results), "resumed_from_disk": len(results) - len(todo),
            "valid_json": sum(r["valid"] for r in results),
            "cache_hits": sum(r["cache_hit"] for r in fresh), "wall_seconds": round(wall, 1),
            "prompt_tokens": sum(r["prompt_tokens"] for r in fresh), "completion_tokens": completion,
            "completion_tokens_per_second_aggregate": round(completion / wall, 1) if wall else None,
            "workers": workers, "output": str(output)}


def predictions_from_slm(results: list[dict]) -> tuple[dict, dict]:
    ents = {r["id"]: [(e["type"], e["text"]) for e in r["entities"]] for r in results}
    rels = {r["id"]: [(x["head"], x["relation"], x["tail"]) for x in r["relations"]] for r in results}
    return ents, rels


def predictions_from_encoder(encoded: list[dict], texts: dict[str, str], *, entity_threshold: float,
                             relation_threshold: float) -> tuple[dict, dict]:
    ents, rels = {}, {}
    for record in encoded:
        entities, relations = encoder_candidates(record, texts[record["id"]], entity_threshold=entity_threshold,
                                                 relation_threshold=relation_threshold)
        ents[record["id"]] = [(e["type"], e["text"]) for e in entities]
        rels[record["id"]] = [(r["head"], r["relation"], r["tail"]) for r in relations]
    return ents, rels


def score_predictions(ents: dict, rels: dict, labels: list[dict], texts: dict[str, str]) -> dict:
    return {"entities_lenient": score_entities(ents, labels, texts), "entities_strict": score_entities(ents, labels, texts, strict=True),
            "relations_lenient": score_relations(rels, labels, texts), "relations_strict": score_relations(rels, labels, texts, strict=True)}


def tune_encoder(encoded: list[dict], labels: list[dict], texts: dict[str, str], *,
                 entity_grid=(0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9), relation_grid=(0.3, 0.5, 0.7, 0.9)) -> dict:
    """Pick thresholds by development micro-F1 (lenient). Development papers only."""
    rows = []
    for et in entity_grid:
        ents, _ = predictions_from_encoder(encoded, texts, entity_threshold=et, relation_threshold=1.1)
        rows.append({"entity_threshold": et, "micro": score_entities(ents, labels, texts)["micro"]})
    best_entity = max(rows, key=lambda r: (r["micro"]["f1"], -r["entity_threshold"]))
    rel_rows = []
    for rt in relation_grid:
        _, rels = predictions_from_encoder(encoded, texts, entity_threshold=0.0, relation_threshold=rt)
        rel_rows.append({"relation_threshold": rt, "micro": score_relations(rels, labels, texts).get("micro")})
    rel_rows = [r for r in rel_rows if r["micro"]]
    best_rel = max(rel_rows, key=lambda r: (r["micro"]["f1"], -r["relation_threshold"])) if rel_rows else None
    return {"entity_grid": rows, "best_entity": best_entity, "relation_grid": rel_rows, "best_relation": best_rel}


def summarize_runs(entries: list[dict]) -> dict:
    """Build the K1 comparison table from run entries.

    Each entry: ``{"name", "model", "variant", "score": <score-dev JSON>, "run": <run-slm stats or None>,
    "gpu_mib": int | None, "total_parameters_b": float, "eligible": bool}``.
    """
    rows = []
    for entry in entries:
        score = entry["score"]
        ent = score["entities_lenient"]
        rel = score["relations_lenient"]
        run = entry.get("run") or {}
        rows.append({
            "name": entry["name"], "model": entry["model"], "variant": entry["variant"],
            "eligible": entry.get("eligible"), "total_parameters_b": entry.get("total_parameters_b"),
            "entity_precision": ent["micro"]["precision"], "entity_recall": ent["micro"]["recall"],
            "entity_f1": ent["micro"]["f1"], "entity_f1_strict": score["entities_strict"]["micro"]["f1"],
            "method_f1": ent["Method"]["f1"], "task_f1": ent["Task"]["f1"], "dataset_f1": ent["Dataset"]["f1"],
            "relation_f1": (rel.get("micro") or {}).get("f1"),
            "relation_f1_strict": (score["relations_strict"].get("micro") or {}).get("f1"),
            "valid_json_rate": (run.get("valid_json", None) / run["papers"]) if run.get("papers") else None,
            "wall_seconds": run.get("wall_seconds"), "completion_tokens_per_second": run.get("completion_tokens_per_second_aggregate"),
            "completion_tokens": run.get("completion_tokens"), "gpu_mib": entry.get("gpu_mib"),
        })
    return {"evaluation_kind": "ai_assessed_reference_labels", "reference": "data/manifests/enrichment-dev-labels-v1",
            "matching": "lenient token-set Jaccard >= 0.5, one-to-one, type-aware (primary); strict = identical normalized string",
            "rows": rows}

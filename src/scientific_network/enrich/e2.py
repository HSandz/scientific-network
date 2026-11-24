"""E2 orchestration: mentions, surface-form merging and the node threshold (specification §4.2 steps 2-5)."""

import json
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np

from scientific_network.enrich.entities import aggregate_entities, merge_surfaces, paper_mentions, paper_relations
from scientific_network.enrich.k1 import read_jsonl, write_jsonl


def embed_surfaces(surfaces: list[dict], workdir: Path, *, device: str = "cuda") -> dict[tuple[str, str], np.ndarray]:
    """Embed each distinct (type, key) surface with all-MiniLM-L6-v2 in the ops/extract environment."""
    rows = [{"id": f"{s['type']}|{s['key']}", "text": s["key"]} for s in surfaces]
    write_jsonl(workdir / "surfaces.jsonl", rows)
    subprocess.run(["uv", "run", "--project", "ops/extract", "python", "ops/extract/embed.py", "--input",
                    str(workdir / "surfaces.jsonl"), "--output", str(workdir / "surface-vectors"), "--device", device], check=True)
    matrix = np.load(workdir / "surface-vectors.npy")
    return {(s["type"], s["key"]): matrix[i] for i, s in enumerate(surfaces)}


def run_extract_entities(texts_path: Path, encoder_path: Path, slm_path: Path, config_path: Path, output_dir: Path,
                         report_path: Path, *, merge_threshold: float, min_papers: int, device: str = "cuda") -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    entity_threshold = config["slm"]["candidate_entity_threshold"]
    baseline_threshold = 0.7
    texts = {r["id"]: r for r in read_jsonl(texts_path)}
    encoded = {r["id"]: r for r in read_jsonl(encoder_path)}
    slm = {r["id"]: r for r in read_jsonl(slm_path)}
    output_dir.mkdir(parents=True, exist_ok=True)
    mentions, relations, invalid = [], [], []
    for paper_id, row in texts.items():
        if paper_id not in slm or not slm[paper_id].get("valid", False):
            invalid.append(paper_id)
            continue
        found = paper_mentions(paper_id, row["text"], encoded[paper_id], slm[paper_id], entity_threshold=entity_threshold,
                               baseline_threshold=baseline_threshold, extractor=config["encoder"]["extractor"],
                               method_version=config["config_version"])
        mentions.extend(found)
        relations.extend(paper_relations(paper_id, row["text"], slm[paper_id], found))
    write_jsonl(output_dir / "mentions.jsonl", mentions)
    write_jsonl(output_dir / "paper-relations.jsonl", relations)
    kept = [m for m in mentions if m["status"] == "kept"]
    surfaces = sorted({(m["type"], m["key"]) for m in kept})
    vectors = embed_surfaces([{"type": t, "key": k} for t, k in surfaces], output_dir, device=device)
    keys_by_type: dict[str, list[str]] = {}
    for entity_type, key in surfaces:
        keys_by_type.setdefault(entity_type, []).append(key)
    merge = merge_surfaces(keys_by_type, vectors, threshold=merge_threshold)
    (output_dir / "merge-map.json").write_text(json.dumps(
        {"threshold": merge_threshold, "pairs": sorted([[a[0], a[1], b[1]] for a, b in merge.items() if a != b])}, ensure_ascii=False))
    aggregated = aggregate_entities(mentions, merge, min_papers=min_papers)
    write_jsonl(output_dir / "entities.jsonl", aggregated["nodes"])
    baseline = [m for m in mentions if m["in_encoder_baseline"]]
    baseline_merge = aggregate_entities(
        [{**m, "status": "kept", "type": m["proposed_type"]} for m in baseline], {}, min_papers=min_papers)
    per_type = Counter(n["type"] for n in aggregated["nodes"])
    report = {
        "config_version": config["config_version"], "papers": len(texts), "papers_without_valid_slm_output": len(invalid),
        "candidate_mentions": len(mentions), "kept_mentions": len(kept),
        "dropped_mentions": len(mentions) - len(kept),
        "drop_reasons": dict(Counter(m["drop_reason"] for m in mentions if m["status"] == "dropped")),
        "retyped_mentions": sum(1 for m in kept if m["retyped_from"]),
        "kept_mentions_by_type": dict(Counter(m["type"] for m in kept)),
        "distinct_surface_forms": len(surfaces), "surface_forms_merged": sum(1 for a, b in merge.items() if a != b),
        "merge_threshold": merge_threshold, "node_threshold_papers": min_papers,
        "entity_groups_before_threshold": aggregated["groups"], "entity_groups_below_threshold": aggregated["below_threshold"],
        "nodes": len(aggregated["nodes"]), "nodes_by_type": dict(per_type),
        "encoder_only_baseline": {"threshold": baseline_threshold, "mentions": len(baseline),
                                  "nodes": len(baseline_merge["nodes"]),
                                  "nodes_by_type": dict(Counter(n["type"] for n in baseline_merge["nodes"]))},
        "paper_relations": len(relations), "paper_relations_same_sentence": sum(1 for r in relations if r["same_sentence"]),
        "outputs": str(output_dir),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    return report

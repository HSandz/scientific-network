"""Enrichment v3: fresh development sample for single-paper ``APPLIED_TO`` and the fresh E4 v3 audit (D042 amendment 2026-11-25).

Everything here excludes material anyone has seen: the 100 enrichment development papers, the 200 test papers and every paper that
appears in a v1 or v2 audit or development sample (found by scanning those files for paper IDs, so no sample can be forgotten).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PAPER_ID = re.compile(r"paper:(?:aaai|ijcai):\d{4}:\d+")
DEV_SEED_V3 = 2026112503
AUDIT_SEED_V3 = 2026112504

SEEN_FILES = (
    "data/manifests/enrichment-splits-v1/development.jsonl", "data/manifests/enrichment-splits-v1/test.jsonl",
    "data/manifests/enrichment-dev-labels-v1/labels.jsonl",
    "reports/enrichment-v1/audit/sample.json", "data/processed/enrichment-audit-v1/items.json",
    "data/processed/enrichment-audit-v2/items.json", "reports/enrichment-v2/audit/sample.json",
    "reports/enrichment-v2/dev/applied-to-informational-labels.jsonl", "reports/enrichment-v2/dev/evaluated-on-dev-labels.jsonl",
    "reports/enrichment-v2/dev/link-dev-labels.jsonl", "reports/enrichment-v2/dev/part-of-dev-labels.jsonl",
    "reports/enrichment-v2/dev/member-of-dev-labels.jsonl",
)


def seen_papers(root: Path = Path(".")) -> dict[str, set[str]]:
    """Paper IDs per source file that anyone has seen (development, test, audit or informational samples)."""
    out = {}
    for name in SEEN_FILES:
        path = root / name
        out[name] = set(PAPER_ID.findall(path.read_text(encoding="utf-8"))) if path.exists() else set()
    return out


def applied_to_candidates(graph: dict) -> list[dict]:
    """Single-paper same-sentence ``APPLIED_TO`` edges of a graph built with the rule switched on."""
    evidence = {e["id"]: e for e in graph["evidence"]}
    nodes = {n["id"]: n for n in graph["nodes"]}
    out = []
    for e in graph["edges"]:
        if e["relation"] == "APPLIED_TO" and e["properties"].get("support_rule") == "single_paper_same_sentence":
            ev = evidence[e["evidence_ids"][0]]
            out.append({"edge_id": e["edge_id"], "source_id": e["source_id"], "target_id": e["target_id"], "paper_id": ev["paper_id"],
                        "head": nodes[e["source_id"]]["name"], "tail": nodes[e["target_id"]]["name"]})
    return sorted(out, key=lambda r: r["edge_id"])


# ---------------------------------------------------------------------------
# Packets

def relation_items_for(graph: dict, texts: dict[str, str], edge_ids: list[str]) -> dict:
    """E4 relation items (the shown paper's title and abstract with the head and tail spans marked) for the given edges."""
    from scientific_network.enrich.quality import item_id, support_text
    nodes = {n["id"]: n for n in graph["nodes"]}
    evidence = {e["id"]: e for e in graph["evidence"]}
    edges = {e["edge_id"]: e for e in graph["edges"]}
    items = {}
    for edge_id in edge_ids:
        e = edges[edge_id]
        ev = evidence[e["evidence_ids"][0]]
        items[item_id("rel", edge_id)] = {
            "item_id": item_id("rel", edge_id), "axis": "relation", "relation": e["relation"],
            "head": f"{nodes[e['source_id']]['name']} ({nodes[e['source_id']]['label']})",
            "tail": f"{nodes[e['target_id']]['name']} ({nodes[e['target_id']]['label']})",
            "papers": [support_text(texts, ev["paper_id"], [ev["head_span"], ev["tail_span"]])]}
    return items


def write_single_packet(items: dict, channel: str, out_dir: Path, name: str) -> dict:
    """One packet holding every item for one channel (D = development labeler); returns its path and SHA-256."""
    from hashlib import sha256
    from scientific_network.enrich.quality import instructions
    ordered = sorted(items.values(), key=lambda i: (i["axis"], i["item_id"]))
    body = {"channel": channel, "shard": 1, "kind": "judgement",
            "instructions": {axis: instructions(axis) for axis in sorted({i["axis"] for i in ordered})},
            "answer_format": {"file": f"answers/{name}.jsonl", "line": {"item_id": "...", "verdict": "correct|incorrect|unclear",
                                                                       "supported_in": "relation items only: integer", "note": "<=20 words"}},
            "items": ordered}
    path = out_dir / "packets" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"path": str(path), "channel": channel, "items": len(ordered), "sha256": sha256(path.read_bytes()).hexdigest()}


def freeze_applied_to_dev(*, candidates_graph_path: Path, texts_path: Path, out_dir: Path, report_dir: Path, size: int = 40, seed: int = DEV_SEED_V3) -> dict:
    """Draw the fresh development sample for single-paper APPLIED_TO (D042 v3 amendment) and write its packet and receipt."""
    from hashlib import sha256
    from scientific_network.enrich.k1 import read_jsonl
    from scientific_network.enrich.quality import draw
    graph = json.loads(candidates_graph_path.read_text(encoding="utf-8"))
    texts = {r["id"]: r["text"] for r in read_jsonl(texts_path)}
    candidates = applied_to_candidates(graph)
    seen = seen_papers()
    seen_all = set().union(*seen.values())
    pool = [c for c in candidates if c["paper_id"] not in seen_all]
    chosen = draw([c["edge_id"] for c in pool], size, seed, "applied_to_dev_v3")
    items = relation_items_for(graph, texts, chosen)
    packet = write_single_packet(items, "D", out_dir, "D-applied-to-dev")
    sample = {"purpose": "fresh development sample for the single-paper same-sentence APPLIED_TO rule, labeled on the E4 relation rubric by a fresh evaluator context (D042 v3 amendment)",
              "seed": seed, "size_requested": size, "candidates_total": len(candidates), "excluded_paper_sources": {k: len(v) for k, v in seen.items()},
              "excluded_papers_total": len(seen_all), "candidates_after_paper_exclusion": len(pool), "sampled": len(chosen), "edge_ids": chosen,
              "candidates_graph_version": graph["graph_version"], "candidates_graph_sha256": sha256(candidates_graph_path.read_bytes()).hexdigest(),
              "packet": {"file": "D-applied-to-dev.json", "sha256": packet["sha256"], "items": packet["items"]},
              "evaluation_kind": "ai_assessed_development_material_not_evidence"}
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "applied-to-dev-sample.json").write_text(json.dumps(sample, indent=1, sort_keys=True), encoding="utf-8")
    (out_dir / "applied-to-dev-items.json").write_text(json.dumps(items, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return sample

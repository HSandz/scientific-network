"""GraphRAG retrieval modes: local search (entity-centric) and global search (map-reduce over reports) (spec §6.2)."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Callable

import numpy as np

from scientific_network.rag.llm import LLMClient, LLMError
from scientific_network.rag.sqlite_vectors import SQLiteVectorStore
from scientific_network.rag.tools import RAGToolset

GLOBAL_MAP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["points"],
    "properties": {
        "points": {
            "type": "array",
            "maxItems": 6,
            "items": {
                "type": "object",
                "required": ["claim", "importance", "paper_ids"],
                "properties": {
                    "claim": {"type": "string"},
                    "importance": {"type": "integer", "minimum": 1, "maximum": 10},
                    "paper_ids": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}


def _pack_within_budget(sections: list[tuple[str, str]], char_budget: int) -> tuple[str, list[str]]:
    packed: list[str] = []
    included_labels: list[str] = []
    used = 0
    for label, text in sections:
        block = f"## {label}\n{text.strip()}\n"
        if used + len(block) > char_budget:
            remaining = char_budget - used
            if remaining > 200:
                packed.append(block[:remaining])
                included_labels.append(label)
            break
        packed.append(block)
        included_labels.append(label)
        used += len(block)
    return "\n".join(packed), included_labels


def local_search(
    query: str,
    *,
    toolset: RAGToolset,
    vector_store: SQLiteVectorStore,
    embed_fn: Callable[[str], np.ndarray],
    char_budget: int = 14000,
    top_reports: int = 4,
    top_entities: int = 6,
    top_chunks: int = 10,
) -> dict[str, Any]:
    """Entity-centric local search: link entities -> k-hop neighborhoods -> related reports + chunks -> budget pack."""
    q_vec = embed_fn(query)
    matched_entities = vector_store.search("entity_description", q_vec, top_k=top_entities)
    matched_reports = vector_store.search("community_report", q_vec, top_k=top_reports)
    matched_chunks = vector_store.search("abstract_chunk", q_vec, top_k=top_chunks)

    # Also run deterministic name/surface entity find over query noun phrases / tokens
    linked_ids: list[str] = []
    for e in matched_entities[:3]:
        linked_ids.append(e["id"])

    # Pull 1-hop neighborhoods for top linked entities
    neighbor_lines: list[str] = []
    subgraph_nodes: dict[str, dict[str, Any]] = {}
    subgraph_edges: list[dict[str, Any]] = []
    paper_ids: list[str] = []

    for eid in linked_ids[:2]:
        nb = toolset.neighbors(eid, limit=15)
        for n in nb.subgraph_nodes:
            subgraph_nodes[n["id"]] = n
        subgraph_edges.extend(nb.subgraph_edges[:15])
        paper_ids.extend(nb.paper_ids)
        for r in nb.rows[:10]:
            neighbor_lines.append(f"- {eid} --[{r['relation']}]--> {r['neighbor_name']} ({r['neighbor_id']}, support={r['support_count']})")

    report_lines = []
    for rep in matched_reports:
        pids = rep.get("metadata", {}).get("paper_ids", [])
        paper_ids.extend(pids)
        report_lines.append(f"- [{rep['id']}] {rep['text']} (papers: {', '.join(pids[:5])})")

    entity_lines = [f"- [{e['id']}] {e['text']}" for e in matched_entities]
    chunk_lines = []
    for c in matched_chunks:
        pid = c.get("metadata", {}).get("paper_id")
        if pid:
            paper_ids.append(pid)
        chunk_lines.append(f"- [{pid}] {c['text']}")

    context, sections_used = _pack_within_budget([
        ("Entity descriptions", "\n".join(entity_lines)),
        ("1-hop graph neighbors", "\n".join(neighbor_lines) or "None"),
        ("Related community reports", "\n".join(report_lines) or "None"),
        ("Abstract sentence chunks", "\n".join(chunk_lines) or "None"),
    ], char_budget)

    return {
        "mode": "local",
        "linked_entity_ids": linked_ids,
        "context": context,
        "sections_used": sections_used,
        "paper_ids": list(dict.fromkeys(paper_ids))[:60],
        "subgraph_nodes": list(subgraph_nodes.values()),
        "subgraph_edges": subgraph_edges,
        "matched_reports": [r["id"] for r in matched_reports],
    }


def global_search(
    query: str,
    *,
    llm: LLMClient,
    reports_path: Path = Path("reports/final-exam/rag-v1/community-reports.json"),
    vector_store: SQLiteVectorStore | None = None,
    embed_fn: Callable[[str], np.ndarray] | None = None,
    top_reports: int = 14,
    batch_size: int = 5,
    prompt_version: str = "rag-global-v1",
) -> dict[str, Any]:
    """Corpus-wide map-reduce over community reports (spec §6.2)."""
    all_reports = json.loads(reports_path.read_text(encoding="utf-8")).get("reports", []) if reports_path.exists() else []
    if not all_reports:
        return {"mode": "global", "answer": "No community reports available.", "points": [], "paper_ids": [], "reports_used": []}

    # Select top relevant reports (preferring L1 research + top N1/N2 by vector similarity if available, else centrality)
    selected: list[dict[str, Any]]
    if vector_store is not None and embed_fn is not None:
        q_vec = embed_fn(query)
        hits = vector_store.search("community_report", q_vec, top_k=top_reports)
        hit_ids = [h["id"] for h in hits]
        by_id = {r["community_id"]: r for r in all_reports}
        selected = [by_id[cid] for cid in hit_ids if cid in by_id]
    else:
        selected = sorted(all_reports, key=lambda r: (-int(r.get("level", 0)), -int(r.get("centrality_rating", 0)), -int(r.get("paper_count", 0))))[:top_reports]

    # Map pass over report batches
    map_points: list[dict[str, Any]] = []
    allowed_pids: set[str] = set()
    for start in range(0, len(selected), batch_size):
        batch = selected[start:start + batch_size]
        for rep in batch:
            for kf in rep.get("key_findings", []):
                allowed_pids.update(kf.get("paper_ids", []))
        user_msg = (
            f"Question: {query}\n\n"
            "Community reports:\n"
            + json.dumps([{
                "community_id": r["community_id"], "network": r["network"], "title": r["title"],
                "summary": r["summary"], "key_findings": r["key_findings"], "paper_count": r["paper_count"],
            } for r in batch], ensure_ascii=False)
        )
        try:
            res = llm.complete(
                prompt_version=f"{prompt_version}-map",
                system="Extract key claims from these community reports relevant to the question. Only use numbers and paper_ids present in the reports.",
                user=user_msg,
                schema=GLOBAL_MAP_SCHEMA,
                schema_name="global_map",
                max_tokens=512,
            )
            if isinstance(res.parsed, dict):
                for pt in res.parsed.get("points", []):
                    clean_pids = [p for p in pt.get("paper_ids", []) if p in allowed_pids]
                    map_points.append({
                        "claim": pt["claim"],
                        "importance": int(pt.get("importance", 5)),
                        "paper_ids": clean_pids,
                    })
        except LLMError:
            continue

    map_points.sort(key=lambda p: -p["importance"])
    top_points = map_points[:12]

    # Reduce pass
    reduce_sys = (
        "Synthesize a clear, concise answer to the question using ONLY the ranked community findings below. "
        "Cite paper IDs in brackets like [paper:...] and only state numbers present in the findings."
    )
    reduce_user = f"Question: {query}\n\nRanked community findings:\n" + json.dumps(top_points, ensure_ascii=False)
    try:
        red = llm.complete(prompt_version=f"{prompt_version}-reduce", system=reduce_sys, user=reduce_user, max_tokens=600)
        answer_text = red.content.strip()
    except LLMError as exc:
        answer_text = f"Global synthesis failed: {exc}"

    cited_pids = [p for pt in top_points for p in pt.get("paper_ids", [])]
    return {
        "mode": "global",
        "answer": answer_text,
        "points": top_points,
        "paper_ids": list(dict.fromkeys(cited_pids))[:40],
        "reports_used": [r["community_id"] for r in selected],
        "ai_generated_label": "AI-generated from graph data",
    }

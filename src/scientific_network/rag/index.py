"""GraphRAG index builder (spec §6.2; D042 amendment 2026-11-25).

Builds:
  1. Research-graph community hierarchy (weighted co-occurrence of Method, Task,
     Dataset, Topic nodes; Level 1 res=1.5 -> 18 super-communities, recursive
     Level 0 res=1.2 -> 148 nested leaves).
  2. Grounded community reports via Qwen3.5-4B from structured graph inputs only,
     validating every cited paper_id and numeric figure (retry once, else drop).
  3. Entity descriptions (Wikipedia leads when linked; AI-generated from mentions
     otherwise).
  4. Embeddings with all-MiniLM-L6-v2 exported to SQLite and Neo4j vector indexes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
import gzip
import json
import os
from pathlib import Path
import re
from typing import Any

from dotenv import load_dotenv
import igraph as ig
import leidenalg
import neo4j
import numpy as np
import yaml

from scientific_network.enrich.load5 import ENRICHED_BOLT_PORT
from scientific_network.rag.llm import LLMClient, LLMConfig, LLMError
from scientific_network.rag.sqlite_vectors import SQLiteVectorStore

REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["title", "summary", "key_findings", "centrality_rating", "centrality_rationale"],
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "key_findings": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "object",
                "required": ["claim", "paper_ids"],
                "properties": {
                    "claim": {"type": "string"},
                    "paper_ids": {"type": "array", "minItems": 1, "maxItems": 4, "items": {"type": "string"}},
                },
            },
        },
        "centrality_rating": {"type": "integer", "minimum": 1, "maximum": 10},
        "centrality_rationale": {"type": "string"},
    },
}

ENTITY_DESC_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["description"],
    "properties": {
        "description": {"type": "string"},
    },
}

_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_:])-?\d+(?:\.\d+)?%?")
_PAPER_ID_RE = re.compile(r"paper:(?:aaai|ijcai):\d{4}:[A-Za-z0-9_.-]+")


def _extract_input_numbers(obj: Any) -> set[float]:
    nums: set[float] = set()
    if isinstance(obj, bool):
        return nums
    if isinstance(obj, (int, float)):
        nums.add(float(obj))
        nums.add(round(float(obj), 1))
        nums.add(round(float(obj), 2))
        nums.add(round(float(obj), 3))
        nums.add(round(float(obj) * 100.0, 1))
        nums.add(round(float(obj) * 100.0, 2))
        return nums
    if isinstance(obj, str):
        # Ignore numbers embedded inside paper/entity IDs
        cleaned = _PAPER_ID_RE.sub(" ", obj)
        cleaned = re.sub(r"\b(?:method|task|dataset|organization|researcher|topic|venue|research|N1|N2):[A-Za-z0-9_:-]+", " ", cleaned)
        for m in _NUMBER_RE.findall(cleaned):
            val_s = m.rstrip("%")
            try:
                v = float(val_s)
            except ValueError:
                continue
            nums.add(v)
        return nums
    if isinstance(obj, list):
        for item in obj:
            nums |= _extract_input_numbers(item)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                for m in _NUMBER_RE.findall(k):
                    try:
                        nums.add(float(m.rstrip("%")))
                    except ValueError:
                        pass
            nums |= _extract_input_numbers(v)
    return nums


def _extract_text_numbers(text: str) -> list[float]:
    cleaned = _PAPER_ID_RE.sub(" ", text)
    cleaned = re.sub(r"\b(?:method|task|dataset|organization|researcher|topic|venue|research|N1|N2):[A-Za-z0-9_:-]+", " ", cleaned)
    # Ignore hyphenated/suffixed model/dataset names and community level markers like L0, L1, L1:3
    cleaned = re.sub(r"\b[A-Za-z]+-\d+\b|\b\d+[Dd]\b|\bL[01](?::\d+)?\b", " ", cleaned)
    out = []
    for m in _NUMBER_RE.findall(cleaned):
        val_s = m.rstrip("%")
        try:
            out.append(float(val_s))
        except ValueError:
            continue
    return out


def validate_report_grounding(
    report: dict[str, Any],
    allowed_paper_ids: set[str],
    input_payload: dict[str, Any],
) -> list[str]:
    """Ensure every cited paper_id and every number in the generated report exists in the structured input."""
    errors: list[str] = []
    cited = [pid for kf in report.get("key_findings", []) for pid in kf.get("paper_ids", [])]
    if not cited:
        errors.append("no paper_ids cited in key_findings")
    bad_pids = [pid for pid in cited if pid not in allowed_paper_ids]
    if bad_pids:
        errors.append(f"ungrounded paper_ids not in input: {bad_pids[:5]}")

    allowed_nums = _extract_input_numbers(input_payload)
    allowed_nums.update({float(report.get("centrality_rating", 0))})
    # Allow integer years from corpus scope 2021..2025 if years are in payload
    text_blob = " ".join([
        str(report.get("title", "")),
        str(report.get("summary", "")),
        str(report.get("centrality_rationale", "")),
        *[str(kf.get("claim", "")) for kf in report.get("key_findings", [])],
    ])
    for val in _extract_text_numbers(text_blob):
        if any(abs(val - a) <= max(0.05, 0.015 * abs(a)) for a in allowed_nums):
            continue
        errors.append(f"ungrounded number {val:g} not present in structured input")
    return errors


def build_research_communities(
    graph: dict[str, Any],
    cfg: dict[str, Any],
    analysis_dir: Path,
) -> dict[str, Any]:
    """Build the 2-level weighted research-graph Leiden hierarchy over Method/Task/Dataset/Topic nodes."""
    rcfg = cfg["communities"]["research_graph"]
    target_labels = set(rcfg["labels"])
    nodes = {n["id"]: n for n in graph["nodes"]}

    # Gather paper -> subject nodes and subject -> papers
    paper_subjects: dict[str, set[str]] = defaultdict(set)
    subject_papers: dict[str, set[str]] = defaultdict(set)
    paper_year: dict[str, int] = {}
    paper_in_cites: Counter = Counter()
    paper_orgs: dict[str, list[str]] = defaultdict(list)

    for nid, n in nodes.items():
        if n["label"] == "Paper" and "year" in (n.get("properties") or {}):
            paper_year[nid] = int(n["properties"]["year"])

    for e in graph["edges"]:
        rel = e["relation"]
        if rel in ("HAS_TOPIC", "USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
            s, t = e["source_id"], e["target_id"]
            if t in nodes and nodes[t]["label"] in target_labels:
                paper_subjects[s].add(t)
                subject_papers[t].add(s)
        elif rel == "CITES":
            paper_in_cites[e["target_id"]] += 1

    for a in graph.get("affiliation_observations", []):
        oid = a["organization_id"]
        if oid in nodes:
            paper_orgs[a["paper_id"]].append(oid)

    # Trend classes map from analysis-v2
    trend_lookup: dict[str, dict[str, Any]] = {}
    for kind in ("topic", "method", "task", "dataset"):
        tp = analysis_dir / "trends" / f"trends-{kind}.csv"
        if tp.exists():
            with tp.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    trend_lookup[row["id"]] = {
                        "class": row["class"],
                        "total_papers": int(row["total_papers"]),
                        "recent_window_papers": int(row["recent_window_papers"]),
                        "base_window_papers": int(row["base_window_papers"]),
                    }

    # Weighted co-occurrence edges between subjects
    pair_w: Counter = Counter()
    for _pid, ss in paper_subjects.items():
        lst = sorted(ss)
        for i, a in enumerate(lst):
            for b in lst[i + 1:]:
                pair_w[(a, b)] += 1

    ids = sorted(subject_papers)
    idx = {v: i for i, v in enumerate(ids)}
    min_w = int(rcfg.get("min_edge_weight", 1))
    edges = [(idx[a], idx[b]) for (a, b), w in pair_w.items() if w >= min_w]
    weights = [w for (_ab, w) in pair_w.items() if w >= min_w]

    g = ig.Graph(n=len(ids), edges=edges, directed=False)
    g.vs["id"] = ids
    g.es["weight"] = weights
    lcc = g.connected_components().giant()
    seed = int(rcfg["seed"])

    l1_part = leidenalg.find_partition(
        lcc,
        leidenalg.RBConfigurationVertexPartition,
        weights="weight",
        resolution_parameter=float(rcfg["level1_resolution"]),
        seed=seed,
        n_iterations=-1,
    )
    l1_counts = Counter(l1_part.membership)
    # Order L1 IDs by descending size
    l1_order = {old: rank for rank, (old, _) in enumerate(sorted(l1_counts.items(), key=lambda x: (-x[1], x[0])))}

    communities_map: dict[str, dict[str, Any]] = {}
    l1_to_l0: dict[str, list[str]] = defaultdict(list)
    l0_counter = 0

    def _build_comm_entry(cid: str, level: int, parent_cid: str | None, member_ids: list[str]) -> dict[str, Any]:
        sorted_members = sorted(
            member_ids,
            key=lambda mid: (-len(subject_papers[mid]), mid),
        )
        member_objs = []
        comm_papers: set[str] = set()
        for mid in sorted_members:
            ps = subject_papers[mid]
            comm_papers |= ps
            tr = trend_lookup.get(mid, {})
            member_objs.append({
                "id": mid,
                "label": nodes[mid]["label"],
                "name": nodes[mid]["name"],
                "papers": len(ps),
                "trend_class": tr.get("class", "unknown"),
                "recent_2024_2025": tr.get("recent_window_papers", 0),
                "base_2021_2022": tr.get("base_window_papers", 0),
            })

        # Rank papers in community by (# matching entities in community, in_corpus_citations, year)
        p_hits = Counter()
        for mid in sorted_members[:25]:
            for pid in subject_papers[mid]:
                p_hits[pid] += 1
        top_paper_ids = sorted(
            comm_papers,
            key=lambda pid: (-p_hits[pid], -paper_in_cites[pid], -paper_year.get(pid, 0), pid),
        )[: int(cfg["reports"]["max_papers_in_input"])]
        top_papers = [
            {
                "id": pid,
                "title": nodes[pid]["name"],
                "year": paper_year.get(pid),
                "in_corpus_citations": int(paper_in_cites[pid]),
            }
            for pid in top_paper_ids
        ]

        org_counts = Counter()
        yr_counts = Counter()
        for pid in comm_papers:
            yr = paper_year.get(pid)
            if yr:
                yr_counts[str(yr)] += 1
            for oid in set(paper_orgs.get(pid, [])):
                org_counts[oid] += 1

        top_orgs = [
            {"id": oid, "name": nodes[oid]["name"], "papers": cnt}
            for oid, cnt in org_counts.most_common(8)
        ]
        kind_counts = Counter(m["label"] for m in member_objs)
        return {
            "community_id": cid,
            "network": "research",
            "level": level,
            "parent_id": parent_cid,
            "size": len(sorted_members),
            "label_counts": dict(kind_counts),
            "paper_count": len(comm_papers),
            "papers_by_year": {str(y): yr_counts.get(str(y), 0) for y in range(2021, 2026)},
            "members": member_objs,
            "top_entities": member_objs[: int(cfg["reports"]["max_entities_in_input"])],
            "top_papers": top_papers,
            "top_organizations": top_orgs,
            "children": [],
        }

    split_min = int(rcfg.get("level0_split_min_size", 25))
    l0_res = float(rcfg["level0_resolution"])

    for old_c1, l1_rank in sorted(l1_order.items(), key=lambda x: x[1]):
        l1_cid = f"research:L1:{l1_rank}"
        vs1 = [i for i, m in enumerate(l1_part.membership) if m == old_c1]
        m_ids1 = [lcc.vs[i]["id"] for i in vs1]
        communities_map[l1_cid] = _build_comm_entry(l1_cid, 1, None, m_ids1)

        if len(vs1) < split_min:
            l0_cid = f"research:L0:{l0_counter}"
            l0_counter += 1
            communities_map[l0_cid] = _build_comm_entry(l0_cid, 0, l1_cid, m_ids1)
            l1_to_l0[l1_cid].append(l0_cid)
        else:
            sub = lcc.induced_subgraph(vs1)
            p0 = leidenalg.find_partition(
                sub,
                leidenalg.RBConfigurationVertexPartition,
                weights="weight",
                resolution_parameter=l0_res,
                seed=seed,
                n_iterations=-1,
            )
            by_c0: dict[int, list[str]] = defaultdict(list)
            for v_idx, c0 in enumerate(p0.membership):
                by_c0[c0].append(sub.vs[v_idx]["id"])
            for _c0, m_ids0 in sorted(by_c0.items(), key=lambda x: (-len(x[1]), x[0])):
                l0_cid = f"research:L0:{l0_counter}"
                l0_counter += 1
                communities_map[l0_cid] = _build_comm_entry(l0_cid, 0, l1_cid, m_ids0)
                l1_to_l0[l1_cid].append(l0_cid)

        communities_map[l1_cid]["children"] = list(l1_to_l0[l1_cid])

    l1_sizes = [c["size"] for c in communities_map.values() if c["level"] == 1]
    l0_sizes = [c["size"] for c in communities_map.values() if c["level"] == 0]
    min_rep = int(rcfg["min_members_for_report"])
    return {
        "graph_version": graph["graph_version"],
        "nodes_total": g.vcount(),
        "edges_total": g.ecount(),
        "lcc_nodes": lcc.vcount(),
        "lcc_edges": lcc.ecount(),
        "seed": seed,
        "level1_resolution": float(rcfg["level1_resolution"]),
        "level0_resolution": l0_res,
        "level1_count": len(l1_sizes),
        "level1_ge_min": sum(1 for s in l1_sizes if s >= min_rep),
        "level0_count": len(l0_sizes),
        "level0_ge_min": sum(1 for s in l0_sizes if s >= min_rep),
        "min_members_for_report": min_rep,
        "level1_sizes": sorted(l1_sizes, reverse=True),
        "level0_sizes_top20": sorted(l0_sizes, reverse=True)[:20],
        "communities": communities_map,
    }


def _collect_n1_n2_communities(graph: dict[str, Any], cfg: dict[str, Any], analysis_dir: Path) -> list[dict[str, Any]]:
    """Package N1 (>=50) and N2 (>=10) S3 communities into structured inputs for report generation."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    paper_year = {n["id"]: int(n["properties"]["year"]) for n in graph["nodes"] if n["label"] == "Paper" and "year" in (n.get("properties") or {})}
    paper_in_cites: Counter = Counter()
    researcher_papers: dict[str, set[str]] = defaultdict(set)
    org_papers: dict[str, set[str]] = defaultdict(set)
    for e in graph["edges"]:
        if e["relation"] == "CITES":
            paper_in_cites[e["target_id"]] += 1
        elif e["relation"] == "AUTHORED":
            researcher_papers[e["source_id"]].add(e["target_id"])
    for a in graph.get("affiliation_observations", []):
        org_papers[a["organization_id"]].add(a["paper_id"])

    entries = []
    for net, min_sz in (("N1", int(cfg["communities"]["n1"]["min_members_for_report"])),
                        ("N2", int(cfg["communities"]["n2"]["min_members_for_report"]))):
        cm_json = json.loads((analysis_dir / "communities" / f"communities-{net}.json").read_text(encoding="utf-8"))
        labels = cm_json.get("labels", {})
        ki = cm_json.get("key_individuals", {})
        by_comm: dict[str, list[str]] = defaultdict(list)
        with gzip.open(analysis_dir / "communities" / f"membership-{net}.csv.gz", "rt", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                by_comm[row["level0"]].append(row["id"])
        for c_str, mids in sorted(by_comm.items(), key=lambda x: (-len(x[1]), int(x[0]))):
            if len(mids) < min_sz:
                continue
            comm_papers: set[str] = set()
            for mid in mids:
                comm_papers |= (researcher_papers[mid] if net == "N1" else org_papers[mid])
            top_pids = sorted(comm_papers, key=lambda p: (-paper_in_cites[p], -paper_year.get(p, 0), p))[: int(cfg["reports"]["max_papers_in_input"])]
            lbl = labels.get(c_str, {})
            k_ind = ki.get(c_str, {})
            hubs = [{"id": i, "name": nodes[i]["name"]} for i in k_ind.get("hubs", [])[:5] if i in nodes]
            brokers = [{"id": i, "name": nodes[i]["name"]} for i in k_ind.get("brokers_participation", [])[:5] if i in nodes]
            entries.append({
                "community_id": f"{net}:{c_str}",
                "network": net,
                "level": 0,
                "size": len(mids),
                "paper_count": len(comm_papers),
                "top_topics": lbl.get("Topic", [])[:5],
                "top_methods": lbl.get("Method", [])[:5],
                "top_tasks": lbl.get("Task", [])[:5],
                "top_organizations": lbl.get("Organization", [])[:5],
                "hubs": hubs,
                "brokers": brokers,
                "top_papers": [{"id": p, "title": nodes[p]["name"], "year": paper_year.get(p), "in_corpus_citations": int(paper_in_cites[p])} for p in top_pids],
            })
    return entries


_REPORT_SYSTEM = (
    "You write concise, grounded community summaries for an AI research knowledge graph (AAAI & IJCAI 2021-2025). "
    "Be brief: 1-2 sentence summary, 2-3 single-sentence key_findings, 1 sentence centrality_rationale. "
    "Use ONLY the structured JSON provided. Every paper_id in key_findings must come verbatim from top_papers. "
    "Every number you write in title, summary, claims, or rationale MUST match a number in the structured JSON. "
    "Do not invent metrics, paper IDs, or external facts. Return strict JSON matching the schema."
)


def generate_community_reports(
    research_comms: dict[str, Any],
    n1_n2_entries: list[dict[str, Any]],
    cfg: dict[str, Any],
    llm: LLMClient,
    *,
    max_reports: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Generate and validate grounded community reports for research L1/L0, N1, and N2 communities."""
    min_res = int(cfg["communities"]["research_graph"]["min_members_for_report"])
    prompt_ver = cfg["reports"]["prompt_version"]
    ai_label = cfg["reports"]["ai_generated_label"]

    inputs: list[dict[str, Any]] = []
    for cid, c in sorted(research_comms["communities"].items(), key=lambda x: (-x[1]["level"], -x[1]["size"], x[0])):
        if c["size"] >= min_res and c["top_papers"]:
            inputs.append({
                "community_id": cid,
                "network": "research",
                "level": c["level"],
                "size": c["size"],
                "paper_count": c["paper_count"],
                "papers_by_year": c["papers_by_year"],
                "top_entities": c["top_entities"],
                "top_organizations": c["top_organizations"],
                "top_papers": c["top_papers"],
            })
    for e in n1_n2_entries:
        if e["top_papers"]:
            inputs.append(e)

    if max_reports is not None:
        inputs = inputs[:max_reports]

    reports: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    stats = {
        "attempted": len(inputs),
        "succeeded_first_try": 0,
        "succeeded_retry": 0,
        "dropped": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "by_network": Counter(),
    }

    for idx_i, payload in enumerate(inputs):
        cid = payload["community_id"]
        allowed_pids = {p["id"] for p in payload["top_papers"]}
        user_msg = "Structured community data:\n" + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        parsed = None
        last_errs: list[str] = []
        used_retry = False
        for attempt_idx in (0, 1):
            pv = prompt_ver if attempt_idx == 0 else f"{prompt_ver}-groundretry"
            msg = user_msg if attempt_idx == 0 else (
                user_msg + f"\n\nYour previous draft failed grounding checks: {'; '.join(last_errs)}. "
                "Fix these errors strictly: cite ONLY paper_ids from top_papers and use ONLY numbers present in the JSON."
            )
            try:
                res = llm.complete(prompt_version=pv, system=_REPORT_SYSTEM, user=msg, schema=REPORT_SCHEMA, schema_name="community_report")
                stats["prompt_tokens"] += res.prompt_tokens
                stats["completion_tokens"] += res.completion_tokens
                cand = res.parsed
                errs = validate_report_grounding(cand, allowed_pids, payload) if isinstance(cand, dict) else ["invalid parsed object"]
                if not errs:
                    parsed = cand
                    used_retry = attempt_idx == 1
                    break
                last_errs = errs
            except LLMError as exc:
                last_errs = [str(exc)]

        if parsed is None:
            stats["dropped"] += 1
            dropped.append({"community_id": cid, "network": payload["network"], "reason": "; ".join(last_errs)})
            continue

        if used_retry:
            stats["succeeded_retry"] += 1
        else:
            stats["succeeded_first_try"] += 1
        stats["by_network"][payload["network"]] += 1

        reports.append({
            "community_id": cid,
            "network": payload["network"],
            "level": payload["level"],
            "size": payload["size"],
            "paper_count": payload["paper_count"],
            "title": parsed["title"],
            "summary": parsed["summary"],
            "key_findings": parsed["key_findings"],
            "centrality_rating": parsed["centrality_rating"],
            "centrality_rationale": parsed["centrality_rationale"],
            "ai_generated_label": ai_label,
            "model": llm.config.model,
            "prompt_version": prompt_ver,
        })
        if (idx_i + 1) % 25 == 0:
            print(f"[rag-reports] {idx_i + 1}/{len(inputs)} ok={len(reports)} dropped={stats['dropped']}", flush=True)

    stats["by_network"] = dict(stats["by_network"])
    stats["dropped_details"] = dropped
    return reports, stats


_ENTITY_SYS = (
    "Write a concise 1-2 sentence technical definition of the given AI research entity based ONLY on the provided "
    "abstract mentions from AAAI/IJCAI papers. Do not invent facts or numbers outside the mentions."
)


def build_entity_descriptions(
    graph: dict[str, Any],
    cfg: dict[str, Any],
    llm: LLMClient | None = None,
    *,
    link_leads_path: Path = Path("data/interim/enrichment-v1/link/link-leads.jsonl"),
    org_wiki_path: Path = Path("data/interim/enrichment-v1/org-wikipedia.json"),
    texts_path: Path = Path("data/interim/enrichment-v1/texts.jsonl"),
    max_llm_entities: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build entity descriptions for Method, Task, Dataset, and Organization nodes."""
    leads: dict[str, str] = {}
    if link_leads_path.exists():
        with link_leads_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rec = json.loads(line)
                    leads[rec["id"]] = rec["text"]

    org_wiki: dict[str, dict[str, Any]] = {}
    if org_wiki_path.exists():
        org_wiki = json.loads(org_wiki_path.read_text(encoding="utf-8"))

    # Paper texts for unlinked entity mentions
    paper_texts: dict[str, str] = {}
    if texts_path.exists():
        with texts_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rec = json.loads(line)
                    paper_texts[rec["id"]] = rec["text"]

    nodes = {n["id"]: n for n in graph["nodes"]}
    node_enrichments = graph.get("node_enrichments") or {}
    entity_papers: dict[str, list[str]] = defaultdict(list)
    entity_topics: dict[str, Counter] = defaultdict(Counter)
    paper_topics: dict[str, list[str]] = defaultdict(list)
    for e in graph["edges"]:
        if e["relation"] == "HAS_TOPIC":
            paper_topics[e["source_id"]].append(nodes[e["target_id"]]["name"])
        elif e["relation"] in ("USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
            entity_papers[e["target_id"]].append(e["source_id"])

    for eid, pids in entity_papers.items():
        for pid in pids:
            entity_topics[eid].update(paper_topics.get(pid, []))

    min_llm_papers = int(cfg["entity_descriptions"]["llm_min_paper_count"])
    ai_label = cfg["entity_descriptions"]["ai_generated_label"]
    prompt_ver = cfg["entity_descriptions"]["prompt_version"]

    descriptions: list[dict[str, Any]] = []
    stats = {"wikipedia_linked": 0, "llm_from_mentions": 0, "template_from_mentions": 0, "llm_failures": 0}
    llm_count = 0

    target_nodes = [n for n in graph["nodes"] if n["label"] in ("Method", "Task", "Dataset", "Organization")]
    target_nodes.sort(key=lambda n: (n["label"], -(n.get("properties") or {}).get("paper_count", 0), n["id"]))

    for n in target_nodes:
        nid, lab, name = n["id"], n["label"], n["name"]
        props = n.get("properties") or {}
        if lab == "Organization":
            ne = node_enrichments.get(nid) or {}
            w_title = ne.get("wikipedia_title") or props.get("wikipedia_title")
            w_url = ne.get("wikipedia_url") or props.get("wikipedia_url")
            w_rev = ne.get("wikipedia_revision_id") or props.get("wikipedia_revision_id")
            wiki_rec = org_wiki.get(w_title) if w_title else None
            if wiki_rec and wiki_rec.get("lead"):
                stats["wikipedia_linked"] += 1
                descriptions.append({
                    "id": nid, "label": lab, "name": name,
                    "description": wiki_rec["lead"][:1200],
                    "source_kind": "wikipedia",
                    "wikipedia_url": wiki_rec.get("url") or w_url,
                    "wikipedia_revision_id": wiki_rec.get("revision_id") or w_rev,
                    "license": "CC BY-SA 4.0",
                    "attribution": "Text from English Wikipedia contributors, licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).",
                    "provenance_label": f"Wikipedia (rev {wiki_rec.get('revision_id') or w_rev}, CC BY-SA 4.0)",
                })
                continue
            sector = props.get("sector") or "unknown sector"
            cc = props.get("country_code") or "unknown country"
            descriptions.append({
                "id": nid, "label": lab, "name": name,
                "description": f"{name} is an organization ({sector}, country code {cc}) appearing in the AAAI/IJCAI 2021-2025 corpus.",
                "source_kind": "template_from_graph_metadata",
                "generation_method": "template",
                "wikipedia_url": w_url,
                "wikipedia_revision_id": w_rev,
                "provenance_label": "Template-generated from graph metadata",
            })
            stats["template_from_mentions"] += 1
            continue

        # Method, Task, Dataset
        if props.get("linked") and props.get("wikipedia_title") in leads:
            w_title = props["wikipedia_title"]
            w_rev = props.get("wikipedia_revision_id")
            w_url = props.get("wikipedia_url")
            stats["wikipedia_linked"] += 1
            descriptions.append({
                "id": nid, "label": lab, "name": name,
                "description": leads[w_title][:1200],
                "source_kind": "wikipedia",
                "wikipedia_url": w_url,
                "wikipedia_revision_id": w_rev,
                "license": "CC BY-SA 4.0",
                "attribution": "Text from English Wikipedia contributors, licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).",
                "provenance_label": f"Wikipedia (rev {w_rev}, CC BY-SA 4.0)",
            })
            continue

        pids = entity_papers.get(nid, [])
        top_topics = [t for t, _c in entity_topics[nid].most_common(3)]
        pc = int(props.get("paper_count") or len(pids))
        # Gather sample mention sentences
        snippets: list[str] = []
        name_l = name.lower()
        for pid in pids[:15]:
            txt = paper_texts.get(pid, "")
            for sent in re.split(r"(?<=[.!?])\s+", txt):
                if name_l in sent.lower() or any(sf.lower() in sent.lower() for sf in list((props.get("surfaces") or {}).keys())[:3]):
                    snippets.append(f"[{pid}] {sent[:260]}")
                    break
            if len(snippets) >= 4:
                break

        desc_text = None
        if llm is not None and pc >= min_llm_papers and snippets and (max_llm_entities is None or llm_count < max_llm_entities):
            llm_count += 1
            user_msg = json.dumps({"entity": name, "type": lab, "paper_count": pc, "mentions": snippets}, ensure_ascii=False)
            try:
                res = llm.complete(prompt_version=prompt_ver, system=_ENTITY_SYS, user=user_msg, schema=ENTITY_DESC_SCHEMA, schema_name="entity_desc", max_tokens=200)
                if isinstance(res.parsed, dict) and res.parsed.get("description"):
                    desc_text = res.parsed["description"]
                    stats["llm_from_mentions"] += 1
            except LLMError:
                stats["llm_failures"] += 1

        if not desc_text:
            stats["template_from_mentions"] += 1
            topic_str = ", ".join(top_topics) if top_topics else "AI research"
            desc_text = f"{name} is a {lab.lower()} entity appearing in {pc} AAAI/IJCAI 2021-2025 papers, primarily in {topic_str}."
            descriptions.append({
                "id": nid, "label": lab, "name": name,
                "description": desc_text,
                "source_kind": "template_from_mentions",
                "generation_method": "template",
                "sample_paper_ids": pids[:5],
                "provenance_label": "Template-generated from graph counts and mentions",
            })
        else:
            descriptions.append({
                "id": nid, "label": lab, "name": name,
                "description": desc_text,
                "source_kind": "llm_from_mentions",
                "generation_method": "llm",
                "model": llm.config.model if llm is not None else None,
                "sample_paper_ids": pids[:5],
                "provenance_label": f"AI-generated (LLM) from paper mentions ({ai_label})",
            })

    return descriptions, stats


def extract_annotated_chunks(
    graph: dict[str, Any],
    *,
    texts_path: Path = Path("data/interim/enrichment-v1/texts.jsonl"),
    max_chunks: int = 12000,
) -> list[dict[str, Any]]:
    """Extract abstract sentences annotated with their Method/Task/Dataset/Topic entities."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    paper_entities: dict[str, list[dict[str, str]]] = defaultdict(list)
    paper_in_cites: Counter = Counter()
    for e in graph["edges"]:
        if e["relation"] in ("USES_METHOD", "ADDRESSES_TASK", "USES_DATASET"):
            t = nodes.get(e["target_id"])
            if t:
                paper_entities[e["source_id"]].append({"id": t["id"], "label": t["label"], "name": t["name"]})
        elif e["relation"] == "CITES":
            paper_in_cites[e["target_id"]] += 1

    if not texts_path.exists():
        return []

    candidates: list[tuple[int, int, str, dict[str, Any]]] = []
    with texts_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rec = json.loads(line)
            pid = rec["id"]
            ents = paper_entities.get(pid)
            if not ents:
                continue
            sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", rec["text"]) if len(s.strip()) >= 30]
            for s_idx, sent in enumerate(sents):
                s_low = sent.lower()
                matched = [e for e in ents if e["name"].lower() in s_low]
                if not matched:
                    continue
                candidates.append((
                    -len(matched),
                    -paper_in_cites[pid],
                    f"{pid}#s{s_idx}",
                    {
                        "id": f"{pid}#s{s_idx}",
                        "paper_id": pid,
                        "year": rec.get("year"),
                        "venue_id": rec.get("venue_id"),
                        "text": sent[:500],
                        "entity_ids": [e["id"] for e in matched],
                        "entity_names": [e["name"] for e in matched],
                    },
                ))
    candidates.sort(key=lambda x: (x[0], x[1], x[2]))
    return [x[3] for x in candidates[:max_chunks]]


def load_neo4j_vector_indexes(
    records: list[dict[str, Any]],
    *,
    dim: int = 384,
    neo4j_uri: str | None = None,
    batch_size: int = 1000,
) -> dict[str, int]:
    """Load RagReport, RagEntityDesc, RagChunk nodes with vector embeddings and create Neo4j vector indexes."""
    load_dotenv(override=False)
    uri = neo4j_uri or os.environ.get("EXPLORER_ENRICHED_NEO4J_URI") or f"bolt://127.0.0.1:{ENRICHED_BOLT_PORT}"
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "")
    if not password:
        raise RuntimeError("NEO4J_PASSWORD is required to load Neo4j vector indexes")

    label_for_kind = {
        "community_report": ("RagReport", "rag_report_vec"),
        "entity_description": ("RagEntityDesc", "rag_entity_vec"),
        "abstract_chunk": ("RagChunk", "rag_chunk_vec"),
    }
    by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        by_kind[rec["kind"]].append({
            "id": rec["id"],
            "text": rec["text"][:1500],
            "metadata_json": json.dumps(rec.get("metadata") or {}, ensure_ascii=False),
            "embedding": [float(x) for x in rec["embedding"]],
        })

    counts: dict[str, int] = {}
    with neo4j.GraphDatabase.driver(uri, auth=(user, password), connection_timeout=15) as driver:
        with driver.session(database=os.environ.get("NEO4J_DATABASE", "neo4j")) as session:
            for kind, (label, index_name) in label_for_kind.items():
                session.run(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE").consume()
                session.run(
                    f"CREATE VECTOR INDEX {index_name} IF NOT EXISTS FOR (n:{label}) ON (n.embedding) "
                    f"OPTIONS {{indexConfig: {{`vector.dimensions`: {dim}, `vector.similarity_function`: 'cosine'}}}}"
                ).consume()
                rows = by_kind.get(kind, [])
                for start in range(0, len(rows), batch_size):
                    session.run(
                        f"UNWIND $rows AS row MERGE (n:{label} {{id: row.id}}) "
                        "SET n.text = row.text, n.metadata_json = row.metadata_json, n.embedding = row.embedding, n.layer = 'rag_index'",
                        rows=rows[start:start + batch_size],
                    ).consume()
                counts[label] = len(rows)
    return counts


def build_full_rag_index(
    config_path: Path,
    *,
    skip_llm: bool = False,
    skip_neo4j: bool = False,
    max_reports: int | None = None,
    max_llm_entities: int | None = None,
) -> dict[str, Any]:
    """End-to-end Phase 3 GraphRAG index build: communities -> reports -> entity descriptions -> embeddings -> SQLite + Neo4j."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    graph = json.loads(Path(cfg["graph"]["path"]).read_text(encoding="utf-8"))
    analysis_dir = Path(cfg["analysis_dir"])

    print("[phase3] building research-graph Leiden hierarchy...", flush=True)
    res_comms = build_research_communities(graph, cfg, analysis_dir)
    (out_dir / "research-communities.json").write_text(json.dumps(res_comms, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[phase3] research L1={res_comms['level1_count']} L0={res_comms['level0_count']} (L0>=5: {res_comms['level0_ge_min']})", flush=True)

    n1_n2 = _collect_n1_n2_communities(graph, cfg, analysis_dir)
    llm_client = None if skip_llm else LLMClient(LLMConfig.from_mapping(cfg["llm"]))

    reports_path = out_dir / "community-reports.json"
    if llm_client is not None:
        print(f"[phase3] generating community reports for {res_comms['level1_ge_min']} L1 + {res_comms['level0_ge_min']} L0 + {len(n1_n2)} N1/N2...", flush=True)
        reports, report_stats = generate_community_reports(res_comms, n1_n2, cfg, llm_client, max_reports=max_reports)
        reports_path.write_text(json.dumps({"reports": reports}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        (out_dir / "report-stats.json").write_text(json.dumps(report_stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        reports = json.loads(reports_path.read_text(encoding="utf-8")).get("reports", []) if reports_path.exists() else []
        report_stats = json.loads((out_dir / "report-stats.json").read_text(encoding="utf-8")) if (out_dir / "report-stats.json").exists() else {}

    print("[phase3] building entity descriptions...", flush=True)
    descs, desc_stats = build_entity_descriptions(graph, cfg, llm_client, max_llm_entities=max_llm_entities)
    (out_dir / "entity-descriptions.json").write_text(json.dumps({"descriptions": descs, "stats": desc_stats}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print("[phase3] extracting annotated abstract chunks...", flush=True)
    chunks = extract_annotated_chunks(graph, max_chunks=int(cfg["embeddings"]["max_chunk_sentences"]))
    vectors_sqlite_path = Path(cfg["vectors_sqlite_path"])
    vectors_sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    (vectors_sqlite_path.parent / "chunks.json").write_text(json.dumps({"chunks": chunks}, ensure_ascii=False) + "\n", encoding="utf-8")

    if llm_client is not None:
        llm_client.close()

    # Build embeddings with all-MiniLM-L6-v2
    print("[phase3] embedding reports, entity descriptions, and chunks...", flush=True)
    from sentence_transformers import SentenceTransformer
    ecfg = cfg["embeddings"]
    model = SentenceTransformer(ecfg["model_name"], device="cpu")

    records: list[dict[str, Any]] = []
    texts_to_encode: list[str] = []
    meta_rows: list[tuple[str, str, str, dict[str, Any]]] = []

    for r in reports:
        txt = f"{r['title']}. {r['summary']} " + " ".join(kf["claim"] for kf in r.get("key_findings", []))
        texts_to_encode.append(txt)
        meta_rows.append(("community_report", r["community_id"], txt, {
            "network": r["network"], "level": r["level"], "title": r["title"],
            "centrality_rating": r["centrality_rating"],
            "paper_ids": [pid for kf in r.get("key_findings", []) for pid in kf.get("paper_ids", [])],
        }))

    for d in descs:
        txt = f"{d['name']} ({d['label']}): {d['description']}"
        texts_to_encode.append(txt)
        meta_rows.append(("entity_description", d["id"], txt, {
            "label": d["label"], "name": d["name"], "source_kind": d["source_kind"],
            "provenance_label": d["provenance_label"],
        }))

    for c in chunks:
        texts_to_encode.append(c["text"])
        meta_rows.append(("abstract_chunk", c["id"], c["text"], {
            "paper_id": c["paper_id"], "year": c.get("year"), "entity_ids": c["entity_ids"],
        }))

    vecs = model.encode(texts_to_encode, batch_size=int(ecfg["batch_size"]), normalize_embeddings=True, show_progress_bar=False)
    for (kind, rid, txt, meta), vec in zip(meta_rows, vecs):
        records.append({"kind": kind, "id": rid, "text": txt, "metadata": meta, "embedding": vec})

    store = SQLiteVectorStore(Path(cfg["vectors_sqlite_path"]))
    sqlite_counts = store.write(records, dim=int(ecfg["dimension"]))

    neo4j_counts: dict[str, int] = {}
    if not skip_neo4j:
        print("[phase3] loading Neo4j vector indexes on 7690...", flush=True)
        neo4j_counts = load_neo4j_vector_indexes(records, dim=int(ecfg["dimension"]))

    summary = {
        "graph_version": graph["graph_version"],
        "research_communities": {"level1": res_comms["level1_count"], "level0": res_comms["level0_count"], "level0_ge_5": res_comms["level0_ge_min"]},
        "report_stats": report_stats,
        "entity_description_stats": desc_stats,
        "chunks_count": len(chunks),
        "sqlite_vector_counts": sqlite_counts,
        "neo4j_vector_counts": neo4j_counts,
    }
    (out_dir / "index-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def load_neo4j_vectors_from_sqlite(config_path: Path) -> dict[str, int]:
    """Load precomputed SQLite vectors into Neo4j 7690 vector indexes."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    store = SQLiteVectorStore(Path(cfg["vectors_sqlite_path"]))
    records: list[dict[str, Any]] = []
    for kind in ("community_report", "entity_description", "abstract_chunk"):
        items, mat = store.load_kind(kind)
        for item, vec in zip(items, mat):
            records.append({**item, "embedding": vec})
    return load_neo4j_vector_indexes(records, dim=int(cfg["embeddings"]["dimension"]))

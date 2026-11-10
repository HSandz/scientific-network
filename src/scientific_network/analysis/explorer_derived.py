"""Deterministic exploratory summaries; never changes a frozen graph or analysis.

Run with explicit input/config/output paths using python -m ...explorer_derived.
"""
from collections import Counter, defaultdict
from hashlib import sha256
import argparse
import json
from pathlib import Path

import yaml


def derive(graph: dict, config: dict) -> dict:
    years = set(config["years"])
    graph = {**graph, "edges": [e for e in graph["edges"] if e.get("validation_status") == "accepted"]}
    nodes = {n["id"]: n for n in graph["nodes"]}
    papers = {i: n for i, n in nodes.items() if n["label"] == "Paper" and n["properties"].get("is_core") and n["properties"].get("year") in years}
    venue, indegree = {}, Counter()
    for e in graph["edges"]:
        if e["relation"] == "PUBLISHED_IN" and e["source_id"] in papers:
            venue[e["source_id"]] = e["target_id"]
        if e["relation"] == "CITES" and e["source_id"] in papers and e["target_id"] in papers:
            indegree[e["target_id"]] += 1
    cohorts = defaultdict(list)
    for pid, paper in papers.items():
        cohorts[(venue.get(pid, "unknown"), paper["properties"]["year"])].append(pid)
    cohort_rows, top_rows = [], []
    for (vid, year), ids in sorted(cohorts.items()):
        distribution = Counter(indegree[i] for i in ids)
        cumulative = 0
        percentiles = {}
        for k, count in sorted(distribution.items()):
            cumulative += count
            percentiles[k] = cumulative / len(ids)
        cohort_rows.append({"venue_id": vid, "year": year, "paper_denominator": len(ids), "zero_in_degree_count": distribution[0], "distribution": [{"in_degree": k, "paper_count": n} for k, n in sorted(distribution.items())]})
        for pid in sorted(ids, key=lambda i: (-indegree[i], i))[:5]:
            top_rows.append({"paper_id": pid, "title": papers[pid]["name"], "venue_id": vid, "year": year, "in_degree": indegree[pid], "cohort_paper_denominator": len(ids), "empirical_percentile_including_ties": percentiles[indegree[pid]]})
    # Deterministic connected-component membership for representative drilldowns.
    researchers = sorted(i for i,n in nodes.items() if n["label"] == "Researcher")
    parent = {i:i for i in researchers}
    degree = Counter()
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for edge in graph["edges"]:
        if edge["relation"] == "COAUTHORED_WITH":
            a,b = edge["source_id"], edge["target_id"]
            if a in parent and b in parent:
                ra,rb = root(a),root(b)
                parent[max(ra,rb)] = min(ra,rb)
                degree.update((a,b))
    groups = defaultdict(list)
    for i in researchers:
        groups[root(i)].append(i)
    component_examples = []
    for members in sorted(groups.values(), key=lambda g: (-len(g),g[0]))[:25]:
        representative = min(members, key=lambda i: (-degree[i], i))
        component_examples.append({"component_id": "component:"+sha256("\n".join(members).encode()).hexdigest()[:16], "size": len(members), "representative_id": representative, "representative": nodes[representative]["name"], "selection": "highest accepted coauthor degree, stable ID tie-break; bounded ego is illustrative"})
    evidence = {e["id"]: e for e in graph["evidence"]}
    topics = defaultdict(set)
    for e in graph["edges"]:
        if e["relation"] == "HAS_TOPIC" and e["source_id"] in papers:
            topics[e["source_id"]].add(e["target_id"])
    pairs = []
    for e in graph["edges"]:
        if e["relation"] != "COLLABORATED_WITH":
            continue
        supports = set()
        for eid in e["evidence_ids"]:
            supports.update(evidence.get(eid, {}).get("support_paper_ids", []))
        supports &= papers.keys()
        pairs.append((e, supports))
    persistence = []
    for e, support in sorted(pairs, key=lambda row: (-len(row[1]), row[0]["edge_id"]))[:config["pair_limit"]]:
        per_year = Counter(papers[pid]["properties"]["year"] for pid in support)
        topic_counts = Counter(t for pid in support for t in topics[pid])
        persistence.append({"edge_id": e["edge_id"], "source_id": e["source_id"], "target_id": e["target_id"], "source": nodes[e["source_id"]]["name"], "target": nodes[e["target_id"]]["name"], "distinct_support_papers": len(support), "active_year_count": len(per_year), "by_year": [{"year": y, "distinct_support_papers": per_year[y]} for y in sorted(years)], "inferred_topics": [{"topic_id": tid, "topic": nodes[tid]["name"], "distinct_support_papers": n} for tid,n in sorted(topic_counts.items(), key=lambda r: (-r[1],r[0]))], "support_paper_ids": sorted(support)})
    return {"component_examples": component_examples, "topic_families": [{"topic_id": e["source_id"], "family_id": e["target_id"], "family": nodes[e["target_id"]]["name"]} for e in graph["edges"] if e["relation"] == "SUBTOPIC_OF"], "citation_cohorts": cohort_rows, "cohort_leaders": top_rows, "organization_pair_persistence": persistence}


def build(graph_path: Path, config_path: Path, output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing existing derived artifact: {output}")
    raw, cfg_raw = graph_path.read_bytes(), config_path.read_bytes()
    graph, config = json.loads(raw), yaml.safe_load(cfg_raw)
    result = {"version": config["version"], "status": config["status"], "method_version": config["method"], "graph_version": graph["graph_version"], "graph_sha256": sha256(raw).hexdigest(), "config_sha256": sha256(cfg_raw).hexdigest(), "method_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "config": config, "definitions": {"citations": "In-degree from accepted in-corpus CITES only; no global or exposure-adjusted influence claim", "percentile": "Empirical CDF within venue/year; ties receive same upper percentile; includes uncited papers", "persistence": "Accepted R8 evidence distinct support papers by year, including zero years; not continuous partnership or employment", "topics": "Raw distinct supported-paper counts per inferred topic, multilabel counts overlap; missing label is unknown", "components": "All researchers including isolates; accepted R7 connected components; largest 25 by size then stable ID, highest-degree representative then ID tie-break; bounded representative Ego is not full membership", "selection": "Top pairs by full-period distinct paper support; exploratory, no independent evaluation"}, **derive(graph, config)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.graph, args.config, args.output)

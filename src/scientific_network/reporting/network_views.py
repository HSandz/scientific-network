"""Bounded, reproducible network drawings from an immutable release graph.

The drawings are selected illustrations, never a new probability sample or the
complete graph. Only public names, identifiers and source pointers are exported.
"""

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import networkx as nx

METHOD = "release-network-views-v1"
SEED = 42
VIEWS = {
    "researchers": ("Researcher", "COAUTHORED_WITH", "researcher_collaboration", 100),
    "organizations": ("Organization", "COLLABORATED_WITH", "organization_collaboration", 60),
    "citations": ("Paper", "CITES", "core_citations", 80),
}
PALETTE = ["#315f48", "#b57b3c", "#6577a0", "#a35e61", "#528e95", "#a18d46", "#8c6aa0", "#71886a"]


def network_payload(graph: dict, analysis: dict, graph_hash: str) -> dict:
    if analysis.get("graph_version") != graph["graph_version"] or analysis.get("input_sha256") != graph_hash:
        raise ValueError("analysis must bind the exact graph version and bytes")
    if any(e.get("validation_status") != "accepted" for e in graph["edges"]):
        raise ValueError("network views require an accepted release graph")
    by_id = {n["id"]: n for n in graph["nodes"]}
    evidence = {e["id"]: e for e in graph["evidence"]}
    paper_sources = {e["source_id"]: e["target_id"] for e in graph["edges"] if e["relation"] == "PUBLISHED_IN"}
    payload = {"method_version": METHOD, "graph_version": graph["graph_version"], "graph_sha256": graph_hash,
               "is_synthetic": graph.get("is_synthetic", False), "layout_seed": SEED,
               "selection": "top nodes by full-projection fractional strength (citations: in-degree), ties by ID; all induced edges",
               "limitation": "Selected illustrations, not a representative sample. Positions have no geographic or quantitative meaning. Filters act only on displayed nodes/edges.",
               "views": {}}
    for key, (label, relation, projection, limit) in VIEWS.items():
        directed = relation == "CITES"
        drawing = nx.DiGraph() if directed else nx.Graph()
        drawing.add_nodes_from(sorted(n["id"] for n in graph["nodes"] if n["label"] == label))
        rows = sorted((e for e in graph["edges"] if e["relation"] == relation), key=lambda e: e["edge_id"])
        for e in rows:
            drawing.add_edge(e["source_id"], e["target_id"], weight=e["properties"].get("fractional_weight", 1.0))
        expected = analysis["projections"][projection]
        if len(drawing) != expected["node_count"] or len(rows) != expected["edge_count"]:
            raise ValueError("projection inventory differs from bound analysis")
        scores = dict(drawing.in_degree()) if directed else dict(drawing.degree(weight="weight"))
        selected = sorted((n for n in drawing if drawing.degree(n) > 0), key=lambda n: (-scores[n], n))[:limit]
        subgraph = drawing.subgraph(sorted(selected)).copy()
        # Insertion order is fixed so layout does not depend on graph serialization.
        positions = nx.spring_layout(subgraph, seed=SEED, iterations=180, weight="weight", scale=1)
        communities = expected.get("communities", [])
        membership = {n: i for i, group in enumerate(communities[0].get("communities", [])) for n in group} if communities else {}
        nodes = []
        for identifier in sorted(selected):
            n = by_id[identifier]
            props = n.get("properties", {})
            group = str(props.get("year", "unknown")) if directed else str(props.get("sector", "unknown")) if label == "Organization" else str(membership.get(identifier, "unknown"))
            url = props.get("official_url") or ("https://openalex.org/" + identifier.rsplit(":", 1)[-1])
            nodes.append({"id": identifier, "name": n["name"], "label": label, "group": group,
                          "score": round(float(scores[identifier]), 8),
                          "year": props.get("year"), "sector": props.get("sector"),
                          "venue": paper_sources.get(identifier), "url": url,
                          "x": round(float(positions[identifier][0]), 8), "y": round(float(positions[identifier][1]), 8)})
        selected_ids = set(selected)
        edges = []
        for e in rows:
            if not {e["source_id"], e["target_id"]} <= selected_ids:
                continue
            records = [evidence[i] for i in e["evidence_ids"]]
            supports = sorted({p for r in records for p in r.get("support_paper_ids", [])})
            public_sources = []
            if directed:
                public_sources = [{"url": r["source_url"], "sha256": r.get("raw_sha256"), "locator": r.get("source_locator")}
                                  for r in records if r.get("source_url", "").startswith(("https://", "http://"))]
            else:
                public_sources = [{"url": by_id[p]["properties"]["official_url"], "paper_id": p}
                                  for p in supports[:3] if by_id[p]["properties"].get("official_url")]
            edges.append({"edge_id": e["edge_id"], "source": e["source_id"], "target": e["target_id"],
                          "relation": relation, "method_version": e["method_version"],
                          "evidence_kind": e["evidence_kind"], "support_count": e["properties"].get("support_count", 1),
                          "fractional_weight": e["properties"].get("fractional_weight"),
                          "evidence_ids": e["evidence_ids"], "source_links": public_sources,
                          "support_links_note": "Up to three paper links shown; support_count describes full accepted support, not independent semantic verification."})
        payload["views"][key] = {"title": {"researchers": "Researcher collaboration", "organizations": "Organization collaboration", "citations": "Within-corpus citations"}[key],
            "relation": relation, "directed": directed, "full_node_count": len(drawing), "full_edge_count": len(rows),
            "node_limit": limit, "nodes": nodes, "edges": edges,
            "score_name": "in-scope citation in-degree" if directed else "fractional collaboration strength",
            "color_meaning": "edition year" if directed else "organization sector" if label == "Organization" else "stored full-projection Louvain community",
            "community_parameters": {k: communities[0][k] for k in ("algorithm", "seed", "resolution") if k in communities[0]} if communities else None,
            "community_color_note": "Researcher communities use a repeating palette; color equality alone does not prove equal community IDs."}
    return payload


def render_network_figures(payload: dict, output_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import textwrap

    captions = []
    for key, view in payload["views"].items():
        g = nx.DiGraph() if view["directed"] else nx.Graph()
        g.add_nodes_from(n["id"] for n in view["nodes"])
        g.add_edges_from((e["source"], e["target"]) for e in view["edges"])
        positions = {n["id"]: (n["x"], n["y"]) for n in view["nodes"]}
        scores = {n["id"]: n["score"] for n in view["nodes"]}
        groups = sorted({n["group"] for n in view["nodes"]})
        colors = {group: PALETTE[i % len(PALETTE)] for i, group in enumerate(groups)}
        figure = plt.figure(figsize=(11, 8.2), facecolor="#fcfcf8")
        axis = figure.add_axes((.025, .20, .72, .63))
        axis.set_facecolor("#fcfcf8")
        nx.draw_networkx_edges(g, positions, ax=axis, edge_color="#8da198", alpha=.28,
                               width=.7, arrows=view["directed"], arrowsize=8, node_size=75)
        nx.draw_networkx_nodes(g, positions, ax=axis, node_color=[colors[n["group"]] for n in view["nodes"]],
                              node_size=[38 + 150 * scores[n["id"]] / max(1, max(scores.values(), default=1)) for n in view["nodes"]],
                              linewidths=.6, edgecolors="white")
        top = sorted(scores, key=lambda n: (-scores[n], n))[:8]
        by_id = {n["id"]: n for n in view["nodes"]}
        for rank, identifier in enumerate(top, 1):
            axis.annotate(str(rank), positions[identifier], xytext=(5, 5), textcoords="offset points", fontsize=8,
                          bbox={"facecolor": "#fcfcf8", "alpha": .9, "edgecolor": "none", "pad": .8})
        figure.text(.055, .94, view["title"], fontsize=18, color="#244635")
        figure.text(.055, .905, f"Selected {len(g):,} nodes · {len(view['edges']):,} induced edges | Full projection {view['full_node_count']:,} nodes · {view['full_edge_count']:,} edges", fontsize=9, color="#65736a")
        figure.text(.765, .82, "HIGHEST FULL-PROJECTION SCORES", fontsize=7, color="#65736a")
        for rank, identifier in enumerate(top, 1):
            name = textwrap.shorten(by_id[identifier]["name"], width=56, placeholder="…")
            figure.text(.765, .79 - (rank - 1) * .074, textwrap.fill(f"{rank}. {name}", 29), fontsize=8, va="top", color="#244635")
        if key != "researchers":
            legend = "   ".join(f"{group}" for group in groups)
            figure.text(.055, .16, "Color groups: " + legend, fontsize=8, color="#65736a")
            for i, group in enumerate(groups):
                figure.text(.055 + i * .18, .135, "● " + group, color=colors[group], fontsize=8)
        axis.margins(.16)
        axis.axis("off")
        caption = f"Top {view['node_limit']} eligible nodes by {view['score_name']}, ties by ID; all induced {view['relation']} edges. Color: {view['color_meaning']}; size: full-projection score. Labels: eight highest scores. Seed {SEED}. Selected illustration, not a representative sample."
        if view["directed"]:
            caption += " Arrows run citing to cited."
        if key == "researchers":
            caption += " Community palette repeats."
        figure.text(.055, .035, textwrap.fill(caption + " Graph " + payload["graph_version"] + ".", 145), fontsize=8, color="#5c6b61", va="bottom")
        figure.savefig(output_dir / f"{key}-network.png", dpi=180)
        plt.close(figure)
        captions.append(f"### {view['title']}\n\n{caption}\n")
        for kind in ("nodes", "edges"):
            with (output_dir / f"{key}-{kind}.csv").open("w", newline="", encoding="utf-8") as stream:
                rows = view[kind]
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["id"])
                writer.writeheader()
                writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()} for row in rows)
    (output_dir / "captions.md").write_text("\n".join(captions), encoding="utf-8")


def generate_network_views(graph_path: Path, analysis_path: Path, freeze_path: Path, output_dir: Path) -> dict:
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("network views require an unused output directory")
    graph_bytes = graph_path.read_bytes()
    digest = sha256(graph_bytes).hexdigest()
    graph, analysis, freeze = json.loads(graph_bytes), json.loads(analysis_path.read_bytes()), json.loads(freeze_path.read_bytes())
    if freeze.get("graph_sha256") != digest or freeze.get("graph_version") != graph["graph_version"]:
        raise ValueError("content freeze does not bind the graph")
    payload = network_payload(graph, analysis, digest)
    payload["inputs"] = {str(p): sha256(p.read_bytes()).hexdigest() for p in (analysis_path, freeze_path)}
    output_dir.mkdir(parents=True)
    (output_dir / "network-views.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    render_network_figures(payload, output_dir)
    receipt = {"method_version": METHOD, "graph_version": graph["graph_version"], "graph_sha256": digest,
               "files": [{"path": str(p), "sha256": sha256(p.read_bytes()).hexdigest()} for p in sorted(output_dir.iterdir())]}
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("graph", "analysis", "freeze", "output-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(generate_network_views(args.graph, args.analysis, args.freeze, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

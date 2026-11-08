"""Render the six Phase 6 figures and accompanying CSV tables."""

import argparse
import csv
import json
from pathlib import Path


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _caption_text(caption: str, graph_version: str) -> str:
    return f"{caption} Graph version: {graph_version}."


def generate_report_figures(analysis_path: Path, output_dir: Path) -> list[Path]:
    """Write PNG/CSV pairs and captions; refuse to overwrite existing artifacts."""
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    if analysis.get("is_synthetic") or not isinstance(analysis.get("release_metrics"), dict):
        raise ValueError("figures require a non-synthetic analysis artifact with release metrics")
    metrics = analysis["release_metrics"]
    graph_version = analysis["graph_version"]
    expected = [
        "researcher-degree-ccdf.png", "researcher-degree-ccdf.csv",
        "component-sizes.png", "component-sizes.csv",
        "community-topic-profiles.png", "community-topic-profiles.csv",
        "sector-mixing.png", "sector-mixing.csv",
        "topic-trends.png", "topic-trends.csv",
        "top-cited-papers.png", "top-cited-papers.csv",
        "captions.md",
    ]
    if output_dir.exists() and any((output_dir / name).exists() for name in expected):
        raise ValueError("one or more figure outputs already exist; choose a new output directory")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("figure generation requires the analysis extra (matplotlib)") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    captions = []

    def save_figure(name: str, title: str, caption: str, draw, *, figsize=(10, 5.8)) -> None:
        caption_full = _caption_text(caption, graph_version)
        figure, axis = plt.subplots(figsize=figsize)
        draw(axis)
        axis.set_title(title, fontsize=13, pad=12)
        figure.text(0.01, 0.015, caption_full, ha="left", va="bottom", fontsize=7, wrap=True)
        figure.tight_layout(rect=(0, 0.12, 1, 0.96))
        path = output_dir / name
        figure.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(figure)
        captions.append(f"### {title}\n\n{caption_full}\n")

    ccdf = metrics["researcher_degree_ccdf"]["rows"]
    _write_csv(output_dir / "researcher-degree-ccdf.csv", ccdf)

    def draw_ccdf(axis):
        rows = [row for row in ccdf if row["degree"] > 0 and row["fraction_at_least"] > 0]
        axis.step([row["degree"] for row in rows], [row["fraction_at_least"] for row in rows], where="post")
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Distinct coauthors (degree, log scale)")
        axis.set_ylabel("Fraction of researchers with degree ≥ k (log scale)")
        axis.grid(True, which="both", alpha=0.25)

    save_figure(
        "researcher-degree-ccdf.png", "Researcher collaboration degree CCDF",
        "Projection: Researcher–COAUTHORED_WITH–Researcher. Filter: all accepted base graph edges. Counting: unique coauthor neighbors; denominator includes all resolved researchers, including isolates.",
        draw_ccdf,
    )

    sizes = metrics["researcher_component_sizes"]["sizes_descending"]
    component_rows = [{"component_rank": rank, "researcher_count": size} for rank, size in enumerate(sizes, 1)]
    _write_csv(output_dir / "component-sizes.csv", component_rows)

    def draw_components(axis):
        ranks = [row["component_rank"] for row in component_rows]
        values = [row["researcher_count"] for row in component_rows]
        axis.scatter(ranks, values, s=14, color="#167d9a", alpha=0.8)
        axis.set_yscale("log")
        axis.set_xlabel("Component rank (largest first)")
        axis.set_ylabel("Researchers in component (log scale)")
        axis.grid(True, axis="y", alpha=0.25)

    save_figure(
        "component-sizes.png", "Researcher collaboration component sizes",
        "Projection: Researcher–COAUTHORED_WITH–Researcher. Filter: all accepted base graph edges. Counting: connected components over all resolved researchers, including isolates.",
        draw_components,
    )

    community_rows = []
    for profile in metrics["bridge_researchers"]["community_topic_profiles_top_20_by_size"]:
        for topic in profile["top_topics"]:
            community_rows.append({
                "community_id": profile["community_id"],
                "community_member_count": profile["member_count"],
                "community_paper_count": profile["paper_count"],
                "topic_labeled_paper_count": profile["topic_labeled_paper_count"],
                "topic_id": topic["topic_id"],
                "topic": topic["topic"],
                "topic_paper_count": topic["paper_count"],
                "fractional_paper_count": topic["fractional_paper_count"],
                "topic_share": topic["share_of_fractional_topic_mass"],
            })
    _write_csv(output_dir / "community-topic-profiles.csv", community_rows)

    def draw_communities(axis):
        if not community_rows:
            axis.text(0.5, 0.5, "No topic-labeled communities", ha="center", va="center")
            axis.set_axis_off()
            return
        community_ids = list(dict.fromkeys(row["community_id"] for row in community_rows))[:12]
        visible_rows = [row for row in community_rows if row["community_id"] in set(community_ids)]
        topic_mass = {}
        for row in visible_rows:
            topic_mass[row["topic"]] = topic_mass.get(row["topic"], 0.0) + row["fractional_paper_count"]
        topic_names = [topic for topic, _ in sorted(topic_mass.items(), key=lambda item: (-item[1], item[0]))[:10]]
        matrix = [[0.0 for _ in topic_names] for _ in community_ids]
        community_index = {value: index for index, value in enumerate(community_ids)}
        topic_index = {value: index for index, value in enumerate(topic_names)}
        for row in visible_rows:
            if row["topic"] in topic_index:
                matrix[community_index[row["community_id"]]][topic_index[row["topic"]]] = row["topic_share"]
        image = axis.imshow(matrix, aspect="auto", cmap="YlGnBu", vmin=0)
        axis.set_yticks(range(len(community_ids)), [
            f"C{key.rsplit(':', 1)[-1]} (n={next(row['community_member_count'] for row in visible_rows if row['community_id'] == key):,})"
            for key in community_ids
        ])
        axis.set_xticks(range(len(topic_names)), topic_names, rotation=40, ha="right", fontsize=8)
        axis.set_ylabel("Top communities by researcher count")
        axis.figure.colorbar(image, ax=axis, label="Fractional topic share")

    partition = metrics["bridge_researchers"]["community_topic_partition"]
    save_figure(
        "community-topic-profiles.png", "Topic profiles of largest researcher communities",
        f"Projection: Researcher–COAUTHORED_WITH–Researcher, Louvain seed {partition.get('seed')} and resolution {partition.get('resolution')}. Filter: all accepted base graph edges; topics are inferred HAS_TOPIC labels. Counting: distinct papers per community, each fractionally allocated across its labels; top 12 communities are plotted, selected from the top 20 by membership.",
        draw_communities,
        figsize=(12, 7.5),
    )

    sector_data = metrics["sector_mixing"]
    sector_rows = sector_data["matrix"]
    _write_csv(output_dir / "sector-mixing.csv", sector_rows)

    def draw_sector(axis):
        categories = sector_data["categories"]
        values = [[0 for _ in categories] for _ in categories]
        index = {category: pos for pos, category in enumerate(categories)}
        for row in sector_rows:
            values[index[row["row_sector"]]][index[row["column_sector"]]] = row["pair_paper_support_count"]
        image = axis.imshow(values, cmap="Blues")
        axis.set_xticks(range(len(categories)), categories, rotation=35, ha="right")
        axis.set_yticks(range(len(categories)), categories)
        axis.set_xlabel("Partner sector")
        axis.set_ylabel("Organization sector")
        for row in range(len(categories)):
            for col in range(len(categories)):
                axis.text(col, row, f"{values[row][col]:,}", ha="center", va="center", fontsize=8)
        axis.figure.colorbar(image, ax=axis, label="Pair–paper supports")

    save_figure(
        "sector-mixing.png", "Organization collaboration by sector",
        "Projection: Organization–COLLABORATED_WITH–Organization. Filter: all accepted base R8 edges. Counting: distinct organization-pair by core-paper supports; the matrix is symmetric and includes unknown sector.",
        draw_sector,
    )

    topic_rows = metrics["topic_shares_by_year_venue"]["rows"]
    by_year_topic = {}
    labeled_denominators = {}
    for row in topic_rows:
        key = (row["year"], row["venue_id"])
        labeled_denominators[key] = row["labeled_paper_count"]
        aggregate = by_year_topic.setdefault((row["year"], row["topic_id"]), {
            "year": row["year"], "topic_id": row["topic_id"], "topic": row["topic"], "fractional_paper_count": 0.0,
        })
        aggregate["fractional_paper_count"] += row["fractional_paper_count"]
    year_denominator = {}
    for (year, _venue_id), count in labeled_denominators.items():
        year_denominator[year] = year_denominator.get(year, 0) + count
    trend_rows = []
    for (year, _topic_id), row in sorted(by_year_topic.items()):
        denominator = year_denominator.get(year, 0)
        trend_rows.append({
            **row,
            "fractional_paper_count": round(row["fractional_paper_count"], 12),
            "labeled_paper_denominator": denominator,
            "fractional_topic_share": round(row["fractional_paper_count"] / denominator, 12) if denominator else 0.0,
        })
    _write_csv(output_dir / "topic-trends.csv", trend_rows)

    def draw_topics(axis):
        totals = {}
        for row in trend_rows:
            totals[row["topic"]] = totals.get(row["topic"], 0.0) + row["fractional_paper_count"]
        selected = [topic for topic, _ in sorted(totals.items(), key=lambda item: (-item[1], item[0]))[:8]]
        for topic in selected:
            values = [next((row["fractional_topic_share"] for row in trend_rows if row["topic"] == topic and row["year"] == year), 0.0) for year in range(2021, 2026)]
            axis.plot(range(2021, 2026), values, marker="o", linewidth=1.8, label=topic)
        axis.set_xticks(range(2021, 2026))
        axis.set_xlabel("Proceedings year")
        axis.set_ylabel("Share of fractional topic mass")
        axis.grid(True, alpha=0.25)
        axis.legend(fontsize=7, ncol=2)

    save_figure(
        "topic-trends.png", "Inferred topic portfolio trends, 2021–2025",
        "Projection: core Paper–HAS_TOPIC–Topic. Filter: core papers in AAAI and IJCAI, 2021–2025; inferred labels remain pending review. Counting: each labeled paper contributes 1/k to each of k labels; shares normalize over labeled papers across both venues in each year. Lines show the eight largest topics by fractional mass.",
        draw_topics,
    )

    cited = metrics["cited_papers"]["top_by_in_degree"]
    cited_rows = [{"rank": rank, **row} for rank, row in enumerate(cited, 1)]
    _write_csv(output_dir / "top-cited-papers.csv", cited_rows)

    def draw_cited(axis):
        rows = cited[:15]
        labels = [f"{row['title'][:75]}" for row in rows][::-1]
        values = [row["in_degree"] for row in rows][::-1]
        axis.barh(labels, values, color="#ba5d2b")
        axis.set_xlabel("In-scope citing papers (in-degree)")
        axis.tick_params(axis="y", labelsize=7)
        axis.grid(True, axis="x", alpha=0.25)

    save_figure(
        "top-cited-papers.png", "Most cited papers within the release corpus",
        "Projection: directed core Paper–CITES–Paper, citing to cited. Filter: both endpoints are in-scope core papers. Counting: distinct in-scope citing papers (in-degree); citations outside the release corpus are excluded and older papers have more exposure time.",
        draw_cited,
    )

    captions_path = output_dir / "captions.md"
    captions_path.write_text(
        "# Phase 6 figure captions\n\n" + "\n".join(captions), encoding="utf-8"
    )
    return [output_dir / name for name in expected]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    outputs = generate_report_figures(args.analysis, args.output_dir)
    print(json.dumps({"status": "written", "files": [str(path) for path in outputs]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

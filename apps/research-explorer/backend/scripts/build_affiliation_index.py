"""Build the organization -> papers index from the per-paper affiliation triples.

An organization's papers are the papers on which an author listed it, taken from the
``affiliation_observations`` of the frozen release graph (v5 carries them unchanged). The
researcher-level AFFILIATED_WITH edge must not be used for this: it would credit an
organization with every paper of anyone ever affiliated with it. Neo4j does not hold the
triples, so the API reads this small derived file. The input graph is only read.

    uv run python apps/research-explorer/backend/scripts/build_affiliation_index.py \
        --graph data/processed/release-graph-v4/graph.json \
        --output data/processed/navigator-affiliations-v1/index.json.gz
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def build(graph_path: Path) -> dict:
    raw = graph_path.read_bytes()
    graph = json.loads(raw)
    organizations: dict[str, set[str]] = defaultdict(set)
    for obs in graph["affiliation_observations"]:
        organizations[obs["organization_id"]].add(obs["paper_id"])
    return {
        "method": "affiliation-observation-triples",
        "source_graph_version": graph["graph_version"],
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "observations": len(graph["affiliation_observations"]),
        "organizations": {org: sorted(papers) for org, papers in sorted(organizations.items())},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    index = build(args.graph)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.output, "wt", encoding="utf-8") as handle:
        json.dump(index, handle, separators=(",", ":"))
    print(f"{index['observations']} triples, {len(index['organizations'])} organizations -> {args.output}")


if __name__ == "__main__":
    main()

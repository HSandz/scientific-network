"""Read-only entity connections through shared papers (specification §4.3 note, 2026-11-25).

The extracted APPLIED_TO and EVALUATED_ON edges are sparse under the frozen relation rule, so the application answers method-task,
method-dataset and task-dataset questions from papers that carry both entities through the paper-level edges USES_METHOD,
ADDRESSES_TASK and USES_DATASET. The evidence of a connection is its shared papers. Nothing here writes to the graph or adds a predicate.
"""

from __future__ import annotations

from collections import Counter, defaultdict

PAPER_EDGES = {"USES_METHOD": "Method", "ADDRESSES_TASK": "Task", "USES_DATASET": "Dataset"}
TYPE_PAIRS = (("Method", "Task"), ("Method", "Dataset"), ("Task", "Dataset"))
THRESHOLDS = (1, 2, 3, 5)


class CooccurrenceIndex:
    """Paper -> entities index built from a graph dict (nodes, edges) or a list of rows from Neo4j."""

    def __init__(self, nodes: list[dict], edges: list[dict]) -> None:
        self.nodes = {n["id"]: n for n in nodes}
        self.entities_by_paper: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        self.papers_by_entity: dict[str, set[str]] = defaultdict(set)
        for edge in edges:
            kind = PAPER_EDGES.get(edge["relation"])
            if kind is None or edge.get("validation_status", "accepted") != "accepted":
                continue
            self.entities_by_paper[edge["source_id"]][kind].add(edge["target_id"])
            self.papers_by_entity[edge["target_id"]].add(edge["source_id"])

    @classmethod
    def from_graph(cls, graph: dict) -> "CooccurrenceIndex":
        return cls(graph["nodes"], graph["edges"])

    def year(self, paper_id: str) -> int | None:
        node = self.nodes.get(paper_id) or {}
        return (node.get("properties") or {}).get("year")

    def partners(self, entity_id: str, partner_type: str, min_papers: int = 1, limit: int | None = 50) -> list[dict]:
        """Entities of ``partner_type`` that share papers with ``entity_id``, with the shared-paper evidence."""
        shared: dict[str, list[str]] = defaultdict(list)
        for paper in sorted(self.papers_by_entity.get(entity_id, ())):
            for partner in self.entities_by_paper[paper].get(partner_type, ()):
                if partner != entity_id:
                    shared[partner].append(paper)
        rows = [{"entity_id": partner, "name": (self.nodes.get(partner) or {}).get("name"), "shared_papers": len(papers),
                 "years": sorted(y for y in map(self.year, papers) if y is not None), "paper_ids": papers}
                for partner, papers in shared.items() if len(papers) >= min_papers]
        rows.sort(key=lambda r: (-r["shared_papers"], r["name"] or "", r["entity_id"]))
        return rows[:limit] if limit else rows

    def pair_counts(self, type_a: str, type_b: str) -> Counter:
        """Distinct-paper count per (entity of type_a, entity of type_b) pair."""
        counts: Counter = Counter()
        for types in self.entities_by_paper.values():
            for a in types.get(type_a, ()):
                for b in types.get(type_b, ()):
                    counts[(a, b)] += 1
        return counts


def distribution(index: CooccurrenceIndex, top: int = 20) -> dict:
    """Measured co-occurrence distribution per type pair, the top pairs by count, and partner availability for Methods and Tasks."""
    report = {"definition": "pairs of entities that appear together in the paper-level edges of the same paper; counts are distinct papers",
              "thresholds": list(THRESHOLDS), "by_type_pair": {}}
    partner_ready = {}
    for type_a, type_b in TYPE_PAIRS:
        counts = index.pair_counts(type_a, type_b)
        report["by_type_pair"][f"{type_a}-{type_b}"] = {
            "pairs_at_least": {str(t): sum(1 for c in counts.values() if c >= t) for t in THRESHOLDS},
            "top_pairs": [{"a": index.nodes[a]["name"], "a_id": a, "b": index.nodes[b]["name"], "b_id": b, "shared_papers": c}
                          for (a, b), c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]]}
        partner_ready[(type_a, type_b)] = ({a for (a, _), c in counts.items() if c >= 2}, {b for (_, b), c in counts.items() if c >= 2},
                                           {a for (a, _) in counts}, {b for (_, b) in counts})
    nodes_by_type = Counter(n["label"] for n in index.nodes.values() if n["label"] in {"Method", "Task", "Dataset"})
    method_with_task = partner_ready[("Method", "Task")][0]
    task_with_method = partner_ready[("Method", "Task")][1]
    report["entities_with_a_partner_at_2_papers"] = {
        "Method_with_a_Task": {"count": len(method_with_task), "of": nodes_by_type["Method"]},
        "Task_with_a_Method": {"count": len(task_with_method), "of": nodes_by_type["Task"]},
        "Method_with_a_Dataset": {"count": len(partner_ready[("Method", "Dataset")][0]), "of": nodes_by_type["Method"]},
        "Task_with_a_Dataset": {"count": len(partner_ready[("Task", "Dataset")][0]), "of": nodes_by_type["Task"]}}
    report["entities_with_a_partner_at_1_paper"] = {
        "Method_with_a_Task": {"count": len(partner_ready[("Method", "Task")][2]), "of": nodes_by_type["Method"]},
        "Task_with_a_Method": {"count": len(partner_ready[("Method", "Task")][3]), "of": nodes_by_type["Task"]},
        "Method_with_a_Dataset": {"count": len(partner_ready[("Method", "Dataset")][2]), "of": nodes_by_type["Method"]},
        "Task_with_a_Dataset": {"count": len(partner_ready[("Task", "Dataset")][2]), "of": nodes_by_type["Task"]}}
    report["papers_with_both"] = {f"{a}-{b}": sum(1 for t in index.entities_by_paper.values() if t.get(a) and t.get(b)) for a, b in TYPE_PAIRS}
    return report

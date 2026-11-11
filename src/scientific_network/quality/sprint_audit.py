"""Bounded relation-stratified diagnostic draw; no pooled accuracy estimator."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from scientific_network.evaluation.edge_audit import _sample_ids
from scientific_network.evaluation.precision import precision_interval

METHOD = "sprint-relation-audit-release-v1"
SEED = 2026111107


def draw(edges: list[dict], per_relation: int = 8) -> tuple[list[dict], dict]:
    """Equal allocation within accepted relation frames, stable under reordering."""
    if per_relation < 1:
        raise ValueError("per_relation must be positive")
    groups = defaultdict(list)
    seen = set()
    for edge in edges:
        if edge["edge_id"] in seen:
            raise ValueError("duplicate semantic edge ID")
        seen.add(edge["edge_id"])
        if edge["validation_status"] == "accepted":
            groups[edge["relation"]].append(edge)
    selected, strata = [], {}
    for relation, rows in sorted(groups.items()):
        ids = set(_sample_ids([r["edge_id"] for r in rows], per_relation, SEED, relation))
        selected.extend(r for r in rows if r["edge_id"] in ids)
        strata[relation] = {"population": len(rows), "sample": len(ids),
                            "inclusion_probability": len(ids) / len(rows),
                            "census": len(ids) == len(rows)}
    return sorted(selected, key=lambda r: r["edge_id"]), strata


def human_subset(sample: list[dict]) -> tuple[list[str], list[str]]:
    """Freeze 20 SRS cases from the audit sample plus 6 separate risk cases."""
    random_ids = _sample_ids([r["edge_id"] for r in sample], 20, SEED, "human-random")
    candidates = [r for r in sample if r["edge_id"] not in random_ids and r["relation"] in
                  {"HAS_TOPIC", "RESEARCHES_TOPIC", "COLLABORATED_WITH", "AFFILIATED_WITH"}]
    diagnostic = _sample_ids([r["edge_id"] for r in candidates], 6, SEED, "human-risk")
    return random_ids, diagnostic


def summarize(sample: list[dict], reviews: list[dict]) -> dict:
    """Require exactly one actual AI judgment per frozen unit; keep unknowns."""
    expected = {r["edge_id"]: r["relation"] for r in sample}
    seen, counts = set(), defaultdict(lambda: defaultdict(int))
    for row in reviews:
        eid = row["edge_id"]
        if eid not in expected or eid in seen or row["relation"] != expected[eid]:
            raise ValueError("review has duplicate, out-of-frame or mismatched relation")
        if row["decision"] not in {"supported", "unsupported", "unknown"}:
            raise ValueError("invalid review decision")
        if (row.get("reviewer_kind") != "ai" or row.get("reviewer_model") != "gpt-6-luna"
                or row.get("reasoning_effort") != "high" or not row.get("reason")):
            raise ValueError("missing actual AI provenance or evidence explanation")
        if row["decision"] == "supported" and (not row.get("evidence_ids") or not row.get("source_locators")):
            raise ValueError("supported verdict requires evidence and locators")
        seen.add(eid)
        counts[row["relation"]][row["decision"]] += 1
    if seen != expected.keys():
        raise ValueError("incomplete frozen sample reviews")
    per_relation = {}
    for relation, values in sorted(counts.items()):
        interval = precision_interval(values.get("supported", 0), sum(values.values()))
        per_relation[relation] = {d: values.get(d, 0) for d in ("supported", "unsupported", "unknown")}
        per_relation[relation]["conditional_wilson_95"] = {
            "lower": interval["wilson_lower"], "upper": interval["wilson_upper"]}
    return {"evaluation_kind": "ai_agent_review", "human_validation": "not_performed",
            "reviewer_independence": "not_established", "pooled_accuracy": None,
            "per_relation": per_relation}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(graph_path: Path, works_path: Path, output: Path) -> dict:
    """Prepare inspectable cache-backed witnesses without changing frozen inputs."""
    import csv
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from scientific_network.contracts import GraphArtifact
    from scientific_network.evaluation.edge_audit import SPLIT_FIELDS
    from scientific_network.evaluation.review_sheet import SheetContext, render_html
    if output.exists() or output.is_symlink():
        raise ValueError("output exists; use an unused versioned directory")
    graph = GraphArtifact.model_validate_json(graph_path.read_bytes())
    sample, strata = draw([e.model_dump(mode='json') for e in graph.edges])
    random_ids, risk_ids = human_subset(sample)
    context = SheetContext(graph)
    works = {w['paper_id']: w for w in map(json.loads, works_path.open())}
    output.mkdir(parents=True)
    def write(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    write('edge-sample.json', sample)
    packets, human = [], []
    for row in sample:
        edge = context.edges_by_id[row['edge_id']]
        desc, links = context.describe(edge)
        papers = context.papers_for(edge)
        if row['relation'] == 'CITES':
            papers = list(dict.fromkeys(papers + [row['target_id']]))
        witnesses = [works[p] for p in papers if p in works]
        support_ids = {s for i in edge.evidence_ids for s in context.evidence[i].support_edge_ids}
        support = [context.edges_by_id[s].model_dump(mode='json') for s in sorted(support_ids)
                   if context.edges_by_id[s].source_id in papers or context.edges_by_id[s].target_id in papers]
        packets.append({'edge': row, 'subject': context.nodes[edge.source_id].model_dump(mode='json'),
                        'object': context.nodes[edge.target_id].model_dump(mode='json'), 'context': desc,
                        'source_links': links, 'evidence': [context.evidence[i].model_dump(mode='json') for i in edge.evidence_ids],
                        'support_base_edges': support, 'paper_witnesses': witnesses,
                        'affiliation_observations': [o.model_dump(mode='json') for p in papers
                                                     for o in context.paper_observations[p]]})
        if edge.edge_id in random_ids + risk_ids:
            # Existing sheet vocabulary: correct/incorrect/unverifiable; the
            # separate AI ledger uses supported/unsupported/unknown.
            desc['correct_when'] = {
                'AUTHORED': 'Compatible official positional byline and stable OpenAlex author ID on the matched work; identity errors remain possible.',
                'AFFILIATED_WITH': 'Exact paper authorship maps this researcher to this institution, with raw affiliation-string evidence.',
                'CITES': 'Cached source work referenced_works contains the uniquely matched in-scope target work ID.',
            }.get(row['relation'], desc['correct_when'])
            subset = 'random' if edge.edge_id in random_ids else 'diagnostic'
            desc['also_show'] = f"Human subset: {subset}. " + desc.get('also_show', '')
            review = {k: '' for k in SPLIT_FIELDS}
            review.update({'audit_id': METHOD, 'graph_version': graph.graph_version,
                           'graph_sha256': digest(graph_path), 'edge_id': edge.edge_id,
                           'reviewer_id': 'member-1'})
            review.update(desc)
            human.append({'review': review, 'context': desc, 'links': links})
    write('human-allocation.json', {'random_ids': random_ids, 'random_conditional_probability': 20 / len(sample),
                                   'diagnostic_ids': risk_ids, 'diagnostic_is_probability_sample': False,
                                   'human_metrics': None})
    # Both members independently inspect the same small packet; no completed answers.
    for member in ('member-1', 'member-2'):
        rows = [{**r, 'review': {**r['review'], 'reviewer_id': member}} for r in human]
        with (output / f'human-{member}.csv').open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=SPLIT_FIELDS, extrasaction='ignore')
            writer.writeheader(); writer.writerows(r['review'] for r in rows)
        (output / f'human-{member}.html').write_text(render_html(
            {'graph_version': graph.graph_version, 'audit_id': METHOD, 'reviewer_ids': [member]}, SPLIT_FIELDS, rows))
    for index in range(2):
        (output / f'edges-{index+1}.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in packets[index::2]))
    manifest = {'method': METHOD, 'seed': SEED, 'graph_version': graph.graph_version,
                'graph_sha256': digest(graph_path), 'works_sha256': digest(works_path),
                'strata': strata, 'sample_sha256': digest(output / 'edge-sample.json'),
                'prepared_at': datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(),
                'human_validation': 'not_performed', 'pooled_accuracy': None,
                'witness_limit': 3, 'reviewer_independence': 'not_established',
                'source_overlap': 'construction caches',
                'artifact_hashes': {p.name: digest(p) for p in sorted(output.iterdir())}}
    write('manifest.json', manifest)
    return manifest


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph', type=Path, required=True)
    parser.add_argument('--works', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.graph, args.works, args.output), indent=2))


if __name__ == '__main__':
    main()

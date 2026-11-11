"""Bounded relation-stratified diagnostic draw; no pooled accuracy estimator."""
from collections import defaultdict
import hashlib
import html
import json
from pathlib import Path

from scientific_network.evaluation.edge_audit import _sample_ids
from scientific_network.evaluation.precision import precision_interval

METHOD = "sprint-relation-audit-release-v1"
SEED = 2026111107
HUMAN_PACKET_ID = f"{METHOD}-human-packet-v2"


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


def human_selection(sample: list[dict], flagged_ids: list[str]) -> dict:
    """Add flagged cases while preserving the original random and risk selections."""
    random_ids, risk_ids = human_subset(sample)
    sample_ids = [row["edge_id"] for row in sample]
    sample_set = set(sample_ids)
    if len(flagged_ids) != len(set(flagged_ids)):
        raise ValueError("flagged issue ledger contains duplicate edge IDs")
    missing = set(flagged_ids) - sample_set
    if missing:
        raise ValueError("flagged issue edge is outside the frozen sample: " + ", ".join(sorted(missing)))
    flagged = [edge_id for edge_id in flagged_ids if edge_id in sample_set]
    tags = {}
    for edge_id in sample_ids:
        values = []
        if edge_id in random_ids:
            values.append("random")
        if edge_id in risk_ids:
            values.append("risk_diagnostic")
        if edge_id in flagged:
            values.append("flagged_diagnostic")
        if values:
            tags[edge_id] = values
    selected = [edge_id for edge_id in sample_ids if edge_id in tags]
    flagged_random = len(set(flagged) & set(random_ids))
    flagged_risk = len(set(flagged) & set(risk_ids))
    return {
        "random_ids": random_ids,
        "diagnostic_ids": risk_ids,
        "flagged_diagnostic_ids": flagged,
        "selection_tags": tags,
        "unique_review_ids": selected,
        "probability_sample_ids": random_ids,
        "diagnostic_only_ids": [edge_id for edge_id in selected if edge_id not in random_ids],
        "selection_summary": {
            "random_total": len(random_ids),
            "random_flagged_overlap": flagged_random,
            "risk_total": len(risk_ids),
            "risk_flagged_overlap": flagged_risk,
            "flagged_total": len(flagged),
            "unique_total": len(selected),
        },
    }


def _read_issues(path: Path, sample: list[dict]) -> list[dict]:
    issues = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(issues, list) or any(not isinstance(issue, dict) or not issue.get("edge_id") for issue in issues):
        raise ValueError("issues input must be a list of records with edge_id")
    human_selection(sample, [str(issue["edge_id"]) for issue in issues])
    return issues


def _postblind_html(member: str, flagged_issues: list[dict], packet_by_id: dict[str, dict]) -> str:
    """Render Luna's source locators and concerns separately from initial answers."""
    cards = []
    for issue in flagged_issues:
        edge_id = str(issue["edge_id"])
        packet = packet_by_id[edge_id]
        potential_issue = str(issue.get("potential_issue") or "").strip()
        concern = potential_issue or str(issue.get("reason") or "").strip() or "No concise concern supplied."
        locators = []
        for locator in issue.get("source_locators", []):
            text = str(locator)
            source = text.split(" @ ", 1)[0]
            if source.startswith(("https://", "http://")):
                locators.append(f'<li><a href="{html.escape(source, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(text)}</a></li>')
            else:
                locators.append(f"<li>{html.escape(text)}</li>")
        links = "\n".join(locators) or "<li>No source locators recorded.</li>"
        context = packet["context"].get("supporting_context", "")
        cards.append(
            '<article><h2>' + html.escape(str(issue.get("relation", ""))) + " · "
            + html.escape(packet["context"].get("source_name", "")) + " → "
            + html.escape(packet["context"].get("target_name", "")) + "</h2>"
            + '<p class="id">' + html.escape(edge_id) + "</p>"
            + '<p><strong>Luna\'s concern (AI-assessed; not a human finding):</strong> '
            + html.escape(concern) + "</p>"
            + '<p><strong>Source locators from the AI review ledger:</strong></p><ul>' + links + "</ul>"
            + '<details><summary>Full source and support context shown in the initial packet</summary><pre>'
            + html.escape(context) + "</pre></details></article>"
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Post-blind flagged diagnostics</title><style>'
        ':root{font:15px/1.5 system-ui,sans-serif;color:#1d2327;background:#fafaf7}body{max-width:900px;margin:24px auto;padding:0 16px}'
        'article{background:#fff;border:1px solid #d9dde1;border-radius:8px;padding:16px;margin:16px 0}'
        'a{overflow-wrap:anywhere;color:#1b5fa8}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}'
        '.id{font:11px ui-monospace,monospace;overflow-wrap:anywhere;color:#5d6670}'
        '</style></head><body><h1>Post-blind flagged diagnostics</h1>'
        f'<p>For {html.escape(member)}. Open only after recording and exporting the initial review decisions. '
        'The following are AI-assessed concerns, not human findings or independent verification. '
        'The initial packet contains the source evidence without these concerns.</p>'
        + "\n".join(cards) + "</body></html>\n"
    )


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


def prepare(graph_path: Path, works_path: Path, issues_path: Path, output: Path) -> dict:
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
    issues = _read_issues(issues_path, sample)
    selection = human_selection(sample, [str(issue["edge_id"]) for issue in issues])
    random_ids = selection["random_ids"]
    risk_ids = selection["diagnostic_ids"]
    flagged_ids = selection["flagged_diagnostic_ids"]
    context = SheetContext(graph)
    works = {w['paper_id']: w for w in map(json.loads, works_path.open())}
    output.mkdir(parents=True)
    def write(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    write('edge-sample.json', sample)
    packets, human = [], []
    packet_by_id = {}
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
        if edge.edge_id in selection['unique_review_ids']:
            tags = selection['selection_tags'][edge.edge_id]
            human_context = {**desc, 'selection_tags': tags,
                             'also_show': 'Selection tags: ' + ', '.join(tags) + '. ' + desc['also_show']}
            review = {k: '' for k in SPLIT_FIELDS}
            review.update({'audit_id': HUMAN_PACKET_ID, 'graph_version': graph.graph_version,
                           'graph_sha256': digest(graph_path), 'edge_id': edge.edge_id,
                           'reviewer_id': 'member-1'})
            review.update(human_context)
            packet_row = {'review': review, 'context': human_context, 'links': links}
            human.append(packet_row)
            packet_by_id[edge.edge_id] = packet_row
    flagged_issues = [issue for issue in issues if issue['edge_id'] in set(flagged_ids)]
    allocation = {
        **selection,
        'random_conditional_probability': len(random_ids) / len(sample),
        'diagnostic_is_probability_sample': False,
        'flagged_diagnostic_is_probability_sample': False,
        'flagged_source': str(issues_path),
        'probability_sample_ids': selection['probability_sample_ids'],
        'diagnostic_only_ids': selection['diagnostic_only_ids'],
        'reviewer_ids': ['member-1', 'member-2'],
        'reviewer_case_ids': {
            'member-1': selection['unique_review_ids'],
            'member-2': selection['unique_review_ids'],
        },
        'initial_answers': 'blank',
        'human_metrics': None,
    }
    write('human-allocation.json', allocation)
    # Both members independently inspect the same small packet; no completed answers.
    for member in ('member-1', 'member-2'):
        rows = [{**r, 'review': {**r['review'], 'reviewer_id': member}} for r in human]
        with (output / f'human-{member}.csv').open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=SPLIT_FIELDS, extrasaction='ignore')
            writer.writeheader(); writer.writerows(r['review'] for r in rows)
        (output / f'human-{member}.html').write_text(render_html(
            {'graph_version': graph.graph_version, 'audit_id': HUMAN_PACKET_ID, 'reviewer_ids': [member],
             'selection_summary': selection['selection_summary'],
             'postblind_diagnostic_available': bool(flagged_issues),
             'packet_note': 'This packet has a prespecified random subset, the prior risk-diagnostic subset, and all cases listed in the existing AI issue ledger. Overlapping cases appear once and retain every selection tag. Only the random tag carries probability-based inclusion.'},
            SPLIT_FIELDS, rows))
        (output / f'human-{member}-flagged-post-blind.html').write_text(
            _postblind_html(member, flagged_issues, packet_by_id))
    for index in range(2):
        (output / f'edges-{index+1}.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in packets[index::2]))
    manifest = {'method': METHOD, 'seed': SEED, 'graph_version': graph.graph_version,
                'graph_sha256': digest(graph_path), 'works_sha256': digest(works_path),
                'strata': strata, 'sample_sha256': digest(output / 'edge-sample.json'),
                'prepared_at': datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(),
                'human_validation': 'not_performed', 'pooled_accuracy': None,
                'witness_limit': 3, 'reviewer_independence': 'not_established',
                'source_overlap': 'construction caches', 'issues_sha256': digest(issues_path),
                'human_packet_id': HUMAN_PACKET_ID, 'human_selection': allocation,
                'artifact_hashes': {p.name: digest(p) for p in sorted(output.iterdir())}}
    write('manifest.json', manifest)
    return manifest


def update_sampling_manifest(path: Path, allocation: dict, issues_path: Path,
                             packet_root: Path, sample_sha256: str) -> dict:
    """Append the human packet v2 receipt without changing frozen sample fields."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for field, allocation_field in (("human_random_ids", "random_ids"), ("human_diagnostic_ids", "diagnostic_ids")):
        if manifest.get(field) != allocation[allocation_field]:
            raise ValueError(f"existing frozen {field} differs from regenerated selection")
    if manifest.get("human_random_conditional_probability") != allocation["random_conditional_probability"]:
        raise ValueError("existing random inclusion probability differs from regenerated selection")
    if manifest.get("sample_sha256") != sample_sha256:
        raise ValueError("generated edge sample differs from the frozen sample")
    files = [f"human-{member}.{suffix}" for member in allocation["reviewer_ids"] for suffix in ("csv", "html")]
    files += ["human-allocation.json"]
    files += [f"human-{member}-flagged-post-blind.html" for member in allocation["reviewer_ids"]]
    manifest["human_flagged_diagnostic_ids"] = allocation["flagged_diagnostic_ids"]
    manifest["human_flagged_diagnostic_probability_sample"] = False
    manifest["human_packet_v2"] = {
        "audit_id": HUMAN_PACKET_ID,
        "issues_source": str(issues_path),
        "issues_sha256": digest(issues_path),
        "unique_review_ids": allocation["unique_review_ids"],
        "unique_review_count": len(allocation["unique_review_ids"]),
        "selection_tags": allocation["selection_tags"],
        "probability_sample_ids": allocation["probability_sample_ids"],
        "diagnostic_only_ids": allocation["diagnostic_only_ids"],
        "reviewer_case_ids": allocation["reviewer_case_ids"],
        "initial_answers": allocation["initial_answers"],
        "human_validation": "not_performed",
        "packet_sha256": {name: digest(packet_root / name) for name in files},
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph', type=Path, required=True)
    parser.add_argument('--works', type=Path, required=True)
    parser.add_argument('--issues', type=Path, required=True,
                        help='authoritative AI-flagged edge ledger (issues.json)')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sampling-manifest', type=Path,
                        help='existing frozen manifest to extend with the supplemental packet receipt')
    args = parser.parse_args()
    prepared = prepare(args.graph, args.works, args.issues, args.output)
    if args.sampling_manifest:
        allocation = json.loads((args.output / 'human-allocation.json').read_text(encoding='utf-8'))
        prepared['updated_sampling_manifest'] = update_sampling_manifest(
            args.sampling_manifest, allocation, args.issues, args.output, prepared['sample_sha256'])
    print(json.dumps(prepared, indent=2))


if __name__ == '__main__':
    main()
